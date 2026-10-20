# Mach messages: processor_set

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/processor_set.defs](../../../xnu/osfmk/mach/processor_set.defs#L1). Listed in the kernel kobject subsystem table, subject to the registration guards and per-slot skips. The destination's typed capability still controls admission.
Registration evidence: [`mig_e`](../../../xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 4000: processor_set_statistics

**Interface contract:**

> Return scheduling statistics for a processor set.

**Mechanism:** Only the boot compatibility set is accepted. LOAD_INFO reports global scheduler load/Mach-factor values and global task/thread totals after checking capacity; the routine does not aggregate a private membership list under a set lock. Unsupported flavors return invalid-argument, while another set returns invalid-processor-set. [processor_set_statistics](../../../xnu/osfmk/kern/processor.c#L1595-L1627).

**Declarations:** [`processor_set_statistics`](../../../xnu/osfmk/mach/processor_set.defs#L77) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine processor_set_statistics(
         pset : processor_set_name_t;
         flavor : processor_set_flavor_t;
 out info_out : processor_set_info_t, CountInOut);
```

**Local body:** [`processor_set_statistics`](../../../xnu/osfmk/kern/processor.c#L1595).

### 4001: processor_set_destroy

Historical processor-set destruction request; the local body determines whether this implementation supports it.

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [processor_set_destroy](../../../xnu/osfmk/mach/processor_set.defs#L91).

**Declarations:** [`processor_set_destroy`](../../../xnu/osfmk/mach/processor_set.defs#L91) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine processor_set_destroy(
  set : processor_set_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 4002: processor_set_max_priority

Historical processor-set maximum-priority update.

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [processor_set_max_priority](../../../xnu/osfmk/mach/processor_set.defs#L94).

**Declarations:** [`processor_set_max_priority`](../../../xnu/osfmk/mach/processor_set.defs#L94) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine processor_set_max_priority(
  processor_set : processor_set_t;
  max_priority : int;
  change_threads : boolean_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 4003: processor_set_policy_enable

Historical processor-set policy-enablement request.

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [processor_set_policy_enable](../../../xnu/osfmk/mach/processor_set.defs#L99).

**Declarations:** [`processor_set_policy_enable`](../../../xnu/osfmk/mach/processor_set.defs#L99) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine processor_set_policy_enable(
  processor_set : processor_set_t;
  policy : int);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 4004: processor_set_policy_disable

Historical processor-set policy-disablement request.

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [processor_set_policy_disable](../../../xnu/osfmk/mach/processor_set.defs#L103).

**Declarations:** [`processor_set_policy_disable`](../../../xnu/osfmk/mach/processor_set.defs#L103) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine processor_set_policy_disable(
  processor_set : processor_set_t;
  policy : int;
  change_threads : boolean_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 4005: processor_set_tasks

**Interface contract:**

> List all tasks in processor set.

**Mechanism:** The shared enumeration accepts only `sched_boot_pset`, allocates arrays outside `tasks_threads_lock`, then retries until capacity covers the current global lists. It references IPC-active, non-exec-copy tasks under the lock, filters them through MAC exposure policy afterward, compacts the result, and converts references into task ports. The flavored entry validates CONTROL/READ/INSPECT/NAME; the older entry selects CONTROL. Allocation and filtering therefore precede capability publication. [processor_set_tasks](../../../xnu/osfmk/kern/processor.c#L1636-L1922).

**Declarations:** [`processor_set_tasks`](../../../xnu/osfmk/mach/processor_set.defs#L112) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine processor_set_tasks(
  processor_set : processor_set_t;
 out task_list : task_array_t);
```

**Local body:** [`processor_set_tasks`](../../../xnu/osfmk/kern/processor.c#L1893).
Calls visible in this body include `processor_set_tasks_internal`.

[Implementation excerpt](../../../xnu/osfmk/kern/processor.c#L1893-L1899):
<!-- source-excerpt: ../../../xnu/osfmk/kern/processor.c#L1893-L1899 -->
```c
processor_set_tasks(
	processor_set_t         pset,
	task_array_t            *task_list,
	mach_msg_type_number_t  *count)
{
	return processor_set_tasks_internal(pset, task_list, count, TASK_FLAVOR_CONTROL);
}
```

### 4006: processor_set_threads

Request the threads assigned to a processor set, with the capability flavor and local implementation limits.

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [processor_set_threads](../../../xnu/osfmk/mach/processor_set.defs#L124).

**Declarations:** [`processor_set_threads`](../../../xnu/osfmk/mach/processor_set.defs#L124) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine processor_set_threads(
  processor_set : processor_set_t;
 out thread_list : thread_act_array_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 4007: processor_set_policy_control

Historical processor-set scheduling-policy control.

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [processor_set_policy_control](../../../xnu/osfmk/mach/processor_set.defs#L127).

**Declarations:** [`processor_set_policy_control`](../../../xnu/osfmk/mach/processor_set.defs#L127) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine processor_set_policy_control(
 pset : processor_set_t;
 flavor : processor_set_flavor_t;
 policy_info : processor_set_info_t;
 change : boolean_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 4008: processor_set_stack_usage

Request processor-set stack-use statistics through the declared debugging interface.

**Mechanism:** This name survives in client declarations, while the kernel-server profiles reserve its slot with `skip`. There is no corresponding local server routine to trace here; the historical argument list must not be read as an implemented operation in this kernel. [processor_set_stack_usage](../../../xnu/osfmk/mach/processor_set.defs#L132).

**Declarations:** [`processor_set_stack_usage`](../../../xnu/osfmk/mach/processor_set.defs#L132) (`client64`, `client32`, `libsyscall64`, `sender64`).
**Reserved instead in:** `server64`, `server32`, `local64`.

**Fields after preprocessing (`client64`):**

```text
routine processor_set_stack_usage(
  pset : processor_set_t;
 out ltotal : unsigned;
 out space : vm_size_t;
 out resident : vm_size_t;
 out maxusage : vm_size_t;
 out maxstack : vm_offset_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.

### 4009: processor_set_info

**Interface contract:**

> Get information about processor set.

**Mechanism:** Rejects a null set and dispatches compatibility information flavors with per-layout capacity checks. BASIC_INFO reports the global available processor count and timeshare default; policy defaults/limits expose scheduler constants rather than a configurable independent set policy. Successful flavors return the real host and their actual word count; unsupported flavors fail. [processor_set_info](../../../xnu/osfmk/kern/processor.c#L1461-L1590).

**Declarations:** [`processor_set_info`](../../../xnu/osfmk/mach/processor_set.defs#L144) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine processor_set_info(
                set_name : processor_set_name_t;
                flavor : int;
        out host : host_t;
        out info_out : processor_set_info_t, CountInOut);
```

**Local body:** [`processor_set_info`](../../../xnu/osfmk/kern/processor.c#L1461).

### 4010: processor_set_tasks_with_flavor

**Interface contract:**

> List all tasks(/inspect/read) in processor set based on flavor.

**Mechanism:** The shared enumeration accepts only `sched_boot_pset`, allocates arrays outside `tasks_threads_lock`, then retries until capacity covers the current global lists. It references IPC-active, non-exec-copy tasks under the lock, filters them through MAC exposure policy afterward, compacts the result, and converts references into task ports. The flavored entry validates CONTROL/READ/INSPECT/NAME; the older entry selects CONTROL. Allocation and filtering therefore precede capability publication. [processor_set_tasks_with_flavor](../../../xnu/osfmk/kern/processor.c#L1636-L1922).

**Declarations:** [`processor_set_tasks_with_flavor`](../../../xnu/osfmk/mach/processor_set.defs#L153) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine processor_set_tasks_with_flavor(
  processor_set : processor_set_t;
  flavor : mach_task_flavor_t;
 out task_list : task_array_t);
```

**Local body:** [`processor_set_tasks_with_flavor`](../../../xnu/osfmk/kern/processor.c#L1907).
Calls visible in this body include `processor_set_tasks_internal`.

[Implementation excerpt](../../../xnu/osfmk/kern/processor.c#L1907-L1922):
<!-- source-excerpt: ../../../xnu/osfmk/kern/processor.c#L1907-L1922 -->
```c
processor_set_tasks_with_flavor(
	processor_set_t         pset,
	mach_task_flavor_t      flavor,
	task_array_t            *task_list,
	mach_msg_type_number_t  *count)
{
	switch (flavor) {
	case TASK_FLAVOR_CONTROL:
	case TASK_FLAVOR_READ:
	case TASK_FLAVOR_INSPECT:
	case TASK_FLAVOR_NAME:
		return processor_set_tasks_internal(pset, task_list, count, flavor);
	default:
		return KERN_INVALID_ARGUMENT;
	}
}
```

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
