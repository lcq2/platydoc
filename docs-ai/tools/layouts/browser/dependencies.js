// SPDX-License-Identifier: GPL-2.0-only
// Conservative dependency evidence, not an evaluator for arbitrary C conditions.
(function (root, factory) {
  const api = factory(typeof module === 'object' && module.exports ? require('./contracts.js') : root.LayoutContracts);
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.LayoutDependencies = api;
})(globalThis, function (C) {
  'use strict';
  const order = (a, b) => a < b ? -1 : a > b ? 1 : 0;
  const fail = message => {throw new Error('Layout dependencies: ' + message);};
  const clone = value => JSON.parse(C.canonical(value));
  const own = (o, k) => Object.hasOwn(o, k);
  const id = async (prefix, value) => prefix + ':' + await C.sha256(C.canonical(value));
  const names = text => [...new Set((text.match(/[A-Za-z_][A-Za-z_0-9]*/g) || []))].sort(order);
  const byteLength = text => new TextEncoder().encode(text).length;
  const cache = new Map(), validatedAnalyses = new WeakSet();
  function freeze(value) {if (value && typeof value === 'object' && !Object.isFrozen(value)) {for (const nested of Object.values(value)) freeze(nested); Object.freeze(value);} return value;}

  // Translation phase splicing precedes comment recognition. The mapping keeps
  // raw UTF-8 byte positions despite CRLF, astral characters and continuations.
  function lexical(text) {
    const bytes = new Uint32Array(text.length + 1);
    let count = 0;
    for (let i = 0; i < text.length;) {
      const point = text.codePointAt(i), width = point > 0xffff ? 2 : 1;
      bytes[i] = count; if (width === 2) bytes[i + 1] = count;
      count += point < 0x80 ? 1 : point < 0x800 ? 2 : point < 0x10000 ? 3 : 4;
      i += width; bytes[i] = count;
    }
    const chars = [], offsets = [];
    for (let i = 0; i < text.length; ++i) {
      if (text[i] === '\\' && (text[i + 1] === '\n' || (text[i + 1] === '\r' && text[i + 2] === '\n'))) {
        i += text[i + 1] === '\r' ? 2 : 1; continue;
      }
      offsets.push(bytes[i]); chars.push(text[i]);
    }
    offsets.push(count);
    const logical = chars.join(''), clean = [...chars];
    let state = 'code', quote = '';
    for (let i = 0; i < chars.length; ++i) {
      const ch = chars[i], next = chars[i + 1];
      if (state === 'block') {if (ch !== '\n' && ch !== '\r') clean[i] = ' '; if (ch === '*' && next === '/') {clean[++i] = ' '; state = 'code';} continue;}
      if (state === 'line') {if (ch === '\n') state = 'code'; else if (ch !== '\r') clean[i] = ' '; continue;}
      if (state === 'quote') {
        if (ch !== '\n' && ch !== '\r') clean[i] = ' ';
        if (ch === '\\' && i + 1 < chars.length) {if (chars[i + 1] !== '\n') clean[++i] = ' ';}
        else if (ch === quote || ch === '\n') state = 'code';
        continue;
      }
      if (ch === '/' && next === '*') {clean[i] = clean[++i] = ' '; state = 'block';}
      else if (ch === '/' && next === '/') {clean[i] = clean[++i] = ' '; state = 'line';}
      else if (ch === '"' || ch === "'") {quote = ch; clean[i] = ' '; state = 'quote';}
    }
    return {logical, clean: clean.join(''), offsets, bytes: count, unterminated: state === 'block' || state === 'quote'};
  }
  function identifiers(expression) {
    const lex = lexical(expression); let text = lex.clean;
    const queries = [];
    const query = /\b(__has_feature|__has_extension|__has_attribute|__has_c_attribute|__has_builtin|__has_include_next|__has_include|__is_identifier)\s*\(/g;
    let match;
    while ((match = query.exec(text))) {
      let depth = 1, end = query.lastIndex;
      while (end < text.length && depth) {if (text[end] === '(') ++depth; else if (text[end] === ')') --depth; ++end;}
      queries.push({operator: match[1], argument: lex.logical.slice(query.lastIndex, end - 1).trim()});
      text = text.slice(0, match.index) + ' '.repeat(end - match.index) + text.slice(end);
      query.lastIndex = end;
    }
    return {identifiers: names(text.replace(/\b[0-9](?:[eEpP][+-]|[A-Za-z_0-9.])*/g, match => ' '.repeat(match.length))).filter(name => name !== 'defined'), queries};
  }
  function scan(text) {
    const lex = lexical(text), directives = [], branches = [], definitions = [], pragmas = [], issues = [];
    if (lex.unterminated) issues.push('unterminated-comment-or-literal');
    const stack = [];
    const guards = () => stack.map(frame => frame.current);
    let begin = 0;
    while (begin < lex.clean.length) {
      let end = lex.clean.indexOf('\n', begin); if (end < 0) end = lex.clean.length;
      const line = lex.clean.slice(begin, end).replace(/\r$/, ''), match = /^\s*#\s*([A-Za-z_][A-Za-z_0-9]*)\b(.*)$/.exec(line);
      if (/^\s*%:/.test(line) || /\?\?[=/]/.test(line)) issues.push('unsupported-directive-digraph-or-trigraph');
      if (match) {
        const hash = begin + line.indexOf('#'), commandEnd = begin + match[0].length - match[2].length;
        const raw = lex.logical.slice(commandEnd, end).trim();
        const directive = {kind: match[1], argument: raw, begin_bytes: lex.offsets[hash],
          end_bytes: lex.offsets[end < lex.clean.length ? end + 1 : end], guards: guards()};
        directives.push(directive);
        if (['if', 'ifdef', 'ifndef'].includes(directive.kind)) {
          const branch = {...directive, body_begin_bytes: directive.end_bytes, body_end_bytes: lex.bytes,
            previous: [], ...identifiers(raw), include_guard: false};
          const index = branches.push(branch) - 1;
          stack.push({current: index, members: [index], outer: directive.guards});
        } else if (['elif', 'elifdef', 'elifndef', 'else'].includes(directive.kind)) {
          const frame = stack.at(-1);
          if (!frame) issues.push('unmatched-' + directive.kind);
          else {
            branches[frame.current].body_end_bytes = directive.begin_bytes;
            const branch = {...directive, guards: frame.outer, body_begin_bytes: directive.end_bytes, body_end_bytes: lex.bytes,
              previous: [...frame.members], ...identifiers(raw), include_guard: false};
            frame.current = branches.push(branch) - 1; frame.members.push(frame.current);
          }
        } else if (directive.kind === 'endif') {
          const frame = stack.pop();
          if (!frame) issues.push('unmatched-endif');
          else {branches[frame.current].body_end_bytes = directive.begin_bytes; for (const member of frame.members) branches[member].matching_endif_bytes = directive.begin_bytes; frame.end = directive.end_bytes;}
        } else if (directive.kind === 'define') {
          const definition = /^([A-Za-z_][A-Za-z_0-9]*)(\([^)]*\))?\s*([\s\S]*)$/.exec(raw);
          if (!definition) issues.push('unparsed-macro-definition');
          else {
            const parameters = definition[2] ? names(definition[2]) : [];
            definitions.push({...directive, name: definition[1], parameters, function_like: Boolean(definition[2]),
              replacement: definition[3], ...identifiers(definition[3])});
          }
        } else if (directive.kind === 'pragma') pragmas.push({...directive, ...identifiers(raw)});
        else if (!['include', 'include_next', 'undef', 'line', 'error', 'warning', 'ident', 'import', ''].includes(directive.kind)) issues.push('unindexed-directive-' + directive.kind);
      }
      begin = end + 1;
    }
    if (stack.length) issues.push('unclosed-condition');
    for (const branch of branches) {
      if (branch.kind !== 'ifndef' || !/^[A-Za-z_][A-Za-z_0-9]*$/.test(branch.argument) || branch.matching_endif_bytes === undefined || branches.some(other => other.previous.includes(branches.indexOf(branch)))) continue;
      const next = directives.find(directive => directive.begin_bytes >= branch.end_bytes);
      const body = new TextDecoder().decode(new TextEncoder().encode(text).slice(branch.body_begin_bytes, branch.matching_endif_bytes));
      const hasPayload = lexical(body).clean.replace(/^\s*#.*$/gm, '').trim() || directives.some(directive => ['include', 'include_next'].includes(directive.kind) && directive.guards.includes(branches.indexOf(branch)));
      if (hasPayload && next?.kind === 'define' && next.argument.split(/\s/)[0] === branch.argument && next.guards.includes(branches.indexOf(branch)) && !directives.some(directive => directive.kind === 'undef' && directive.argument === branch.argument)) branch.include_guard = true;
    }
    // A conventional guard requires surrounding-file structure, not its name.
    const first = directives[0], second = directives[1], last = directives.at(-1);
    if (first && second && last && first.kind === 'ifndef' && /^\w+$/.test(first.argument) &&
        second.kind === 'define' && second.argument.split(/\s/)[0] === first.argument && last.kind === 'endif') {
      const before = new TextEncoder().encode(text).slice(0, first.begin_bytes);
      const after = new TextEncoder().encode(text).slice(last.end_bytes);
      if (!lexical(new TextDecoder().decode(before)).clean.trim() && !lexical(new TextDecoder().decode(after)).clean.trim() &&
          branches[0]?.body_end_bytes === last.begin_bytes && branches[0]?.previous.length === 0 && !branches.some(branch => branch.previous.includes(0))) branches[0].include_guard = true;
    }
    return {branches, definitions, pragmas, directives, issues: [...new Set(issues)].sort(order), bytes: lex.bytes};
  }

  const ignoredIdentifiers = new Set(names('L u U u8 __has_feature __has_extension __has_attribute __has_c_attribute __has_builtin __has_include __has_include_next __is_identifier defined struct union enum typedef const volatile restrict unsigned signed long short int char float double void _Bool _Alignas _Alignof sizeof __attribute__ aligned packed push pop pack'));
  const physical = point => point && point.file && Number.isSafeInteger(point.offset_bytes);
  const overlaps = (a, b) => a && b && a.file === b.file && a.begin_bytes < b.end_bytes && b.begin_bytes < a.end_bytes;
  const contains = (range, offset) => range && range.begin_bytes <= offset && offset < range.end_bytes;
  function baseDocument(document) {
    const result = clone(document);
    result.dependencies = {contract: 'platydoc.dependencies', version: 1, status: 'not-computed', coverage: 'unknown',
      configuration_ids: [result.configuration.id], relations: []};
    return result;
  }
  function typeMeaning(type, document, active = new Set()) {
    if (!type) return null;
    const result = {...type};
    result.aliases = (type.aliases || []).map(alias => {
      if (active.has(alias)) return {id: alias, recursive: true};
      const variant = document.declarations.variants.find(v => v.declaration_id === alias);
      return {id: alias, underlying: typeMeaning(variant?.underlying_type, document, new Set([...active, alias]))};
    });
    if (type.element) result.element = typeMeaning(type.element, document, active);
    if (type.pointee) result.pointee = typeMeaning(type.pointee, document, active);
    return result;
  }
  function effectBetween(a, b, declarationID) {
    const left = a.layouts.entries.find(v => v.declaration_id === declarationID), right = b.layouts.entries.find(v => v.declaration_id === declarationID);
    if (!left || !right || a.layouts.status !== 'success' || b.layouts.status !== 'success') return null;
    const components = [];
    if (left.size_bytes !== right.size_bytes) components.push('size');
    if (left.alignment_bytes !== right.alignment_bytes) components.push('alignment');
    const lf = new Map(left.fields.map(f => [f.declaration_id, f])), rf = new Map(right.fields.map(f => [f.declaration_id, f]));
    for (const fieldID of new Set([...lf.keys(), ...rf.keys()])) {
      const x = lf.get(fieldID), y = rf.get(fieldID);
      if (!x || !y) {components.push('field-presence'); continue;}
      if (x.offset_bits !== y.offset_bits) components.push('field-offset');
      if (x.bit_width !== y.bit_width) components.push('bit-width');
      if (C.canonical(typeMeaning(x.type, a)) !== C.canonical(typeMeaning(y.type, b))) components.push('field-type');
    }
    return [...new Set(components)].sort(order);
  }
  function directive(request, name) {
    return own(request.macros || {}, name) ? {state: request.macros[name] === null ? 'explicit-undefined' : 'defined', value: request.macros[name]} : {state: 'not-requested'};
  }
  function comparisonContext(request) {
    const result = {...request};
    for (const name of ['macros', 'records', 'observe_macros', 'trace_files', 'trace_dependencies', 'dependency_files']) delete result[name];
    return result;
  }
  async function discover(entries, options = {}) {
    if (!Array.isArray(entries) || !entries.length) fail('nonempty entries required');
    const nodes = new Map(), edges = new Map(), sources = new Map(), observations = [], configurationMap = new Map(), issues = new Set();
    const node = value => {
      const existing = nodes.get(value.id);
      if (existing && C.canonical(existing) !== C.canonical(value)) fail('conflicting node ' + value.id);
      nodes.set(value.id, value); return value.id;
    };
    const macro = name => node({id: 'macro:' + name, kind: 'macro', name, source_id: null, range: null, details: {category: /^__(?:has_|is_)/.test(name) ? 'compiler-query-availability' : name === 'volatile' ? 'build-context-macro' : 'preprocessor-macro'}});
    const edge = (from, to, kind, storage, evidence, configuration) => {
      if (!from || !to || from === to) return;
      const key = C.canonical([from, to, kind, storage]);
      if (!edges.has(key)) edges.set(key, {from, to, kind, storage, configurations: new Set(), evidence: new Map()});
      const value = edges.get(key); if (configuration) value.configurations.add(configuration);
      if (evidence) value.evidence.set(C.canonical(evidence), evidence);
    };
    const configurations = [], scans = new Map(), entryContexts = [];
    for (const entry of entries) {
      if (!entry || typeof entry.name !== 'string' || !entry.request || !entry.result || !entry.document) fail('entry requires name/request/result/document');
      const document = baseDocument(entry.document); await C.validate(document);
      const requested = Object.fromEntries(Object.entries(entry.request).filter(([key]) => key !== 'files'));
      requested.macros = Object.fromEntries(Object.entries(entry.request.macros || {}).map(([name, value]) => [name, value === null ? {state: 'undefined'} : {state: 'defined', replacement: value}]));
      if (C.canonical(requested) !== C.canonical(document.configuration.requested)) fail('request/context mismatch');
      const configID = document.configuration.id, baselineHash = await C.sha256(C.canonical(document));
      if (configurationMap.has(configID)) {
        const existing = configurationMap.get(configID);
        if (existing.base_contract_sha256 !== baselineHash) fail('same configuration has conflicting documents');
        existing.names.push(entry.name); continue;
      }
      const trace = entry.result.dependency_trace;
      if (!trace || trace.contract !== 'platydoc.compiler-dependency-evidence' || trace.version !== 1) fail('compiler dependency trace required');
      const configuration = {id: configID, names: [entry.name], status: document.layouts.status, base_contract_sha256: baselineHash,
        requested_macros: clone(entry.request.macros || {}), effective_macros: clone(document.configuration.effective.macros),
        trace: {truncated: trace.truncated, dropped_events: trace.dropped_events, retained_events: trace.events.length,
          events_before_filter: trace.filtering.events_before, relevant_files: [...trace.filtering.relevant_files].sort(order)}};
      configurationMap.set(configID, configuration); configurations.push(configuration);
      if (trace.truncated) issues.add('compiler-event-limit');
      const fileMap = new Map(), wanted = new Set(trace.filtering.relevant_files);
      for (const input of document.configuration.inputs) {
        const text = entry.request.files[input.path];
        if (typeof text !== 'string') fail('missing source bytes');
        if (byteLength(text) !== input.bytes || await C.sha256(text) !== input.sha256 || (entry.request.source_paths?.[input.path] || input.path) !== input.source_path) fail('source bytes/provenance mismatch');
        const sourceID = 'source:' + input.sha256 + ':' + input.path + ':' + input.source_path;
        const source = {id: sourceID, file: input.path, source_path: input.source_path, sha256: input.sha256, size_bytes: byteLength(text)};
        sources.set(sourceID, source); fileMap.set(input.path, source);
        if (!wanted.has(input.path)) continue;
        let parsed = cache.get(input.sha256);
        if (!parsed) {parsed = scan(text); cache.set(input.sha256, parsed);}
        scans.set(sourceID, parsed);
        for (const issue of parsed.issues) issues.add(issue);
      }
      const evidence = (range, description, sequence = null) => {
        const source = range && fileMap.get(range.file);
        return source ? {source_id: source.id, begin_bytes: range.begin_bytes, end_bytes: range.end_bytes,
          configuration_id: configID, sequence, description} : null;
      };
      const rawNodes = new Map(), definitionNodes = new Map();
      for (const [file, source] of fileMap) {
        const parsed = scans.get(source.id); if (!parsed) continue;
        const regions = parsed.branches.map((branch, index) => {
          const regionID = 'region:' + source.id + ':' + branch.begin_bytes + ':' + branch.kind;
          node({id: regionID, kind: 'condition', name: branch.kind + ' ' + branch.argument, source_id: source.id,
            range: {begin_bytes: branch.begin_bytes, end_bytes: branch.end_bytes},
            details: {operator: branch.kind, expression: branch.argument, body_begin_bytes: branch.body_begin_bytes,
              body_end_bytes: branch.body_end_bytes, include_guard: branch.include_guard, queries: branch.queries}});
          rawNodes.set(regionID, {branch, source, parsed, index});
          for (const name of branch.identifiers) if (!ignoredIdentifiers.has(name))
            edge(macro(name), regionID, branch.include_guard ? 'include-precondition' : 'condition-input', !branch.include_guard,
              evidence({file, ...branch}, 'raw conditional input'), configID);
          return regionID;
        });
        const guards = (item, target) => {
          for (const index of item.guards || []) edge(regions[index], target, 'conditional-region', !parsed.branches[index].include_guard,
            evidence({file, ...parsed.branches[index]}, 'enclosing conditional branch'), configID);
          for (const index of item.previous || []) edge(regions[index], target, 'alternative-branch', !parsed.branches[index].include_guard,
            evidence({file, ...parsed.branches[index]}, 'prior branch determines alternative availability'), configID);
        };
        parsed.branches.forEach((branch, index) => guards(branch, regions[index]));
        for (const definition of parsed.definitions) {
          const definitionID = 'definition:' + source.id + ':' + definition.begin_bytes + ':' + definition.name;
          node({id: definitionID, kind: 'macro-definition', name: definition.name, source_id: source.id,
            range: {begin_bytes: definition.begin_bytes, end_bytes: definition.end_bytes},
            details: {replacement: definition.replacement, parameters: definition.parameters, function_like: definition.function_like}});
          definitionNodes.set(file + ':' + definition.name + ':' + definition.begin_bytes, {id: definitionID, definition});
          guards(definition, definitionID);
        }
        for (const pragma of parsed.pragmas) {
          const pragmaID = 'pragma:' + source.id + ':' + pragma.begin_bytes;
          node({id: pragmaID, kind: 'pragma', name: pragma.argument, source_id: source.id,
            range: {begin_bytes: pragma.begin_bytes, end_bytes: pragma.end_bytes}, details: {}});
          guards(pragma, pragmaID);
          for (const name of pragma.identifiers) if (!ignoredIdentifiers.has(name)) edge(macro(name), pragmaID, 'pragma-input', true,
            evidence({file, ...pragma}, 'pragma token'), configID);
        }
      }
      const declarationMap = new Map(document.declarations.entries.map(d => [d.id, d]));
      const factMap = new Map(trace.ast.map(f => [f.id, f]));
      for (const fact of trace.ast) {
        const declaration = declarationMap.get(fact.id), anchor = declaration?.source || fact.source;
        const range = fact.expansion || fact.spelling, source = range && fileMap.get(range.file);
        node({id: fact.id, kind: declaration ? 'declaration' : 'ast-symbol', name: fact.name, source_id: source?.id || null,
          range: range ? {begin_bytes: range.begin_bytes, end_bytes: range.end_bytes} : null, details: {kind: fact.kind}});
        const connectConditions = (file, offset, target, reason) => {
          const s = fileMap.get(file), parsed = s && scans.get(s.id); if (!parsed) return;
          for (const [regionID, value] of rawNodes) if (value.source.id === s.id &&
              value.branch.body_begin_bytes <= offset && offset < value.branch.body_end_bytes)
            edge(regionID, target, reason, !value.branch.include_guard, evidence({file, ...value.branch}, reason), configID);
        };
        if (range) connectConditions(range.file, range.begin_bytes, fact.id, 'declaration-guard');
        for (const site of [...(range?.include_sites || []), ...(anchor?.includes || [])]) if (physical(site))
          connectConditions(site.file, site.offset_bytes, fact.id, 'guarded-include');
        if (declaration?.owner_id) edge(fact.id, declaration.owner_id, 'field-storage', true, evidence(range, 'field contributes to owning record'), configID);
        if (fact.container_id) {
          edge(fact.container_id, fact.id, 'enum-membership', true, evidence(range, 'enumerator value can depend on conditional predecessors'), configID);
        }
        for (const reference of fact.implicit_successor ? fact.references || [] : []) edge(reference, fact.id, 'implicit-enumerator-successor', true,
          evidence(range, 'Clang value declaration reference'), configID);
        for (const expression of fact.expressions || []) for (const reference of expression.references)
          edge(reference, fact.id, expression.role, expression.storage, evidence(expression.expansion || expression.spelling, 'Clang ' + expression.role), configID);
        if (['record', 'enum', 'type-record'].includes(fact.kind) && range) {
          // Includes inactive source regions, but does not invent inactive AST declarations.
          for (const [regionID, value] of rawNodes) if (value.source.file === range.file &&
              range.begin_bytes < value.branch.begin_bytes && value.branch.begin_bytes < range.end_bytes)
            edge(regionID, fact.id, 'potential-inactive-member', !value.branch.include_guard,
              evidence({file: range.file, ...value.branch}, 'conditional source region inside declaration'), configID);
        }
      }
      const typeEdges = (type, target, storage, range) => {
        if (!type) return;
        for (const alias of type.aliases || []) edge(alias, target, storage ? 'alias-storage' : 'alias-reference', storage, evidence(range, 'Clang typedef resolution'), configID);
        if (type.record_id) edge(type.record_id, target, storage ? 'embedded-storage' : 'pointer-reference', storage, evidence(range, storage ? 'embedded record storage' : 'pointer referent does not contribute storage'), configID);
        if (type.element) typeEdges(type.element, target, storage, range);
        if (type.pointee) typeEdges(type.pointee, target, false, range);
      };
      for (const layout of document.layouts.entries) for (const field of layout.fields) typeEdges(field.type, field.declaration_id, true, factMap.get(field.declaration_id)?.expansion);
      for (const variant of document.declarations.variants) if (variant.underlying_type) typeEdges(variant.underlying_type, variant.declaration_id, true, factMap.get(variant.declaration_id)?.expansion);
      const definitionFor = state => {
        if (!physical(state.definition)) return macro(state.name);
        const parsed = fileMap.get(state.definition.file), candidates = parsed && scans.get(parsed.id)?.definitions;
        const definition = candidates?.find(d => d.name === state.name && d.begin_bytes <= state.definition.offset_bytes && state.definition.offset_bytes < d.end_bytes);
        return definition ? definitionNodes.get(state.definition.file + ':' + state.name + ':' + definition.begin_bytes)?.id : macro(state.name);
      };
      const eventMap = new Map(trace.events.map(event => [event.sequence, event]));
      const expanded = new Map();
      for (const event of trace.events) {
        const states = (event.macro_states || []).map(index => trace.macros[index]);
        if (event.macro !== undefined) states.push(trace.macros[event.macro]);
        if (states.some(state => !state)) fail('dangling compiler macro state');
        if (['if', 'ifdef', 'ifndef', 'elif', 'elifdef', 'elifndef'].includes(event.kind)) {
          const source = fileMap.get(event.location.file), parsed = source && scans.get(source.id);
          const branch = parsed?.branches.find(b => b.begin_bytes <= event.location.offset_bytes && event.location.offset_bytes < b.end_bytes);
          if (branch) {
            const region = [...rawNodes].find(([, r]) => r.source.id === source.id && r.branch === branch)?.[0];
            observations.push({configuration_id: configID, region_id: region, sequence: event.sequence, value: event.value ?? event.evaluation ?? null,
              include_sites: clone(event.range?.include_sites || []), macros: clone(states)});
            for (const state of states) if (branch.identifiers.includes(state.name)) edge(definitionFor(state), region, 'evaluated-condition-input', !branch.include_guard,
              evidence(event.range, 'event-time definition in condition', event.sequence), configID);
          }
        }
        if (event.kind !== 'expand') continue;
        const state = trace.macros[event.macro], origin = definitionFor(state);
        if (event.range) {
          if (!expanded.has(event.range.file)) expanded.set(event.range.file, []);
          expanded.get(event.range.file).push({event, state, origin});
        }
      }
      for (const fact of trace.ast) {
        const layoutField = document.layouts.entries.flatMap(layout => layout.fields).find(field => field.declaration_id === fact.id);
        const variant = document.declarations.variants.find(variant => variant.declaration_id === fact.id);
        const pointer = (layoutField?.type || variant?.underlying_type)?.kind === 'pointer';
        const ranges = ['record', 'enum', 'type-record'].includes(fact.kind) ? (fact.attributes || []).map(attribute => attribute.expansion).filter(Boolean) : [fact.expansion].filter(Boolean);
        for (const range of ranges) for (const {event, origin} of expanded.get(range.file) || []) if (overlaps(range, event.range)) {
          const expressions = (fact.expressions || []).filter(expression => overlaps(expression.expansion, event.range));
          const storage = expressions.length ? expressions.some(expression => expression.storage) : !pointer;
          edge(origin, fact.id, 'macro-expansion', storage, evidence(event.range, 'event-time macro expansion', event.sequence), configID);
        }
        // Only currently active pack state reaches the record, not already-popped frames.
        if (fact.kind === 'record') {
          const stack = []; let current = null, uncertain = false;
          for (const sequence of fact.preceding_pragmas || []) {
            const event = eventMap.get(sequence); if (!event) fail('dangling pragma event sequence');
            const source = fileMap.get(event.location.file), parsed = source && scans.get(source.id);
            const pragma = parsed?.pragmas.find(p => p.begin_bytes <= event.location.offset_bytes && event.location.offset_bytes < p.end_bytes);
            if (!pragma || !/^pack\s*\(/.test(pragma.argument)) continue;
            if (!/^pack\s*\(\s*(?:push(?:\s*,\s*[0-9]+)?|pop|[0-9]+)?\s*\)$/.test(pragma.argument)) {issues.add('unsupported-named-or-combined-pack-state'); uncertain = true; continue;}
            if (/\bpush\b/.test(pragma.argument)) {stack.push({current, uncertain}); current = {source, pragma, event};}
            else if (/\bpop\b/.test(pragma.argument)) {const prior = stack.pop(); current = prior?.current || null; uncertain = prior?.uncertain ?? uncertain;}
            else {current = /^pack\s*\(\s*\)/.test(pragma.argument) ? null : {source, pragma, event}; uncertain = false;}
          }
          if (current && !uncertain) edge('pragma:' + current.source.id + ':' + current.pragma.begin_bytes, fact.id, 'packing-state', true,
            evidence({file: current.source.file, ...current.pragma}, 'active pragma pack state', current.event.sequence), configID);
        }
      }
      // Resolve replacement dependencies at the actual expansion time. Raw tokens
      // alone do not prove that an identifier was a macro in this occurrence.
      for (const events of expanded.values()) for (const outer of events) {
        const definitionNode = nodes.get(outer.origin);
        if (definitionNode?.kind !== 'macro-definition') continue;
        const tokens = identifiers(definitionNode.details.replacement).identifiers.filter(name => !definitionNode.details.parameters.includes(name));
        for (const token of tokens) {
          const nested = events.find(inner => inner.state.name === token && inner.event.sequence >= outer.event.sequence && overlaps(inner.event.range, outer.event.range));
          if (nested) edge(nested.origin, outer.origin, 'macro-replacement', true, evidence(outer.event.range, 'nested event-time replacement expansion', outer.event.sequence), configID);
        }
      }
      entryContexts.push({entry, document, configuration});
    }
    // Drop edges to omitted/non-layout AST providers rather than inventing IDs.
    for (const [key, value] of edges) if (!nodes.has(value.from) || !nodes.has(value.to)) {edges.delete(key); issues.add('unresolved-ast-provider');}
    const rootIDs = new Set(entryContexts.flatMap(context => context.document.layouts.entries.map(layout => layout.declaration_id)));
    const reverse = new Map(); for (const [key, relation] of edges) {if (!reverse.has(relation.to)) reverse.set(relation.to, []); reverse.get(relation.to).push([key, relation]);}
    const usefulNodes = new Set(rootIDs), usefulEdges = new Set(), pending = [...rootIDs];
    while (pending.length) {
      const target = pending.pop();
      for (const [key, relation] of reverse.get(target) || []) {
        usefulEdges.add(key); if (!usefulNodes.has(relation.from)) {usefulNodes.add(relation.from); pending.push(relation.from);}
      }
    }
    const omitted = {nodes: nodes.size - usefulNodes.size, edges: edges.size - usefulEdges.size};
    for (const key of edges.keys()) if (!usefulEdges.has(key)) edges.delete(key);
    for (const key of nodes.keys()) if (!usefulNodes.has(key)) nodes.delete(key);
    const relevantObservations = observations.filter(observation => nodes.has(observation.region_id));
    const edgeList = [...edges].sort(([a], [b]) => order(a, b)).map(([, value], index) => ({id: 'edge:' + index,
      from: value.from, to: value.to, kind: value.kind, storage: value.storage,
      configurations: [...value.configurations].sort(order), evidence: [...value.evidence.values()].sort((a, b) => order(C.canonical(a), C.canonical(b)))}));
    const comparisons = [];
    for (let i = 0; i < entryContexts.length; ++i) for (let j = i + 1; j < entryContexts.length; ++j) {
      const left = entryContexts[i], right = entryContexts[j], a = left.entry.request, b = right.entry.request;
      const changed = [...new Set([...Object.keys(a.macros || {}), ...Object.keys(b.macros || {})])].filter(name => C.canonical(directive(a, name)) !== C.canonical(directive(b, name))).sort(order);
      const sameContext = C.canonical(comparisonContext(a)) === C.canonical(comparisonContext(b));
      const common = left.document.layouts.entries.map(l => l.declaration_id).filter(declarationID => right.document.layouts.entries.some(l => l.declaration_id === declarationID));
      const effects = common.map(declaration_id => ({declaration_id, components: effectBetween(left.document, right.document, declaration_id)})).filter(effect => effect.components !== null);
      comparisons.push({id: 'comparison:' + comparisons.length, from: left.configuration.id, to: right.configuration.id, changed_macros: changed,
        attribution: sameContext && changed.length === 1 ? 'single-macro-intervention' : 'joint-context-difference',
        context_equal_except_macros: sameContext, effects});
    }
    const incoming = new Map();
    for (const relation of edgeList) if (relation.storage) {
      if (!incoming.has(relation.to)) incoming.set(relation.to, []); incoming.get(relation.to).push(relation);
    }
    const roots = [...new Set(entryContexts.flatMap(context => context.document.layouts.entries.map(l => l.declaration_id)))].sort(order), controls = [];
    for (const rootID of roots) {
      const found = new Map();
      for (const configuration of configurations) {
        if (!entryContexts.find(context => context.configuration.id === configuration.id)?.document.layouts.entries.some(layout => layout.declaration_id === rootID)) continue;
        const queue = [{id: rootID, path: []}], visited = new Set();
        while (queue.length) {
          const next = queue.shift(); if (visited.has(next.id)) continue; visited.add(next.id);
          const current = nodes.get(next.id);
          if (current?.kind === 'macro') {if (!found.has(current.name)) found.set(current.name, next.path); continue;}
          for (const relation of incoming.get(next.id) || []) if (relation.configurations.includes(configuration.id)) queue.push({id: relation.from, path: [relation.id, ...next.path]});
        }
      }
      for (const [name, path] of [...found].sort(([a], [b]) => order(a, b))) {
        const relevant = comparisons.filter(comparison => comparison.attribution === 'single-macro-intervention' && comparison.changed_macros[0] === name && comparison.effects.some(effect => effect.declaration_id === rootID));
        const changes = relevant.filter(comparison => comparison.effects.some(effect => effect.declaration_id === rootID && effect.components.length));
        controls.push({declaration_id: rootID, macro: name, classification: changes.length ? 'demonstrated' : 'potential', paths: [path],
          comparisons: relevant.map(comparison => comparison.id), observed_changes: changes.map(comparison => comparison.id),
          observed_no_change: relevant.filter(comparison => !changes.includes(comparison)).map(comparison => comparison.id)});
      }
    }
    const usedSources = new Set([...nodes.values()].map(node => node.source_id).filter(Boolean));
    for (const edge of edgeList) for (const evidence of edge.evidence) usedSources.add(evidence.source_id);
    const analysis = {contract: 'platydoc.dependency-analysis', version: 1, space: {id: options.space_id || 'explicit-inputs',
      kind: 'explicit-named-configurations', cases: entries.map(entry => ({name: entry.name, configuration_id: entry.document.configuration.id})),
      enumeration: 'all-supplied-cases', arbitrary_combination_coverage: 'unknown'},
      configurations: configurations.sort((a, b) => order(a.id, b.id)), sources: [...sources.values()].filter(source => usedSources.has(source.id)).sort((a, b) => order(a.id, b.id)),
      nodes: [...nodes.values()].sort((a, b) => order(a.id, b.id)), edges: edgeList,
      observations: relevantObservations.sort((a, b) => order(a.configuration_id, b.configuration_id) || a.sequence - b.sequence), comparisons, controls,
      coverage: {discovery: 'partial', conditional_index: 'supplied-relevant-source-files', inactive_declarations: 'source-regions-only',
        unobserved_branches: 'unknown', omitted_events: 'unknown', issues: [...issues].sort(order),
        omitted_graph: omitted, limitations: ['raw-conditions-not-arbitrarily-evaluated', 'unvisited-includes-and-configurations-unknown', 'non-value-type-expressions-partial', 'packing-named-stack-subset']}};
    analysis.id = await id('dependency-analysis-v1', analysis);
    await validate(analysis); return analysis;
  }
  function controlsFor(analysis, declarationID) {return analysis.controls.filter(control => control.declaration_id === declarationID);}
  async function validate(analysis, documents = []) {
    const bindings = async () => {for (const document of documents) {
      const configuration = analysis.configurations.find(configuration => configuration.id === document.configuration.id);
      if (!configuration || configuration.base_contract_sha256 !== await C.sha256(C.canonical(baseDocument(document)))) fail('analysis/document binding mismatch');
    }};
    if (validatedAnalyses.has(analysis)) {await bindings(); return analysis;}
    const keys = (value, expected) => {
      if (!value || typeof value !== 'object' || Array.isArray(value) || C.canonical(Object.keys(value).sort(order)) !== C.canonical([...expected].sort(order))) fail('unexpected object shape');
    };
    const integer = value => {if (!Number.isSafeInteger(value) || value < 0) fail('unsafe numeric evidence');};
    keys(analysis, ['contract', 'version', 'id', 'space', 'configurations', 'sources', 'nodes', 'edges', 'observations', 'comparisons', 'controls', 'coverage']);
    if (analysis.contract !== 'platydoc.dependency-analysis' || analysis.version !== 1) fail('unsupported analysis version');
    C.canonical(analysis);
    const {id: analysisID, ...material} = analysis;
    if (analysisID !== await id('dependency-analysis-v1', material)) fail('analysis hash mismatch');
    const uniqueMap = (list, label) => {
      if (!Array.isArray(list)) fail('expected ' + label + ' array');
      const map = new Map(); for (const value of list) {if (!value || typeof value.id !== 'string' || map.has(value.id)) fail('duplicate/invalid ' + label); map.set(value.id, value);} return map;
    };
    const sources = uniqueMap(analysis.sources, 'source'), nodes = uniqueMap(analysis.nodes, 'node'), configurations = uniqueMap(analysis.configurations, 'configuration'), edges = uniqueMap(analysis.edges, 'edge'), comparisons = uniqueMap(analysis.comparisons, 'comparison');
    keys(analysis.space, ['id', 'kind', 'cases', 'enumeration', 'arbitrary_combination_coverage']);
    if (typeof analysis.space.id !== 'string' || analysis.space.kind !== 'explicit-named-configurations' || analysis.space.enumeration !== 'all-supplied-cases' || analysis.space.arbitrary_combination_coverage !== 'unknown') fail('invalid finite space coverage');
    const caseNames = new Set();
    for (const entry of analysis.space.cases) {keys(entry, ['name', 'configuration_id']); if (typeof entry.name !== 'string' || caseNames.has(entry.name) || !configurations.has(entry.configuration_id)) fail('invalid named case'); caseNames.add(entry.name);}
    for (const source of sources.values()) {keys(source, ['id', 'file', 'source_path', 'sha256', 'size_bytes']); integer(source.size_bytes);
      if (!/^[a-f0-9]{64}$/.test(source.sha256) || typeof source.file !== 'string' || !source.file.startsWith('/inputs/') || typeof source.source_path !== 'string' || source.id !== 'source:' + source.sha256 + ':' + source.file + ':' + source.source_path) fail('invalid source binding');}
    const checkRange = (sourceID, begin, end) => {integer(begin); integer(end); if (!sources.has(sourceID) || begin > end || end > sources.get(sourceID).size_bytes) fail('source range outside supplied bytes');};
    const checkEvidence = evidence => {keys(evidence, ['source_id', 'begin_bytes', 'end_bytes', 'configuration_id', 'sequence', 'description']);
      checkRange(evidence.source_id, evidence.begin_bytes, evidence.end_bytes); if (!configurations.has(evidence.configuration_id) || typeof evidence.description !== 'string') fail('invalid evidence binding'); if (evidence.sequence !== null) integer(evidence.sequence);};
    for (const configuration of configurations.values()) {
      keys(configuration, ['id', 'names', 'status', 'base_contract_sha256', 'requested_macros', 'effective_macros', 'trace']);
      if (!/^config-v1:[a-f0-9]{64}$/.test(configuration.id) || !/^[a-f0-9]{64}$/.test(configuration.base_contract_sha256) || !['success', 'invalid-configuration', 'compilation-error', 'incomplete-type', 'unsupported'].includes(configuration.status)) fail('invalid configuration binding');
      keys(configuration.trace, ['truncated', 'dropped_events', 'retained_events', 'events_before_filter', 'relevant_files']);
      if (typeof configuration.trace.truncated !== 'boolean') fail('invalid trace truncation');
      for (const name of ['dropped_events', 'retained_events', 'events_before_filter']) integer(configuration.trace[name]);
      if (configuration.trace.retained_events > configuration.trace.events_before_filter || (!configuration.trace.truncated && configuration.trace.dropped_events)) fail('inconsistent event coverage');
      for (const name of configuration.names) if (!analysis.space.cases.some(entry => entry.name === name && entry.configuration_id === configuration.id)) fail('configuration case alias mismatch');
    }
    for (const node of nodes.values()) {
      keys(node, ['id', 'kind', 'name', 'source_id', 'range', 'details']);
      if (!['macro', 'condition', 'macro-definition', 'pragma', 'declaration', 'ast-symbol'].includes(node.kind) || typeof node.name !== 'string') fail('invalid graph node');
      if (node.source_id === null) {if (node.range !== null) fail('range without source');}
      else {keys(node.range, ['begin_bytes', 'end_bytes']); checkRange(node.source_id, node.range.begin_bytes, node.range.end_bytes);}
      if (node.kind === 'macro') {
        keys(node.details, ['category']);
        if (!/^[A-Za-z_][A-Za-z_0-9]*$/.test(node.name) || node.id !== 'macro:' + node.name || !['compiler-query-availability', 'build-context-macro', 'preprocessor-macro'].includes(node.details.category)) fail('invalid macro control');
      }
      if (node.kind === 'condition') {integer(node.details.body_begin_bytes); integer(node.details.body_end_bytes); checkRange(node.source_id, node.details.body_begin_bytes, node.details.body_end_bytes); if (typeof node.details.include_guard !== 'boolean') fail('invalid guard classification');}
    }
    const kinds = new Set(['include-precondition', 'condition-input', 'conditional-region', 'alternative-branch', 'pragma-input', 'declaration-guard', 'guarded-include', 'field-storage', 'enum-membership', 'implicit-enumerator-successor', 'expression-reference', 'array-bound', 'bit-width', 'alignment', 'initializer', 'enum-initializer', 'potential-inactive-member', 'alias-storage', 'alias-reference', 'embedded-storage', 'pointer-reference', 'evaluated-condition-input', 'macro-expansion', 'packing-state', 'macro-replacement']);
    for (const relation of edges.values()) {
      keys(relation, ['id', 'from', 'to', 'kind', 'storage', 'configurations', 'evidence']);
      if (!nodes.has(relation.from) || !nodes.has(relation.to) || !kinds.has(relation.kind) || typeof relation.storage !== 'boolean' || !relation.evidence.length || relation.configurations.some(config => !configurations.has(config))) fail('dangling/invalid graph edge');
      if (['pointer-reference', 'alias-reference', 'include-precondition'].includes(relation.kind) && relation.storage) fail('non-storage edge propagates layout');
      relation.evidence.forEach(evidence => {checkEvidence(evidence); if (!relation.configurations.includes(evidence.configuration_id)) fail('edge evidence outside applicability');});
    }
    for (const observation of analysis.observations) {
      keys(observation, ['configuration_id', 'region_id', 'sequence', 'value', 'include_sites', 'macros']); integer(observation.sequence);
      if (!configurations.has(observation.configuration_id) || nodes.get(observation.region_id)?.kind !== 'condition' || ![null, 'true', 'false', 'not-evaluated'].includes(observation.value)) fail('dangling/invalid conditional observation');
      const site = point => {
        keys(point, ['file', 'line', 'column', 'offset_bytes']);
        if (typeof point.file !== 'string') fail('invalid source site path');
        integer(point.line); integer(point.column); integer(point.offset_bytes);
        if (point.file) {const candidates = analysis.sources.filter(source => source.file === point.file);
          // Include ancestors may be pruned from the retained graph. Their file
          // names stay evidence, but are never presented as byte-bound nodes.
          if (candidates.length && !candidates.some(source => point.offset_bytes <= source.size_bytes)) fail('source site out of bounds');}
      };
      if (!Array.isArray(observation.include_sites) || !Array.isArray(observation.macros)) fail('observation arrays required');
      observation.include_sites.forEach(site);
      for (const state of observation.macros) {
        keys(state, ['name', 'defined', 'replacement', 'function_like', 'builtin', 'parameters', 'definition']);
        if (!/^[A-Za-z_][A-Za-z_0-9]*$/.test(state.name) || typeof state.defined !== 'boolean' || typeof state.function_like !== 'boolean' || typeof state.builtin !== 'boolean' || !Array.isArray(state.parameters) || state.parameters.some(name => typeof name !== 'string')) fail('invalid event-time macro state');
        if (state.defined ? typeof state.replacement !== 'string' : state.replacement !== null) fail('macro definition/replacement mismatch');
        if (state.definition !== null) site(state.definition);
      }
    }
    for (const comparison of comparisons.values()) {
      keys(comparison, ['id', 'from', 'to', 'changed_macros', 'attribution', 'context_equal_except_macros', 'effects']);
      if (!configurations.has(comparison.from) || !configurations.has(comparison.to) || comparison.from === comparison.to || !['single-macro-intervention', 'joint-context-difference'].includes(comparison.attribution) || typeof comparison.context_equal_except_macros !== 'boolean') fail('invalid comparison');
      if (comparison.attribution === 'single-macro-intervention' && (!comparison.context_equal_except_macros || comparison.changed_macros.length !== 1)) fail('confounded causal attribution');
      for (const effect of comparison.effects) {keys(effect, ['declaration_id', 'components']); if (!nodes.has(effect.declaration_id) || effect.components.some(component => !['size', 'alignment', 'field-presence', 'field-offset', 'bit-width', 'field-type'].includes(component))) fail('invalid observed effect');}
    }
    for (const control of analysis.controls) {
      keys(control, ['declaration_id', 'macro', 'classification', 'paths', 'comparisons', 'observed_changes', 'observed_no_change']);
      if (!nodes.has(control.declaration_id) || !nodes.has('macro:' + control.macro) || !['potential', 'demonstrated'].includes(control.classification) || !control.paths.length) fail('invalid control');
      for (const path of control.paths) {
        let at = 'macro:' + control.macro; if (!path.length) fail('empty reason path');
        for (const relationID of path) {const relation = edges.get(relationID); if (!relation || !relation.storage || relation.from !== at) fail('broken storage reason path'); at = relation.to;}
        if (at !== control.declaration_id) fail('reason path ends at wrong declaration');
        const applicability = path.map(id => edges.get(id).configurations);
        if (!applicability[0].some(configuration => applicability.every(list => list.includes(configuration)))) fail('reason path mixes incompatible configurations');
      }
      for (const comparisonID of [...control.comparisons, ...control.observed_changes, ...control.observed_no_change]) {
        const comparison = comparisons.get(comparisonID);
        if (!comparison || comparison.attribution !== 'single-macro-intervention' || comparison.changed_macros[0] !== control.macro || !comparison.effects.some(effect => effect.declaration_id === control.declaration_id)) fail('uncontrolled evidence attribution');
      }
      if ((control.classification === 'demonstrated') !== Boolean(control.observed_changes.length)) fail('demonstration status mismatch');
      for (const comparisonID of control.observed_changes) if (!comparisons.get(comparisonID).effects.find(effect => effect.declaration_id === control.declaration_id).components.length) fail('claimed change has no effect');
      for (const comparisonID of control.observed_no_change) if (comparisons.get(comparisonID).effects.find(effect => effect.declaration_id === control.declaration_id).components.length) fail('no-change evidence changes layout');
    }
    keys(analysis.coverage, ['discovery', 'conditional_index', 'inactive_declarations', 'unobserved_branches', 'omitted_events', 'issues', 'limitations', 'omitted_graph']);
    if (analysis.coverage.discovery !== 'partial' || analysis.coverage.unobserved_branches !== 'unknown' || analysis.coverage.omitted_events !== 'unknown') fail('unsupported completeness claim');
    await bindings();
    freeze(analysis); validatedAnalyses.add(analysis);
    return analysis;
  }
  async function attach(document, analysis) {
    await validate(analysis, [document]);
    const result = baseDocument(document);
    result.dependencies = {contract: 'platydoc.dependencies', version: 2, status: 'partial', coverage: 'partial',
      configuration_ids: [result.configuration.id], analysis_id: analysis.id,
      roots: result.layouts.entries.map(layout => layout.declaration_id).sort(order)};
    return result;
  }
  return {discover, validate, attach, controlsFor, baseDocument, scan};
});
