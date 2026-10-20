#!/usr/bin/env python3
"""Enumerate local MIG declarations under explicit documentation profiles.

This runs the C preprocessor, not MIG or a kernel build. Type includes are omitted
from preprocessing: declarations retain MIG type names; this is not wire-layout
generation. Each subprocess has a timeout. Authored explanations live separately.
"""

from collections import defaultdict
import argparse
import json
from pathlib import Path
import re
import subprocess

from paths import DOCS, SOURCE_ROOT, require_source
from doc_license import with_license_notice


OUT = DOCS / "interfaces" / "mach-messages"
REGISTERED = {
    "mach_vm", "mach_port", "mach_host", "host_priv", "clock", "processor",
    "processor_set", "device", "task", "thread_act", "vm32_map", "UNDReply",
    "mach_voucher", "memory_entry", "restartable", "exc", "mach_exc",
    "arcade_register", "mach_eventlink",
}
DECLARATION_ONLY = {
    "clock_priv", "host_security", "ledger", "mach_voucher_attr_control",
    "prof", "semaphore", "upl", "vm_map", "netname",
}
PROFILES = {
    "server64": ["KERNEL", "KERNEL_SERVER", "MACH_KERNEL_PRIVATE",
                 "XNU_KERNEL_PRIVATE", "KERNEL_PRIVATE", "__LP64__", "IOKIT",
                 "VM32_SUPPORT", "CONFIG_ARCADE", "CONFIG_ROSETTA"],
    "server32": ["KERNEL", "KERNEL_SERVER", "MACH_KERNEL_PRIVATE",
                 "XNU_KERNEL_PRIVATE", "KERNEL_PRIVATE", "__ILP32__", "IOKIT",
                 "VM32_SUPPORT", "CONFIG_ARCADE", "CONFIG_ROSETTA"],
    "client64": ["__LP64__", "IOKIT", "VM32_SUPPORT", "PRIVATE"],
    "client32": ["__ILP32__", "IOKIT", "VM32_SUPPORT", "PRIVATE"],
    "libsyscall64": ["__LP64__", "LIBSYSCALL_INTERFACE", "IOKIT",
                     "VM32_SUPPORT", "PRIVATE"],
    "sender64": ["KERNEL", "KERNEL_USER", "__LP64__", "IOKIT",
                 "VM32_SUPPORT", "CONFIG_ARCADE", "CONFIG_ROSETTA",
                 "EXC_SERVER_AUDITTOKEN", "MACH_EXC_SERVER_AUDITTOKEN"],
    "local64": ["KERNEL", "KERNEL_SERVER", "MACH_KERNEL_PRIVATE",
                "XNU_KERNEL_PRIVATE", "__LP64__", "_MACH_VM_PUBLISH_AS_LOCAL_",
                "VM32_SUPPORT", "IOKIT", "CONFIG_ARCADE", "CONFIG_ROSETTA"],
}


def uncomment(text):
    return re.sub(r"/\*.*?\*/|//[^\n]*",
                  lambda m: "\n" * m[0].count("\n"), text, flags=re.S)


def preprocess(path, profile):
    source = path.read_text()
    source = re.sub(r"^[ \t]*#[ \t]*include[^\n]*", "", source, flags=re.M)
    relative = path.relative_to(SOURCE_ROOT).as_posix()
    source = f'#line 1 "{relative}"\n' + source
    result = subprocess.run(
        ["cpp", "-E", "-undef", "-nostdinc", "-x", "c",
         *["-D" + key + "=1" for key in PROFILES[profile]], "-"],
        input=source, text=True, capture_output=True, timeout=10, check=True)
    plain, source_lines, current = [], [], 0
    for line in result.stdout.splitlines():
        directive = re.match(r'#\s+(\d+)\s+"([^"]+)"', line)
        if directive:
            current = int(directive[1])
            continue
        plain.append(line)
        source_lines.append(current)
        current += 1
    return "\n".join(plain), source_lines


def adjacent_comment(path, line):
    before = "\n".join(path.read_text().splitlines()[:line - 1])
    blocks = list(re.finditer(r"/\*(.*?)\*/", before, re.S))
    if not blocks:
        return ""
    last = blocks[-1]
    gap = re.sub(r"^\s*#[^\n]*", "", before[last.end():], flags=re.M).strip()
    if gap:
        return ""
    comment = re.sub(r"^\s*\* ?", "", last[1], flags=re.M)
    return re.sub(r"\s+", " ", comment).strip()


def parse(path, profile):
    text, locations = preprocess(path, profile)
    subsystem = re.search(r"\bsubsystem\s+((?:\w+\s+)*?)(\d+)\s*;", text, re.I)
    if not subsystem:
        return None
    name = subsystem[1].split()[-1]
    base, number = int(subsystem[2]), int(subsystem[2])
    prefix_match = re.search(r"\bserverprefix\s+(\w+)\s*;", text, re.I)
    prefix = prefix_match[1] if prefix_match else ""
    user_match = re.search(r"\buserprefix\s+(\w+)\s*;", text, re.I)
    user_prefix = user_match[1] if user_match else ""
    items = []
    pattern = re.compile(r"\b(skip)\s*;|\b(simpleroutine|routine)\s+(\w+)\s*\(", re.I)
    for match in pattern.finditer(text, subsystem.end()):
        line = locations[text[:match.start()].count("\n")]
        if match[1]:
            items.append({"id": number, "kind": "skip", "line": line})
        else:
            end = text.find(");", match.end())
            if end < 0:
                raise ValueError(f"Unterminated declaration: {path}:{line}")
            end_line = locations[text[:end + 2].count("\n")]
            signature = text[match.start():end + 2]
            items.append({"id": number, "kind": match[2].lower(),
                          "name": match[3], "server_symbol": prefix + match[3],
                          "sender_symbol": user_prefix + match[3],
                          "line": line, "end_line": end_line,
                          "signature": signature,
                          "comment": adjacent_comment(path, line)})
        number += 1
    return {"subsystem": name, "base": base, "serverprefix": prefix,
            "userprefix": user_prefix, "items": items}


def index_code(data):
    names = set()
    for source in data["interfaces"]:
        for profile in source["profiles"].values():
            if profile:
                for item in profile["items"]:
                    if item["kind"] != "skip":
                        names.update([item["name"], item["server_symbol"],
                                      item["sender_symbol"]])
    alternatives = "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))
    definition = re.compile(r"(?m)^[ \t]*(?:[\w*]+[ \t]+)*?(" +
                            alternatives + r")\s*\([^;{}]*?\)\s*\{")
    invocation = re.compile(r"\b(" + alternatives + r")\s*\(")
    definitions, occurrences = defaultdict(list), defaultdict(list)
    for top in ("osfmk", "bsd", "iokit", "libkern", "libsyscall", "security"):
        for path in sorted((SOURCE_ROOT / top).rglob("*")):
            if path.suffix not in {".c", ".cpp", ".m"}:
                continue
            text = path.read_text(errors="replace")
            relative = path.relative_to(SOURCE_ROOT).as_posix()
            masked = re.sub(r"/\*.*?\*/|//[^\n]*",
                            lambda m: "".join("\n" if c == "\n" else " " for c in m[0]),
                            text, flags=re.S)
            # A signature can contain alternative parameter spellings followed
            # by #endif before its opening brace. Preserve source offsets.
            masked = re.sub(r"^[ \t]*#[^\n]*",
                            lambda m: " " * len(m[0]), masked, flags=re.M)
            for match in definition.finditer(masked):
                end_match = re.search(r"(?m)^}", text[match.end():])
                end = match.end() + end_match.end() if end_match else match.end()
                body = uncomment(text[match.end():end])
                calls = list(dict.fromkeys(re.findall(r"\b([A-Za-z_]\w*)\s*\(", body)))
                calls = [c for c in calls if c not in {
                    "if", "while", "for", "switch", "sizeof", "return", "defined",
                    "__unused", "__attribute__", "assert", "assertf", "assert3u",
                    "__improbable", "__probable", "panic"}]
                definitions[match[1]].append({
                    "path": relative, "line": text.count("\n", 0, match.start()) + 1,
                    "end_line": text.count("\n", 0, end) + 1, "calls": calls[:40],
                    "body_sample": body[:1500]})
            # These are navigation occurrences, not automatically inferred callers.
            clean = uncomment(text)
            for match in invocation.finditer(clean):
                if len(occurrences[match[1]]) < 8:
                    occurrences[match[1]].append({
                        "path": relative, "line": clean.count("\n", 0, match.start()) + 1})
    return {"definitions": definitions, "occurrences": occurrences}


def collect():
    sources = []
    wrappers, types = [], []
    all_defs = sorted(SOURCE_ROOT.rglob("*.defs"))
    for path in all_defs:
        text = uncomment(path.read_text())
        relative = path.relative_to(SOURCE_ROOT).as_posix()
        if relative.startswith("tests/"):
            continue
        if not re.search(r"\bsubsystem\b", text, re.I):
            includes = re.findall(r'#include\s*[<"]([^>"]+\.defs)', text)
            (wrappers if includes and ("libsyscall/" in relative or
                         path.name == "mach_notify.defs") else types).append(
                             {"path": relative, "includes": includes})
            continue
        profiles = {profile: parse(path, profile) for profile in PROFILES}
        raw_starts = [text[:m.start()].count("\n") + 1 for m in
                      re.finditer(r"\b(?:simpleroutine|routine)\b", text, re.I)]
        covered = {item["line"] for data in profiles.values() if data
                   for item in data["items"] if item["kind"] != "skip"}
        sources.append({"path": relative, "profiles": profiles,
                        "raw_routine_lines": raw_starts,
                        "uncovered_routine_lines": sorted(set(raw_starts) - covered)})
    return {"profiles": PROFILES, "interfaces": sources,
            "include_wrappers": wrappers, "type_definitions": types}


def normalized(name):
    for prefix in ("_kernelrpc_", "vm32_"):
        name = name.removeprefix(prefix)
    for suffix in ("_external", "_from_user", "_mig"):
        name = name.removesuffix(suffix)
    return name


def source_link(path, line, label):
    return f"[{label}](../../../xnu/{path}#L{line})"


def authored_descriptions(data):
    authored = {}
    for line in (OUT / "descriptions.tsv").read_text().splitlines():
        if not line.strip():
            continue
        name, purpose = line.split("\t", 1)
        if name in authored:
            raise ValueError(f"Duplicate description: {name}")
        authored[name] = purpose
    comments = {}
    for source in data["interfaces"]:
        for profile in source["profiles"].values():
            if not profile:
                continue
            for item in profile["items"]:
                if item["kind"] != "skip" and len(item["comment"]) > 20:
                    comments.setdefault(normalized(item["name"]), item["comment"])
    return authored, comments


def purpose_for(variants, authored, comments):
    names = list(dict.fromkeys([v["name"] for _, v in variants]))
    for name in names:
        for key in (name, normalized(name)):
            if key in authored:
                return authored[key], False
    for _, item in variants:
        if len(item["comment"]) > 20:
            return item["comment"], True
    for name in names:
        key = normalized(name)
        if key.startswith("io_"):
            # Explicitly shared operations with different serialization/address ABIs.
            stem = key
            for suffix in ("_64", "_buf", "_bin", "_ool"):
                stem = stem.removesuffix(suffix)
            if stem in authored:
                return authored[stem] + " This declaration uses the buffer/serialization/address-width variant shown in its fields.", False
        aliases = [key]
        if key.startswith("vm_"):
            aliases.append("mach_" + key)
        if key == "vm_region_recurse_64":
            aliases.append("mach_vm_region_recurse")
        if key == "vm_region":
            aliases.append("mach_vm_region")
        for alias in aliases:
            if alias in authored:
                return authored[alias], False
            if alias in comments:
                return comments[alias], True
    return "", False


def render(data, index):
    authored, comments = authored_descriptions(data)
    mechanisms = {}
    for path in sorted(OUT.glob("mechanisms-*.json")):
        entries = json.loads(path.read_text())
        duplicate = set(entries) & set(mechanisms)
        if duplicate:
            raise ValueError(f"Duplicate mechanisms in {path.name}: {sorted(duplicate)}")
        mechanisms.update(entries)
    missing = []
    missing_mechanisms = []
    summary = []
    for source in data["interfaces"]:
        path = source["path"]
        stem = Path(path).stem
        by_id = defaultdict(list)
        for profile_name, profile in source["profiles"].items():
            if profile:
                for item in profile["items"]:
                    by_id[item["id"]].append((profile_name, item))
        if stem in REGISTERED:
            route = ("Listed in the kernel kobject subsystem table, subject to the registration "
                     "guards and per-slot skips. The destination's typed capability still controls admission.")
        elif stem in DECLARATION_ONLY:
            route = ("Not listed as a separate subsystem in this checkout's `mig_e` table. "
                     "Local bodies, generated interfaces and compatibility aliases are distinguished below; "
                     "a declaration alone does not establish an active kernel message endpoint.")
        else:
            route = ("Service/callback interface outside the ordinary kernel kobject table. "
                     "Follow local sender/receiver evidence; external service bodies are not supplied by the declaration.")
        lines = [
            f"# Mach messages: {stem}", "",
            "[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) "
            "· [Kernel entry map](../README.md)", "",
            source_link(path, 1, path) + ". " + route,
            "Registration evidence: [`mig_e`](../../../xnu/osfmk/kern/ipc_kobject.c#L171-L197).", "",
            "## Reading these entries", "",
            "IDs are computed from the explicit preprocessing profiles in the catalog guide, "
            "counting both routines and `skip` slots. They are not discovered from a running kernel. "
            "Each entry retains all observed names/declaration locations; the displayed fields come "
            "from the first non-skipped profile. Alternative declarations can have different fields. "
            "`simpleroutine` is one-way at the MIG interface level.", "",
            "An **interface contract** block quotes the adjacent local `.defs` comment with whitespace "
            "normalized. **Mechanism** paragraphs explain selected implementation decisions. "
            "**Local body** links and call names identify implementation evidence; syntactic "
            "call lists are reading aids, not a proof that every listed call executes on every path. "
            "Short complete implementation bodies are included where especially useful.", "",
            "## Complete routine and reserved-slot catalog", "",
        ]
        routines = skipped = explained = 0
        for number, all_variants in sorted(by_id.items()):
            variants = [(p, i) for p, i in all_variants if i["kind"] != "skip"]
            if not variants:
                skipped += 1
                first = all_variants[0][1]
                lines.extend([f"### {number}: reserved", "",
                              f"`skip` in all listed profiles. {source_link(path, first['line'], 'Source slot')}.", ""])
                continue
            routines += 1
            first_profile, first = variants[0]
            purpose, quoted = purpose_for(variants, authored, comments)
            if not purpose:
                missing.append((path, number, first["name"]))
                purpose = "MISSING AUTHORED DESCRIPTION"
            lines.extend([f"### {number}: {first['name']}", ""])
            if quoted:
                lines.extend(["**Interface contract:**", "", "> " + purpose, ""])
            else:
                lines.extend([purpose, ""])
            mechanism = next((mechanisms[key] for _, item in variants
                              for key in (item["name"], item["server_symbol"])
                              if key in mechanisms), None)
            if mechanism:
                explained += 1
                lines.extend(["**Mechanism:** " + mechanism, ""])
            else:
                missing_mechanisms.append((path, number, first["name"]))
            decls = defaultdict(list)
            for profile, item in variants:
                decls[(item["name"], item["line"])].append(profile)
            lines.append("**Declarations:** " + "; ".join(
                source_link(path, line, f"`{name}`") + " (`" + "`, `".join(profiles) + "`)"
                for (name, line), profiles in decls.items()) + ".")
            skip_profiles = [p for p, item in all_variants if item["kind"] == "skip"]
            if skip_profiles:
                lines.append("**Reserved instead in:** `" + "`, `".join(skip_profiles) + "`.")
            lines.extend(["", f"**Fields after preprocessing (`{first_profile}`):**", "",
                          "```text", re.sub(r"\n\s*\n", "\n", first["signature"]), "```", ""])
            server = [(p, v) for p, v in variants if p in {"server64", "server32", "local64"}]
            symbols = list(dict.fromkeys(v["server_symbol"] for _, v in (server or variants)))
            definitions = []
            for symbol in symbols:
                for definition in index["definitions"].get(symbol, []):
                    if (symbol, definition) not in definitions:
                        definitions.append((symbol, definition))
            if definitions:
                for symbol, definition in definitions[:4]:
                    label = "User wrapper" if definition["path"].startswith("libsyscall/") else "Local body"
                    lines.append(f"**{label}:** " + source_link(
                        definition["path"], definition["line"], f"`{symbol}`") + ".")
                    calls = definition["calls"]
                    if calls:
                        lines.append("Calls visible in this body include " +
                                     ", ".join(f"`{c}`" for c in calls[:12]) + ".")
                    if not server:
                        lines.append("This body/reference does not override the kernel-server slot's reserved or declaration-only status.")
                    if definition["end_line"] - definition["line"] <= 18:
                        url = f"../../../xnu/{definition['path']}#L{definition['line']}-L{definition['end_line']}"
                        original = (SOURCE_ROOT / definition["path"]).read_text().splitlines()
                        lines.extend(["", f"[Implementation excerpt]({url}):",
                                      f"<!-- source-excerpt: {url} -->", "```c",
                                      "\n".join(original[definition["line"]-1:definition["end_line"]]), "```"])
                    lines.append("")
                if all(d["path"].startswith("libsyscall/") for _, d in definitions):
                    lines.extend(["Only a user-library body was resolved here; that is not a kernel receiver implementation.", ""])
            else:
                occurrences = []
                for _, item in variants:
                    for symbol in (item["sender_symbol"], item["name"], item["server_symbol"]):
                        for ref in index["occurrences"].get(symbol, []):
                            if ref not in occurrences:
                                occurrences.append(ref)
                lines.append("**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.")
                if occurrences:
                    lines.append("Local source occurrences to follow: " + ", ".join(
                        source_link(ref["path"], ref["line"], f"{ref['path']}:{ref['line']}")
                        for ref in occurrences[:4]) + ". These may be senders, wrappers or declarations; they do not establish a local receiver.")
                lines.append("")
        summary.append({"file": path, "page": stem + ".md", "slots": len(by_id),
                        "routine_slots": routines, "reserved_slots": skipped,
                        "mechanism_slots": explained,
                        "bases": sorted({p["base"] for p in source["profiles"].values() if p}),
                        "route": route})
        if not by_id:
            lines.extend(["This subsystem declaration has no routines or skipped slots in the inspected profiles.", ""])
        (OUT / f"{stem}.md").write_text(with_license_notice("\n".join(lines)))
    if missing:
        raise ValueError("Missing purposes: " + json.dumps(missing))
    if missing_mechanisms:
        raise ValueError("Missing mechanisms: " + json.dumps(missing_mechanisms))
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    lines = [
        "# MIG subsystem and source inventory", "",
        "[Message dispatch guide](README.md) · [All kernel entry interfaces](../README.md)", "",
        "This table covers every non-test `.defs` file containing a subsystem declaration. "
        "Counts combine the explicit profiles; overlapping numeric ranges are not summed into "
        "a global ABI. For example, `vm_map`/`vm32_map` share compatibility numbering, and "
        "unrelated external receivers can use the same IDs.", "",
        "| Definition and routine catalog | Base IDs | Slots across profiles | With a routine in at least one profile | Always skipped | Registration category |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in summary:
        stem = Path(row["file"]).stem
        category = ("Kernel kobject registration (guarded)" if stem in REGISTERED else
                    "Declaration/compatibility; not separately registered" if stem in DECLARATION_ONLY
                    else "Service/callback boundary")
        lines.append(f"| [{stem}]({row['page']}) | " +
                     ", ".join(str(b) for b in row["bases"]) +
                     f" | {row['slots']} | {row['routine_slots']} | {row['reserved_slots']} | {category} |")
    for key, title in (("include_wrappers", "Include wrappers"),
                       ("type_definitions", "Supporting type definitions")):
        lines.extend(["", "## " + title, "",
                      "These files are accounted for separately; they do not create an additional independent routine catalog.", ""])
        for row in data[key]:
            lines.append("- " + source_link(row["path"], 1, row["path"]) +
                         (": includes `" + "`, `".join(row["includes"]) + "`." if row["includes"] else "."))
    tests = sorted(p.relative_to(SOURCE_ROOT).as_posix() for p in (SOURCE_ROOT / "tests").rglob("*.defs"))
    lines.extend(["", "## Test interfaces", "",
                  "Test-specific exception servers and replacement declarations are not production kernel entry surfaces.", ""])
    lines.extend("- " + source_link(p, 1, p) for p in tests)
    lines.extend(["", "## Reconciliation", "",
                  f"- **{len(summary)}** subsystem-bearing definition files.",
                  f"- **{sum(len(s['raw_routine_lines']) for s in data['interfaces'])}** raw routine declaration sites; every site appears in at least one profile.",
                  f"- **{sum(r['routine_slots'] for r in summary)}** per-file ID slots with a routine in at least one profile, plus **{sum(r['reserved_slots'] for r in summary)}** always-skipped per-file slots.",
                  f"- **{sum(r['mechanism_slots'] for r in summary)}** routine slots with authored mechanism or explicit implementation-boundary explanations.",
                  "- Counts include historical, external and overlapping compatibility interfaces. They are not the number of callable kernel RPCs.",
                  ""])
    (OUT / "subsystems.md").write_text(with_license_notice("\n".join(lines)))
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render-only", action="store_true",
                        help="Use the saved source/profile and code inventories.")
    args = parser.parse_args()
    require_source()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.render_only:
        data = json.loads((OUT / "inventory.json").read_text())
        index = json.loads((OUT / "code-index.json").read_text())
    else:
        data = collect()
        (OUT / "inventory.json").write_text(json.dumps(data, indent=2) + "\n")
        index = index_code(data)
        (OUT / "code-index.json").write_text(json.dumps(index, indent=2) + "\n")
    unresolved = {s["path"]: s["uncovered_routine_lines"]
                  for s in data["interfaces"] if s["uncovered_routine_lines"]}
    if unresolved:
        raise ValueError("Routine declarations outside profile matrix: " +
                         json.dumps(unresolved))
    print(f"{len(data['interfaces'])} subsystem-bearing definition files")
    print("Declarations outside profile matrix:", json.dumps(unresolved))
    canonical = sum(len(d["profiles"]["server64"]["items"])
                    for d in data["interfaces"] if d["profiles"]["server64"])
    print(f"{canonical} slots across server64 declaration profiles")
    summary = render(data, index)
    print(f"Rendered {len(summary)} subsystem catalogs")
    print(f"{sum(s['mechanism_slots'] for s in summary)} routine slots with authored mechanisms")


if __name__ == "__main__":
    main()
