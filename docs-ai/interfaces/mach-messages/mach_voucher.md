# Mach messages: mach_voucher

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/mach_voucher.defs](../../../platydoc-data/xnu/osfmk/mach/mach_voucher.defs#L1). Listed in the kernel kobject subsystem table, subject to the registration guards and per-slot skips. The destination's typed capability still controls admission.
Registration evidence: [`mig_e`](../../../platydoc-data/xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 5400: mach_voucher_extract_attr_content

**Interface contract:**

> extract just the content data for a <voucher, key> pair

**Mechanism:** Maps the key to the voucher's immutable value index; an unused value produces an empty successful output. Otherwise it finds the registered manager/control, rejects an absent manager, and calls `ivace_lookup_values`, whose current body returns exactly one handle for a present value. The manager's extraction callback receives that handle and the caller's capacity, and its status is returned directly. These bytes are manager-defined. [Implementation](../../../platydoc-data/xnu/osfmk/ipc/ipc_voucher.c#L1668), [value lookup](../../../platydoc-data/xnu/osfmk/ipc/ipc_voucher.c#L515).

**Declarations:** [`mach_voucher_extract_attr_content`](../../../platydoc-data/xnu/osfmk/mach/mach_voucher.defs#L39) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_voucher_extract_attr_content(
  voucher : ipc_voucher_t;
  key : mach_voucher_attr_key_t;
 out content : mach_voucher_attr_content_t, CountInOut);
```

**Local body:** [`mach_voucher_extract_attr_content`](../../../platydoc-data/xnu/osfmk/ipc/ipc_voucher.c#L1668).
Calls visible in this body include `iv_key_to_index`, `iv_lookup`, `ivgt_lookup`, `ivace_lookup_values`.

### 5401: mach_voucher_extract_attr_recipe

**Interface contract:**

> extract a recipe to reconstitue a <voucher, key> pair item in a future voucher

**Mechanism:** Requires room for a recipe header after locating a present attribute, initializes key/command/previous-voucher fields and gives the remaining capacity to the manager extractor. On success it reports header plus actual content length. Missing attributes return zero length; insufficient header capacity returns `KERN_NO_SPACE`. [`Implementation`](../../../platydoc-data/xnu/osfmk/ipc/ipc_voucher.c#L1737).

**Declarations:** [`mach_voucher_extract_attr_recipe`](../../../platydoc-data/xnu/osfmk/mach/mach_voucher.defs#L48) (`server64`, `server32`, `libsyscall64`, `sender64`, `local64`); [`_kernelrpc_mach_voucher_extract_attr_recipe`](../../../platydoc-data/xnu/osfmk/mach/mach_voucher.defs#L46) (`client64`, `client32`).

**Fields after preprocessing (`server64`):**

```text
routine mach_voucher_extract_attr_recipe(
  voucher : ipc_voucher_t;
  key : mach_voucher_attr_key_t;
 out recipe : mach_voucher_attr_raw_recipe_t, CountInOut);
```

**Local body:** [`mach_voucher_extract_attr_recipe`](../../../platydoc-data/xnu/osfmk/ipc/ipc_voucher.c#L1737).
Calls visible in this body include `iv_key_to_index`, `iv_lookup`, `ivgt_lookup`, `ivace_lookup_values`.

**User wrapper:** [`mach_voucher_extract_attr_recipe`](../../../platydoc-data/xnu/libsyscall/mach/mach_port.c#L736).
Calls visible in this body include `mach_voucher_extract_attr_recipe_trap`, `_kernelrpc_mach_voucher_extract_attr_recipe`.

[Implementation excerpt](../../../platydoc-data/xnu/libsyscall/mach/mach_port.c#L736-L751):
<!-- source-excerpt: ../../../platydoc-data/xnu/libsyscall/mach/mach_port.c#L736-L751 -->
```c
mach_voucher_extract_attr_recipe(
	mach_port_name_t voucher,
	mach_voucher_attr_key_t key,
	mach_voucher_attr_raw_recipe_t recipe,
	mach_msg_type_number_t *recipe_size)
{
	kern_return_t rv;

	rv = mach_voucher_extract_attr_recipe_trap(voucher, key, recipe, recipe_size);

	if (rv == MACH_SEND_INVALID_DEST) {
		rv = _kernelrpc_mach_voucher_extract_attr_recipe(voucher, key, recipe, recipe_size);
	}

	return rv;
}
```

### 5402: mach_voucher_extract_all_attr_recipes

**Interface contract:**

> extract a recipe array to reconstitue all the key values in a future voucher

**Mechanism:** Iterates voucher key indices, skips unused values and appends a header/content record per present attribute. Insufficient capacity or an extraction callback error stops the walk; only full completion writes the final used size. A missing manager is asserted against and, in the explicit fallback branch, skipped rather than returned as an error. The immutable voucher is unchanged. [`Implementation`](../../../platydoc-data/xnu/osfmk/ipc/ipc_voucher.c#L1820).

**Declarations:** [`mach_voucher_extract_all_attr_recipes`](../../../platydoc-data/xnu/osfmk/mach/mach_voucher.defs#L55) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_voucher_extract_all_attr_recipes(
  voucher : ipc_voucher_t;
 out recipes : mach_voucher_attr_raw_recipe_array_t, CountInOut);
```

**Local body:** [`mach_voucher_extract_all_attr_recipes`](../../../platydoc-data/xnu/osfmk/ipc/ipc_voucher.c#L1820).
Calls visible in this body include `iv_lookup`, `ivgt_lookup`, `os_sub3_overflow`, `ivace_lookup_values`, `iv_index_to_key`.

### 5403: mach_voucher_attr_command

**Interface contract:**

> execute a command against a given voucher attribute

**Mechanism:** Finds the manager/control for the requested key and resolves the voucher's value handles, then dispatches `ivam_command` with command number and input/output buffers. Each manager defines the actual command semantics and validation; the common voucher layer validates voucher/manager presence and supplies the associated values. [`Implementation`](../../../platydoc-data/xnu/osfmk/ipc/ipc_voucher.c#L1972).

**Declarations:** [`mach_voucher_attr_command`](../../../platydoc-data/xnu/osfmk/mach/mach_voucher.defs#L60) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_voucher_attr_command(
  voucher : ipc_voucher_t;
  key : mach_voucher_attr_key_t;
  command : mach_voucher_attr_command_t;
  in_content : mach_voucher_attr_content_t;
 out out_content : mach_voucher_attr_content_t, CountInOut);
```

**Local body:** [`mach_voucher_attr_command`](../../../platydoc-data/xnu/osfmk/ipc/ipc_voucher.c#L1972).
Calls visible in this body include `iv_key_to_index`, `ivgt_lookup`, `iv_lookup`, `ivace_lookup_values`.

### 5404: mach_voucher_debug_info

**Interface contract:**

> extract a recipe array to reconstitue all the key values in a future voucher

**Mechanism:** Development/debug builds translate the named send right, convert it to a referenced voucher, unlock the port, extract all recipes and release the voucher. Invalid names/types fail. The nondevelopment/nondebug body returns `KERN_NOT_SUPPORTED`, so a declaration alone does not imply recipe inspection is available. [`Implementation`](../../../platydoc-data/xnu/osfmk/ipc/ipc_voucher.c#L1911).

**Declarations:** [`mach_voucher_debug_info`](../../../platydoc-data/xnu/osfmk/mach/mach_voucher.defs#L68) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_voucher_debug_info(
  task : ipc_space_read_t;
  voucher_name: mach_port_name_t;
 out recipes : mach_voucher_attr_raw_recipe_array_t, CountInOut);
```

**Local body:** [`mach_voucher_debug_info`](../../../platydoc-data/xnu/osfmk/ipc/ipc_voucher.c#L1913).

[Implementation excerpt](../../../platydoc-data/xnu/osfmk/ipc/ipc_voucher.c#L1913-L1920):
<!-- source-excerpt: ../../../platydoc-data/xnu/osfmk/ipc/ipc_voucher.c#L1913-L1920 -->
```c
mach_voucher_debug_info(
	ipc_space_t                                     __unused space,
	mach_port_name_t                                __unused voucher_name,
	mach_voucher_attr_raw_recipe_array_t            __unused recipes,
	mach_voucher_attr_raw_recipe_array_size_t       __unused *in_out_size)
{
	return KERN_NOT_SUPPORTED;
}
```

**Local body:** [`mach_voucher_debug_info`](../../../platydoc-data/xnu/osfmk/ipc/ipc_voucher.c#L1923).
Calls visible in this body include `MACH_PORT_VALID`, `ipc_port_translate_send`, `convert_port_to_voucher`, `ip_mq_unlock`, `mach_voucher_extract_all_attr_recipes`, `ipc_voucher_release`.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
