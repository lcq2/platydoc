# Mach messages: clock

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/clock.defs](../../../xnu/osfmk/mach/clock.defs#L1). Listed in the kernel kobject subsystem table, subject to the registration guards and per-slot skips. The destination's typed capability still controls admission.
Registration evidence: [`mig_e`](../../../xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 1000: clock_get_time

**Interface contract:**

> Get the clock time. Available to all.

**Mechanism:** Rejects a null clock, then calls that clock’s `c_gettime` operation. The system-clock implementation converts system nanoseconds into `mach_timespec_t`; the calendar implementation uses calendar nanoseconds instead. The destination clock object selects the time domain, rather than a caller-supplied flavor. [clock_get_time](../../../xnu/osfmk/kern/clock_oldops.c#L274-L310).

**Declarations:** [`clock_get_time`](../../../xnu/osfmk/mach/clock.defs#L57) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine clock_get_time(
  clock_serv : clock_serv_t;
 out cur_time : mach_timespec_t);
```

**Local body:** [`clock_get_time`](../../../xnu/osfmk/kern/clock_oldops.c#L274).

[Implementation excerpt](../../../xnu/osfmk/kern/clock_oldops.c#L274-L282):
<!-- source-excerpt: ../../../xnu/osfmk/kern/clock_oldops.c#L274-L282 -->
```c
clock_get_time(
	clock_t                 clock,
	mach_timespec_t *cur_time)      /* OUT */
{
	if (clock == CLOCK_NULL) {
		return KERN_INVALID_ARGUMENT;
	}
	return (*clock->cl_ops->c_gettime)(cur_time);
}
```

### 1001: clock_get_attributes

**Interface contract:**

> Get clock attributes. Available to all.

**Mechanism:** Requires a clock object and an installed `c_getattr` callback. The supplied clocks require exactly one output word. System-clock resolution and alarm-resolution flavors return a 10 ms value; the calendar clock reports the same time resolution but zero alarm resolution. Unknown flavors return `KERN_INVALID_VALUE`; a missing operation returns `KERN_FAILURE`. [clock_get_attributes](../../../xnu/osfmk/kern/clock_oldops.c#L316-L380).

**Declarations:** [`clock_get_attributes`](../../../xnu/osfmk/mach/clock.defs#L65) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine clock_get_attributes(
  clock_serv : clock_serv_t;
 in flavor : clock_flavor_t;
 out clock_attr : clock_attr_t, CountInOut);
```

**Local body:** [`clock_get_attributes`](../../../xnu/osfmk/kern/clock_oldops.c#L316).
Calls visible in this body include `c_getattr`.

[Implementation excerpt](../../../xnu/osfmk/kern/clock_oldops.c#L316-L329):
<!-- source-excerpt: ../../../xnu/osfmk/kern/clock_oldops.c#L316-L329 -->
```c
clock_get_attributes(
	clock_t                                 clock,
	clock_flavor_t                  flavor,
	clock_attr_t                    attr,           /* OUT */
	mach_msg_type_number_t  *count)         /* IN/OUT */
{
	if (clock == CLOCK_NULL) {
		return KERN_INVALID_ARGUMENT;
	}
	if (clock->cl_ops->c_getattr) {
		return clock->cl_ops->c_getattr(flavor, attr, count);
	}
	return KERN_FAILURE;
}
```

### 1002: clock_alarm

**Interface contract:**

> Setup a clock alarm. Available to all.

**Mechanism:** Only the system clock is supported. A missing reply capability fails immediately; an invalid or already-due time instead produces an immediate alarm reply and returns RPC success. Future alarms take a recycled or newly allocated record under the alarm lock, store the reply right, deadline and sequence number, then enter the ordered alarm machinery. Allocation drops and reacquires the lock. [clock_alarm](../../../xnu/osfmk/kern/clock_oldops.c#L388-L452).

**Declarations:** [`clock_alarm`](../../../xnu/osfmk/mach/clock.defs#L74) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine clock_alarm(
  clock_serv : clock_serv_t;
  alarm_type : alarm_type_t;
  alarm_time : mach_timespec_t;
                alarm_port : clock_reply_t =
   MACH_MSG_TYPE_MAKE_SEND_ONCE|polymorphic);
```

**Local body:** [`clock_alarm`](../../../xnu/osfmk/kern/clock_oldops.c#L388).
Calls visible in this body include `IP_VALID`, `check_time`, `clock_alarm_reply`, `LOCK_ALARM`, `UNLOCK_ALARM`, `zalloc_flags`, `post_alarm`.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
