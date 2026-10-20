#!/usr/bin/env python3
"""Generate the Markdown handbook TOC from chapter titles and section headings."""

from collections import Counter
from pathlib import Path
import re

from check_links import DOCS, prose_lines
from doc_license import with_license_notice


# Order follows the reading route, retaining both introductions and deeper chapters.
GROUPS = [
    ("Orientation and review", ".", [
        "README", "architecture", "source-map", "reading-guide",
        "coverage-audit", "expansion-audit", "coverage", "glossary", "source-index",
    ]),
    ("Execution, scheduling, waits and timers", "subsystems/runtime", [
        "README", "objects-and-lifecycle", "scheduling", "scheduler-execution",
        "ast-mechanism", "ast-flavors",
        "priority-qos-and-quanta", "realtime-deadlines-and-runqueues",
        "clutch-and-edge", "cpu-eligibility-and-scheduler-variants",
        "waits-and-locks", "wait-and-turnstile-protocols",
        "time-and-accounting", "timer-and-thread-call-lifetime",
    ]),
    ("Virtual memory, hardware mappings and allocators", "subsystems/vm", [
        "README", "mapping-walkthroughs", "maps-and-faults", "virtual-address-maps",
        "objects-and-pages", "fault-resolution", "pmap-arm64",
        "pmap-translation-walkthroughs",
        "pmap-mapping-lifecycle", "pmap-tlb-and-cache", "pmap-x86",
        "wiring-and-memory-entries", "pagers-and-upl", "reclaim-and-pressure",
        "memorystatus-and-freezer", "kernel-allocation", "zone-allocator",
        "kalloc-heaps-and-routing", "typed-allocation", "kernel-virtual-allocation",
        "read-only-and-special-zones", "allocator-interfaces",
    ]),
    ("Processes, signals, descriptors and event servicing", "subsystems/processes", [
        "README", "lifecycle", "process-transitions", "syscalls-signals",
        "signal-delivery-and-return", "descriptors-ipc", "events-threads",
        "kqueue-and-workloops", "pthread-workqueue-lifecycle", "async-io",
    ]),
    ("Mach IPC and exception delivery", "subsystems/ipc", [
        "README", "names-and-rights", "ports-and-rights-lifecycle", "message-path",
        "message-send-receive", "kernel-rpc-and-exceptions", "exception-delivery",
        "policies-and-attribution", "guards-and-policy-enforcement",
        "vouchers-and-importance",
    ]),
    ("System-call and Mach entry-point map", "interfaces", [
        "README", "machine-entry-points", "mach-traps",
    ]),
    ("BSD system-call catalog", "interfaces/bsd-syscalls", [
        "README", "number-index", "processes-credentials-and-policy",
        "signals-and-thread-control", "events-pthreads-and-async-io",
        "files-and-descriptors", "filesystem-namespace", "filesystem-metadata",
        "filesystem-mounts-and-control", "virtual-memory", "local-ipc",
        "sockets-and-network-policy", "skywalk", "security-and-audit",
        "time-and-accounting", "diagnostics-and-system-control",
    ]),
    ("Mach message and MIG interface catalog", "interfaces/mach-messages", [
        "README", "subsystems", "mach_port", "mach_vm", "task", "thread_act",
        "mach_host", "host_priv", "processor", "processor_set", "clock",
        "device", "mach_voucher", "mach_eventlink", "memory_entry", "restartable",
        "exc", "mach_exc", "notify", "memory_object",
    ]),
    ("VFS, filesystem objects and storage I/O", "subsystems/vfs", [
        "README", "vnodes-mounts-and-dispatch", "pathname-and-authorization",
        "name-cache-and-vnode-reclaim", "vnode-cache-identity-and-reuse",
        "namespace-mutations", "mount-lifecycle",
        "io-and-cache", "file-data-cache-and-read-path", "buffer-cache-and-block-io",
        "clustered-writeback", "filesystems-and-nfs",
        "device-nodes-and-fifos", "stacked-filesystems", "nfs-server-requests",
    ]),
    ("Sockets, transports, interfaces and Skywalk", "subsystems/networking", [
        "README", "sockets", "socket-lifecycle-and-io", "tcp-ip-interfaces",
        "tcp-connections-and-timers", "packets-routes-and-interfaces",
        "policy-extensions", "skywalk", "skywalk-lifecycles",
    ]),
    ("IOKit, drivers and kernel libraries", "subsystems/drivers", [
        "README", "bootstrap-and-bsd-integration", "libkern-and-kext-runtime",
        "object-runtime-and-collections", "registry-and-service-lifecycle",
        "registry-planes-and-properties", "service-matching-and-termination",
        "service-notifications-and-arbitration",
        "user-clients-and-driverkit", "user-client-and-driverkit-lifetime",
        "driverkit-dispatch-and-actions", "shared-data-queues-and-notifications",
        "workloops-and-power", "workloop-and-power-protocols",
        "interrupt-routing-and-command-queues", "device-power-state-machine",
        "system-sleep-and-wake", "memory-and-dma",
        "memory-descriptors-and-cpu-mappings", "dma-preparation-and-mapping",
        "dma-segment-walkthrough",
        "reporting-and-performance-control",
    ]),
    ("Authorization, audit and protected execution", "subsystems/security", [
        "README", "credentials-and-policy", "credential-and-policy-lifetimes",
        "code-signing", "signature-format-and-blob-validation",
        "vnode-signature-lifecycle", "executable-signature-policy",
        "page-signature-validation", "audit", "audit-pipeline", "protected-execution",
        "sptm", "txm", "exclaves", "exclaves-execution",
        "exclaves-resources-and-memory", "exclaves-services",
    ]),
    ("Boot, exception levels, CPU lifecycle and platform services", "subsystems/platform", [
        "README", "boot", "execution", "arm64-exception-entry",
        "arm64-exception-return", "arm64-assembly-walkthroughs",
        "arm64-context-switching", "exception-levels-and-monitors",
        "hardware-mappings", "platform-services", "cpu-power-lifecycle",
        "hibernation-image-creation", "hibernation-restore", "x86-sleep-and-resume",
    ]),
    ("Paths and protocols across subsystems", "cross-cutting", [
        "execution-paths", "executable-loading", "ownership-and-locking",
        "smr-and-publication", "completion-and-failure",
    ]),
    ("Build, tests and observation", "development", [
        "build-and-tests", "observability",
    ]),
    ("Coverage audits and expansion plans", "audits", [
        "runtime-ipc-platform", "vm-and-drivers", "processes-vfs-networking",
        "security-and-development",
    ]),
]


def headings(path):
    """Use the same heading convention as the local-link checker."""
    title = None
    sections = []
    seen = Counter()
    for _, line in prose_lines(path):
        match = re.match(r"^(#{1,6})\s+(.+?)(?:\s+#+)?$", line)
        if not match:
            continue
        level, text = len(match[1]), match[2]
        plain = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", text)
        plain = re.sub(r"<[^>]*>", "", plain)
        slug = re.sub(r"[^\w\- ]", "", plain.lower()).replace(" ", "-")
        duplicate = seen[slug]
        seen[slug] += 1
        anchor = f"{slug}-{duplicate}" if duplicate else slug
        if level == 1 and title is None:
            title = plain
        elif level == 2:
            sections.append((plain, anchor))
    if title is None:
        raise ValueError(f"Missing chapter title: {path}")
    return title, sections


def main():
    output = DOCS / "table-of-contents.md"
    pages = set(DOCS.rglob("*.md")) - {output}
    covered = set()
    lines = [
        "# XNU handbook: complete table of contents", "",
        "[Guide index](README.md) · [Expansion audit](expansion-audit.md) · "
        "[Coverage and verification](coverage.md)", "",
        "This is the reviewable Markdown handbook structure. Every Markdown page "
        "is listed below, with its main section headings where useful. Introductory "
        "guides establish the objects and vocabulary; the subsequent implementation "
        "chapters explain decisions, concurrency, ownership, errors and teardown. "
        "Build the local HTML book, including SVG diagrams, with `python3 make_docs.py`; "
        "see [build and reading instructions](development/building-html.md).", "",
        "Use [the expansion audit](expansion-audit.md) to find the newly deepened "
        "topics, and [the source index](source-index.md) to navigate from a source "
        "file back to its explanations. Section links here target the Markdown "
        "headings; source excerpts retain checkout-relative references.", "",
        "Regenerate with `python3 docs-ai/tools/build_toc.py`.", "",
    ]
    for number, (label, directory, order) in enumerate(GROUPS, 1):
        group = [p for p in pages if p.parent == DOCS / directory]
        rank = {name: i for i, name in enumerate(order)}
        group.sort(key=lambda p: (rank.get(p.stem, len(order)), p.name))
        lines.extend([f"## {number}. {label}", ""])
        for page in group:
            title, sections = headings(page)
            target = page.relative_to(DOCS).as_posix()
            lines.append(f"- [{title}]({target})")
            if page.stem not in {"README", "source-index", "glossary", "coverage",
                                 "expansion-audit"}:
                for text, anchor in sections:
                    lines.append(f"  - [{text}]({target}#{anchor})")
            covered.add(page)
        lines.append("")
    if pages != covered:
        raise ValueError("Unclassified pages: " + ", ".join(
            str(p.relative_to(DOCS)) for p in sorted(pages - covered)))
    lines.extend([f"Listed: {len(covered)} pages, excluding this contents page.", ""])
    output.write_text(with_license_notice("\n".join(lines)))
    print(f"Listed {len(covered)} pages in {output.relative_to(DOCS)}")


if __name__ == "__main__":
    main()
