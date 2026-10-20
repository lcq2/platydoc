# Mach messages: mach_exc

[Message catalog and dispatch](README.md) · [All subsystem ranges](subsystems.md) · [Kernel entry map](../README.md)

[osfmk/mach/mach_exc.defs](../../../xnu/osfmk/mach/mach_exc.defs#L1). Listed in the kernel kobject subsystem table, subject to the registration guards and per-slot skips. The destination's typed capability still controls admission.
Registration evidence: [`mig_e`](../../../xnu/osfmk/kern/ipc_kobject.c#L171-L197).

## Reading these entries

IDs are computed from the explicit preprocessing profiles in the catalog guide, counting both routines and `skip` slots. They are not discovered from a running kernel. Each entry retains all observed names/declaration locations; the displayed fields come from the first non-skipped profile. Alternative declarations can have different fields. `simpleroutine` is one-way at the MIG interface level.

An **interface contract** block quotes the adjacent local `.defs` comment with whitespace normalized. **Mechanism** paragraphs explain selected implementation decisions. **Local body** links and call names identify implementation evidence; syntactic call lists are reading aids, not a proof that every listed call executes on every path. Short complete implementation bodies are included where especially useful.

## Complete routine and reserved-slot catalog

### 2405: mach_exception_raise

Deliver a Mach exception with wide exception-code elements and thread/task rights.

**Mechanism:** For default exception behavior, XNU exports control ports in developer mode or for a corpse, otherwise read ports, and sends the wide exception codes. The local Unix receiver verifies its destination, converts the thread port to a read reference and calls `handle_ux_exception`; it consumes the supplied task/thread send rights only on success and always drops the converted thread reference. [Local path](../../../xnu/osfmk/kern/ux_handler.c#L130).

**Declarations:** [`mach_exception_raise`](../../../xnu/osfmk/mach/mach_exc.defs#L80) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_exception_raise(
   exception_port : mach_port_t;
   thread : mach_port_t;
   task : mach_port_t;
   exception : exception_type_t;
   code : mach_exception_data_t
   );
```

**Local body:** [`catch_mach_exception_raise`](../../../xnu/osfmk/kern/ux_handler.c#L130).
Calls visible in this body include `convert_port_to_thread_read`, `handle_ux_exception`, `ipc_port_release_send`, `thread_deallocate`.

### 2406: mach_exception_raise_state

Deliver wide exception codes and thread-state data, accepting replacement state in the reply.

**Mechanism:** The `EXCEPTION_STATE` sender obtains architecture state with `thread_getstatus_to_user`, allocates reply-state storage and sends wide exception codes with a flavor/count. A successful reply is validated through `thread_setstatus_from_user`, except for corpse notification. The local Unix receiver for this state-only form returns `KERN_INVALID_ARGUMENT`; a user exception server supplies the useful receiver. [Local path](../../../xnu/osfmk/kern/exception.c#L298).

**Declarations:** [`mach_exception_raise_state`](../../../xnu/osfmk/mach/mach_exc.defs#L100) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_exception_raise_state(
   exception_port : mach_port_t;
   exception : exception_type_t;
   code : mach_exception_data_t, const;
    inout flavor : int;
   old_state : thread_state_t, const;
      out new_state : thread_state_t
   );
```

**Local body:** [`catch_mach_exception_raise_state`](../../../xnu/osfmk/kern/ux_handler.c#L214).

[Implementation excerpt](../../../xnu/osfmk/kern/ux_handler.c#L214-L226):
<!-- source-excerpt: ../../../xnu/osfmk/kern/ux_handler.c#L214-L226 -->
```c
catch_mach_exception_raise_state(
	__unused mach_port_t                    exception_port,
	__unused exception_type_t               exception,
	__unused const mach_exception_data_t    code,
	__unused mach_msg_type_number_t         codeCnt,
	__unused int                           *flavor,
	__unused const thread_state_t           old_state,
	__unused mach_msg_type_number_t         old_stateCnt,
	__unused thread_state_t                 new_state,
	__unused mach_msg_type_number_t        *new_stateCnt)
{
	return KERN_INVALID_ARGUMENT;
}
```

### 2407: mach_exception_raise_state_identity

Deliver wide exception codes, thread/task rights and state, accepting replacement state in the reply.

**Mechanism:** The state-and-identity sender exports policy-selected task/thread capabilities as well as old thread state, flavor and wide codes. A successful reply is imported through architecture/state validation only when the exception is not `EXC_CORPSE_NOTIFY` and the exported thread port is `IKOT_THREAD_CONTROL`; the read-port delivery branch does not import returned state. The in-kernel Unix handler is an invalid-argument stub for this behavior; its presence in the generated exception subsystem does not mean it implements state editing. [Local path](../../../xnu/osfmk/kern/exception.c#L503-L579).

**Declarations:** [`mach_exception_raise_state_identity`](../../../xnu/osfmk/mach/mach_exc.defs#L121) (`server64`, `server32`, `client64`, `client32`, `libsyscall64`, `sender64`, `local64`).

**Fields after preprocessing (`server64`):**

```text
routine mach_exception_raise_state_identity(
   exception_port : mach_port_t;
   thread : mach_port_t;
   task : mach_port_t;
   exception : exception_type_t;
   code : mach_exception_data_t;
    inout flavor : int;
   old_state : thread_state_t;
      out new_state : thread_state_t
   );
```

**Local body:** [`catch_mach_exception_raise_state_identity`](../../../xnu/osfmk/kern/ux_handler.c#L246).

[Implementation excerpt](../../../xnu/osfmk/kern/ux_handler.c#L246-L260):
<!-- source-excerpt: ../../../xnu/osfmk/kern/ux_handler.c#L246-L260 -->
```c
catch_mach_exception_raise_state_identity(
	__unused mach_port_t                   exception_port,
	__unused mach_port_t                   thread,
	__unused mach_port_t                   task,
	__unused exception_type_t              exception,
	__unused mach_exception_data_t         code,
	__unused mach_msg_type_number_t        codeCnt,
	__unused int                          *flavor,
	__unused thread_state_t                old_state,
	__unused mach_msg_type_number_t        old_stateCnt,
	__unused thread_state_t                new_state,
	__unused mach_msg_type_number_t       *new_stateCnt)
{
	return KERN_INVALID_ARGUMENT;
}
```

### 2408: mach_exception_raise_identity_protected

Deliver an exception using a task identity token and thread identifier instead of exposing ordinary control rights.

**Mechanism:** Creates a task identity token and sends its port plus numeric thread ID instead of exporting task/thread control ports. This behavior requires wide exception codes. A task becoming inactive during identity-token creation is treated specially. The local Unix receiver returns invalid argument; registered external exception servers can implement this protocol. [Local path](../../../xnu/osfmk/kern/exception.c#L398).

**Declarations:** [`mach_exception_raise_identity_protected`](../../../xnu/osfmk/mach/mach_exc.defs#L145) (`server64`, `server32`, `sender64`, `local64`).
**Reserved instead in:** `client64`, `client32`, `libsyscall64`.

**Fields after preprocessing (`server64`):**

```text
routine mach_exception_raise_identity_protected(
   exception_port : mach_port_t;
   thread_id : uint64_t;
   task_id_token_t : mach_port_t;
   exception : exception_type_t;
   code : mach_exception_data_t
   );
```

**Local body:** [`catch_mach_exception_raise_identity_protected`](../../../xnu/osfmk/kern/ux_handler.c#L263).

[Implementation excerpt](../../../xnu/osfmk/kern/ux_handler.c#L263-L272):
<!-- source-excerpt: ../../../xnu/osfmk/kern/ux_handler.c#L263-L272 -->
```c
catch_mach_exception_raise_identity_protected(
	__unused mach_port_t               exception_port,
	__unused uint64_t                  thread_id,
	__unused mach_port_t               task_id_token,
	__unused exception_type_t          exception,
	__unused mach_exception_data_t     code,
	__unused mach_msg_type_number_t    codeCnt)
{
	return KERN_INVALID_ARGUMENT;
}
```

### 2409: mach_exception_raise_backtrace

**Interface contract:**

> MACH_EXC_SERVER_TASKIDTOKEN

**Mechanism:** Sends an `EXC_CORPSE_NOTIFY` message containing a kcdata/backtrace-object port to eligible live exception endpoints. The sender tries its candidate ports and stops on success or receive-port death. The local Unix receiver returns invalid argument; interpretation of the diagnostic object by another receiver is outside that body. [Local path](../../../xnu/osfmk/kern/exception.c#L646).

**Declarations:** [`mach_exception_raise_backtrace`](../../../xnu/osfmk/mach/mach_exc.defs#L169) (`server64`, `server32`, `sender64`, `local64`).
**Reserved instead in:** `client64`, `client32`, `libsyscall64`.

**Fields after preprocessing (`server64`):**

```text
routine mach_exception_raise_backtrace(
   exception_port : mach_port_t;
   kcdata_object_t : mach_port_t;
   exception : exception_type_t;
   code : mach_exception_data_t
   );
```

**Local body:** [`catch_mach_exception_raise_backtrace`](../../../xnu/osfmk/kern/ux_handler.c#L275).

[Implementation excerpt](../../../xnu/osfmk/kern/ux_handler.c#L275-L283):
<!-- source-excerpt: ../../../xnu/osfmk/kern/ux_handler.c#L275-L283 -->
```c
catch_mach_exception_raise_backtrace(
	__unused mach_port_t               exception_port,
	__unused mach_port_t               kcdata_object,
	__unused exception_type_t          exception,
	__unused mach_exception_data_t     code,
	__unused mach_msg_type_number_t    codeCnt)
{
	return KERN_INVALID_ARGUMENT;
}
```

### 2410: mach_exception_raise_state_identity_protected

**Interface contract:**

> Same as identity_protected above, but also handles an in/out thread_state_t.

**Mechanism:** Combines a task identity token and thread ID with exported architecture state. Pointer-authentication policy affects state-export/import flags; a successful reply goes through `thread_setstatus_from_user` unless it is corpse notification. The local Unix receiver is an invalid-argument stub, so the implemented sender and a capable external receiver are distinct. [Local path](../../../xnu/osfmk/kern/exception.c#L432).

**Declarations:** [`mach_exception_raise_state_identity_protected`](../../../xnu/osfmk/mach/mach_exc.defs#L195) (`server64`, `server32`, `sender64`, `local64`).
**Reserved instead in:** `client64`, `client32`, `libsyscall64`.

**Fields after preprocessing (`server64`):**

```text
routine mach_exception_raise_state_identity_protected(
   exception_port : mach_port_t;
   thread_id : uint64_t;
   task_id_token_t : mach_port_t;
   exception : exception_type_t;
   code : mach_exception_data_t;
   inout flavor : int;
   old_state : thread_state_t;
      out new_state : thread_state_t
   );
```

**Local body:** [`catch_mach_exception_raise_state_identity_protected`](../../../xnu/osfmk/kern/ux_handler.c#L286).

[Implementation excerpt](../../../xnu/osfmk/kern/ux_handler.c#L286-L300):
<!-- source-excerpt: ../../../xnu/osfmk/kern/ux_handler.c#L286-L300 -->
```c
catch_mach_exception_raise_state_identity_protected(
	__unused mach_port_t               exception_port,
	__unused uint64_t                  thread_id,
	__unused mach_port_t               task_id_token,
	__unused exception_type_t          exception,
	__unused mach_exception_data_t     code,
	__unused mach_msg_type_number_t    codeCnt,
	__unused int                      *flavor,
	__unused thread_state_t            old_state,
	__unused mach_msg_type_number_t    old_stateCnt,
	__unused thread_state_t            new_state,
	__unused mach_msg_type_number_t   *new_stateCnt)
{
	return KERN_INVALID_ARGUMENT;
}
```

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
