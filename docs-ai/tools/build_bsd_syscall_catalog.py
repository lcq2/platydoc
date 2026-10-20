#!/usr/bin/env python3
"""Reconcile the BSD syscall catalog with every syscalls.master alternative.

The source master determines numbers, signatures, audit events and conditional
branches. Authored metadata supplies purpose/mechanism descriptions; this tool
does not infer an explanation from a syscall's name.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from paths import DOCS, SOURCE_ROOT, require_source

MASTER = SOURCE_ROOT / "bsd/kern/syscalls.master"
DEST = DOCS / "interfaces/bsd-syscalls"
META = DEST / "descriptions.json"
STUBS = {"nosys", "enosys"}


def parse_master():
    rows = []
    stack = []
    for lineno, line in enumerate(MASTER.read_text().splitlines(), 1):
        directive = re.match(r"^\s*#\s*(if|ifdef|ifndef|elif|else|endif)\b(.*)", line)
        if directive:
            op, text = directive.groups()
            text = re.sub(r"/\*.*?\*/|//.*", "", text).strip()
            if op in {"if", "ifdef", "ifndef"}:
                term = text if op == "if" else f"defined({text})"
                if op == "ifndef":
                    term = f"!({term})"
                stack.append({"prior": [term], "current": term})
            elif op == "elif":
                frame = stack[-1]
                frame["current"] = f"!({' || '.join(frame['prior'])}) && ({text})"
                frame["prior"].append(text)
            elif op == "else":
                stack[-1]["current"] = f"!({' || '.join(stack[-1]['prior'])})"
            else:
                stack.pop()
            continue
        match = re.match(r"^(\d+)\s+(\w+)\s+(\w+)\s+\{([^}]+)\}(.*)", line)
        if not match:
            if re.match(r"^\d", line):
                raise ValueError(f"Unparsed master declaration at line {lineno}")
            continue
        number, audit, outputs, signature, comment = match.groups()
        signature = " ".join(signature.split())
        symbol = re.search(r"(\w+)\s*\(", signature).group(1)
        rows.append({
            "number": int(number), "name": symbol, "signature": signature,
            "audit": audit, "outputs": outputs, "line": lineno,
            "condition": " && ".join(f"({frame['current']})" for frame in stack) or "always",
            "comment": comment.strip().strip("{}").strip(),
            "stub": symbol in STUBS,
        })
    if stack:
        raise ValueError("Unbalanced master conditionals")
    numbers = sorted({row["number"] for row in rows})
    if numbers != list(range(numbers[-1] + 1)):
        raise ValueError("The master has unaccounted number gaps")
    return rows


def index_implementations(names):
    pattern = re.compile(
        r"(?m)^(?P<name>" + "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))
        + r")\s*\([^;{}]*?\)\s*\{"
    )
    result = {name: [] for name in sorted(names)}
    for top in ("bsd", "osfmk", "security", "libkern", "iokit", "pexpert"):
        for path in sorted((SOURCE_ROOT / top).rglob("*")):
            if path.suffix not in {".c", ".cpp", ".m"}:
                continue
            text = path.read_text(errors="replace")
            for match in pattern.finditer(text):
                start = match.start()
                # The next unindented close brace bounds these C function bodies.
                end_match = re.search(r"(?m)^}", text[match.end():])
                end = match.end() + end_match.end() if end_match else match.end()
                body = text[match.end():end]
                calls = list(dict.fromkeys(re.findall(r"\b([A-Za-z_]\w*)\s*\(", body)))
                calls = [c for c in calls if c not in {
                    "if", "while", "for", "switch", "sizeof", "return",
                    "defined", "__unused", "__attribute__",
                }]
                result[match.group("name")].append({
                    "path": str(path.relative_to(SOURCE_ROOT)),
                    "line": text.count("\n", 0, start) + 1,
                    "end_line": text.count("\n", 0, end) + 1,
                    "calls": calls[:60],
                })
    return result


def link_source(path, line, label):
    return f"[{label}](../../../xnu/{path}#L{line})"


def render(rows, metadata):
    active = [r for r in rows if not r["stub"]]
    names = {r["name"] for r in active}
    missing = names - metadata.keys()
    extra = metadata.keys() - names
    if missing or extra:
        raise ValueError(f"Metadata mismatch: missing={sorted(missing)}, extra={sorted(extra)}")
    families = {}
    outputs = {}
    for row in active:
        entry = metadata[row["name"]]
        for field in ("family", "purpose", "mechanism", "implementation"):
            if not entry.get(field):
                raise ValueError(f"{row['name']}: missing authored {field}")
        for implementation in entry["implementation"]:
            path = SOURCE_ROOT / implementation["path"]
            lines = path.read_text().splitlines()
            line = implementation["line"]
            if not (0 < line <= len(lines)):
                raise ValueError(f"{row['name']}: invalid implementation line")
        if not any(re.match(r"^" + re.escape(row["name"]) + r"\s*\(",
                            (SOURCE_ROOT / i["path"]).read_text().splitlines()[i["line"] - 1])
                   for i in entry["implementation"]):
            if row["name"] != "vfork" or not all("local handler absent" in i.get("label", "") for i in entry["implementation"]):
                raise ValueError(f"{row['name']}: no implementation link points at its definition")
        families.setdefault(entry["family"], []).append((row, entry))
    for family, entries in sorted(families.items()):
        title = family.replace("-", " ").capitalize()
        lines = [
            f"# BSD syscalls: {title}", "",
            "[Dispatch and catalog guide](README.md) · [Every number and configuration alternative](number-index.md)",
            "",
            "This page is generated from `syscalls.master` and authored `descriptions.json`. "
            "The signature is the master declaration, not the internal handler's `(proc, args, retval)` ABI. "
            "Descriptions identify selected local mechanisms; they do not claim every branch was audited.",
            "",
        ]
        for row, entry in sorted(entries, key=lambda pair: pair[0]["number"]):
            name, n = row["name"], row["number"]
            lines.extend([
                f"## {n}: {name}", "",
                f"`{row['signature']}`", "",
                f"**Declaration:** {link_source('bsd/kern/syscalls.master', row['line'], 'syscalls.master')} "
                f"· **Condition:** `{row['condition']}` · **Audit event:** `{row['audit']}`.", "",
                entry["purpose"], "",
            ])
            implementations = ", ".join(
                link_source(i["path"], i["line"], i.get("label", name))
                for i in entry["implementation"]
            )
            lines.extend([f"**Implementation:** {implementations}. {entry['mechanism']}", ""])
            if entry.get("details"):
                lines.extend([entry["details"], ""])
        outputs[f"{family}.md"] = "\n".join(lines)
    lines = [
        "# BSD syscall number and configuration index", "",
        "[Dispatch and catalog guide](README.md)", "",
        "Every declaration alternative in `bsd/kern/syscalls.master` appears below. "
        "Conditions preserve the preprocessor branches without selecting a product build. "
        "A reserved or disabled entry is not an available operation. "
        "Number 0 is the table's `nosys` entry, while architecture dispatch separately recognizes indirect syscall encoding.",
        "",
        "| Number | Master declaration / implementation catalog | Condition | Reserved/disabled annotation |",
        "| ---: | --- | --- | --- |",
    ]
    for row in rows:
        name = row["name"]
        source = link_source("bsd/kern/syscalls.master", row["line"], name)
        if not row["stub"]:
            family = metadata[name]["family"]
            source += f" · [mechanism]({family}.md#{row['number']}-{name})"
        condition = row["condition"].replace("|", "\\|")
        note = row["comment"].replace("|", "\\|")
        if row["stub"] and not note:
            note = "Unavailable/reserved implementation (`" + name + "`)."
        lines.append(f"| {row['number']} | {source} | `{condition}` | {note} |")
    lines.extend([
        "", "## Reconciliation", "",
        f"- Distinct syscall numbers: **{len({r['number'] for r in rows})}**, "
        f"from **0** through **{max(r['number'] for r in rows)}**.",
        f"- Declaration alternatives: **{len(rows)}**.",
        f"- Non-stub declarations with authored purpose and implementation mechanism: **{len(active)}**.",
        f"- `nosys`/`enosys` alternatives: **{len(rows) - len(active)}**.",
        "- These are source declarations across configurations, not the enabled calls in one running kernel.",
        "",
    ])
    outputs["number-index.md"] = "\n".join(lines)
    return {family: len(entries) for family, entries in families.items()}, outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory-only", action="store_true")
    parser.add_argument("--check", action="store_true", help="validate all generated files without writing them")
    args = parser.parse_args()
    require_source()
    DEST.mkdir(parents=True, exist_ok=True)
    rows = parse_master()
    implementations = index_implementations({r["name"] for r in rows})
    inventory = {
        "master": str(MASTER.relative_to(SOURCE_ROOT)),
        "master_sha256": hashlib.sha256(MASTER.read_bytes()).hexdigest(),
        "rows": rows, "implementation_candidates": implementations,
    }
    outputs = {"inventory.json": json.dumps(inventory, indent=2) + "\n"}
    print(f"Inventoried {len(rows)} declarations / {len({r['number'] for r in rows})} numbers.")
    if not args.inventory_only:
        families, pages = render(rows, json.loads(META.read_text()))
        outputs.update(pages)
        print(f"Validated authored metadata and rendered {sum(families.values())} implementations in {len(families)} families.")
    if args.check:
        stale = [name for name, text in outputs.items()
                 if not (DEST / name).exists() or (DEST / name).read_text() != text]
        if stale:
            raise ValueError("Generated catalog is stale: " + ", ".join(stale))
        print(f"All {len(outputs)} generated files match their source and authored metadata.")
    else:
        for name, text in outputs.items():
            (DEST / name).write_text(text)
    missing = [n for n, locations in implementations.items() if not locations]
    if missing:
        print("Definitions requiring explicit resolution:", ", ".join(sorted(missing)))


if __name__ == "__main__":
    main()
