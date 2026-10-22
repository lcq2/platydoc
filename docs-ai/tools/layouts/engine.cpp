// SPDX-License-Identifier: GPL-2.0-only
// The same Clang frontend entry point is compiled for the host and WebAssembly.
#include "clang/AST/ASTConsumer.h"
#include "clang/AST/ASTContext.h"
#include "clang/AST/Decl.h"
#include "clang/AST/Attr.h"
#include "clang/AST/Expr.h"
#include "clang/AST/TypeLoc.h"
#include "clang/AST/RecordLayout.h"
#include "clang/AST/RecursiveASTVisitor.h"
#include "clang/Basic/Diagnostic.h"
#include "clang/Basic/SourceManager.h"
#include "clang/Basic/TargetInfo.h"
#include "clang/Basic/Version.h"
#include "clang/Driver/Compilation.h"
#include "clang/Driver/Driver.h"
#include "clang/Driver/Job.h"
#include "clang/Frontend/CompilerInstance.h"
#include "clang/Frontend/CompilerInvocation.h"
#include "clang/Frontend/FrontendAction.h"
#include "clang/Lex/Lexer.h"
#include "clang/Lex/PPCallbacks.h"
#include "clang/Lex/Preprocessor.h"
#include "llvm/ADT/StringExtras.h"
#include "llvm/Support/JSON.h"
#include "llvm/Support/MemoryBuffer.h"
#include "llvm/Support/SHA256.h"
#include "llvm/Support/VirtualFileSystem.h"
#include "llvm/Support/raw_ostream.h"
#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <memory>
#include <map>
#include <set>
#include <string>
#include <vector>

#ifndef LAYOUT_LLVM_REVISION
#error "The build must identify the pinned LLVM revision"
#endif

using namespace clang;
namespace json = llvm::json;

namespace {
constexpr size_t MaxRequestBytes = 64 * 1024 * 1024;

json::Object location(SourceLocation loc, const SourceManager &sm) {
  loc = sm.getFileLoc(loc);
  if (loc.isInvalid()) return {};
  return json::Object{{"file", sm.getFilename(loc).str()},
          {"line", sm.getSpellingLineNumber(loc)},
          {"column", sm.getSpellingColumnNumber(loc)},
          {"offset_bytes", sm.getFileOffset(loc)}};
}

// Identities contain source bytes, physical paths, scopes and complete macro
// frames; names, AST ordinals, configurations and raw SourceLocations are absent.
class Identities {
  SourceManager &sm;
  const std::map<std::string, std::string> &paths;
  std::map<std::string, std::string> hashes;
  std::string barePointKey(SourceLocation loc) {
    if (loc.isInvalid()) return "invalid";
    loc = sm.getFileLoc(loc);
    auto path = sm.getFilename(loc).str();
    auto found = paths.find(path);
    const auto &physical = found == paths.end() ? path : found->second;
    return std::to_string(physical.size()) + ":" + physical + ":" + hash(loc) + ":" +
           std::to_string(sm.getFileOffset(loc));
  }
  std::string pointKey(SourceLocation loc) {
    if (loc.isInvalid()) return "invalid";
    loc = sm.getFileLoc(loc);
    std::string result = barePointKey(loc);
    SourceLocation include = sm.getIncludeLoc(sm.getFileID(loc));
    while (include.isValid()) {
      result += "|via:" + barePointKey(include);
      include = sm.getIncludeLoc(sm.getFileID(sm.getFileLoc(include)));
    }
    return result;
  }
  std::string anchorKey(SourceLocation loc) {
    SourceLocation spelling = sm.getSpellingLoc(loc);
    std::string result = pointKey(spelling);
    while (loc.isMacroID()) {
      auto range = sm.getImmediateExpansionRange(loc);
      result += "|begin:" + pointKey(sm.getSpellingLoc(range.getBegin())) +
                "|end:" + pointKey(sm.getSpellingLoc(range.getEnd())) +
                "|caller:" + pointKey(sm.getFileLoc(loc));
      loc = sm.getImmediateMacroCallerLoc(loc);
    }
    SourceLocation include = sm.getIncludeLoc(sm.getFileID(spelling));
    while (include.isValid()) {
      result += "|include:" + pointKey(include);
      include = sm.getIncludeLoc(sm.getFileID(sm.getFileLoc(include)));
    }
    return result;
  }
public:
  std::set<const RecordDecl *> records;
  std::set<const TypedefNameDecl *> aliases;
  Identities(SourceManager &sm, const std::map<std::string, std::string> &paths)
      : sm(sm), paths(paths) {}
  std::string hash(SourceLocation loc) {
    loc = sm.getFileLoc(loc);
    auto path = sm.getFilename(loc).str();
    auto found = hashes.find(path);
    if (found != hashes.end()) return found->second;
    llvm::SHA256 digest;
    digest.update(sm.getBufferData(sm.getFileID(loc)));
    return hashes[path] = llvm::toHex(digest.final(), true);
  }
  json::Object barePoint(SourceLocation loc) {
    if (loc.isInvalid()) return {};
    loc = sm.getFileLoc(loc);
    auto result = location(loc, sm);
    auto path = sm.getFilename(loc).str();
    auto found = paths.find(path);
    result["source_path"] = found == paths.end() ? path : found->second;
    result["sha256"] = hash(loc);
    if (sm.isWrittenInScratchSpace(loc) || path.empty() || path.front() == '<')
      result["unsupported"] = true;
    return result;
  }
  json::Object point(SourceLocation loc) {
    auto result = barePoint(loc);
    json::Array sites;
    if (loc.isValid()) {
      SourceLocation include = sm.getIncludeLoc(sm.getFileID(sm.getFileLoc(loc)));
      while (include.isValid()) {
        sites.push_back(barePoint(include));
        include = sm.getIncludeLoc(sm.getFileID(sm.getFileLoc(include)));
      }
    }
    result["include_sites"] = std::move(sites);
    return result;
  }
  json::Object anchor(SourceLocation loc) {
    if (loc.isInvalid()) return json::Object{{"unsupported", true}};
    SourceLocation spelling = sm.getSpellingLoc(loc);
    json::Object result{{"spelling", point(spelling)}};
    json::Array frames;
    while (loc.isMacroID()) {
      auto range = sm.getImmediateExpansionRange(loc);
      frames.push_back(json::Object{
          {"begin", point(sm.getSpellingLoc(range.getBegin()))},
          {"end", point(sm.getSpellingLoc(range.getEnd()))},
          {"caller", point(sm.getFileLoc(loc))}});
      loc = sm.getImmediateMacroCallerLoc(loc);
    }
    result["expansions"] = std::move(frames);
    json::Array includes;
    SourceLocation include = sm.getIncludeLoc(sm.getFileID(spelling));
    while (include.isValid()) {
      includes.push_back(point(include));
      include = sm.getIncludeLoc(sm.getFileID(sm.getFileLoc(include)));
    }
    result["includes"] = std::move(includes);
    return result;
  }
  std::string id(const Decl *decl) {
    if (const auto *record = dyn_cast<RecordDecl>(decl)) {
      if (const auto *definition = record->getDefinition()) decl = definition;
      else decl = record->getCanonicalDecl();
    }
    std::string key = std::string(decl->getDeclKindName()) + "|" + anchorKey(decl->getLocation());
    for (const DeclContext *scope = decl->getLexicalDeclContext();
         scope && !scope->isTranslationUnit(); scope = scope->getLexicalParent()) {
      const auto *owner = Decl::castFromDeclContext(scope);
      key += "|scope:" + std::string(owner->getDeclKindName()) + ":" + anchorKey(owner->getLocation());
    }
    llvm::SHA256 digest;
    digest.update(key);
    return "decl-v1:" + llvm::toHex(digest.final(), true);
  }
  json::Object declaration(const NamedDecl *decl, llvm::StringRef kind) {
    json::Array scopes;
    for (const DeclContext *scope = decl->getLexicalDeclContext();
         scope && !scope->isTranslationUnit(); scope = scope->getLexicalParent()) {
      const auto *owner = Decl::castFromDeclContext(scope);
      scopes.push_back(json::Object{{"kind", owner->getDeclKindName()},
                                    {"source", anchor(owner->getLocation())}});
    }
    return json::Object{{"id", id(decl)}, {"kind", kind.str()}, {"ast_kind", decl->getDeclKindName()},
        {"name", decl->getNameAsString()}, {"source", anchor(decl->getLocation())},
        {"scope", std::move(scopes)}};
  }
};

class Diagnostics final : public DiagnosticConsumer {
public:
  json::Array entries;
  bool error = false;

  void HandleDiagnostic(DiagnosticsEngine::Level level,
                        const Diagnostic &info) override {
    DiagnosticConsumer::HandleDiagnostic(level, info);
    error |= level >= DiagnosticsEngine::Error;
    llvm::SmallString<256> message;
    info.FormatDiagnostic(message);
    const char *severity = level >= DiagnosticsEngine::Fatal ? "fatal" :
        level >= DiagnosticsEngine::Error ? "error" :
        level == DiagnosticsEngine::Warning ? "warning" : "note";
    json::Object entry{{"severity", severity}, {"message", message.str().str()},
                       {"id", info.getID()}};
    if (info.hasSourceManager())
      entry["location"] = location(info.getLocation(), info.getSourceManager());
    entries.push_back(std::move(entry));
  }
};

json::Object typeInfo(QualType type, ASTContext &context, Identities &identity) {
  json::Object result{{"spelling", type.getAsString()}};
  json::Array aliasIDs;
  QualType desugared = type;
  while (true) {
    if (const auto *alias = dyn_cast<TypedefType>(desugared.getTypePtr())) {
      identity.aliases.insert(alias->getDecl());
      aliasIDs.push_back(identity.id(alias->getDecl()));
      desugared = alias->getDecl()->getUnderlyingType();
    } else {
      QualType next = desugared.getSingleStepDesugaredType(context);
      if (next == desugared) break;
      desugared = next;
    }
  }
  result["aliases"] = std::move(aliasIDs);
  if (const auto *array = context.getAsArrayType(type)) {
    result["kind"] = "array";
    result["element"] = typeInfo(array->getElementType(), context, identity);
    if (const auto *constant = dyn_cast<ConstantArrayType>(array)) {
      // JSON's integer domain is signed 64-bit. Reject larger bounds rather
      // than truncate an APInt. Such a type is not useful in this prototype.
      if (constant->getSize().getActiveBits() > 63)
        result["unsupported"] = "array bound exceeds the protocol integer domain";
      else
        result["count"] = static_cast<int64_t>(constant->getSize().getZExtValue());
    } else {
      result["count"] = nullptr;
    }
    result["flexible"] = type->isIncompleteArrayType();
  } else if (const auto *record = type->getAs<RecordType>()) {
    result["kind"] = "record";
    const RecordDecl *decl = record->getDecl();
    if (const auto *definition = decl->getDefinition()) decl = definition;
    identity.records.insert(decl);
    result["record_id"] = identity.id(decl);
  } else {
    result["kind"] = type->isPointerType() ? "pointer" : "scalar";
    if (type->isPointerType()) result["pointee"] = typeInfo(type->getPointeeType(), context, identity);
  }
  if (!type->isIncompleteType() && !type->isFunctionType()) {
    result["size_bits"] = static_cast<int64_t>(context.getTypeSize(type));
    result["alignment_bits"] = static_cast<int64_t>(context.getTypeAlign(type));
  } else {
    result["size_bits"] = nullptr;
    result["alignment_bits"] = nullptr;
  }
  return result;
}

struct DependencyEvidence {
  bool enabled = false, truncated = false;
  size_t dropped = 0;
  static constexpr size_t Limit = 40000;
  json::Array events, ast, macros;
  std::map<std::string, int64_t> macroIndex;
  std::set<std::string> expansionFiles;
  std::vector<std::pair<SourceLocation, size_t>> pragmas;
  int64_t intern(json::Object value) {
    json::Value stored(std::move(value));
    std::string key; llvm::raw_string_ostream stream(key); stream << stored; stream.flush();
    auto found = macroIndex.find(key); if (found != macroIndex.end()) return found->second;
    const int64_t index = macros.size(); macroIndex[key] = index; macros.push_back(std::move(stored)); return index;
  }
  void event(json::Object entry) {
    if (events.size() >= Limit) {truncated = true; ++dropped; return;}
    entry["sequence"] = static_cast<int64_t>(events.size());
    events.push_back(std::move(entry));
  }
};

// Byte intervals are half-open physical source ranges. Spelling and expansion
// intervals stay separate; no scratch or raw SourceLocation encoding escapes.
json::Value dependencyRange(SourceRange range, const SourceManager &sm,
                            const LangOptions &language, bool spelling = false) {
  if (range.isInvalid()) return nullptr;
  SourceLocation begin = spelling ? sm.getSpellingLoc(range.getBegin()) : sm.getExpansionRange(range.getBegin()).getBegin();
  SourceLocation end = spelling ? sm.getSpellingLoc(range.getEnd()) : sm.getExpansionRange(range.getEnd()).getEnd();
  begin = sm.getFileLoc(begin); end = sm.getFileLoc(end);
  if (begin.isInvalid() || end.isInvalid() || sm.getFileID(begin) != sm.getFileID(end) || sm.getFilename(begin).empty() || sm.isWrittenInScratchSpace(begin)) return nullptr;
  auto after = Lexer::getLocForEndOfToken(end, 0, sm, language);
  if (after.isInvalid() || sm.getFileOffset(after) < sm.getFileOffset(begin)) return nullptr;
  json::Array sites;
  for (auto site = sm.getIncludeLoc(sm.getFileID(begin)); site.isValid(); site = sm.getIncludeLoc(sm.getFileID(sm.getFileLoc(site))))
    sites.push_back(location(site, sm));
  return json::Object{{"file", sm.getFilename(begin).str()}, {"begin_bytes", sm.getFileOffset(begin)},
      {"end_bytes", sm.getFileOffset(after)}, {"include_sites", std::move(sites)}};
}

class DependencyExpressions final : public RecursiveASTVisitor<DependencyExpressions> {
public:
  std::set<const NamedDecl *> references;
  bool VisitUnaryExprOrTypeTraitExpr(UnaryExprOrTypeTraitExpr *expr) {
    QualType type = expr->getTypeOfArgument();
    while (!type.isNull()) {
      if (const auto *alias = dyn_cast<TypedefType>(type.getTypePtr())) {references.insert(alias->getDecl()); type = alias->getDecl()->getUnderlyingType(); continue;}
      if (const auto *array = dyn_cast<ArrayType>(type.getCanonicalType().getTypePtr())) {type = array->getElementType(); continue;}
      if (const auto *record = type->getAs<RecordType>()) references.insert(record->getDecl()->getDefinition() ? record->getDecl()->getDefinition() : record->getDecl());
      break; // Pointer operands use pointer geometry, never referent storage.
    }
    return true;
  }
  bool VisitDeclRefExpr(DeclRefExpr *expr) {references.insert(expr->getDecl()); return true;}
};

class DependencyAST {
  ASTContext &context;
  Identities &identity;
  DependencyEvidence &evidence;
  std::set<const NamedDecl *> seen;
public:
  DependencyAST(ASTContext &context, Identities &identity, DependencyEvidence &evidence)
      : context(context), identity(identity), evidence(evidence) {}
  void capture(const NamedDecl *decl, llvm::StringRef role) {
    if (!evidence.enabled || !seen.insert(decl).second || decl->getLocation().isInvalid()) return;
    auto &sm = context.getSourceManager();
    json::Array expressions, refs, attributes;
    std::set<const NamedDecl *> references;
    auto expression = [&](const Expr *expr, llvm::StringRef kind, bool storage = true) {
      if (!expr) return;
      DependencyExpressions visitor;
      visitor.TraverseStmt(const_cast<Expr *>(expr));
      references.insert(visitor.references.begin(), visitor.references.end());
      json::Array ids;
      std::vector<std::string> orderedReferences;
      for (auto *ref : visitor.references) orderedReferences.push_back(identity.id(ref));
      std::sort(orderedReferences.begin(), orderedReferences.end());
      for (const auto &id : orderedReferences) ids.push_back(id);
      expressions.push_back(json::Object{{"role", kind.str()}, {"storage", storage},
          {"expansion", dependencyRange(expr->getSourceRange(), sm, context.getLangOpts())},
          {"spelling", dependencyRange(expr->getSourceRange(), sm, context.getLangOpts(), true)},
          {"references", std::move(ids)}});
    };
    TypeSourceInfo *type = nullptr;
    if (const auto *field = dyn_cast<FieldDecl>(decl)) {
      type = field->getTypeSourceInfo();
      if (field->isBitField()) expression(field->getBitWidth(), "bit-width");
    } else if (const auto *alias = dyn_cast<TypedefNameDecl>(decl)) type = alias->getTypeSourceInfo();
    else if (const auto *variable = dyn_cast<VarDecl>(decl)) {type = variable->getTypeSourceInfo(); expression(variable->getInit(), "initializer");}
    if (type) {
      bool storage = true;
      for (TypeLoc loc = type->getTypeLoc(); !loc.isNull(); loc = loc.getNextTypeLoc()) {
        if (loc.getType()->isPointerType()) storage = false;
        if (auto array = loc.getAs<ArrayTypeLoc>()) expression(array.getSizeExpr(), "array-bound", storage);
      }
    }
    for (const Attr *attr : decl->attrs()) {
      attributes.push_back(json::Object{{"name", attr->getSpelling() ? attr->getSpelling() : "implicit"},
          {"expansion", dependencyRange(attr->getRange(), sm, context.getLangOpts())},
          {"spelling", dependencyRange(attr->getRange(), sm, context.getLangOpts(), true)}});
      if (const auto *aligned = dyn_cast<AlignedAttr>(attr))
        if (aligned->isAlignmentExpr()) expression(aligned->getAlignmentExpr(), "alignment");
    }
    json::Object fact{{"id", identity.id(decl)}, {"kind", role.str()}, {"name", decl->getNameAsString()},
        {"source", role == "field" || role == "record" || role == "alias" ? json::Value(nullptr) : json::Value(identity.anchor(decl->getLocation()))},
        {"expansion", dependencyRange(decl->getSourceRange(), sm, context.getLangOpts())},
        {"spelling", dependencyRange(decl->getSourceRange(), sm, context.getLangOpts(), true)},
        {"expressions", std::move(expressions)}, {"attributes", std::move(attributes)}};
    if (const auto *constant = dyn_cast<EnumConstantDecl>(decl)) {
      if (constant->getInitExpr()) expression(constant->getInitExpr(), "enum-initializer");
      else {
        const auto *enumeration = cast<EnumDecl>(constant->getDeclContext());
        const EnumConstantDecl *previous = nullptr;
        for (const auto *candidate : enumeration->enumerators()) {
          if (candidate == constant) break;
          previous = candidate;
        }
        if (previous) references.insert(previous);
        fact["implicit_successor"] = previous != nullptr;
      }
      const auto *enumeration = cast<EnumDecl>(constant->getDeclContext());
      fact["container_id"] = identity.id(enumeration);
      llvm::SmallString<32> value;
      constant->getInitVal().toString(value, 10);
      fact["value_decimal"] = value.str().str();
      capture(enumeration, "enum");
      // enum expressions were appended after constructing the fact.
      fact["expressions"] = std::move(expressions);
    }
    if (const auto *record = dyn_cast<RecordDecl>(decl)) {
      json::Array before;
      for (const auto &[loc, sequence] : evidence.pragmas)
        if (sm.isBeforeInTranslationUnit(loc, record->getBeginLoc())) before.push_back(static_cast<int64_t>(sequence));
      fact["preceding_pragmas"] = std::move(before);
      fact["packed"] = record->hasAttr<PackedAttr>();
      fact["max_field_alignment_bits"] = record->getAttr<MaxFieldAlignmentAttr>() ?
          json::Value(record->getAttr<MaxFieldAlignmentAttr>()->getAlignment()) : json::Value(nullptr);
    }
    fact["explicit_alignment_bits"] = decl->getMaxAlignment();
    for (const auto *ref : references) {
      refs.push_back(identity.id(ref));
      if (isa<EnumConstantDecl>(ref)) capture(ref, "enumerator");
      else if (isa<VarDecl>(ref)) capture(ref, "variable");
      else if (isa<RecordDecl>(ref)) capture(ref, "type-record");
      else if (isa<TypedefNameDecl>(ref)) capture(ref, "type-alias");
    }
    std::sort(refs.begin(), refs.end(), [](const json::Value &a, const json::Value &b) { return *a.getAsString() < *b.getAsString(); });
    fact["references"] = std::move(refs);
    evidence.ast.push_back(std::move(fact));
  }
};

class DeclarationVisitor final : public RecursiveASTVisitor<DeclarationVisitor> {
public:
  std::vector<RecordDecl *> records;
  std::vector<TypedefNameDecl *> aliases;
  bool VisitRecordDecl(RecordDecl *decl) {
    if (decl->isThisDeclarationADefinition() && !decl->isInvalidDecl()) records.push_back(decl);
    return true;
  }
  bool VisitTypedefNameDecl(TypedefNameDecl *decl) { aliases.push_back(decl); return true; }
};

class LayoutConsumer final : public ASTConsumer {
  json::Array &records, &declarations;
  DependencyEvidence &evidence;
  const std::set<std::string> &wanted;
  const std::map<std::string, std::string> &paths;
  std::set<const RecordDecl *> selected;
  void select(const RecordDecl *record, ASTContext &context) {
    record = record->getDefinition();
    if (!record || !selected.insert(record).second) return;
    for (const auto *field : record->fields()) {
      QualType type = field->getType();
      while (const auto *array = context.getAsArrayType(type)) type = array->getElementType();
      if (const auto *embedded = type->getAs<RecordType>()) select(embedded->getDecl(), context);
    }
  }
public:
  LayoutConsumer(json::Array &output, json::Array &declarations, DependencyEvidence &evidence,
                 const std::set<std::string> &names,
                 const std::map<std::string, std::string> &paths)
      : records(output), declarations(declarations), evidence(evidence), wanted(names), paths(paths) {}
  void HandleTranslationUnit(ASTContext &context) override {
    if (context.getDiagnostics().hasErrorOccurred()) return;
    DeclarationVisitor visitor;
    visitor.TraverseDecl(context.getTranslationUnitDecl());
    Identities identity(context.getSourceManager(), paths);
    DependencyAST dependencies(context, identity, evidence);
    for (auto *record : visitor.records)
      if (wanted.empty() || wanted.count(record->getNameAsString())) select(record, context);
    for (auto *record : visitor.records) {
      if (!selected.count(record)) continue;
      identity.records.insert(record);
      const auto &layout = context.getASTRecordLayout(record);
      json::Array fields;
      unsigned index = 0;
      for (const FieldDecl *field : record->fields()) {
        dependencies.capture(field, "field");
        auto declaration = identity.declaration(field, "field");
        declaration["owner_id"] = identity.id(record);
        declarations.push_back(std::move(declaration));
        json::Object item{{"id", identity.id(field)}, {"name", field->getNameAsString()},
            {"index", index},
            {"offset_bits", static_cast<int64_t>(layout.getFieldOffset(index))},
            {"anonymous_record", field->isAnonymousStructOrUnion()},
            {"type", typeInfo(field->getType(), context, identity)},
            {"location", location(field->getLocation(), context.getSourceManager())}};
        item["bit_width"] = field->isBitField() ? json::Value(field->getBitWidthValue()) : json::Value(nullptr);
        fields.push_back(std::move(item));
        ++index;
      }
      records.push_back(json::Object{
          {"id", identity.id(record)}, {"name", record->getNameAsString()},
          {"kind", record->isUnion() ? "union" : "struct"},
          {"size_bytes", layout.getSize().getQuantity()},
          {"alignment_bytes", layout.getAlignment().getQuantity()},
          {"fields", std::move(fields)},
          {"location", location(record->getLocation(), context.getSourceManager())}});
    }
    // Include aliases related to selected storage, including pointer aliases;
    // pointer targets are declaration references, never extra layout roots.
    for (auto *alias : visitor.aliases) {
      QualType type = alias->getUnderlyingType();
      while (true) {
        if (const auto *array = context.getAsArrayType(type)) type = array->getElementType();
        else if (type->isPointerType()) type = type->getPointeeType();
        else break;
      }
      if (const auto *record = type->getAs<RecordType>())
        if (selected.count(record->getDecl()->getDefinition())) identity.aliases.insert(alias);
    }
    std::set<const TypedefNameDecl *> processed;
    while (processed.size() != identity.aliases.size()) {
      std::vector<const TypedefNameDecl *> pending(identity.aliases.begin(), identity.aliases.end());
      for (auto *alias : pending) {
        if (!processed.insert(alias).second) continue;
        dependencies.capture(alias, "alias");
        auto declaration = identity.declaration(alias, "alias");
        declaration["underlying_type"] = typeInfo(alias->getUnderlyingType(), context, identity);
        declarations.push_back(std::move(declaration));
      }
    }
    for (auto *record : identity.records) {
      dependencies.capture(record, "record");
      auto declaration = identity.declaration(record, record->isUnion() ? "union" : "struct");
      declaration["complete"] = record->isCompleteDefinition();
      declarations.push_back(std::move(declaration));
    }
    std::sort(evidence.ast.begin(), evidence.ast.end(), [](const json::Value &a, const json::Value &b) {
      return *a.getAsObject()->getString("id") < *b.getAsObject()->getString("id");
    });
    std::sort(declarations.begin(), declarations.end(), [](const json::Value &a, const json::Value &b) {
      return *a.getAsObject()->getString("id") < *b.getAsObject()->getString("id");
    });
  }
};

class FileTrace final : public PPCallbacks {
  SourceManager &source;
  std::set<std::string> &files;
  json::Array &probes;
public:
  FileTrace(SourceManager &source, std::set<std::string> &files, json::Array &probes)
      : source(source), files(files), probes(probes) {}
  void FileChanged(SourceLocation loc, FileChangeReason reason,
                   SrcMgr::CharacteristicKind, FileID) override {
    if (reason != EnterFile || loc.isInvalid()) return;
    if (auto file = source.getFileEntryRefForID(source.getFileID(loc)))
      files.insert(file->getName().str());
  }
  void InclusionDirective(SourceLocation, const Token &, llvm::StringRef,
                          bool, CharSourceRange, OptionalFileEntryRef file,
                          llvm::StringRef, llvm::StringRef, const Module *,
                          bool, SrcMgr::CharacteristicKind) override {
    if (file) files.insert(file->getName().str());
  }
  void HasInclude(SourceLocation loc, llvm::StringRef name, bool angled,
                  OptionalFileEntryRef file, SrcMgr::CharacteristicKind) override {
    json::Object probe{{"name", name.str()}, {"angled", angled},
                       {"location", location(loc, source)}};
    if (file) {
      files.insert(file->getName().str());
      probe["resolved"] = file->getName().str();
    } else probe["resolved"] = nullptr;
    probes.push_back(std::move(probe));
  }
};

class DependencyPP final : public PPCallbacks {
  Preprocessor &pp;
  DependencyEvidence &evidence;
  int64_t macro(llvm::StringRef name, const MacroInfo *info) {
    json::Array parameters;
    std::string replacement;
    if (info) {
      for (const Token &token : info->tokens()) {
        if (!replacement.empty()) replacement += " ";
        replacement += pp.getSpelling(token);
      }
      if (info->isFunctionLike()) for (const IdentifierInfo *parameter : info->params()) parameters.push_back(parameter->getName().str());
    }
    auto &sm = pp.getSourceManager();
    auto definition = info ? location(info->getDefinitionLoc(), sm) : json::Object{};
    return evidence.intern(json::Object{{"name", name.str()}, {"defined", info != nullptr},
        {"replacement", info ? json::Value(replacement) : json::Value(nullptr)},
        {"function_like", info && info->isFunctionLike()}, {"builtin", info && info->isBuiltinMacro()},
        {"parameters", std::move(parameters)}, {"definition", definition.empty() ? json::Value(nullptr) : json::Value(std::move(definition))}});
  }
  bool physical(SourceLocation loc) {
    auto &sm = pp.getSourceManager(); loc = sm.getFileLoc(loc);
    return loc.isValid() && !sm.getFilename(loc).empty() && !sm.getFilename(loc).starts_with("<");
  }
  json::Object base(llvm::StringRef kind, SourceLocation loc, SourceRange range) {
    return json::Object{{"kind", kind.str()}, {"location", location(loc, pp.getSourceManager())},
        {"range", dependencyRange(range, pp.getSourceManager(), pp.getLangOpts())}};
  }
  void condition(llvm::StringRef kind, SourceLocation loc, SourceRange range,
                 ConditionValueKind value) {
    if (!physical(loc)) return;
    auto entry = base(kind, loc, range);
    entry["value"] = value == CVK_True ? "true" : value == CVK_False ? "false" : "not-evaluated";
    json::Array states;
    auto &sm = pp.getSourceManager();
    SourceLocation begin = sm.getFileLoc(range.getBegin()), end = sm.getFileLoc(range.getEnd());
    if (begin.isValid() && end.isValid() && sm.getFileID(begin) == sm.getFileID(end)) {
      auto after = Lexer::getLocForEndOfToken(end, 0, sm, pp.getLangOpts());
      auto buffer = sm.getBufferData(sm.getFileID(begin));
      if (after.isValid() && sm.getFileOffset(after) <= buffer.size() && sm.getFileOffset(begin) <= sm.getFileOffset(after)) {
        Lexer lexer(sm.getLocForStartOfFile(sm.getFileID(begin)), pp.getLangOpts(), buffer.begin(),
                    buffer.begin() + sm.getFileOffset(begin), buffer.end());
        Token token;
        std::set<std::string> names;
        while (true) {
          lexer.LexFromRawLexer(token);
          if (token.is(tok::eof) || sm.getFileOffset(token.getLocation()) >= sm.getFileOffset(after)) break;
          if (token.is(tok::raw_identifier)) names.insert(token.getRawIdentifier().str());
        }
        for (const auto &name : names) if (name != "defined")
          states.push_back(macro(name, pp.getMacroDefinition(pp.getIdentifierInfo(name)).getMacroInfo()));
      }
    }
    entry["macro_states"] = std::move(states);
    evidence.event(std::move(entry));
  }
  void definedCondition(llvm::StringRef kind, SourceLocation loc, const Token &token,
                        const MacroDefinition &definition, bool inverse) {
    if (!physical(loc)) return;
    auto entry = base(kind, loc, SourceRange(token.getLocation(), token.getLocation()));
    const auto *info = definition.getMacroInfo();
    entry["value"] = (info != nullptr) != inverse ? "true" : "false";
    json::Array states;
    states.push_back(macro(pp.getSpelling(token), info));
    entry["macro_states"] = std::move(states);
    evidence.event(std::move(entry));
  }
public:
  DependencyPP(Preprocessor &pp, DependencyEvidence &evidence) : pp(pp), evidence(evidence) {}
  void If(SourceLocation loc, SourceRange range, ConditionValueKind value) override {condition("if", loc, range, value);}
  void Elif(SourceLocation loc, SourceRange range, ConditionValueKind value, SourceLocation) override {condition("elif", loc, range, value);}
  void Ifdef(SourceLocation loc, const Token &name, const MacroDefinition &definition) override {definedCondition("ifdef", loc, name, definition, false);}
  void Ifndef(SourceLocation loc, const Token &name, const MacroDefinition &definition) override {definedCondition("ifndef", loc, name, definition, true);}
  void Else(SourceLocation loc, SourceLocation) override {if (physical(loc)) evidence.event(base("else", loc, SourceRange(loc, loc)));}
  void Endif(SourceLocation loc, SourceLocation) override {if (physical(loc)) evidence.event(base("endif", loc, SourceRange(loc, loc)));}
  void Defined(const Token &name, const MacroDefinition &definition, SourceRange range) override {
    if (!physical(name.getLocation())) return;
    auto entry = base("defined", name.getLocation(), range);
    entry["macro"] = macro(pp.getSpelling(name), definition.getMacroInfo()); evidence.event(std::move(entry));
  }
  void MacroDefined(const Token &name, const MacroDirective *directive) override {
    if (!physical(name.getLocation())) return;
    auto entry = base("define", name.getLocation(), SourceRange(name.getLocation(), directive->getMacroInfo()->getDefinitionEndLoc()));
    entry["macro"] = macro(pp.getSpelling(name), directive->getMacroInfo()); evidence.event(std::move(entry));
  }
  void MacroUndefined(const Token &name, const MacroDefinition &definition, const MacroDirective *) override {
    if (!physical(name.getLocation())) return;
    auto entry = base("undef", name.getLocation(), SourceRange(name.getLocation(), name.getLocation()));
    entry["macro"] = macro(pp.getSpelling(name), definition.getMacroInfo()); evidence.event(std::move(entry));
  }
  void MacroExpands(const Token &name, const MacroDefinition &definition, SourceRange range, const MacroArgs *) override {
    if (!physical(name.getLocation())) return;
    auto file = pp.getSourceManager().getFilename(pp.getSourceManager().getFileLoc(name.getLocation())).str();
    if (!evidence.expansionFiles.empty() && !evidence.expansionFiles.count(file)) return;
    auto entry = base("expand", name.getLocation(), range);
    entry["macro"] = macro(pp.getSpelling(name), definition.getMacroInfo()); evidence.event(std::move(entry));
  }
  void SourceRangeSkipped(SourceRange range, SourceLocation) override {
    if (physical(range.getBegin())) evidence.event(base("skipped", range.getBegin(), range));
  }
  void PragmaDirective(SourceLocation loc, PragmaIntroducerKind) override {
    if (!physical(loc)) return;
    const size_t sequence = evidence.events.size(); evidence.event(base("pragma", loc, SourceRange(loc, loc)));
    if (evidence.events.size() > sequence) evidence.pragmas.emplace_back(loc, sequence);
  }
};

class LayoutAction final : public ASTFrontendAction {
  json::Array &records, &declarations;
  DependencyEvidence &evidence;
  const std::map<std::string, std::string> &paths;
  const std::set<std::string> &wanted;
  const std::set<std::string> &observe;
  std::set<std::string> &consumed;
  json::Object &macros;
  json::Array &probes;
  bool trace;
public:
  LayoutAction(json::Array &output, json::Array &declarations, DependencyEvidence &evidence,
               const std::map<std::string, std::string> &paths,
               const std::set<std::string> &wanted,
               const std::set<std::string> &observe,
               std::set<std::string> &consumed, json::Object &macros,
               json::Array &probes, bool trace)
      : records(output), declarations(declarations), evidence(evidence), paths(paths), wanted(wanted), observe(observe), consumed(consumed),
        macros(macros), probes(probes), trace(trace) {}
  bool BeginSourceFileAction(CompilerInstance &compiler) override {
    if (trace || evidence.enabled)
      compiler.getPreprocessor().addPPCallbacks(std::make_unique<FileTrace>(
          compiler.getSourceManager(), consumed, probes));
    if (evidence.enabled) compiler.getPreprocessor().addPPCallbacks(std::make_unique<DependencyPP>(compiler.getPreprocessor(), evidence));
    return true;
  }
  void EndSourceFileAction() override {
    auto &preprocessor = getCompilerInstance().getPreprocessor();
    for (const auto &name : observe) {
      auto *info = preprocessor.getMacroInfo(preprocessor.getIdentifierInfo(name));
      if (!info) {
        macros[name] = nullptr;
        continue;
      }
      std::string tokens;
      for (const auto &token : info->tokens()) {
        if (!tokens.empty()) tokens += " ";
        tokens += preprocessor.getSpelling(token);
      }
      macros[name] = json::Object{{"replacement", tokens},
          {"function_like", info->isFunctionLike()},
          {"location", location(info->getDefinitionLoc(), preprocessor.getSourceManager())}};
    }
  }
  std::unique_ptr<ASTConsumer> CreateASTConsumer(CompilerInstance &,
                                               llvm::StringRef) override {
    return std::make_unique<LayoutConsumer>(records, declarations, evidence, wanted, paths);
  }
};

json::Object failure(llvm::StringRef message) {
  return json::Object{{"schema", 2}, {"status", "invalid-request"}, {"records", json::Array{}},
          {"diagnostics", json::Array{json::Object{{"severity", "error"},
                                                  {"message", message.str()}}}}};
}

bool pathAllowed(llvm::StringRef path) {
  if (!path.starts_with("/inputs/") || path.contains('\0') ||
      path.contains('\\') || path.contains('\n') || path.contains('\r')) return false;
  llvm::SmallVector<llvm::StringRef, 8> parts;
  path.split(parts, '/');
  for (auto part : parts) if (part == "." || part == "..") return false;
  return true;
}

bool macroAllowed(llvm::StringRef name) {
  if (name.empty() || !(std::isalpha(static_cast<unsigned char>(name[0])) || name[0] == '_'))
    return false;
  for (unsigned char c : name)
    if (!(std::isalnum(c) || c == '_')) return false;
  return true;
}

bool safeLayoutNumbers(const json::Value &value) {
  constexpr int64_t MaxSafeJSONInteger = 9007199254740991LL;
  if (auto number = value.getAsInteger())
    return *number >= 0 && *number <= MaxSafeJSONInteger;
  if (const auto *object = value.getAsObject()) {
    if (object->get("unsupported")) return false;
    for (const auto &entry : *object)
      if (!safeLayoutNumbers(entry.second)) return false;
  }
  if (const auto *array = value.getAsArray())
    for (const auto &entry : *array)
      if (!safeLayoutNumbers(entry)) return false;
  return true;
}

json::Object analyze(llvm::StringRef input) {
  if (input.size() > MaxRequestBytes) return failure("request exceeds 64 MiB");
  auto parsed = json::parse(input);
  if (!parsed) {
    llvm::consumeError(parsed.takeError());
    return failure("invalid JSON");
  }
  const auto *request = parsed->getAsObject();
  if (!request) return failure("request must be an object");
  // This is deliberately a narrow prototype: no arbitrary compiler arguments,
  // plugins, modules, response files, PCH files, or host filesystem access.
  const std::set<std::string> keys{"target", "main", "files", "macros", "records",
      "include_dirs", "forced_includes", "target_cpu", "target_arch", "target_features",
      "language", "blocks", "kernel_mode", "ptrauth_intrinsics", "ptrauth_calls", "observe_macros", "trace_files", "source_paths", "trace_dependencies", "dependency_files"};
  for (const auto &entry : *request)
    if (!keys.count(entry.first.str())) return failure("unknown request key");
  auto target = request->getString("target");
  auto main = request->getString("main");
  const auto *files = request->getObject("files");
  if (!target || (*target != "aarch64-apple-darwin" && *target != "arm64e-apple-darwin" &&
                  *target != "aarch64-apple-ios" && *target != "arm64e-apple-ios"))
    return failure("target must explicitly be aarch64-apple-darwin, arm64e-apple-darwin, aarch64-apple-ios or arm64e-apple-ios");
  if (!main || !pathAllowed(*main) || !files || !files->getString(*main))
    return failure("main must name a supplied /inputs/ file");
  auto fs = llvm::makeIntrusiveRefCnt<llvm::vfs::InMemoryFileSystem>();
  fs->setCurrentWorkingDirectory("/inputs");
  for (const auto &file : *files) {
    auto content = file.second.getAsString();
    if (!pathAllowed(file.first) || !content)
      return failure("files must map /inputs/ paths to strings");
    if (!fs->addFile(llvm::StringRef(file.first), 0,
                     llvm::MemoryBuffer::getMemBufferCopy(*content, llvm::StringRef(file.first))))
      return failure("duplicate virtual input path");
  }
  std::map<std::string, std::string> sourcePaths;
  if (const auto *mapping = request->getObject("source_paths")) {
    for (const auto &entry : *mapping) {
      auto physical = entry.second.getAsString();
      if (!files->getString(entry.first) || !physical || physical->empty() ||
          physical->contains('\0') || physical->contains('\n') || physical->contains('\r') ||
          physical->contains('\\') || physical->contains("..")) return failure("invalid source path mapping");
      sourcePaths[entry.first.str()] = physical->str();
    }
  } else if (request->get("source_paths")) return failure("source_paths must be an object");
  std::string language = "gnu11";
  if (const auto it = request->find("language"); it != request->end()) {
    if (!it->second.getAsString() || (*it->second.getAsString() != "gnu11" &&
                                   *it->second.getAsString() != "gnu17"))
      return failure("language must be gnu11 or gnu17");
    language = it->second.getAsString()->str();
  }
  std::vector<std::string> args{"-triple", target->str(), "-x", "c", "-std=" + language,
      "-ffreestanding", "-fsyntax-only", "-nostdsysteminc", "-nobuiltininc",
      "-ferror-limit", "20"};
  if (const auto it = request->find("include_dirs"); it != request->end()) {
    const auto *dirs = it->second.getAsArray();
    if (!dirs) return failure("include_dirs must be an ordered array");
    for (const auto &dir : *dirs) {
      if (!dir.getAsString() || !pathAllowed(*dir.getAsString()))
        return failure("include directories must be below /inputs/");
      args.insert(args.end(), {"-I", dir.getAsString()->str()});
    }
  } else args.insert(args.end(), {"-I", "/inputs"});
  if (const auto it = request->find("forced_includes"); it != request->end()) {
    const auto *headers = it->second.getAsArray();
    if (!headers) return failure("forced_includes must be an ordered array");
    for (const auto &header : *headers) {
      if (!header.getAsString() || !pathAllowed(*header.getAsString()) ||
          !files->getString(*header.getAsString()))
        return failure("forced includes must name supplied /inputs/ files");
      args.insert(args.end(), {"-include", header.getAsString()->str()});
    }
  }
  std::string driverCPU, driverArch;
  std::vector<std::string> featureOverrides;
  if (const auto it = request->find("target_cpu"); it != request->end()) {
    auto cpu = it->second.getAsString();
    if (!cpu || cpu->empty() || cpu->size() > 80 || cpu->front() == '-')
      return failure("invalid target CPU");
    for (unsigned char c : *cpu)
      if (!(std::isalnum(c) || c == '-' || c == '_')) return failure("invalid target CPU");
    if (*cpu == "native") return failure("host-dependent native CPU is unsupported");
    driverCPU = cpu->str();
  }
  if (const auto it = request->find("target_arch"); it != request->end()) {
    const auto arch = it->second.getAsString();
    if (!arch || *arch != "armv8.5a+sme2")
      return failure("unsupported target architecture selection");
    if (!driverCPU.empty()) return failure("select target_cpu or target_arch, not both");
    driverArch = arch->str();
  }
  if (const auto it = request->find("target_features"); it != request->end()) {
    const auto *features = it->second.getAsArray();
    if (!features) return failure("target_features must be an array");
    for (const auto &entry : *features) {
      auto feature = entry.getAsString();
      if (!feature || feature->size() < 2 || feature->size() > 80 ||
          (feature->front() != '+' && feature->front() != '-'))
        return failure("invalid target feature");
      for (unsigned char c : feature->drop_front())
        if (!(std::isalnum(c) || c == '-' || c == '_' || c == '.'))
          return failure("invalid target feature");
      // Clang's AST-only AArch64 path silently accepts unknown feature names.
      // Keep this prototype's supported overrides explicit and fail closed.
      const std::set<std::string> supported{"v8.5a", "sme2"};
      if (!supported.count(feature->drop_front().str()))
        return failure("unsupported target feature override");
      featureOverrides.push_back(feature->str());
    }
  }
  if (const auto it = request->find("blocks"); it != request->end()) {
    if (!it->second.getAsBoolean()) return failure("blocks must be boolean");
    if (*it->second.getAsBoolean()) args.push_back("-fblocks");
  }
  if (const auto it = request->find("kernel_mode"); it != request->end()) {
    if (!it->second.getAsBoolean()) return failure("kernel_mode must be boolean");
    if (*it->second.getAsBoolean())
      args.insert(args.end(), {"-fno-builtin", "-fgnuc-version=4.2.1", "-fmax-type-align=16"});
  }
  for (const auto &option : {std::pair<const char *, const char *>{"ptrauth_intrinsics", "-fptrauth-intrinsics"},
                            {"ptrauth_calls", "-fptrauth-calls"}}) {
    if (const auto it = request->find(option.first); it != request->end()) {
      const auto enabled = it->second.getAsBoolean();
      if (!enabled) return failure(std::string(option.first) + " must be boolean");
      if (*enabled) args.push_back(option.second);
    }
  }
  bool trace = false;
  if (const auto it = request->find("trace_files"); it != request->end()) {
    if (!it->second.getAsBoolean()) return failure("trace_files must be boolean");
    trace = *it->second.getAsBoolean();
  }
  DependencyEvidence dependencyEvidence;
  if (const auto it = request->find("trace_dependencies"); it != request->end()) {
    if (!it->second.getAsBoolean()) return failure("trace_dependencies must be boolean");
    dependencyEvidence.enabled = *it->second.getAsBoolean();
  }
  if (const auto it = request->find("dependency_files"); it != request->end()) {
    const auto *names = it->second.getAsArray();
    if (!names) return failure("dependency_files must be an array");
    for (const auto &name : *names) {
      if (!name.getAsString() || !files->getString(*name.getAsString())) return failure("dependency_files must name supplied files");
      dependencyEvidence.expansionFiles.insert(name.getAsString()->str());
    }
  }
  std::set<std::string> observe;
  if (const auto it = request->find("observe_macros"); it != request->end()) {
    const auto *names = it->second.getAsArray();
    if (!names) return failure("observe_macros must be an array");
    for (const auto &name : *names) {
      if (!name.getAsString() || !macroAllowed(*name.getAsString()))
        return failure("invalid observed macro name");
      observe.insert(name.getAsString()->str());
    }
  }
  if (const auto it = request->find("macros"); it != request->end()) {
    const auto *macros = it->second.getAsObject();
    if (!macros) return failure("macros must be an object");
    // llvm::json::Object uses a hash map; sort compiler inputs explicitly.
    std::vector<std::string> definitions;
    for (const auto &macro : *macros) {
      if (!macroAllowed(macro.first)) return failure("invalid macro name");
      if (trace || !observe.empty()) observe.insert(macro.first.str());
      if (macro.second.getAsNull()) definitions.push_back("-U" + macro.first.str());
      else if (auto value = macro.second.getAsString()) {
        if (value->contains('\0') || value->contains('\n') || value->contains('\r'))
          return failure("macro values must be single-line strings");
        definitions.push_back("-D" + macro.first.str() + "=" + value->str());
      } else return failure("macro values must be strings or null (undefined)");
    }
    std::sort(definitions.begin(), definitions.end());
    args.insert(args.end(), definitions.begin(), definitions.end());
  }
  std::set<std::string> wanted;
  if (const auto it = request->find("records"); it != request->end()) {
    const auto *names = it->second.getAsArray();
    if (!names || names->empty()) return failure("records must be a nonempty array");
    for (const auto &name : *names) {
      if (!name.getAsString() || name.getAsString()->empty())
        return failure("record selections must be nonempty names");
      wanted.insert(name.getAsString()->str());
    }
  }
  Diagnostics diagnostics;
  // diagnostics outlives CompilerInstance, which borrows it. The instance owns
  // the source manager, preprocessor, AST, and virtual files for this request.
  CompilerInstance compiler;
  compiler.setInvocation(std::make_shared<CompilerInvocation>());
  compiler.createDiagnostics(*fs, &diagnostics, false);
  json::Object driverTarget;
  if (!driverCPU.empty() || !driverArch.empty()) {
    // Build the pinned upstream driver's command in the same isolated VFS.
    // Never execute its jobs; retain only validated CPU/feature expansion.
    driver::Driver driver("/inputs/clang", target->str(), compiler.getDiagnostics(),
                          "layout target expansion", fs);
    driver.setCheckInputsExist(false);
    std::vector<std::string> driverArgs{"/inputs/clang", "--no-default-config",
        "--target=" + target->str(), "-nostdinc", "-fsyntax-only", "-mkernel",
        "-x", "c", driverCPU.empty() ? "-march=" + driverArch : "-mcpu=" + driverCPU,
        main->str()};
    std::vector<const char *> driverArgv;
    for (const auto &arg : driverArgs) driverArgv.push_back(arg.c_str());
    std::unique_ptr<driver::Compilation> compilation(driver.BuildCompilation(driverArgv));
    if (!compilation || diagnostics.error || compilation->getJobs().size() != 1)
      return failure("pinned driver could not expand target selection");
    const auto &command = *compilation->getJobs().begin();
    const auto &expanded = command.getArguments();
    json::Array features;
    std::string resolvedCPU;
    for (size_t i = 0; i + 1 < expanded.size(); ++i) {
      llvm::StringRef option(expanded[i]);
      if (option != "-target-cpu" && option != "-target-feature") continue;
      std::string value(expanded[++i]);
      args.insert(args.end(), {option.str(), value});
      if (option == "-target-cpu") resolvedCPU = value;
      else features.push_back(value);
    }
    if (resolvedCPU.empty()) return failure("pinned driver omitted target CPU");
    driverTarget["cpu"] = resolvedCPU;
    driverTarget["features"] = std::move(features);
    driverTarget["source_option"] = driverCPU.empty() ? "-march=" + driverArch : "-mcpu=" + driverCPU;
  }
  for (const auto &feature : featureOverrides)
    args.insert(args.end(), {"-target-feature", feature});
  args.push_back(main->str());
  std::vector<const char *> argv;
  for (const auto &arg : args) argv.push_back(arg.c_str());
  bool valid = CompilerInvocation::CreateFromArgs(compiler.getInvocation(), argv,
                                                 compiler.getDiagnostics());
  json::Array records, declarations;
  std::set<std::string> consumed;
  json::Object effectiveMacros;
  json::Array includeProbes;
  if (valid && !diagnostics.error) {
    compiler.createFileManager(fs);
    LayoutAction action(records, declarations, dependencyEvidence, sourcePaths, wanted, observe, consumed, effectiveMacros, includeProbes, trace);
    valid = compiler.ExecuteAction(action);
  }
  std::string status = valid && !diagnostics.error ? "ok" : "error";
  if (status == "ok") {
    std::set<std::string> identities;
    for (const auto &record : records) {
      const auto *object = record.getAsObject();
      const bool unique = identities.insert(object->getString("id")->str()).second;
      if (!unique || !safeLayoutNumbers(record)) {
        status = "unsupported-layout";
        diagnostics.entries.push_back(json::Object{{"severity", "error"},
            {"message", unique ? "layout exceeds JavaScript's exact integer range" :
              "ambiguous record identity in nested macro expansions"}});
        break;
      }
    }
  }
  if (status == "ok" && !wanted.empty()) {
    std::set<std::string> found;
    for (const auto &record : records)
      found.insert(record.getAsObject()->getString("name")->str());
    for (const auto &name : wanted) {
      if (!found.count(name)) {
        status = "unavailable-type";
        diagnostics.entries.push_back(json::Object{
            {"severity", "error"}, {"message", "no complete record definition: " + name}});
      }
    }
  }
  if (status == "ok") {
    std::set<std::string> ids;
    for (const auto &declaration : declarations)
      if (!ids.insert(declaration.getAsObject()->getString("id")->str()).second ||
          !safeLayoutNumbers(declaration)) {
        status = "unsupported-layout";
        diagnostics.entries.push_back(json::Object{{"severity", "error"}, {"message", "ambiguous or unsupported source declaration identity (including token-paste scratch buffers)"}});
        break;
      }
    for (const auto &name : wanted) {
      size_t matches = 0;
      for (const auto &record : records) matches += record.getAsObject()->getString("name") == name;
      if (matches > 1) {
        status = "unsupported-layout";
        diagnostics.entries.push_back(json::Object{{"severity", "error"}, {"message", "ambiguous record name selection: " + name}});
      }
    }
  }
  if (status != "ok") { records.clear(); declarations.clear(); }
  json::Array options;
  for (const auto &arg : args) options.push_back(arg);
  json::Object response{{"schema", 2}, {"status", status},
          {"compiler", json::Object{{"version", CLANG_VERSION_STRING},
                                   {"revision", LAYOUT_LLVM_REVISION},
                                   {"engine_sha256", LAYOUT_ENGINE_SHA256}}},
          {"target", target->str()}, {"options", std::move(options)},
          {"records", std::move(records)}, {"declarations", std::move(declarations)},
          {"diagnostics", std::move(diagnostics.entries)}};
  if (dependencyEvidence.enabled) {
    std::set<std::string> relevant = dependencyEvidence.expansionFiles;
    auto collectSourceFiles = [&](auto &&self, const json::Value &value) -> void {
      if (const auto *object = value.getAsObject()) {
        if (auto file = object->getString("file"); file && !file->empty()) relevant.insert(file->str());
        for (const auto &entry : *object) self(self, entry.second);
      } else if (const auto *array = value.getAsArray()) for (const auto &entry : *array) self(self, entry);
    };
    if (const auto *catalog = response.getArray("declarations")) for (const auto &entry : *catalog) {
      collectSourceFiles(collectSourceFiles, *entry.getAsObject()->get("source"));
      collectSourceFiles(collectSourceFiles, *entry.getAsObject()->get("scope"));
    }
    for (const auto &fact : dependencyEvidence.ast) {
      const auto *object = fact.getAsObject();
      if (const auto *source = object->get("source")) collectSourceFiles(collectSourceFiles, *source);
      for (const auto *key : {"expansion", "spelling"})
        if (const auto *range = object->getObject(key)) relevant.insert(range->getString("file")->str());
    }
    if (relevant.empty()) relevant.insert(consumed.begin(), consumed.end());
    auto macroRefs = [](json::Object &entry) {
      std::vector<int64_t> refs;
      if (auto value = entry.getInteger("macro")) refs.push_back(*value);
      if (auto *states = entry.getArray("macro_states")) for (const auto &value : *states) refs.push_back(*value.getAsInteger());
      return refs;
    };
    bool changed = true;
    while (changed) {
      const size_t previous = relevant.size();
      for (auto &event : dependencyEvidence.events) {
        auto *entry = event.getAsObject(); auto *loc = entry->getObject("location");
        if (!loc || !relevant.count(loc->getString("file")->str())) continue;
        for (auto index : macroRefs(*entry))
          if (const auto *definition = dependencyEvidence.macros[index].getAsObject()->getObject("definition"))
            if (auto file = definition->getString("file"); file && !file->empty()) relevant.insert(file->str());
      }
      changed = previous != relevant.size();
    }
    const size_t originalEvents = dependencyEvidence.events.size();
    json::Array kept, interned;
    std::set<int64_t> used;
    for (auto &event : dependencyEvidence.events) {
      auto *entry = event.getAsObject(); auto *loc = entry->getObject("location");
      if (*entry->getString("kind") != "pragma" && (!loc || !relevant.count(loc->getString("file")->str()))) continue;
      for (auto index : macroRefs(*entry)) used.insert(index);
      kept.push_back(std::move(event));
    }
    std::map<int64_t, int64_t> remap;
    for (auto old : used) {remap[old] = interned.size(); interned.push_back(std::move(dependencyEvidence.macros[old]));}
    for (auto &event : kept) {
      auto *entry = event.getAsObject();
      if (auto value = entry->getInteger("macro")) (*entry)["macro"] = remap[*value];
      if (auto *states = entry->getArray("macro_states")) for (auto &value : *states) value = remap[*value.getAsInteger()];
    }
    dependencyEvidence.events = std::move(kept);
    json::Array relevantFiles;
    for (const auto &file : relevant) relevantFiles.push_back(file);
    json::Array scope, opened;
    for (const auto &file : dependencyEvidence.expansionFiles) scope.push_back(file);
    for (const auto &file : consumed) opened.push_back(file);
    response["dependency_trace"] = json::Object{{"contract", "platydoc.compiler-dependency-evidence"}, {"version", 1},
        {"ranges", "half-open-utf8-bytes"}, {"events", std::move(dependencyEvidence.events)},
        {"ast", std::move(dependencyEvidence.ast)}, {"macros", std::move(interned)},
        {"filtering", json::Object{{"kind", "selected-source-and-macro-origin-closure"}, {"events_before", static_cast<int64_t>(originalEvents)}, {"relevant_files", std::move(relevantFiles)}}}, {"expansion_files", std::move(scope)},
        {"opened_files", std::move(opened)}, {"truncated", dependencyEvidence.truncated},
        {"dropped_events", static_cast<int64_t>(dependencyEvidence.dropped)}, {"event_limit", static_cast<int64_t>(DependencyEvidence::Limit)}};
  }
  if (!observe.empty()) response["effective_macros"] = std::move(effectiveMacros);
  if (!driverTarget.empty()) response["driver_target"] = std::move(driverTarget);
  if (trace) {
    json::Object inputs;
    for (const auto &file : *files) {
      llvm::SHA256 hash;
      hash.update(*file.second.getAsString());
      inputs[file.first] = llvm::toHex(hash.final(), true);
    }
    json::Array consumedFiles;
    for (const auto &name : consumed) consumedFiles.push_back(name);
    response["input_sha256"] = std::move(inputs);
    response["consumed_files"] = std::move(consumedFiles);
    response["include_probes"] = std::move(includeProbes);
  }
  return response;
}
} // namespace

// A request owns all its files. No AST, compiler instance, or input survives the
// call; the only transferred allocation is the JSON result, freed explicitly.
extern "C" char *layout_analyze(const char *input) {
  if (!input) return nullptr;
  std::string output;
  llvm::raw_string_ostream stream(output);
  stream << json::Value(analyze(input));
  stream.flush();
  char *result = static_cast<char *>(std::malloc(output.size() + 1));
  if (result) std::memcpy(result, output.c_str(), output.size() + 1);
  return result;
}

extern "C" void layout_free(char *result) { std::free(result); }

#ifndef __EMSCRIPTEN__
int main() {
  // Bound input bytes; callers must also impose their own process timeout.
  std::string input;
  char buffer[4096];
  while (std::cin.read(buffer, sizeof buffer) || std::cin.gcount()) {
    input.append(buffer, static_cast<size_t>(std::cin.gcount()));
    if (input.size() > MaxRequestBytes) break;
  }
  char *result = layout_analyze(input.c_str());
  if (!result) return 2;
  std::cout << result << '\n';
  layout_free(result);
  return 0; // Analysis status is part of the JSON protocol.
}
#endif
