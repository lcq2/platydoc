# Structure layouts

[Key structures](README.md) · [Task storage](task-and-shared-ro.md) · [Recount accounting](../subsystems/runtime/recount-and-resource-attribution.md)

Explore a structure's size, alignment and field offsets for a selected source configuration. The HTML handbook includes an interactive layout browser here; it works offline, including when opened directly from the extracted handbook ZIP. JavaScript is required for the browser below.

<div id="structure-layout-explorer"></div>

## Find a field and its offset

Start from [the task layout](layout-browser.md?declaration=task), [thread machine state](layout-browser.md?declaration=machine_thread), [a thread group](layout-browser.md?declaration=thread_group), [an IPv6 interface address](layout-browser.md?declaration=in6_ifaddr), [the IPv6 header](layout-browser.md?declaration=ip6_hdr) or [the Recount track layout](layout-browser.md?declaration=recount_track). Select a configuration, expand embedded structures and choose an array index to follow the storage occupied by a field. Search narrows the available structures or field paths.

The declaration gutter shows offsets from the root object in hexadecimal, such as `(+0x30)`. The selected-field panel also shows the offset from its immediate parent. For an embedded array element, the root offset includes the containing fields and the selected index multiplied by the element stride. The decimal control changes the display without changing the layout.

A pointer occupies storage for an address. Following an available pointer target opens a separate object whose offsets start at zero. It does not add the pointee's fields to the containing allocation. Union members can overlap; bitfield positions include a bit remainder and width. A flexible array has a tail offset and element stride, but its allocation length is not determined by `sizeof`.

## Choose the preprocessing configuration

The supplied profiles target `arm64e-apple-ios`: RELEASE and DEVELOPMENT configurations generated from XNU's `iPhoneOS` rules, with T8103 and VMAPPLE board selections. These are source-analysis contexts, not identified shipped iPhone or iPad kernels. **Directives** shows requested macro definitions and the effective values observed by the compiler. An absent override, an explicit `#undef`, and `#define FLAG 0` are different: an `#ifdef FLAG` branch remains selected when the replacement is zero.

The iOS baseline explicitly defines `XNU_TARGET_OS_IOS=1` and `XNU_PLATFORM_iPhoneOS=1`, following [XNU's deployment-target rules](../../platydoc-data/xnu/makedefs/MakeInc.def#L132-L151). It also uses the matching [iPhoneOS configuration options](../../platydoc-data/xnu/config/MASTER.arm64.iPhoneOS), rather than changing a single macro on a MacOSX configuration. `XNU_TARGET_OS_OSX` is undefined. This matters for [MAC labels](../../platydoc-data/xnu/security/_label.h#L71-L89): defining the OSX macro even as zero selects seven policy slots; the iOS branch selects three or four according to `CONFIG_VNGUARD`. The profiles do not supply a complete SDK deployment environment or reproduce Apple-private compiler behavior.

Pointer-authentication intrinsics and calls are enabled in every supplied profile, so PAC-dependent fields remain present. Manual overrides that disable the required PAC context are rejected. For layout analysis, the entry source applies `#define __ptrauth(...)` with an empty replacement: this removes pointer-authentication qualifiers while retaining the pointer fields and their storage. The bundled upstream compiler cannot parse all of [XNU's qualifier forms](../../platydoc-data/xnu/libkern/os/base.h#L354-L364). The applied compatibility directive is visible in the configuration; it does not model pointer signing or authentication at runtime.

The two Recount shortcuts illustrate fields controlled by configuration:

| Control | Preprocessor flag | Effect on Recount storage |
| --- | --- | --- |
| CPI metrics | `CONFIG_PERVASIVE_CPI` | Includes `rm_instructions` and `rm_cycles`, the instruction and CPU-cycle counters used for cycles-per-instruction accounting. |
| Energy | `CONFIG_PERVASIVE_ENERGY` | Includes `ru_energy_nj`, CPU energy measured in nanojoules. |

These fields are conditional in [the Recount declaration](../../platydoc-data/xnu/osfmk/kern/recount.h#L139-L155). The switches change the source layout being analyzed; they do not start performance or energy monitoring in the browser. Other structures can depend on different flags. Source-dependency evidence explains known relationships, while unvisited branches and arbitrary flag combinations remain outside the verified profile set.

Changes to the supplied profiles are labeled as what-if configurations. A requested value may be redefined by an included header; inspect the effective value before interpreting the result. The selected target and CPU do not imply that private Apple compiler features are enabled.

## Compare and reopen a selection

Comparison starts from the selected profile's baseline. Pin the current result to compare subsequent changes against it. Added and excluded fields, changed field types and shifted offsets are marked; an excluded field has no current offset or size. Array element-size changes can move nested fields even when their local offsets stay the same.

The page URL preserves the selected root, field, array indices, profile, overrides and display options. Copy it to reopen that selection, or use browser Back and Forward. Pinned comparisons last only for the current session and are not included in the URL. A field known only from a pinned configuration may therefore be unavailable after reopening. Invalid or unavailable selections show a diagnostic instead of reusing prior offsets; reset the profile to recover.

## Scope and source evidence

The `thread_group` context parses the complete original `osfmk/kern/thread_group.c`, where its private definition lives. The entry source suppresses only that include's `-Wstatic-in-inline` warnings; linking and code generation are outside layout analysis. Macro-generated declaration names retain their macro invocation and expansion provenance, so token-pasted aliases do not prevent layouts such as `proc`, `vnode` or `in6_ifaddr` from opening.

The [`ucred_rw`](layout-browser.md?declaration=ucred_rw) context parses the complete original `bsd/kern/kern_credential.c` with `sys/sysproto.h` generated by XNU's own syscall script. Two Apple-only allocator builtins receive explicit, scoped layout-only replacements: `__builtin_xnu_type_summary(...)` becomes `0`, and `__builtin_xnu_type_signature(...)` becomes an empty string. These replacements affect allocator metadata, not [the four field declarations](../../platydoc-data/xnu/bsd/kern/kern_credential.c#L3295-L3300) or their types. The browser supports this structure's layout, not the resulting allocator flags, signatures or behavior. **Directives** displays the complete analysis entry, including these definitions and their scope.

The [`vnode_pager`](layout-browser.md?declaration=vnode_pager) context parses the complete original `osfmk/vm/bsd_vm.c`. Its Mach interface headers are generated locally from XNU's original `.defs` files with a pinned Linux-compatible Apple MIG source build. The prepared browser package includes the generated headers and their provenance; readers need no MIG installation. The [original pager declaration](../../platydoc-data/xnu/osfmk/vm/bsd_vm.c#L89-L100) remains unchanged.

The [`ubc_info`](layout-browser.md?declaration=ubc_info) and [`cs_blob`](layout-browser.md?declaration=cs_blob) context preserves the complete original headers and their PAC and code-signing-monitor guards. Its dependencies include older Apple-published TrustCache headers with their original notices, plus minimal, explicitly synthetic CoreEntitlements declarations used only to parse unrelated metadata records. These are layout-only parser placeholders, not reconstructed CoreEntitlements layouts or implementations. Neither target structure embeds those types. Changing the placeholder size and alignment leaves the returned target layouts unchanged. The context rejects outputs that expose placeholder-dependent types, and **Directives** shows the compatibility declarations. Original KDK headers are not included in the handbook package.

The HTML coverage table lists the inventoried structures and their availability in each base configuration. Available entries open the corresponding header context; unavailable entries explain the compiler, missing-header or declaration boundary. Separate contexts keep kernel, VM, BSD, IPC and networking header selections explicit, including IPv6 wire headers, options, routes, neighbor discovery and multicast state. Complete embedded records returned with an available root can also be explored. This finite inventory does not cover every structure in XNU. Results describe the bundled `xnu-12377.121.6` source, pinned upstream compiler and explicit configuration; they are not a claim about an unidentified shipped kernel or Apple-private LLVM behavior.

Source actions open the matching handbook source view where available, or download the exact analyzed header. Compilation and dependency analysis run locally in a worker; they need no installed compiler, server or network connection. Traced XNU analysis can use substantial memory. The worker is released after a request when its WebAssembly capacity exceeds the reuse threshold; that threshold does not limit memory during compilation. Cancelling an analysis stops that worker and clears the pending layout.

The [build guide](../development/building-html.md) explains artifact preparation, provenance and stale-input checks. Structure offsets complement the allocation and lifetime explanations in this section; they do not establish that an arbitrary pointer is valid or that a field can be accessed without synchronization.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
