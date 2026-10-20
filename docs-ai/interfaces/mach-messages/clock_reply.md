# Mach messages: clock_reply

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/clock_reply.defs](../../../xnu/osfmk/mach/clock_reply.defs#L1). Service/callback interface outside the ordinary kernel kobject table. Follow local sender/receiver evidence; external service bodies are not supplied by the declaration.
Registration evidence: [`mig_e`](../../../xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 3125107: clock_alarm_reply

**Interface contract:**

> Reply routine for clock_alarm.

**Mechanism:** Clock alarm servicing forms this one-way completion with alarm result/type/time and sends it on the supplied reply capability. Both immediate/invalid-time handling and later alarm completion have local send sites. The receiver consumes the notification; it is not a request to program the clock. [Local path](../../../xnu/osfmk/kern/clock_oldops.c#L419).

**Declarations:** [`clock_alarm_reply`](../../../xnu/osfmk/mach/clock_reply.defs#L50) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
simpleroutine clock_alarm_reply(
                alarm_port : clock_reply_t;
  alarm_code : kern_return_t;
  alarm_type : alarm_type_t;
  alarm_time : mach_timespec_t);
```

**Implementation boundary:** no same-symbol receiver body was resolved in the indexed local C/C++ implementation files.
Local source occurrences to follow: [osfmk/kern/clock_oldops.c:419](../../../xnu/osfmk/kern/clock_oldops.c#L419), [osfmk/kern/clock_oldops.c:676](../../../xnu/osfmk/kern/clock_oldops.c#L676). These may be senders, wrappers or declarations; they do not establish a local receiver.
