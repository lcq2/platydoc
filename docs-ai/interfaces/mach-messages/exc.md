# Mach messages: exc

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/exc.defs](../../../platydoc-data/xnu/osfmk/mach/exc.defs#L1). Listed in the kernel kobject subsystem table, subject to the registration guards and per-slot skips. The destination's typed capability still controls admission.
Registration evidence: [`mig_e`](../../../platydoc-data/xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 2401: exception_raise

Deliver a traditional Mach exception with thread/task rights and 32-bit exception-code elements; the receiver chooses its policy.

**Mechanism:** The sender selects this older narrow-code form for `EXCEPTION_DEFAULT` without `MACH_EXCEPTION_CODES`, exporting task/thread ports at the policy-selected flavor. The in-kernel Unix receiver first requires `ux_handler_port`, widens the two codes and delegates to `catch_mach_exception_raise`; a different registered exception server may implement its own receiver. See [exception delivery](../../subsystems/ipc/exception-delivery.md). [Local path](../../../platydoc-data/xnu/osfmk/kern/exception.c#L355).

**Declarations:** [`exception_raise`](../../../platydoc-data/xnu/osfmk/mach/exc.defs#L80) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine exception_raise(
   exception_port : mach_port_t;
   thread : mach_port_t;
   task : mach_port_t;
   exception : exception_type_t;
   code : exception_data_t
   );
```

**Local body:** [`catch_exception_raise`](../../../platydoc-data/xnu/osfmk/kern/ux_handler.c#L173).
Calls visible in this body include `catch_mach_exception_raise`.

### 2402: exception_raise_state

Deliver a traditional exception with thread-state flavor/data and accept replacement state in the reply.

**Mechanism:** The `EXCEPTION_STATE` sender obtains architecture state with `thread_getstatus_to_user`, allocates reply-state storage and sends narrow exception codes with a flavor/count. A successful reply is validated through `thread_setstatus_from_user`, except for corpse notification. The local Unix receiver for this state-only form returns `KERN_INVALID_ARGUMENT`; a user exception server supplies the useful receiver. [Local path](../../../platydoc-data/xnu/osfmk/kern/exception.c#L298).

**Declarations:** [`exception_raise_state`](../../../platydoc-data/xnu/osfmk/mach/exc.defs#L100) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine exception_raise_state(
   exception_port : mach_port_t;
   exception : exception_type_t;
   code : exception_data_t, const;
    inout flavor : int;
   old_state : thread_state_t, const;
      out new_state : thread_state_t
   );
```

**Local body:** [`catch_exception_raise_state`](../../../platydoc-data/xnu/osfmk/kern/ux_handler.c#L199).

[Implementation excerpt](../../../platydoc-data/xnu/osfmk/kern/ux_handler.c#L199-L211):
<!-- source-excerpt: ../../../platydoc-data/xnu/osfmk/kern/ux_handler.c#L199-L211 -->
```c
catch_exception_raise_state(
	__unused mach_port_t                 exception_port,
	__unused exception_type_t            exception,
	__unused const exception_data_t      code,
	__unused mach_msg_type_number_t      codeCnt,
	__unused int                        *flavor,
	__unused const thread_state_t        old_state,
	__unused mach_msg_type_number_t      old_stateCnt,
	__unused thread_state_t              new_state,
	__unused mach_msg_type_number_t     *new_stateCnt)
{
	return KERN_INVALID_ARGUMENT;
}
```

### 2403: exception_raise_state_identity

Deliver a traditional exception with both thread/task identity rights and state; accept replacement state in the reply.

**Mechanism:** The state-and-identity sender exports policy-selected task/thread capabilities as well as old thread state, flavor and narrow codes. A successful reply is imported through architecture/state validation only when the exception is not `EXC_CORPSE_NOTIFY` and the exported thread port is `IKOT_THREAD_CONTROL`; the read-port delivery branch does not import returned state. The in-kernel Unix handler is an invalid-argument stub for this behavior; its presence in the generated exception subsystem does not mean it implements state editing. [Local path](../../../platydoc-data/xnu/osfmk/kern/exception.c#L503-L579).

**Declarations:** [`exception_raise_state_identity`](../../../platydoc-data/xnu/osfmk/mach/exc.defs#L121) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine exception_raise_state_identity(
   exception_port : mach_port_t;
   thread : mach_port_t;
   task : mach_port_t;
   exception : exception_type_t;
   code : exception_data_t;
    inout flavor : int;
   old_state : thread_state_t;
      out new_state : thread_state_t
   );
```

**Local body:** [`catch_exception_raise_state_identity`](../../../platydoc-data/xnu/osfmk/kern/ux_handler.c#L229).

[Implementation excerpt](../../../platydoc-data/xnu/osfmk/kern/ux_handler.c#L229-L243):
<!-- source-excerpt: ../../../platydoc-data/xnu/osfmk/kern/ux_handler.c#L229-L243 -->
```c
catch_exception_raise_state_identity(
	__unused mach_port_t                exception_port,
	__unused mach_port_t                thread,
	__unused mach_port_t                task,
	__unused exception_type_t           exception,
	__unused exception_data_t           code,
	__unused mach_msg_type_number_t     codeCnt,
	__unused int                       *flavor,
	__unused thread_state_t             old_state,
	__unused mach_msg_type_number_t     old_stateCnt,
	__unused thread_state_t             new_state,
	__unused mach_msg_type_number_t    *new_stateCnt)
{
	return KERN_INVALID_ARGUMENT;
}
```

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
