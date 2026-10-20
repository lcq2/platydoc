"""Build a source-derived alphabetical index from parsed documentation pages.

The renderer supplies section IDs.  This module never recomputes a slug, so
duplicate headings and renderer-specific IDs retain working destinations.
Only prose, headings and inline code participate; fenced source snippets do not.
"""

from __future__ import annotations

from collections import defaultdict
import html
import re
from urllib.parse import urldefrag


# Reading vocabulary used in the guides.  An alias is indexed only when it
# actually occurs in a page; it is not an invented definition or destination.
_CONCEPTS = {
    "AST": ("asynchronous system trap", "asynchronous system traps"),
    "COW": ("copy-on-write", "copy on write"),
    "DMA": ("direct memory access",),
    "IPC": ("interprocess communication", "inter-process communication"),
    "MIG": ("Mach Interface Generator",),
    "SMR": ("safe memory reclamation",),
    "QoS": ("quality of service", "quality-of-service"),
    "UBC": ("unified buffer cache",),
    "UPL": ("universal page list", "universal page lists"),
    "VFS": ("virtual filesystem", "virtual file system"),
    "TLB": ("translation lookaside buffer",),
    "ASID": ("address-space identifier", "address space identifier"),
    "PCID": ("process-context identifier", "process context identifier"),
    "PTE": ("page-table entry", "page table entry"),
    "PPL": ("Page Protection Layer",),
    "SPTM": ("Secure Page Table Monitor",),
    "TXM": ("Trusted Execution Monitor",),
    "PAC": ("pointer authentication",),
    "KPTI": ("kernel page-table isolation", "kernel page table isolation"),
    "SIP": ("System Integrity Protection",),
    "MAC": ("mandatory access control", "mandatory-access-control"),
    "BSM": ("Basic Security Module",),
    "TCP": ("Transmission Control Protocol",),
    "UDP": ("User Datagram Protocol",),
    "NFS": ("Network File System",),
    "BSD": (),
    "Mach": (),
    "IOKit": (),
    "DriverKit": (),
    "Exclaves": (),
    "Skywalk": (),
    "CodeDirectory": (),
    "SuperBlob": (),
    "CDHash": (),
    "VM map": ("virtual memory map",),
    "VM object": ("virtual memory object",),
    "VM page": ("physical page metadata",),
    "Pmap": ("physical map",),
    "Wait queue": ("wait queues", "wait queue"),
    "Turnstile": ("turnstiles",),
    "Priority inheritance": (),
    "Reference counting": ("reference count", "reference counts"),
    "Grace period": ("grace periods",),
    "Page fault": ("page faults",),
    "Page wiring": ("wired pages",),
    "Memory pressure": (),
    "Compressor": ("memory compression",),
    "Swap": (),
    "Hibernate": ("hibernation",),
    "Sleep and wake": ("system sleep", "system wake",),
    "Context switch": ("context switching", "context switches"),
    "Continuation": ("continuations",),
    "Interrupt": ("interrupts",),
    "Scheduler": ("scheduling",),
    "Kqueue": ("kqueues",),
    "Knote": ("knotes",),
    "Workloop": ("workloops", "work loop", "work loops"),
    "Workqueue": ("workqueues",),
    "Vnode": ("vnodes",),
    "Mount": ("mounts",),
    "Name cache": (),
    "Buffer cache": (),
    "File descriptor": ("file descriptors",),
    "Socket": ("sockets",),
    "Mbuf": ("mbufs",),
    "Credential": ("credentials",),
    "Audit": ("auditing",),
    "Code signing": ("code-signing",),
    "Entitlement": ("entitlements",),
    "Mach port": ("Mach ports",),
    "Send right": ("send rights",),
    "Receive right": ("receive rights",),
    "Send-once right": ("send-once rights",),
    "Voucher": ("vouchers",),
    "Exception": ("exceptions",),
    "Signal": ("signals",),
    "System call": ("system calls", "syscall", "syscalls"),
}

_KNOWN_SYMBOLS = {
    "proc", "task", "thread", "uthread", "vnode", "mount", "pmap", "mbuf",
    "socket", "sockbuf", "inpcb", "tcpcb", "knote", "kqueue", "ucred",
    "turnstile", "ledger", "semaphore", "persona", "uio", "ifnet", "domain",
    "protosw", "fileproc", "fileglob", "filedesc", "selinfo", "clist",
}
_IGNORE_SYMBOLS = {
    "NULL", "TRUE", "FALSE", "true", "false", "void", "bool", "boolean_t",
    "size_t", "ssize_t", "uintptr_t", "intptr_t", "uint8_t", "uint16_t",
    "uint32_t", "uint64_t", "int8_t", "int16_t", "int32_t", "int64_t",
    "unsigned", "signed", "char", "short", "int", "long", "float", "double",
    "static", "const", "volatile", "struct", "union", "enum", "__unused",
    "KERN_SUCCESS", "MACH_PORT_NULL", "MACH_PORT_DEAD", "MACH_MSG_SUCCESS",
    "retval", "return", "sizeof", "assert", "assertf", "panic", "printf",
    "DEBUG", "DEVELOPMENT", "CONFIG", "TODO", "FIXME", "ENOSYS", "EINVAL",
    "ENOMEM", "EFAULT", "ENOTSUP", "EPERM", "ENOENT", "EINTR", "ERESTART",
    "EJUSTRETURN", "EWOULDBLOCK", "nosys", "enosys", "kern_invalid",
}
_GENERIC_HEADING = re.compile(
    r"^(?:sources?\b|inspection\b|reading (?:route|order|these|the)\b|"
    r"scope\b|limits?\b|validation\b|verification\b|reconciliation\b|"
    r"regeneration\b|documentation\b|navigation\b|contents?\b|"
    r"references?\b|further reading\b|overview$|summary$|"
    r"what (?:was|is) inspected\b|how to read\b|complete (?:routine|table)\b|"
    r"reserved$|slots? \d|[Pp][123]\s*[:—-])", re.I
)
_INLINE = re.compile(r"(?<!`)`([^`\n]+)`(?!`)")
_IDENTIFIER = re.compile(r"[A-Za-z_]\w*(?:::[A-Za-z_]\w*)*")
_HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)(?:\s+#+)?\s*$")
_LINK = re.compile(r"!?\[([^\]]*)\]\([^)]+\)")
_INTERFACE_HEADING = re.compile(
    r"^(?:(?:slot|trap|syscall|message)\s+)?\d+\s*[:.)—-]\s*"
    r"`?([A-Za-z_]\w*)`?(?:\s*\([^)]*\))?$", re.I
)
_CONCEPT_LOOKUP = {
    term.casefold(): canonical
    for canonical, aliases in _CONCEPTS.items()
    for term in (canonical, *aliases)
}
_CONCEPT_PATTERN = re.compile(
    r"(?<![\w])(?:" +
    "|".join(re.escape(s) for s in sorted(_CONCEPT_LOOKUP, key=len, reverse=True)) +
    r")(?![\w])", re.I
)


def _plain(text):
    text = _LINK.sub(r"\1", str(text or ""))
    text = re.sub(r"<[^>]+>", "", text)
    return " ".join(html.unescape(text).replace("`", "").replace("**", "").split())


def _heading_term(title):
    title = _plain(title)
    title = re.sub(r"^(?:\d+(?:\.\d+)*[.)]?\s+|[A-Z]\.\s+)", "", title)
    if (not title or len(title) > 100 or len(title.split()) > 13
            or _GENERIC_HEADING.search(title)):
        return None
    return title


def _symbol(value, explicit=False):
    value = html.unescape(value.strip())
    value = re.sub(r"^(?:struct|enum|union|class)\s+", "", value)
    # A function-like inline phrase contributes the callee, never its arguments.
    call = re.match(r"^([A-Za-z_]\w*(?:::[A-Za-z_]\w*)*)\s*\(", value)
    if call:
        value = call.group(1)
        explicit = True
    if not _IDENTIFIER.fullmatch(value) or len(value) > 100:
        return None
    if not re.search(r"[A-Za-z]", value):
        return None
    if value in _IGNORE_SYMBOLS or re.fullmatch(r"(?:u?int\d*_t|[xwrvq]\d+)", value):
        return None
    if value.startswith(("KERN_", "MACH_SEND_", "MACH_RCV_")):
        return None
    if len(value) < 3 or value.strip("_") == "":
        return None
    if (explicit or value in _KNOWN_SYMBOLS or "_" in value
            or "::" in value or re.search(r"[a-z][A-Z]", value)):
        return value
    return None


def _prose_lines(markdown):
    fence = None
    for line in str(markdown or "").splitlines():
        match = re.match(r"^\s*(`{3,}|~{3,})", line)
        if match:
            mark = match.group(1)
            if fence is None:
                fence = (mark[0], len(mark))
            elif mark[0] == fence[0] and len(mark) >= fence[1]:
                fence = None
            continue
        if fence is None and not line.lstrip().startswith("<!--"):
            yield line


def _entry(page, section=None):
    section = section or {}
    base = urldefrag(str(page.get("url") or ""))[0]
    anchor = str(section.get("id") or "")
    return {
        "title": _plain(page.get("title") or page.get("path") or base),
        "heading": _plain(section.get("title") or page.get("title") or ""),
        "url": base + ("#" + anchor if anchor else ""),
        "chapter": page.get("chapter") or "",
    }


def build_concept_index(pages):
    """Return alphabetized ``{term, kind, entries}`` dictionaries.

    Kinds are ``Concepts``, ``Symbols`` and ``Interfaces``. Every entry is a
    supplied page URL plus a supplied section ID (or the page itself). Multiple
    occurrences in the same section are merged, without truncating destinations.
    """
    terms = {}
    priorities = {"Concepts": 0, "Symbols": 1, "Interfaces": 2}

    def add(term, kind, entry, rank=3):
        term = _plain(term).strip(" .:;")
        if not term or len(term) > 120:
            return
        # ``Socket`` as a concept and ``socket`` as a syscall have different
        # destinations and filters. Ordinary symbol mentions merge into an
        # interface definition, but not into similarly spelled prose concepts.
        key = (term.casefold(), "concept" if kind == "Concepts" else "code")
        record = terms.setdefault(key, {
            "term": term, "kind": kind, "_entries": {}, "_rank": rank,
        })
        if rank < record["_rank"]:
            record["term"], record["_rank"] = term, rank
        # An explicit interface definition is more specific than a code mention.
        if priorities[kind] > priorities[record["kind"]]:
            record["kind"] = kind
        old = record["_entries"].get(entry["url"])
        if old is None or rank < old[0]:
            record["_entries"][entry["url"]] = (rank, entry)

    def inspect_line(line, page, entry, glossary=False):
        if line.lstrip().startswith(("<!--", "[Guide index]", "[Documentation home]")):
            return
        for match in _INLINE.finditer(line):
            symbol = _symbol(match.group(1))
            if symbol:
                add(symbol, "Symbols", entry)
        text = _plain(line)
        # Strip link destinations first: file paths must not introduce vocabulary.
        for match in _CONCEPT_PATTERN.finditer(text):
            canonical = _CONCEPT_LOOKUP[match.group().casefold()]
            add(canonical, "Concepts", entry, 2)
        if not line.lstrip().startswith("|"):
            return
        cells = re.split(r"(?<!\\)\|", line.strip().strip("|"))
        if len(cells) < 2 or re.fullmatch(r"\s*:?-+:?\s*", cells[0]):
            return
        first = cells[0].strip()
        if glossary and _plain(first).casefold() not in {"term", "concept", "symbol"}:
            for term in re.split(r"\s+/\s+", first):
                code = _INLINE.fullmatch(term.strip())
                symbol = _symbol(code.group(1)) if code else None
                term = _plain(term)
                if term and len(term.split()) <= 9 and "/" not in term:
                    canonical = _CONCEPT_LOOKUP.get(term.casefold(), term)
                    add(symbol or canonical, "Symbols" if symbol else "Concepts", entry, 0)
            # Table definitions sometimes explicitly expand an abbreviation.
            meaning = _plain(cells[1]).split(":", 1)
            if len(meaning) == 2 and 1 < len(meaning[0].split()) <= 6:
                expansion = meaning[0]
                if not re.search(r"[.!?;]", expansion):
                    add(expansion, "Concepts", entry, 0)
        else:
            for match in _INLINE.finditer(first):
                symbol = _symbol(match.group(1))
                if symbol:
                    add(symbol, "Symbols", entry, 2)
        # Numbered trap tables use a numeric first column and a callee in the
        # next one. Numeric constants, invalid slots and opcode strings do not.
        if str(page.get("path", "")).replace("\\", "/").endswith("interfaces/mach-traps.md"):
            if re.fullmatch(r"\s*\d+\s*", _plain(first)):
                for match in _INLINE.finditer(cells[1]):
                    symbol = _symbol(match.group(1), explicit=True)
                    if symbol:
                        add(symbol, "Interfaces", entry, 1)

    for page in pages:
        path = str(page.get("path") or "").replace("\\", "/")
        glossary = path.rsplit("/", 1)[-1] == "glossary.md"
        sections = page.get("sections") or []
        current = _entry(page)
        headings = defaultdict(list)
        for section in sections:
            headings[_plain(section.get("title")).casefold()].append(section)
            entry = _entry(page, section)
            title = _plain(section.get("title"))
            interface = _INTERFACE_HEADING.fullmatch(title)
            if interface and path.startswith("interfaces/"):
                symbol = _symbol(interface.group(1), explicit=True)
                if symbol:
                    add(symbol, "Interfaces", entry, 1)
            else:
                term = _heading_term(title)
                if term:
                    add(term, "Concepts", entry, 2)
            # Rendered text often flattens fenced code into prose. Prefer the
            # canonical Markdown, which preserves the prose/code distinction.
            # Section-only callers can still supply text without Markdown.
            if not page.get("markdown"):
                for line in _prose_lines(section.get("text", "")):
                    inspect_line(line, page, entry, glossary)
        heading_seen = defaultdict(int)
        for line in _prose_lines(page.get("markdown", "")):
            heading = _HEADING.match(line)
            if heading:
                key = _plain(heading.group(2)).casefold()
                candidates = headings.get(key, [])
                ordinal = heading_seen[key]
                if ordinal < len(candidates):
                    current = _entry(page, candidates[ordinal])
                elif len(heading.group(1)) == 1:
                    current = _entry(page)
                heading_seen[key] += 1
                continue
            inspect_line(line, page, current, glossary)
        # Long-form aliases get their own searchable alphabetic entries, but
        # only when the phrase was actually used in the supplied documentation.
        prose = _plain("\n".join(_prose_lines(page.get("markdown", ""))))
        for canonical, aliases in _CONCEPTS.items():
            for alias in aliases:
                if alias.casefold() == canonical.casefold() or len(alias.split()) < 2:
                    continue
                if re.search(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", prose, re.I):
                    existing = terms.get((canonical.casefold(), "concept"))
                    if existing:
                        for _, occurrence in list(existing["_entries"].values()):
                            if urldefrag(occurrence["url"])[0] == urldefrag(str(page.get("url", "")))[0]:
                                add(alias, "Concepts", occurrence, 2)

    result = []
    for record in terms.values():
        entries = sorted(record["_entries"].values(), key=lambda item: (
            item[0], str(item[1]["chapter"]).casefold(),
            item[1]["title"].casefold(), item[1]["heading"].casefold(), item[1]["url"],
        ))
        result.append({
            "term": record["term"], "kind": record["kind"],
            "entries": [entry for _, entry in entries],
        })
    return sorted(result, key=lambda item: (item["term"].casefold(), item["kind"]))
