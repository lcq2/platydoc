# Coverage audit: security, diagnostics, shared paths and orientation

**Current source-documentation pass.** [Executable-memory policy](../subsystems/vm/executable-memory-policy.md) follows JIT/protection/fault decisions, and the [ARM64 build/MIG walkthrough](../development/arm64-build-and-mig-walkthrough.md) connects concrete configuration/source/header selection to a Mach VM operation. Generated-stub bytes, SDK/tool behavior and external policy remain explicit boundaries. Further debugger and kperf expansion is deferred by request. See the [two-batch record](first-release-expansion.md#22-executable-memory-synchronization-packet-policy-and-build-selection).

**Previous argument/identity pass (historical scope).** The [argument/identity and instrumentation expansion](first-release-expansion.md#21-arguments-identity-integrity-instrumentation-and-packet-state) adds exec identity, kmsg integrity, ARM64 thread-state conversion and dedicated sanitizer/coverage runtime lifetimes. Historical D5 now has selected metadata/reporting and thread/buffer/close paths documented. Compiler internals, unavailable providers, deeper sampling and unreviewed variants remain bounded.

**Previous DTrace batch.** The [DTrace lifecycle companion](../development/dtrace-provider-and-action-lifecycle.md) now implements the selected historical D4 provider-to-action path: consumer state, DOF/DIF admission, ECB activation, ARM64 systrace hooks, recording, loss and teardown. [Current priorities](first-release-expansion.md#19-prioritized-review-ip-control-power-policy-and-instrumentation) retain sanitizer/coverage runtime and deeper sampling/provider combinations; user-space tooling and KDP remain outside this work.

**Earlier follow-up status (historical scope).** Task/thread capabilities, suspension/abort, stackshot, corpses/core files, ARM64 panic and VFS ACL decisions now have mechanism chapters. The [kernel logging companion](../development/kernel-logging-and-firehose.md) expands local encoding, allocation, retry, publication, streaming and text readout; its imported Firehose manager and userspace consumers remain external. New companions explain [personas and membership resolution](../subsystems/security/personas-and-membership-resolution.md), [audit-session capabilities](../subsystems/security/audit-session-capabilities.md), [SMR hash tables](../cross-cutting/smr-hash-tables.md) and the concrete [symbol pool](../subsystems/drivers/symbol-interning.md). Historical findings below are preserved. The [Kdebug companion](../development/kdebug-storage-and-readout.md) now follows local trace storage, timestamp merging, loss and consuming output. The [trust-cache companion](../subsystems/security/trust-cache-control.md) and [process signing/CSR companion](../subsystems/security/code-signing-process-controls.md) now trace local control and ownership; [RW locks](../subsystems/runtime/reader-writer-locks.md) and [ticket/pointer locks](../subsystems/runtime/ticket-and-pointer-locks.md) explain the selected synchronization implementations. Remaining subjects include external policy and trace tooling, sanitizers/coverage runtime, other DTrace providers/actions, unreviewed variants and interleavings. KDP and x86 remain excluded.

The historical C2 worked-operation proposal now has [file mapping through an ARM64 fault](../cross-cutting/mapped-file-to-arm64-fault.md), [user memory through DMA completion](../cross-cutting/user-buffer-to-dma-completion.md) and [Skywalk channel publication/readiness/close](../cross-cutting/skywalk-channel-operation.md). These preserve one address/object/slot ledger across subsystem transitions and distinguish numeric examples from source test assertions and external provider obligations. See the [batch record](first-release-expansion.md#17-iokit-queue-and-service-protocols-and-worked-operations). Other operations and configuration/failure combinations remain useful extensions; C2 below retains its original proposal rather than claiming these traces are still absent.

[Consolidated audit](../coverage-audit.md) · [Existing coverage record](../coverage.md) · [Inventory](inventory.json)

This is an audit of the existing explanations, with selected source-body checks to establish that a proposed expansion has useful local implementation to explain. It is not a new audit of every kernel branch. The starting scope is 29 explanatory pages: 17 security, five cross-cutting, two development, and five orientation pages. Historical coverage records and generated indexes are assessed in the consolidated audit.

“Retain” means the page serves its present purpose; it does not certify exhaustive coverage. “Deepen” means important paths within its subject remain partial. “Add neighbor” means a separate implementation chapter would preserve a useful overview. P1 denotes a foundational or broadly useful missing trace, P2 a valuable next layer, and P3 specialized depth.

## What is already strong

The four recent signature chapters explain container selection, storage transformations, vnode publication, execution admission, hashing, cached masks and invalidation. They should not be expanded simply by repeating the same call graph. Credential publication, audit output, SPTM/TXM and Exclaves also have substantial ownership and failure-path explanations. Missing AMFI, CoreTrust, sandbox policies and secure-monitor bodies remain external; additional prose cannot recover their algorithms.

The largest imbalance here is diagnostics. The observability guide explains selected entry points well, but covers several independent subsystems in one survey. It does not yet give a reader enough detail to reason about an entire crash dump, multi-CPU stackshot, logging queue, or instrumentation lifecycle.

## S1. Task and thread rights as an end-to-end capability path — P1

**Current coverage:** [credentials and task rights](../subsystems/security/credentials-and-policy.md) summarizes `task_for_pid` and conversion; the IPC guides explain port objects and transfer. The flavor-specific acquisition, use and revocation story is still distributed.

**Available evidence:** [`task_inspect_for_pid`](../../xnu/bsd/kern/kern_proc.c#L6122) obtains a target identity and task reference, drops the proc reference before possible upcalls, and passes `TASK_FLAVOR_INSPECT` to MAC. [`task_read_for_pid`](../../xnu/bsd/kern/kern_proc.c#L6244), [`task_name_for_pid`](../../xnu/bsd/kern/kern_proc.c#L6029), [`task_conversion_eval_internal`](../../xnu/osfmk/kern/ipc_tt.c#L2277), and the [flavor conversion helpers](../../xnu/osfmk/kern/ipc_tt.c#L2439) are actual local implementations.

**Proposed expansion:** a capability matrix and two complete traces: acquire a foreign task right; consume it through a generated-interface conversion. Explain name/inspect/read/control, self and corpse exceptions, incoming versus outgoing conversion, Developer Mode/build branches, task/thread references, identity revalidation, copyout failure and reset. Keep the external task-access service and MAC decision distinct from XNU's local gates. This builds on existing IPC rather than restating namespace mechanics.

## S2. Personas and group-resolution identity — P2

**Current coverage:** [credential lifetimes](../subsystems/security/credential-and-policy-lifetimes.md) explicitly excludes personas and external membership handling.

**Available evidence:** [`persona_alloc`](../../xnu/bsd/kern/kern_persona.c#L93), [`persona_proc_adopt`](../../xnu/bsd/kern/kern_persona.c#L714), [`persona_proc_drop`](../../xnu/bsd/kern/kern_persona.c#L772), and [persona syscall dispatch](../../xnu/bsd/kern/sys_persona.c) implement local allocation, association and cleanup. Adoption consumes a persona reference; drop uses a lock-order retry and does not simply restore a previous credential. [`kern_credential.c`](../../xnu/bsd/kern/kern_credential.c) supplies the identity and membership cache machinery. `CONFIG_PERSONAS` is selected in [`config/MASTER`](../../xnu/config/MASTER#L560).

**Proposed expansion:** persona IDs versus UIDs, allocation/lookup/invalidation, spawn adoption and credential derivation, process-count changes, thread identity, drop/exit, membership-cache key/expiry and provider upcalls. Read [persona tests](../../xnu/tests/persona.c) and [adoption tests](../../xnu/tests/rm/persona_adoption.c) for observable contracts without implying they ran. User-service policy and membership database internals remain external.

## S3. Audit-session ports and credential changes — P2

**Current coverage:** [audit](../subsystems/security/audit.md) explicitly surveys session join; [audit pipeline](../subsystems/security/audit-pipeline.md) concentrates on record ownership/output.

**Available evidence:** [`audit_session_self`](../../xnu/bsd/security/audit/audit_session.c#L1223) converts session state into a send right and captures selection-mask state. [`audit_session_join_internal`](../../xnu/bsd/security/audit/audit_session.c#L1391) changes process counts, serializes credential replacement, and releases the supplied typed send right. [Session tests](../../xnu/tests/audit_session.c) and [invalid setter tests](../../xnu/tests/invalid_setaudit_57414044.c) are present.

**Proposed expansion:** `au_sentry` lifetime, session identity versus effective UID, port creation/conversion/no-senders, self/join/spawnjoin, inherited masks, concurrent credential replacement, reference and process counts, failure and session-end events. This connects credential and IPC chapters without repeating trail serialization.

## S4. Trust-cache control, csops and boot security configuration — P2

**Current coverage:** the [signing overview](../subsystems/security/code-signing.md) has short trust-cache and CSR sections; [TXM](../subsystems/security/txm.md) already explains the protected backend.

**Available evidence:** [`load_trust_cache_with_type`](../../xnu/bsd/kern/kern_trustcache.c#L893) validates input intervals, selects embedded/external manifests, checks provider version, type and entitlement, then dispatches. [`xnu_load_trust_cache`](../../xnu/bsd/kern/kern_trustcache.c#L613) and [`xnu_query_trust_cache`](../../xnu/bsd/kern/kern_trustcache.c#L732) expose ordinary-runtime ownership; [`csops_internal`](../../xnu/bsd/kern/kern_proc.c#L3697) supplies a substantial command-dependent interface. [`csr_bootstrap`](../../xnu/bsd/kern/kern_csr.c#L180) and [`csr_check`](../../xnu/bsd/kern/kern_csr.c#L241) have configuration-specific implementations.

**Proposed expansion:** frontend-to-backend matrix, permitted cache types, payload ownership, locking, duplicate/load state, query-token lifetime, csops query versus mutation, audit-token identity checks, copyout and entitlement gates, CSR initialization and consumers. Explain Image4, AMFI and monitor contracts without inventing their verification algorithms. Preserve the distinction between policy configuration, a trusted code identity, and hashing a resident page.

## D1. Crash artifacts: corpse, process core and kernel dump — P1

**Current coverage:** exception and process guides reach fatal outcomes; [observability](../development/observability.md) mostly locates dump infrastructure.

**Available evidence:** [`task_generate_corpse`](../../xnu/osfmk/corpses/corpse.c#L440) creates a corpse task, waits for thread termination, resets selected ports and transfers a task reference to a port with no-senders handling. [`coredump`](../../xnu/bsd/kern/kern_core.c#L376) is a separate current-process VM/VFS operation with eligibility and output policy. [`DebuggerTrapWithState`](../../xnu/osfmk/kern/debug.c#L724) saves debugger state and enters the trap; [`kdp_core_init_output_stages`](../../xnu/osfmk/kdp/kdp_core.c#L1448) builds distinct output stages with availability and configuration limits.

**Proposed expansion:** split into a corpse/process-core chapter and a kernel-panic/dump chapter. Trace exception notification, snapshot ownership and quota, Mach-right release, map traversal, Mach-O core contents, file safety and partial writes; separately trace panic ownership, CPU rendezvous, nested panic, data selection, compression/encryption/output stages and failed output. Use [corpse backtrace](../../xnu/tests/corpse_backtrace.c), [corpse footprint](../../xnu/tests/vm/corpse_footprint.c) and [core-name tests](../../xnu/tests/proc_core_name_24152432.c) as examples of different contracts. External crash-report services and hardware transport remain boundaries.

## D2. Stackshot collection and kcdata consumption — P1

**Current coverage:** [observability](../development/observability.md) gives the entry gate, trap and record layout, but not collection ownership and output assembly.

**Available evidence:** [`kern_stack_snapshot_internal`](../../xnu/osfmk/kern/kern_stackshot.c#L2403) parses versioned options and owns buffer/result handling. [`stackshot_cpu_work_on_queue`](../../xnu/osfmk/kern/kern_stackshot.c#L6166) obtains work items, records tasks into linked kcdata, checks global failure and distinguishes an empty queue from completed population. [CPU work selection](../../xnu/osfmk/kern/kern_stackshot.c#L6198) changes queue order with CPU kind. [kcdata construction](../../xnu/osfmk/kern/kern_cdata.c), [decoder](../../xnu/libkdd/kdd.h), and [stackshot tests](../../xnu/tests/stackshot_tests.m) are present.

**Proposed expansion:** configuration and allocation retry, single/multi-CPU capture, task/thread selection, delta snapshots, controlled faulting, wait/turnstile records, linked-buffer assembly, compression, copyout and cleanup. Include a record diagram and a small source-derived decode example. Separate snapshot consistency limits from generic stop-the-world assumptions. Existing [upstream multithreaded notes](../../xnu/doc/observability/mt_stackshot.md) should supplement the actual selected body.

## D3. Trace consumption and kernel logging queues — P2

**Current coverage:** [observability](../development/observability.md) explains the kdebug producer and ktrace ownership; unified logging is a navigation paragraph.

**Available evidence:** [`_read_trace_events_internal`](../../xnu/bsd/kern/kdebug.c#L2458) and [`_read_trace_events`](../../xnu/bsd/kern/kdebug.c#L2661) provide the consumer side. [`log_queue_add_entry`](../../xnu/libkern/os/log_queue.c#L240) allocates/copies/publishes queued data, while [`log_queue_dispatch_logs`](../../xnu/libkern/os/log_queue.c#L332) publishes success/failure and leaves cleanup to another phase. [Log memory allocation](../../xnu/libkern/os/log_mem.c), [encoding](../../xnu/libkern/os/log_encode.c), [BSD log streaming](../../xnu/bsd/kern/subr_log_stream.c), and [ktrace tests](../../xnu/tests/ktrace/kdebug_tests.c) are local.

**Proposed expansion:** two separate paths. Trace storage-unit allocation, wrap/loss, timestamp merging, filters, read/copyout and reset; then log formatting/public-private data, per-CPU queues, memory pressure, retry/drop, firehose handoff and streaming. The userspace persistence service is external. A queued record is not necessarily delivered or durable.

## D4. DTrace provider-to-action execution — P2

**Current coverage:** the observability chapter explicitly does not audit DIF execution or providers.

**Available evidence:** [`dtrace_probe`](../../xnu/bsd/dev/dtrace/dtrace.c#L7047) validates probe identity, uses predicate caching and checks panic state; [`dtrace_dif_emulate`](../../xnu/bsd/dev/dtrace/dtrace.c#L5767) executes an instruction stream with machine/variable state and fault flags. [`dtrace_enabling_match`](../../xnu/bsd/dev/dtrace/dtrace.c#L12770), [`dtrace_ioctl`](../../xnu/bsd/dev/dtrace/dtrace.c#L17845), provider source and [Darwin glue](../../xnu/bsd/dev/dtrace/dtrace_glue.c) are present. Selection is explicit in [`config/MASTER`](../../xnu/config/MASTER#L623).

**Proposed expansion:** open/configure/enable, provider/probe/ECB/action objects, predicate and DIF validation/execution, scratch/dynamic data, buffering/aggregation, fault/drop reporting, disabling and provider teardown. Start with one actual provider and avoid expanding every opcode before the lifecycle is understandable. Tool-side compilation and policy availability need separate limits.

## D5. Sanitizer and coverage instrumentation lifetimes — P2

**Current coverage:** allocator chapters identify selected hooks; the observability survey locates backends.

**Available evidence:** classic [`kasan_check_range`](../../xnu/san/memory/kasan-classic.c#L358) consults poisoned shadow state; the [TBI implementation](../../xnu/san/memory/kasan-tbi.c#L375) compares tags with different wildcard and enable predicates. [`ksancov_ioctl`](../../xnu/san/coverage/kcov_ksancov.c#L1424) selects allocation, mapping and thread-attachment operations under different locks. [Build selection](../../xnu/san/conf/files), [KASAN tests](../../xnu/san/memory/kasan-test.c), and [KSANCOV tests](../../xnu/tests/ksancov.c) are present.

**Proposed expansion:** allocation/free and redzones/quarantine, shadow/tag geometry, compiler callback versus explicit checks, fake-stack lifetime, report suppression, UBSAN reporting, coverage-buffer mapping and thread detach/close. Distinguish software instrumentation from hardware MTE and from allocator type isolation. Compiler instrumentation internals are not fully supplied here.

## D6. Configuration and test evidence attached to implementation chapters — P1

**Current coverage:** [build and tests](../development/build-and-tests.md) is an effective orientation. Most detailed chapters provide source examples but no local test-to-invariant map.

**Available evidence:** [source selection](../../xnu/bsd/conf/files), [feature definitions](../../xnu/config/MASTER), [Darwin test build](../../xnu/tests/Makefile), [POST documentation](../../xnu/osfmk/tests/README.md), [unit harness](../../xnu/tests/unit/README.md), and [VM parameter tests](../../xnu/tests/vm/vm_parameter_validation.c) allow a useful cross-reference without compiling the kernel.

**Proposed expansion:** add short configuration tables and selected test cases to each new chapter: the invariant asserted, relevant feature/architecture/entitlement, expected failure or partial progress, and the implementation branch. Add a worked generated-interface/source-selection example to the build guide. This is a documentation deliverable, not a request to run unavailable Apple tooling. Prioritize pmap, DMA, Skywalk and other newly expanded paths.

## C1. SMR hash tables and resizing — P2

**Current coverage:** [SMR/publication](../cross-cutting/smr-and-publication.md) is detailed on readers, grace periods and callbacks, but explicitly excludes hash resizing.

**Available evidence:** [`__smr_hash_shrink_and_unlock`](../../xnu/osfmk/kern/smr.c#L2358), [`__smr_hash_grow_and_unlock`](../../xnu/osfmk/kern/smr.c#L2417), [`__smr_shash_rehash_with_target`](../../xnu/osfmk/kern/smr.c#L2927), and [hash traits/interfaces](../../xnu/osfmk/kern/smr_hash.h) contain local array replacement, rehash and grace-period mechanisms.

**Proposed expansion:** contrast serialized-writer and scalable tables, lookup/insert/remove traits, duplicate insertion, grow/shrink/reseed triggers, concurrent-reader visibility and old-array reclamation. Use a real credential or symbol-pool client rather than describing only generic macros. Coordinate the symbol-pool example with the [VM/driver audit](vm-and-drivers.md).

## C2. Worked cross-subsystem operations — P2

**Current coverage:** [execution paths](../cross-cutting/execution-paths.md) provides orientation; [completion/failure](../cross-cutting/completion-and-failure.md) already provides useful comparisons.

**Proposed expansion:** add a small set of concrete object-state walkthroughs: process `mmap` to fault/PTE, user buffer to DMA segments and device completion, and a Skywalk channel from creation through TX/RX and teardown. Use diagrams with address domains, reference owners and failure checkpoints. Link deeper chapters for branch details. This fills a teaching gap, not an absent-kernel-code gap; the requested pmap and DMA expansions directly serve it.

## Chapter-by-chapter disposition

| Existing page | Disposition | Reason or next action |
| --- | --- | --- |
| [Guide index](../README.md) | Retain | Add current audit and expansion routes; avoid turning it into another technical chapter. |
| [Architecture](../architecture.md) | Retain | Keep component model; link address-domain and channel walkthroughs. |
| [Source map](../source-map.md) | Deepen | Reproducible counts and evidence boundaries; directory size is not review depth. |
| [Reading guide](../reading-guide.md) | Deepen | Add concrete pmap/DMA/Skywalk checkpoints as chapters land. |
| [Glossary](../glossary.md) | Retain | Add terms only with their implementation chapters. |
| [Security index](../subsystems/security/README.md) | Retain | Organize S1–S4 without replacing current signing/protected routes. |
| [Credentials and policy](../subsystems/security/credentials-and-policy.md) | Add neighbor | S1 capability matrix and S2 identity mechanisms. |
| [Credential lifetimes](../subsystems/security/credential-and-policy-lifetimes.md) | Retain | Publication/SMR/MAC lifetime already substantial; add S2 link. |
| [Signing overview](../subsystems/security/code-signing.md) | Add neighbor | S4 trust-control and csops remain short. |
| [Signature format](../subsystems/security/signature-format-and-blob-validation.md) | Retain | Current structural/transform path is detailed; add selected tests under D6. |
| [Signature lifecycle](../subsystems/security/vnode-signature-lifecycle.md) | Retain | Current attachment/revalidation/cleanup is detailed. |
| [Executable policy](../subsystems/security/executable-signature-policy.md) | Retain | Preserve provider boundaries; link S1/S4 rather than inventing policy. |
| [Page integrity](../subsystems/security/page-signature-validation.md) | Retain | Integrity predicates and writes/COW/UPL covered; connect expanded pmap route. |
| [Audit overview](../subsystems/security/audit.md) | Add neighbor | S3 session ports and identity transitions. |
| [Audit pipeline](../subsystems/security/audit-pipeline.md) | Retain | Queue/output/failure trace is substantial; token catalog is lower value. |
| [Protected execution map](../subsystems/security/protected-execution.md) | Retain | Preserve local versus external contract distinctions. |
| [SPTM](../subsystems/security/sptm.md) | Retain | Add pmap walkthrough links; external monitor algorithm is unavailable. |
| [TXM](../subsystems/security/txm.md) | Retain | S4 frontend complements its protected backend. |
| [Exclaves overview](../subsystems/security/exclaves.md) | Retain | Useful entry route into detailed companions. |
| [Exclaves execution](../subsystems/security/exclaves-execution.md) | Retain | Detailed local scheduler/RPC/return path; full secure scheduler is external. |
| [Exclaves resources](../subsystems/security/exclaves-resources-and-memory.md) | Retain | Local resource/physical ownership already traced. |
| [Exclaves services](../subsystems/security/exclaves-services.md) | Deepen | P3 individual service failure/diagnostic cases after D1–D2; generated bodies may be absent. |
| [Execution paths](../cross-cutting/execution-paths.md) | Deepen | C2 concrete state/address examples. |
| [Executable loading](../cross-cutting/executable-loading.md) | Add neighbor | Shared-region/dyld pager lifecycle belongs in the VM expansion. |
| [Ownership and locking](../cross-cutting/ownership-and-locking.md) | Retain | Preserve concise shared rules; link concrete protocols. |
| [SMR and publication](../cross-cutting/smr-and-publication.md) | Add neighbor | C1 hash resize/reseed and real clients. |
| [Completion and failure](../cross-cutting/completion-and-failure.md) | Deepen | Add DMA and channel completion contrasts once their detailed paths exist. |
| [Build and tests](../development/build-and-tests.md) | Deepen | D6 configuration/test-to-invariant examples. |
| [Observability](../development/observability.md) | Add neighbors | D1–D5 are independent mechanisms too large for one survey. |

## Boundaries and verification

The recommendations above come from chapter review, file/symbol searches, and selected implementation bodies. They do not imply whole-file verification of DTrace, stackshot, every MAC hook or every configuration. No kernel build, runtime test, trace, dump or hardware experiment was performed. The requested pmap, DMA, ARM64 assembly and thread-switching walkthroughs were completed alongside this audit; the other candidates remain a prioritized backlog. See the [consolidated record](../coverage-audit.md#requested-expansion-tracks).

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
