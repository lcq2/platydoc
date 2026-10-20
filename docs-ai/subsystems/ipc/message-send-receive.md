# Message ownership, queueing, and receive conversion

[IPC overview](README.md) · [End-to-end message path](message-path.md) · [Port and right lifetime](ports-and-rights-lifecycle.md)

The transport is easiest to read as a succession of owners. Before copyin, the sender's IPC space and VM map own the resources named in the message. After successful copyin, a kernel message owns the transferred rights and memory objects. Queueing or direct receiver selection transfers that message onward. Receive copyout installs resources in the receiving space/map, then writes the user layout and frees the kernel message buffer. Error paths must identify which of these transitions has already happened. [`copyin contract`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L3024), [`copyout/deflate contract`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L3122).

## 1. Allocate storage before acquiring message resources

`mach_msg_trap_send()` first rejects sizes below the 24-byte user header, sizes not divisible by four, excessive message sizes, and impossible complex descriptor counts. It allocates an `ipc_kmsg` with `IPC_KMSG_ALLOC_USER`, then calls `ipc_kmsg_copyin_from_user()`. A copyin failure has already cleaned any resources it acquired, so this caller only frees the buffer. A subsequent send failure is a different ownership state: the complete message is still owned, and the trap invokes pseudo-receive to return its resources. [`mach_msg_trap_send()`](../../../xnu/osfmk/ipc/mach_msg.c#L652).

[The send helper distinguishes failed copyin from failed delivery](../../../xnu/osfmk/ipc/mach_msg.c#L718).

<!-- source-excerpt: ../../../xnu/osfmk/ipc/mach_msg.c#L718-L729 -->
```c
	mr = ipc_kmsg_copyin_from_user(kmsg, send_uctx, space, map, priority, &options);
	if (mr != MACH_MSG_SUCCESS) {
		ipc_kmsg_free(kmsg);
		return mr;
	}

	mr = ipc_kmsg_send(kmsg, options, msg_timeout);

	if (mr != MACH_MSG_SUCCESS) {
		mr |= mach_msg_receive_pseudo(kmsg, send_uctx, options, space, map);
		/* kmsg is freed */
	}
```

`struct ipc_kmsg` is a 256-byte allocation with queue linkage, voucher port, importance links, auxiliary size, priority/QoS, signature, and layout flags. It can embed up to 192 bytes of message storage, or 168 bytes of header/descriptor storage plus external-buffer pointers. These are storage thresholds, **not maximum public message sizes**: trailer reservation and worst-case descriptor/header expansion are included when choosing a layout. [`ipc_kmsg fields`](../../../xnu/osfmk/ipc/ipc_kmsg.h#L134), [`ipc_kmsg_alloc()`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L723).

| `ikm_type` | Header and kernel descriptors | Inline payload, trailer, auxiliary data |
|---|---|---|
| `IKM_TYPE_ALL_INLINED` | Embedded in `ikm_big_data` | Same embedded region |
| `IKM_TYPE_UDATA_OOL` | Embedded in `ikm_small_data` | Separate `ikm_udata` allocation |
| `IKM_TYPE_KDATA_OOL` | External linear `ikm_kdata` buffer | Same buffer; auxiliary data disallowed |
| `IKM_TYPE_ALL_OOL` | Separate typed `ikm_kdata` allocation | Separate `ikm_udata` allocation |

Here “OOL” in a layout name means external **kernel message storage**. It is independent of an OOL descriptor transferring a user memory region. `ikm_header()` and other accessors abstract the layout; walking past a header pointer to find all message data is incorrect for split messages. The original [kmsg layout guide](../../../xnu/doc/mach_ipc/kmsg.md) gives useful diagrams, while the allocator and caller determine the current behavior.

The allocator reserves `MAX_TRAILER_SIZE`, checks size arithmetic for overflow, and allows for descriptor inflation before selecting storage. Large split messages separate pointer-bearing header/descriptors from user-controlled payload bytes. The current user send call passes `IPC_KMSG_ALLOC_USER` alone; it does **not** derive `IPC_KMSG_ALLOC_LINEAR` from the call-mode options here. The allocator's older comment about kobject/SEND_ANY callers choosing its linear branch should not replace inspection of this call site. Kernel-originated callers can request other allocation flags. [`allocation flags`](../../../xnu/osfmk/ipc/ipc_kmsg.h#L239), [`user allocation call`](../../../xnu/osfmk/ipc/mach_msg.c#L704), [`layout selection`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L763).

## 2. Inflate bytes, then acquire rights and VM objects

The modern equivalent of the older conceptual “get a kmsg” step is `ipc_kmsg_get_and_inflate_from_user()`. It uses the header/count supplied in `mach_msg_send_uctx_t`, copies descriptor/body bytes from user memory, measures descriptor types and sizes, and converts them to uniform kernel layouts. Initially, cast header names are only placeholders: a pointer-sized field containing a cast name does not yet own a port. Descriptor validation also accumulates OOL allocation requirements and port-array counts for later policy checks. [`get/inflate`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L2891), [`descriptor measurement`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L2730).

`ipc_kmsg_copyin_from_user()` orders these stages deliberately: header schema validation, byte copy/inflation, full schema validation, header-right copyin, destination/reply policy, and body resource copyin. Rejecting malformed byte layouts before resource acquisition reduces the cleanup required. Policy after header copyin can inspect actual destination/reply objects rather than untrusted names. [`ipc_kmsg_copyin_from_user()`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L3055).

[Header-right acquisition precedes object-dependent policy](../../../xnu/osfmk/ipc/ipc_kmsg.c#L3085).

<!-- source-excerpt: ../../../xnu/osfmk/ipc/ipc_kmsg.c#L3085-L3096 -->
```c
	mr = ipc_kmsg_copyin_header(kmsg, space, priority, option64p);
	if (mr != MACH_MSG_SUCCESS) {
		return mr;
	}
	options = *option64p;

	mr = ipc_validate_kmsg_header_from_user(hdr, send_uctx, options);
	if (mr != MACH_MSG_SUCCESS) {
		/* no descriptors have been copied in yet */
		ipc_kmsg_clean_header(kmsg);
		return mr;
	}
```

### Header rights: one coordinated conversion

`ipc_kmsg_copyin_header_rights()` takes the sender IPC space write lock, checks that the space is active, looks up destination/voucher/reply entries, and validates the reply disposition before committing moves. Special handling combines operations when destination and reply/voucher refer to the same entry. That matters for two moves of a right with a limited user-reference count. The destination conversion happens first; validated reply/voucher conversions are then required to succeed. Before releasing the space lock the code locks the destination and captures its notification request. [`header-right conversion`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L1875), [`combined disposition handling`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L1950).

[A header's destination becomes an actual port through ipc_right_copyin](../../../xnu/osfmk/ipc/ipc_kmsg.c#L1958).

<!-- source-excerpt: ../../../xnu/osfmk/ipc/ipc_kmsg.c#L1958-L1970 -->
```c
	dest_type = ipc_kmsg_copyin_dest_disposition(st, &dest_xtra);

	kr = ipc_right_copyin(space, st->dest_name, dest_type,
	    IPC_OBJECT_COPYIN_FLAGS_ALLOW_IMMOVABLE_SEND |
	    dest_xtra, IPC_COPYIN_KMSG_DESTINATION, dest_entry,
	    &st->dest_port, &st->dest_cleanup, NULL);
	if (kr == KERN_SUCCESS) {
		assert(IP_VALID(st->dest_port));
		assert(!IP_VALID(st->dest_cleanup.icc_release_port));
	} else {
		ipc_space_unlock(space);
		return MACH_SEND_INVALID_DEST;
	}
```

`ipc_kmsg_copyin_header()` normalizes dispositions, stores the voucher port in `ikm_voucher_port`, applies destination-dependent state such as send-possible handling, and replaces remote/local names with owned port pointers. It initializes the sender trailer and message signature. The atomicity promised by this function is **header-right conversion**, not an all-or-nothing transaction spanning every descriptor and eventual delivery. A later policy/body failure cleans acquired resources; it does not restore every moved right or deallocated region to its original sender state. [`header conversion contract`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L2020), [`header completion`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L2044).

### Body rights and OOL data

For a port descriptor, `ipc_kmsg_copyin_port_descriptor()` calls `ipc_object_copyin()` with the user's disposition, replaces the name with a port pointer, and records the normalized right type. A transferred receive right also triggers a circularity check against the message destination. That can mark the message circular; the send path destroys a circular message and reports success instead of creating a self-retaining queue cycle. Detailed receive-right transit and reference accounting are in [port lifetime](ports-and-rights-lifecycle.md). [`port descriptor copyin`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L2197), [`circular-message send handling`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L5156).

For an OOL memory descriptor, the address becomes a `vm_map_copy_t`. Large `MACH_MSG_PHYSICAL_COPY` requests that keep the sender mapping first copy bytes into reserved pageable `ipc_kernel_copy_map` space, zero the unused page tail, and obtain a map-copy object from that space. Other cases call `vm_map_copyin()` on the sender's map, passing the descriptor's `deallocate` flag. Small regions can use physical copy; larger ones can use virtual-copy machinery. OOL therefore describes an ABI representation, not a guarantee of zero copying. [`OOL conversion`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L2291), [VM map-copy guide](../vm/README.md).

[The ordinary OOL conversion delegates to the sender VM map](../../../xnu/osfmk/ipc/ipc_kmsg.c#L2346).

<!-- source-excerpt: ../../../xnu/osfmk/ipc/ipc_kmsg.c#L2346-L2358 -->
```c
		switch (vm_map_copyin(map, dsc->u_address, length,
		    dsc->deallocate, &copy)) {
		case KERN_SUCCESS:
			break;
		case KERN_RESOURCE_SHORTAGE:
			return MACH_MSG_VM_KERNEL;
		default:
			return MACH_SEND_INVALID_MEMORY;
		}
	}

	dsc->address = copy;
	return MACH_MSG_SUCCESS;
```

OOL port arrays have two independent resources: the memory containing the input names and the rights those names denote. The converter copies names into a kernel allocation, optionally deallocates the user name-array memory, then converts each name. On failure it destroys the rights already acquired in that array and frees the array. Applicable enhanced policies also restrict array dispositions/counts and destinations. A guarded descriptor has its own receive-right guard/context rules. These types are not implemented by treating arbitrary pointer arrays as transferable kernel pointers. [`OOL port-array conversion`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L2408), [`guarded descriptor inflation`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L2502).

`ipc_kmsg_copyin_body()` tracks the prefix of successfully converted descriptors. If descriptor N fails, the converter for N handles its own partial acquisition; the enclosing loop destroys the header and descriptors 0 through N−1 and frees any unused reserved copy-map space. `ipc_kmsg_clean_descriptors()` switches on type: destroy port rights, discard `vm_map_copy_t`, or destroy an array's rights and free its storage. This is why calling `ipc_kmsg_free()` on a resource-owning message would be insufficient. [`body conversion`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L2801), [`descriptor cleanup`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L1094).

[Cleanup is bounded by the successfully converted descriptor prefix](../../../xnu/osfmk/ipc/ipc_kmsg.c#L2859).

<!-- source-excerpt: ../../../xnu/osfmk/ipc/ipc_kmsg.c#L2859-L2868 -->
```c
		if (MACH_MSG_SUCCESS != mr) {
			/* clean from start of message descriptors to copied_in_dscs */
			ipc_kmsg_clean_header(kmsg);
			ipc_kmsg_clean_descriptors(kbase->msgb_dsc_array,
			    copied_in_dscs);
			if (psize) {
				kmem_free(ipc_kernel_copy_map, paddr, psize);
			}
			return mr;
		}
```

## 3. Check the destination and choose dispatch or queueing

The modern option preflight requires exactly one supported call-mode bit for a send: queue, kobject, DriverKit, or the allowed compatibility mode. Vector sends are limited to queue/compatibility modes. After header conversion, `ipc_validate_kmsg_dest_from_user()` compares the call mode with the destination's actual type. Normal message queues require MQ mode; ordinary kobjects require KOBJECT mode; `IKOT_UEXT_OBJECT` requires DK mode. Additional platform/compatibility branches and send-only kobject restrictions are explicit in the source. These bits declare an intended route; they do not themselves grant access to an otherwise inaccessible port. [`option preflight`](../../../xnu/osfmk/ipc/ipc_policy.c#L237), [`destination policy`](../../../xnu/osfmk/ipc/ipc_policy.c#L787), [policy guide](policies-and-attribution.md).

`ipc_kmsg_send()` then performs voucher preprocessing, locks the destination, checks strict reply context when required, and verifies liveness. A destination in `ipc_space_kernel` is sent directly to `ipc_kobject_server()` with the lock released. That function consumes the request and may return a reply kmsg, which the send path then handles as a new message to the reply destination. Normal destinations proceed to `ipc_mqueue_send_locked()`. No destination port lock is held across the actual kernel RPC implementation. [`send dispatch`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L5129), [kernel RPC ownership](kernel-rpc-and-exceptions.md).

A port dying after copyin is deliberately modeled as a successful send followed by immediate message destruction. The same treatment applies when the port dies while a sender is waiting for queue capacity. This differs from a destination that was invalid during initial name lookup, which returns a send error. A failed kernel-generated reply is also destroyed rather than pseudo-received into the original request buffer. [`dead destination branch`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L5194), [`post-wait and kernel-reply errors`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L5312).

## 4. Reserve capacity, then post the message

The port embeds both `ip_waitq` and `ip_messages`. `ipc_mqueue` holds the kmsg list, sequence number, receiver name, count, limit, and a union used for knotes/priority-inheritance state. It has no separate embedded wait queue in this checkout. Port message-queue locking uses the port's lock; the receive wait queue is part of that same object. [`ipc_port`](../../../xnu/osfmk/ipc/ipc_port.h#L119), [`ipc_mqueue`](../../../xnu/osfmk/ipc/ipc_mqueue.h#L83), [`lock aliases`](../../../xnu/osfmk/ipc/ipc_port.h#L296).

`ipc_mqueue_send_locked()` starts with the port locked. If below the normal limit, it increments `imq_msgcount` and unlocks before posting. Send-once and internal `MACH_SEND_ALWAYS` sends can exceed the ordinary limit only while below the kernel ceiling. With a full queue, a send timeout of zero returns `MACH_SEND_TIMED_OUT`; the hard kernel ceiling can return `MACH_SEND_NO_BUFFER`. [`queue admission`](../../../xnu/osfmk/ipc/ipc_mqueue.c#L432).

[Capacity is reserved before ipc_mqueue_post runs](../../../xnu/osfmk/ipc/ipc_mqueue.c#L447).

<!-- source-excerpt: ../../../xnu/osfmk/ipc/ipc_mqueue.c#L447-L455 -->
```c
	if (!imq_full(mqueue) ||
	    (!imq_full_kernel(mqueue) &&
	    ((option & MACH_SEND_ALWAYS) ||
	    (MACH_MSGH_BITS_REMOTE(ikm_header(kmsg)->msgh_bits) ==
	    MACH_MSG_TYPE_PORT_SEND_ONCE)))) {
		mqueue->imq_msgcount++;
		assert(mqueue->imq_msgcount > 0);
		ip_mq_unlock(port);
	} else {
```

A sender that must wait prepares the port's send turnstile, updates its inheritor, asserts an abort-safe `IPC_MQUEUE_FULL` wait with an optional deadline, unlocks the port, completes inheritance propagation, and blocks. After wake it completes the turnstile association under the port lock, then performs cleanup after unlocking. The wake result maps to success, timeout, interruption, or destination change. See [runtime waits and turnstiles](../runtime/README.md) for scheduler mechanics beneath this IPC-specific protocol. [`send wait`](../../../xnu/osfmk/ipc/ipc_mqueue.c#L479).

When receive releases capacity, `ipc_mqueue_release_msgcount()` decrements the count and may wake the highest-priority blocked sender. A successful wake increments the count again to reserve that slot for the chosen sender. Thus `imq_msgcount` can include a message that is not yet in `imq_messages`; it is an admission/reservation count, not a list-length measurement. [`capacity release`](../../../xnu/osfmk/ipc/ipc_mqueue.c#L587).

[A woken sender inherits the released slot](../../../xnu/osfmk/ipc/ipc_mqueue.c#L612).

<!-- source-excerpt: ../../../xnu/osfmk/ipc/ipc_mqueue.c#L612-L620 -->
```c
		if (waitq_wakeup64_one(&send_turnstile->ts_waitq,
		    IPC_MQUEUE_FULL,
		    THREAD_AWAKENED,
		    WAITQ_PROMOTE_PRIORITY) != KERN_SUCCESS) {
			port->ip_fullwaiters = false;
		} else {
			/* gave away our slot - add reference back */
			port_mq->imq_msgcount++;
		}
```

### Direct delivery and queued delivery

`ipc_mqueue_post()` re-locks the port and calls `waitq_wakeup64_identify_locked()`. Identification removes an eligible waiter from the wait machinery while holding it off the run queue, allowing IPC to fill its receive state safely. A waiter from another facility, without `MACH_RCV_IN_PROGRESS`, is awakened but is not handed the kmsg. For a Mach receiver, posting checks message size, requested trailer size, and auxiliary capacity against that receiver's map/buffers. [`posting and identification`](../../../xnu/osfmk/ipc/ipc_mqueue.c#L640).

When the receiver accepts the message, the sender writes `ith_kmsg`, assigns a sequence number, resumes the receiver, and releases the queue reservation. The message never needs to join the port's list in this case. This is **direct kmsg delivery**. It is not a direct copy into the receiver's user buffer, and the `WAITQ_WAKEUP_DEFAULT` flag is not an explicit CPU/scheduler handoff request. Receiver copyout runs when the receiver resumes. [`direct-delivery branch`](../../../xnu/osfmk/ipc/ipc_mqueue.c#L751).

[Direct delivery gives a kernel message to a waiting thread](../../../xnu/osfmk/ipc/ipc_mqueue.c#L751).

<!-- source-excerpt: ../../../xnu/osfmk/ipc/ipc_mqueue.c#L751-L762 -->
```c
		if ((receiver->ith_state == MACH_MSG_SUCCESS) ||
		    !(receiver->ith_option & MACH_RCV_LARGE)) {
			receiver->ith_kmsg = kmsg;
			receiver->ith_seqno = mqueue->imq_seqno++;

			waitq_resume_identified_thread(waitq, receiver,
			    THREAD_AWAKENED, WAITQ_WAKEUP_DEFAULT);

			/* we didn't need our reserved spot in the queue */
			ipc_mqueue_release_msgcount(mqueue);
			break;
		}
```

If no eligible receiver takes it, the kmsg enters `imq_messages` via `ipc_kmsg_enqueue_qos()`. The port's kqueue list is notified for a newly nonempty queue or relevant QoS change when permitted; port-set notification is handled through wait-queue propagation. A receiver with `MACH_RCV_LARGE` and too small a buffer can be awakened with sizing information while posting continues looking for another receiver. Preserving the message does not reserve it for that particular thread's retry. [`queue/knote branch`](../../../xnu/osfmk/ipc/ipc_mqueue.c#L673), [`too-large direct-delivery branch`](../../../xnu/osfmk/ipc/ipc_mqueue.c#L764).

## 5. Receive from a port or a set of ports

`mach_msg_trap_receive()` resolves the receive name using `ipc_mqueue_copyin()`. It accepts a receive right or a port-set right, takes an object reference, and releases the lookup lock. That reference keeps the object storage alive across waiting; it does not promise the right remains in the same task or the port remains active. For synchronous special-reply waits it also establishes the permitted reply-port/destination link. [`receive setup`](../../../xnu/osfmk/ipc/mach_msg.c#L745), [`receive-name conversion`](../../../xnu/osfmk/ipc/ipc_mqueue.c#L1367).

The trap stores `ith_recv_bufs`, `ith_object`, `ith_option`, and other receive state on the current thread. `ipc_mqueue_receive()` locks the object's wait queue and asks `ipc_mqueue_receive_on_thread_and_unlock()` to select a message or register a wait. For a direct port, it inspects that port's list. For a port set, it asks the set's **prepost list** for a member already indicating queued data, retains that member's port lock, drops the set lock, and selects from the member's queue. The set is a wait/readiness grouping, not one central list into which all member messages move. [`receive selection`](../../../xnu/osfmk/ipc/ipc_mqueue.c#L917).

[A port-set receive starts by locating a ready member wait queue](../../../xnu/osfmk/ipc/ipc_mqueue.c#L931).

<!-- source-excerpt: ../../../xnu/osfmk/ipc/ipc_mqueue.c#L931-L942 -->
```c
	if (waitq_type(waitq) == WQT_PORT_SET) {
		ipc_pset_t pset = ips_from_waitq(waitq);
		wqs_prepost_flags_t wqs_flags = WQS_PREPOST_LOCK;
		struct waitq *port_wq;

		/*
		 * Put the message at the back of the prepost list
		 * if it's not a PEEK.
		 *
		 * Might drop the pset lock temporarily.
		 */
		port_wq = waitq_set_first_prepost(&pset->ips_wqset, wqs_flags);
```

Adding a port to a set also handles the existing-data race: `ipc_mqueue_add_locked()` links wait queues, matches already queued messages to set waiters, or preposts the set when queued data remains without a waiter. Removing the final queued message clears the port's prepost state. These operations prevent a receiver from sleeping indefinitely merely because readiness existed before it joined the wait structure. [`set insertion`](../../../xnu/osfmk/ipc/ipc_mqueue.c#L208), [`empty-queue prepost clearing`](../../../xnu/osfmk/ipc/ipc_mqueue.c#L623).

With no message ready, zero-timeout receive returns immediately. Otherwise the code records `MACH_RCV_IN_PROGRESS`, computes the deadline, prepares a receive turnstile for direct-port waits, and asserts `IPC_MQUEUE_RECEIVE` while retaining the interlock. Only afterward does it unlock. Another thread may then own and modify the sleeping receiver's `ith_*` fields until it resumes. This is the critical wait-registration ordering: the same protected state is used to check for work and to make the waiter visible. [`wait registration`](../../../xnu/osfmk/ipc/ipc_mqueue.c#L990), [`ith ownership comment`](../../../xnu/osfmk/ipc/ipc_mqueue.c#L1059).

The userspace trap uses a continuation when blocking: `thread_block(ipc_mqueue_receive_continue)`. That continuation translates the wait result into `ith_state` and proceeds to `mach_msg_receive_continue()` and result copyout. A thread awakened for delivery does not reselect an arbitrary message; the posting side has already supplied its kmsg or its too-large indication. [`blocking/continuation`](../../../xnu/osfmk/ipc/ipc_mqueue.c#L845), [`wake-result conversion`](../../../xnu/osfmk/ipc/ipc_mqueue.c#L792).

## 6. Convert the selected message into the receiver's namespace

Queued selection computes the user-layout size for the receiver's map, includes its requested trailer, and checks auxiliary space. With `MACH_RCV_LARGE`, an oversized message remains queued and only size/receiver-name information is recorded. Without it, selection removes the message even though the result is `MACH_RCV_TOO_LARGE`; the later error path consumes its resources. Successful selection removes the kmsg, releases/reserves capacity for another sender, and captures the port sequence number. [`queued selection`](../../../xnu/osfmk/ipc/ipc_mqueue.c#L1090).

`mach_msg_receive_results()` immediately snapshots the thread's object, status, options, kmsg, and buffers. Copy operations can fault and cause nested kernel IPC, reusing those per-thread scratch fields. It completes special-reply and receive-turnstile cleanup before releasing the held receive object reference. On success it adopts importance/voucher state, saves destination context, and calls `ipc_kmsg_copyout()`. [`receive results`](../../../xnu/osfmk/ipc/mach_msg.c#L279).

[Receive results save thread scratch before potentially faulting operations](../../../xnu/osfmk/ipc/mach_msg.c#L286).

<!-- source-excerpt: ../../../xnu/osfmk/ipc/mach_msg.c#L286-L300 -->
```c
	/*
	 * /!\IMPORTANT/!\: Pull out values we stashed on thread struct now.
	 * Values may be stomped over if copyio operations in this function
	 * trigger kernel IPC calls.
	 */
	ipc_object_t            object  = self->ith_object;
	mach_msg_return_t       mr      = self->ith_state;
	mach_msg_option64_t     options = self->ith_option;
	ipc_kmsg_t              kmsg    = self->ith_kmsg;

	mach_msg_recv_bufs_t recv_bufs = self->ith_recv_bufs;
	mach_msg_recv_result_t msgr = {
		.msgr_seqno     = self->ith_seqno,
		.msgr_context   = 0,
	};
```

`ipc_kmsg_copyout_header()` reserves space entries that might be needed for reply/voucher rights, grows the table if necessary, and checks object labels/liveness while locking the relevant ports. A send right may merge with an existing name via reverse lookup; send-once rights receive a distinct entry. The destination right is consumed as a delivered-to capability and its receive name is reported in the local field. If that receive right moved away before copyout, the reported destination can be `MACH_PORT_NULL`; if it died, `MACH_PORT_DEAD`, with timestamp checks preserving header-copyout ordering relative to reply-port death. [`header copyout`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L3253), [`destination-name rules`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L3518).

Descriptor copyout then installs carried rights and memory in the receiving task. Port copyout consumes its supplied right even on a failed translation, returning a null/dead name as appropriate. OOL memory copyout validates size and maps the copy with `vm_map_copyout_size()`, or allocates aligned space and uses `vm_map_copy_overwrite()` when needed to preserve the source offset. Failed OOL copyout discards the VM copy and zeroes the returned address/size. The body walker continues after descriptor errors and accumulates `MACH_RCV_BODY_ERROR` plus IPC/VM shortage bits; it does not undo already copied-out descriptors. [`port-copyout contract`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L3629), [`OOL copyout`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L3788), [`body copyout`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L4099).

Only after resource conversion does `ipc_kmsg_put_to_user()` deflate descriptors/header into 32- or 64-bit user layouts, finalize the trailer, and copy bytes to user addresses. Deflation contracts the header/descriptor region while leaving data/trailer positions usable; split messages can require two byte copies. Most `ipc_kmsg` accessors become invalid after this mutation. The remaining operations are byte copyout and `ipc_kmsg_free()`. A byte-copy fault can return `MACH_RCV_INVALID_DATA` after rights or VM mappings have already been installed; receive copyout is not an all-or-nothing write into one buffer. [`deflate contract`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L3147), [`put-to-user`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L4740).

## 7. Errors tell you which resources moved

| Stage/result | Message/resource consequence | Relevant implementation |
|---|---|---|
| Malformed schema, bad initial destination/reply | No complete owned kmsg reaches the queue; header conversion has its own atomic validation contract. | [`copyin sequence`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L3055) |
| Later copyin policy/body failure | Acquired header rights and converted descriptors are destroyed; caller frees storage. Some sender moves/deallocations may already have occurred. | [`body failure cleanup`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L2859) |
| Send queue timeout/interruption after complete copyin | Sender still owns an unsent kmsg; pseudo-copyout attempts to restore resources in sender space/map. | [`trap send failure`](../../../xnu/osfmk/ipc/mach_msg.c#L724) |
| Destination dies after copyin/during wait | Kmsg destroyed; send reports success, equivalent to delivery followed by destruction. | [`send race handling`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L5194) |
| Receive timeout/interruption | No message selected for this receive; any preceding successful send remains effective. | [`wait results`](../../../xnu/osfmk/ipc/ipc_mqueue.c#L792) |
| Receive object changes/dies while waiting | Wait restart becomes `MACH_RCV_PORT_CHANGED` in this generic mqueue receive path. | [`restart mapping`](../../../xnu/osfmk/ipc/ipc_mqueue.c#L810) |
| `MACH_RCV_TOO_LARGE` with `MACH_RCV_LARGE` | Keep message available; report needed message size and optional receiver identity/auxiliary size. | [`size reporting`](../../../xnu/osfmk/ipc/mach_msg.c#L150) |
| Too large without `MACH_RCV_LARGE` | Consume message; copy destination into a minimal header/trailer and destroy its other rights/memory. | [`receive error`](../../../xnu/osfmk/ipc/mach_msg.c#L229) |
| Header copyout error | Rights/body are still intact for the receive-error cleanup path. | [`copyout contract`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L4227) |
| Body copyout error | Header and some resources have been copied out; return the partially converted message with error bits. | [`receive-result error branches`](../../../xnu/osfmk/ipc/mach_msg.c#L360) |
| Final user-buffer write fails | Kmsg storage is freed; resources already installed are not collectively rolled back. | [`put completion`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L4859) |

### Pseudo-receive is compensation, not ordinary receive

`mach_msg_receive_pseudo()` uses the original send buffers as copyout destinations. `ipc_kmsg_copyout_pseudo()` handles both header ports like body-carried rights; destination and reply fields **are not swapped**. It can allocate new names or remap OOL memory, so restoring resources need not restore the original byte values/addresses. It proceeds despite individual failures and returns additional IPC/VM failure bits, which the send helper ORs into the original send error. [`pseudo-receive wrapper`](../../../xnu/osfmk/ipc/mach_msg.c#L612), [`pseudo-copyout`](../../../xnu/osfmk/ipc/ipc_kmsg.c#L4293).

[Pseudo-copyout preserves the send-side header roles](../../../xnu/osfmk/ipc/ipc_kmsg.c#L4345).

<!-- source-excerpt: ../../../xnu/osfmk/ipc/ipc_kmsg.c#L4345-L4347 -->
```c
	hdr->msgh_bits = mbits & MACH_MSGH_BITS_USER;
	hdr->msgh_remote_port = CAST_MACH_NAME_TO_PORT(dest_name);
	hdr->msgh_local_port = CAST_MACH_NAME_TO_PORT(reply_name);
```

This distinction also matters for cleanup libraries: normal `mach_msg_destroy()` does not destroy the received header's local name because delivery has already consumed the destination right. Code handling an unsent message must use the appropriate send-error ownership rules, not assume it is an ordinary received request. The server helpers have dedicated recoverable-send-error handling for this reason. [`mach_msg_destroy()`](../../../xnu/libsyscall/mach/mach_msg.c#L392), [`server send-error handling`](../../../xnu/libsyscall/mach/mach_msg.c#L531).

### Library interruption handling must not resend a completed request

Unless the caller asks to observe send interruptions, `mach_msg2_internal()` retries `MACH_SEND_INTERRUPTED` with the original send arguments. Unless it asks to observe receive interruptions, the library retries `MACH_RCV_INTERRUPTED` with send disabled and send size zero. `mach_msg_options_after_interruption()` also clears synchronous-receive linkage for a combined call's receive-only retry, because that retry no longer identifies a just-sent destination. This preserves the crucial distinction between “the send did not finish” and “the request was sent but the receive was interrupted.” [`interruption options`](../../../xnu/libsyscall/mach/mach_msg.c#L76), [`retry implementation`](../../../xnu/libsyscall/mach/mach_msg.c#L120).

[A receive-interruption retry does not resend the request](../../../xnu/libsyscall/mach/mach_msg.c#L133).

<!-- source-excerpt: ../../../xnu/libsyscall/mach/mach_msg.c#L133-L144 -->
```c
	if ((option64 & MACH64_RCV_INTERRUPT) == 0) {
		while (mr == MACH_RCV_INTERRUPTED) {
			mr = mach_msg2_trap(data,
			    mach_msg_options_after_interruption(option64),
			    msgh_bits_and_send_size & 0xffffffffull, /* zero send size */
			    msgh_remote_and_local_port,
			    msgh_voucher_and_id,
			    desc_count_and_rcv_name,
			    rcv_size_and_priority,
			    timeout);
		}
	}
```

## Source route and limits

For a line-by-line pass, follow `mach_msg_trap_send()` → `ipc_kmsg_copyin_from_user()` → header/body converters → `ipc_kmsg_send()` → `ipc_mqueue_send_locked()` → `ipc_mqueue_post()`. Then switch threads: `mach_msg_trap_receive()` → `ipc_mqueue_receive_on_thread_and_unlock()` → selection or continuation → `mach_msg_receive_results()` → `ipc_kmsg_copyout()` → `ipc_kmsg_put_to_user()`.

The concrete functions above were read through their principal success, blocking, and failure branches. Descriptor inflation/deflation, OOL ports, guarded ports, trailer layouts, queue-set membership, and destination policy were read at the corresponding boundaries. This is not a full proof of every waitq, scheduler, VM-copy, importance, voucher, or security-policy invariant. Their implementations span [runtime](../runtime/README.md), [VM](../vm/README.md), [port lifetime](ports-and-rights-lifecycle.md), and [policy/attribution](policies-and-attribution.md). Kernel-originated RPC, generated MIG handlers, and Mach exception replies continue in [kernel RPC and exceptions](kernel-rpc-and-exceptions.md).
