# Mach messages: processor

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/processor.defs](../../../xnu/osfmk/mach/processor.defs#L1). Listed in the kernel kobject subsystem table, subject to the registration guards and per-slot skips. The destination's typed capability still controls admission.
Registration evidence: [`mig_e`](../../../xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 3000: processor_start_from_user

Start the selected processor through the serialized user-request CPU-start path.

**Mechanism:** The wrapper holds the cluster-powerdown mutex while the scheduler helper checks device support, system-required CPU rules, suspended powerdown, current user-online state and disabled-SMT restrictions. Success sets the user-online bit; restoring all managed CPUs ends manual user core control, and resulting power changes are applied through scheduler machinery. Pulled threads are flushed after scheduler locking is released. [Wrapper](../../../xnu/osfmk/kern/processor.c#L1277-L1293), [scheduler decisions](../../../xnu/osfmk/kern/sched_prim.c#L7465-L7532).

**Declarations:** [`processor_start_from_user`](../../../xnu/osfmk/mach/processor.defs#L83) (`server64`, `server32`, `local64`); [`processor_start`](../../../xnu/osfmk/mach/processor.defs#L86) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine processor_start_from_user(
  processor : processor_t);
```

**Local body:** [`processor_start_from_user`](../../../xnu/osfmk/kern/processor.c#L1277).
Calls visible in this body include `lck_mtx_lock`, `sched_processor_start_user`, `lck_mtx_unlock`.

[Implementation excerpt](../../../xnu/osfmk/kern/processor.c#L1277-L1293):
<!-- source-excerpt: ../../../xnu/osfmk/kern/processor.c#L1277-L1293 -->
```c
processor_start_from_user(
	processor_t                     processor)
{
	if (processor == PROCESSOR_NULL) {
		return KERN_INVALID_ARGUMENT;
	}

	kern_return_t result;

	lck_mtx_lock(&cluster_powerdown_lock);

	result = sched_processor_start_user(processor);

	lck_mtx_unlock(&cluster_powerdown_lock);

	return result;
}
```

### 3001: processor_exit_from_user

Request processor shutdown/offline through the corresponding machine/scheduler path.

**Mechanism:** Serializes with cluster powerdown, then takes the available-cores lock at scheduler interrupt level. The helper rejects unsupported/system-required CPUs, PMGR constraints, suspended powerdown, an already user-offlined CPU, and removal of the last available core. Success clears the user-online bit and applies any resulting powered-core change; pulled runnable threads are flushed after unlocking. [Wrapper](../../../xnu/osfmk/kern/processor.c#L1222-L1238), [scheduler decisions](../../../xnu/osfmk/kern/sched_prim.c#L7390-L7462).

**Declarations:** [`processor_exit_from_user`](../../../xnu/osfmk/mach/processor.defs#L95) (`server64`, `server32`, `local64`); [`processor_exit`](../../../xnu/osfmk/mach/processor.defs#L98) (`client64`, `client32`, `libsyscall64`, `sender64`).

**Fields after preprocessing (`server64`):**

```text
routine processor_exit_from_user(
  processor : processor_t);
```

**Local body:** [`processor_exit_from_user`](../../../xnu/osfmk/kern/processor.c#L1222).
Calls visible in this body include `lck_mtx_lock`, `sched_processor_exit_user`, `lck_mtx_unlock`.

[Implementation excerpt](../../../xnu/osfmk/kern/processor.c#L1222-L1238):
<!-- source-excerpt: ../../../xnu/osfmk/kern/processor.c#L1222-L1238 -->
```c
processor_exit_from_user(
	processor_t     processor)
{
	if (processor == PROCESSOR_NULL) {
		return KERN_INVALID_ARGUMENT;
	}

	kern_return_t result;

	lck_mtx_lock(&cluster_powerdown_lock);

	result = sched_processor_exit_user(processor);

	lck_mtx_unlock(&cluster_powerdown_lock);

	return result;
}
```

### 3002: processor_info

**Interface contract:**

> Return information about this processor.

**Mechanism:** Dispatches basic-info and CPU-load flavors locally after checking output capacity, and passes other flavors to `cpu_info`. Basic-info treats temporary shutdown specially and on x86 also excludes nonrecommended processors. Load output starts with zeroed system/user/idle fields, fills accounted ticks, and explicitly leaves NICE at zero. The host output is set only on a successful flavor implementation. [processor_info](../../../xnu/osfmk/kern/processor.c#L869-L951).

**Declarations:** [`processor_info`](../../../xnu/osfmk/mach/processor.defs#L105) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine processor_info(
  processor : processor_t;
  flavor : processor_flavor_t;
 out host : host_t;
 out processor_info_out: processor_info_t, CountInOut);
```

**Local body:** [`processor_info`](../../../xnu/osfmk/kern/processor.c#L869).
Calls visible in this body include `slot_type`, `slot_subtype`, `processor_cpu_load_info`, `cpu_info`.

### 3003: processor_control

**Interface contract:**

> Do something machine-dependent to processor.

**Mechanism:** After rejecting a null processor, forwards its stable CPU ID and the opaque flavor-dependent word array to the machine `cpu_control` implementation. The generic routine adds no policy changes or scheduling operations; architecture-specific support and its error code determine the result. [processor_control](../../../xnu/osfmk/kern/processor.c#L1427-L1437).

**Declarations:** [`processor_control`](../../../xnu/osfmk/mach/processor.defs#L115) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine processor_control(
  processor : processor_t;
  processor_cmd : processor_info_t);
```

**Local body:** [`processor_control`](../../../xnu/osfmk/kern/processor.c#L1427).
Calls visible in this body include `cpu_control`.

[Implementation excerpt](../../../xnu/osfmk/kern/processor.c#L1427-L1437):
<!-- source-excerpt: ../../../xnu/osfmk/kern/processor.c#L1427-L1437 -->
```c
processor_control(
	processor_t             processor,
	processor_info_t        info,
	mach_msg_type_number_t  count)
{
	if (processor == PROCESSOR_NULL) {
		return KERN_INVALID_ARGUMENT;
	}

	return cpu_control(processor->cpu_id, info, count);
}
```

### 3004: processor_assign

**Interface contract:**

> Assign processor to processor set.

**Mechanism:** This implementation ignores the processor, destination set and wait argument and always returns `KERN_FAILURE`. It does not migrate a CPU or wait for a change, despite the historical interface declaration. [processor_assign](../../../xnu/osfmk/kern/machine.c#L224-L230).

**Declarations:** [`processor_assign`](../../../xnu/osfmk/mach/processor.defs#L127) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine processor_assign(
  processor : processor_t;
  new_set : processor_set_t;
  wait : boolean_t);
```

**Local body:** [`processor_assign`](../../../xnu/osfmk/kern/machine.c#L224).

[Implementation excerpt](../../../xnu/osfmk/kern/machine.c#L224-L230):
<!-- source-excerpt: ../../../xnu/osfmk/kern/machine.c#L224-L230 -->
```c
processor_assign(
	__unused processor_t            processor,
	__unused processor_set_t        new_pset,
	__unused boolean_t              wait)
{
	return KERN_FAILURE;
}
```

### 3005: processor_get_assignment

**Interface contract:**

> Get current assignment for processor.

**Mechanism:** Reads the processor state and rejects offline or pending-offline processors. For an eligible processor it returns `sched_boot_pset`, rather than exposing that processor’s internal cluster set. Thus the user-visible assignment API presents the compatibility processor set, not the scheduler’s full internal topology. [processor_get_assignment](../../../xnu/osfmk/kern/processor.c#L1440-L1458).

**Declarations:** [`processor_get_assignment`](../../../xnu/osfmk/mach/processor.defs#L135) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine processor_get_assignment(
  processor : processor_t;
 out assigned_set : processor_set_name_t);
```

**Local body:** [`processor_get_assignment`](../../../xnu/osfmk/kern/processor.c#L1440).

[Implementation excerpt](../../../xnu/osfmk/kern/processor.c#L1440-L1458):
<!-- source-excerpt: ../../../xnu/osfmk/kern/processor.c#L1440-L1458 -->
```c
processor_get_assignment(
	processor_t     processor,
	processor_set_t *pset)
{
	int state;

	if (processor == PROCESSOR_NULL) {
		return KERN_INVALID_ARGUMENT;
	}

	state = processor->state;
	if (state == PROCESSOR_OFF_LINE || state == PROCESSOR_PENDING_OFFLINE) {
		return KERN_FAILURE;
	}

	*pset = sched_boot_pset;

	return KERN_SUCCESS;
}
```
