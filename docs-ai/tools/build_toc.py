#!/usr/bin/env python3
"""Generate the Markdown handbook TOC from chapter titles and section headings."""

from collections import Counter
from pathlib import Path
import re

from check_links import DOCS, prose_lines
from doc_license import with_license_notice


# Order follows the reading route, retaining both introductions and deeper chapters.
GROUPS = [
    ("Orientation", ".", [
        "README", "architecture", "source-map", "reading-guide",
        "glossary", "source-index",
    ]),
    ("Key structures: allocation, access and lifetime", "structures", [
        "README", "layout-browser", "proc-and-proc-ro", "task-and-shared-ro",
        "read-only-object-updates",
        "thread-and-thread-ro", "credentials-and-credential-storage",
        "mac-label-storage", "ipc-spaces-and-entries", "ipc-ports-and-kobjects",
        "vm-maps-and-entries", "vm-objects-and-backing",
        "vm-pages-and-resident-storage", "pmap-and-translation-storage",
        "memory-entries-and-vm-copies",
        "file-descriptor-tables", "fileprocs-and-fileglobs",
        "vnodes-and-vnode-identity", "ubc-and-vnode-pagers",
        "code-signature-blob-storage",
        "ipc-kmsgs-and-message-storage", "sockets-and-protocol-attachments",
        "socket-buffers-and-record-queues",
        "internet-pcbs-and-transport-storage", "mbufs-and-external-storage",
    ]),
    ("Execution, scheduling, waits and timers", "subsystems/runtime", [
        "README", "objects-and-lifecycle", "suspension-stop-and-abort",
        "scheduling", "scheduler-execution",
        "ast-mechanism", "ast-flavors",
        "priority-qos-and-quanta", "realtime-deadlines-and-runqueues",
        "work-interval-policy-and-thread-groups",
        "clutch-and-edge", "thread-group-accounting-and-cluster-migration",
        "cpu-eligibility-and-scheduler-variants",
        "waits-and-locks", "wait-and-turnstile-protocols",
        "reader-writer-locks", "ticket-and-pointer-locks",
        "time-and-accounting", "clocks-and-time-domains",
        "timer-and-thread-call-lifetime", "recount-and-resource-attribution",
        "ledgers-limits-and-settlement",
    ]),
    ("Virtual memory, hardware mappings and allocators", "subsystems/vm", [
        "README", "mapping-walkthroughs", "maps-and-faults", "virtual-address-maps",
        "api-argument-validation", "executable-memory-policy",
        "objects-and-pages", "mte-tag-storage-and-page-lifecycle",
        "fault-resolution", "pmap-arm64",
        "pmap-translation-walkthroughs",
        "pmap-mapping-lifecycle", "pmap-tlb-and-cache", "pmap-x86",
        "wiring-and-memory-entries", "copy-overwrite-and-remap", "pagers-and-upl",
        "upl-gather-and-completion", "executable-pages-and-upl-io",
        "shared-regions-and-transforming-pagers", "reclaim-and-pressure",
        "compressor-segments-and-swapfiles", "deferred-reclamation",
        "purgeable-memory", "phantom-cache-and-refaults",
        "memorystatus-and-freezer", "kernel-allocation", "zone-allocator",
        "kalloc-heaps-and-routing", "typed-allocation", "kernel-virtual-allocation",
        "read-only-and-special-zones", "allocator-interfaces",
    ]),
    ("Processes, signals, descriptors and event servicing", "subsystems/processes", [
        "README", "lifecycle", "process-transitions",
        "exec-identity-and-inherited-state", "exec-arguments-and-user-stack",
        "syscalls-signals",
        "signal-delivery-and-return", "descriptors-ipc",
        "process-inspection-and-snapshots",
        "pipes-and-unix-socket-rights", "user-lock-wait-and-wake",
        "posix-named-ipc", "system-v-ipc", "tty-and-pty-lifecycle", "events-threads",
        "kqueue-and-workloops", "pthread-workqueue-lifecycle", "async-io",
    ]),
    ("Mach IPC and exception delivery", "subsystems/ipc", [
        "README", "names-and-rights", "ports-and-rights-lifecycle",
        "port-sets-and-waitq-readiness", "message-path",
        "message-send-receive", "complex-message-copyin-and-copyout",
        "message-integrity-and-descriptor-authentication",
        "synchronous-dependencies-and-special-replies",
        "kernel-rpc-and-exceptions", "exception-delivery",
        "policies-and-attribution", "guards-and-policy-enforcement",
        "vouchers-and-importance", "importance-propagation-and-delayed-drops",
        "bank-accounts-and-charging", "semaphores-and-eventlinks",
    ]),
    ("System-call and Mach entry-point map", "interfaces", [
        "README", "machine-entry-points", "command-dispatch-and-validation", "mach-traps",
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
        "permissions-and-acl-evaluation",
        "name-cache-and-vnode-reclaim", "vnode-cache-identity-and-reuse",
        "namespace-mutations", "metadata-and-extended-attributes",
        "advisory-locks-and-leases", "filesystem-event-queues",
        "quota-cache-and-filesystem-boundaries", "mount-lifecycle",
        "io-and-cache", "file-data-cache-and-read-path", "buffer-cache-and-block-io",
        "clustered-writeback", "compressed-file-data", "filesystems-and-nfs",
        "device-nodes-and-fifos", "stacked-filesystems", "nfs-server-requests",
    ]),
    ("Sockets, transports, interfaces and Skywalk", "subsystems/networking", [
        "README", "sockets", "socket-lifecycle-and-io",
        "internet-pcbs-ports-and-lifetime", "udp-send-receive-and-errors",
        "tcp-ip-interfaces", "tcp-connections-and-timers",
        "tcp-loss-recovery-and-congestion-control", "mptcp-sessions-and-subflows",
        "ipv6", "ipv6-addresses-autoconfiguration-and-dad",
        "ipv6-router-advertisements-and-prefix-lifetime",
        "ipv6-source-selection-and-scopes", "ipv6-sockets-and-packet-options",
        "ipv6-input-extension-headers-and-forwarding",
        "ipv6-output-and-neighbor-discovery", "ipv6-neighbor-messages-and-reachability",
        "ipv6-multicast-membership-and-mld", "packets-routes-and-interfaces",
        "routing-control-and-ipv4-arp", "ip-fragment-reassembly-and-icmp",
        "mbuf-allocation-caches-and-pressure",
        "kernel-control-sockets-and-network-statistics",
        "policy-extensions", "bpf-capture-and-filter-lifecycle",
        "pf-rules-states-and-packet-ownership", "ipsec-policy-associations-and-transforms",
        "ipsec-interface-lifecycle",
        "necp-policy-evaluation",
        "necp-clients-and-flow-registration", "socket-content-filtering",
        "flow-diversion-and-provider-lifetime",
        "skywalk", "skywalk-lifecycles",
        "skywalk-controller-provider-and-port-lifetime",
        "skywalk-channel-abi-and-readiness",
        "skywalk-memory-arenas-and-mapping", "skywalk-packets-buflets-and-pools",
        "skywalk-user-and-kernel-pipes",
        "skywalk-namespaces-and-flow-lookup",
        "skywalk-flowswitch-classification-routes-and-datapaths",
        "skywalk-fragments-reassembly-and-flow-tracking",
        "skywalk-tcp-aggregation-segmentation-and-offloads",
        "skywalk-netif-links-queues-and-scheduling",
        "interface-packet-scheduling-and-fq-codel",
        "skywalk-netif-filters-and-reinjection",
        "skywalk-netif-agents-and-traffic-rules",
        "skywalk-diagnostics-configuration-and-tests",
    ]),
    ("IOKit, drivers and kernel libraries", "subsystems/drivers", [
        "README", "bootstrap-and-bsd-integration", "libkern-and-kext-runtime",
        "object-runtime-and-collections", "symbol-interning",
        "kext-loading-and-unloading",
        "serialization-and-property-transport", "nvram-variables-and-persistence",
        "registry-and-service-lifecycle",
        "registry-planes-and-properties", "service-matching-and-termination",
        "service-notifications-and-arbitration",
        "user-clients-and-driverkit", "user-client-and-driverkit-lifetime",
        "external-method-call-lifecycle", "driverkit-dispatch-and-actions",
        "shared-data-queues-and-notifications",
        "workloops-and-power", "workloop-and-power-protocols",
        "interrupt-routing-and-command-queues", "device-power-state-machine",
        "system-sleep-and-wake", "power-assertions-and-idle-policy", "memory-and-dma",
        "memory-descriptors-and-cpu-mappings", "dma-preparation-and-mapping",
        "dma-segment-walkthrough",
        "reporting-and-performance-control",
    ]),
    ("Authorization, audit and protected execution", "subsystems/security", [
        "README", "credentials-and-policy", "credential-and-policy-lifetimes",
        "personas-and-membership-resolution", "task-and-thread-capabilities",
        "arm64-thread-state-conversion",
        "code-signing", "signature-format-and-blob-validation",
        "vnode-signature-lifecycle", "executable-signature-policy",
        "page-signature-validation", "trust-cache-control",
        "code-signing-process-controls", "audit", "audit-pipeline",
        "audit-session-capabilities", "protected-execution",
        "sptm", "txm", "exclaves", "exclaves-execution",
        "exclaves-resources-and-memory", "exclaves-services",
    ]),
    ("Boot, exception levels, CPU lifecycle and platform services", "subsystems/platform", [
        "README", "boot", "bootstrap-memory-and-lockdown",
        "execution", "arm64-exception-entry",
        "arm64-exception-return", "arm64-assembly-walkthroughs", "arm64-user-memory-copy",
        "arm64-context-switching", "exception-levels-and-monitors",
        "hardware-mappings", "platform-services", "cpu-power-lifecycle",
        "hibernation-image-creation", "hibernation-restore", "x86-sleep-and-resume",
    ]),
    ("Paths and protocols across subsystems", "cross-cutting", [
        "execution-paths", "mapped-file-to-arm64-fault",
        "user-buffer-to-dma-completion", "skywalk-channel-operation",
        "executable-loading", "ownership-and-locking",
        "smr-and-publication", "smr-hash-tables", "completion-and-failure",
        "concurrent-operation-walkthroughs",
    ]),
    ("Build, tests and observation", "development", [
        "build-and-tests", "arm64-build-and-mig-walkthrough",
        "observability", "kdebug-storage-and-readout",
        "dtrace-provider-and-action-lifecycle",
        "sanitizer-runtime-and-reporting", "coverage-instrumentation-lifecycle",
        "kernel-logging-and-firehose",
        "stackshot-and-kcdata",
        "corpses-and-process-core-dumps", "panic-coordination-and-records",
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
        "[Guide index](README.md) · [Reading guide](reading-guide.md)", "",
        "This is the reviewable Markdown handbook structure. Every Markdown page "
        "is listed below, with its main section headings where useful. Introductory "
        "guides establish the objects and vocabulary; the subsequent implementation "
        "chapters explain decisions, concurrency, ownership, errors and teardown. "
        "Build the local HTML book, including SVG diagrams, with `python3 make_docs.py`; "
        "see [build and reading instructions](development/building-html.md).", "",
        "Use [the source index](source-index.md) to navigate from a source "
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
            if page.stem not in {"README", "source-index", "glossary"}:
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
