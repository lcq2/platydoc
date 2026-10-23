# Service notifications, replay, and arbitration

A service can become visible, become matched, terminate, or send an interest message while other threads register or remove callbacks. This chapter follows the lock and ownership protocols that connect those events. [Service matching and termination](service-matching-and-termination.md) covers candidate selection and the termination phases; [registry planes](registry-planes-and-properties.md) covers graph snapshots. Here the focus is how notification registration, callback invocation, synchronous waiting, and `open/close` remain coordinated. [`notification structures`](../../../platydoc-data/xnu/iokit/Kernel/IOServicePrivate.h#L81-L139), [`registration`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L6442-L6652).

## 1. Four locks or protocols should not be conflated

| Mechanism | State it coordinates | Important distinction |
|---|---|---|
| `gNotificationLock` | Global matching-notifier sets, interest chains, enabled bits and callback invocation records | Both `LOCKREADNOTIFY` and `LOCKWRITENOTIFY` acquire the same recursive mutex |
| IOService arbitration | A particular service's serialized operations, including lifecycle and open state | Implemented with global active/waiting lock-owner queues and deadlock handling |
| Registry graph lock | Parent/child arrays and registry name/location state | A separate read/write lock |
| Entry property lock | Property dictionary lookup, replacement and snapshot creation | A separate per-entry recursive lock |

The source explicitly orders arbitration before notification locking. A callback being outside `gNotificationLock` does not establish that no other lock is held: external callers can hold arbitration, which is why the optional notifier-arbitration diagnostic is disabled. [`lock order and diagnostic`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L77-L85), [`notification macros`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L301-L313), [`registry locks`](../../../platydoc-data/xnu/iokit/Kernel/IORegistryEntry.cpp#L112-L122), [`arbitration`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L1666-L1929).

The macro names can otherwise suggest a reader/writer design that is not present: [`notification lock macros`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L301-L313).

<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L301-L313 -->
```cpp
#define LOCKREADNOTIFY()        \
    IORecursiveLockLock( gNotificationLock )
#define LOCKWRITENOTIFY()       \
    IORecursiveLockLock( gNotificationLock )
#define LOCKWRITE2READNOTIFY()
#define UNLOCKNOTIFY()          \
    IORecursiveLockUnlock( gNotificationLock )
#define SLEEPNOTIFY(event) \
    IORecursiveLockSleep( gNotificationLock, (void *)(event), THREAD_UNINT )
#define SLEEPNOTIFYTO(event, deadline) \
    IORecursiveLockSleepDeadline( gNotificationLock, (void *)(event), deadline, THREAD_UNINT )
#define WAKEUPNOTIFY(event) \
	IORecursiveLockWakeup( gNotificationLock, (void *)(event), /* wake one */ false )
```

A matching notifier contains its owning ordered-set pointer `whence`, retained matching dictionary, notification type, handler/target/refcon, priority, enabled/waiter state and a queue of active handler invocations. Each invocation record contains the executing thread and a queue link. An interest notifier has a chain link into a particular service's interest list and the same invocation/state concept. Raw `target` and general `ref` fields are not automatically retained; block-handler wrappers explicitly copy/release the block. The client must give ordinary callback context its own valid lifetime. [`structures`](../../../platydoc-data/xnu/iokit/Kernel/IOServicePrivate.h#L88-L139), [`matching setup`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L6460-L6476), [`interest setup`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L2303-L2309), [`block cleanup`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L7197-L7206).

## 2. Installing a matching notifier also captures existing services

`doInstallNotification()` accepts publish, first-publish, matched, first-match, terminated and will-terminate types. It converts the first four to their corresponding service-state masks; termination types use zero and do not replay a current set. Unknown types or a null matching dictionary fail. `setNotification()` initializes a notifier, retains the dictionary, and inserts it into the per-type ordered set in `gNotifications`, ordered using the notifier priority comparator. [`type selection`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L6499-L6539), [`installation`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L6442-L6495), [`priority comparator`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L3660-L3682).

`installNotification()` holds `gNotificationLock` while installing and obtaining the existing-service iterator, then takes an extra notifier reference before unlocking. `addMatchingNotification()` replays that iterator outside the lock, skips services already marked inactive, and invokes the same notifier callback path used for later events. The extra reference permits a callback to call `remove()` during replay. After replay the function checks `whence` under the lock, releases its extra owner, and returns the global null-notifier sentinel if the callback removed the registration. It is therefore possible to receive a callback before the add function returns. [`install extra reference`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L6567-L6588), [`replay and sentinel`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L6614-L6652).

The final replay cleanup makes the self-removal outcome explicit: [`addMatchingNotification`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L6642-L6652).

<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L6642-L6652 -->
```cpp
	LOCKWRITENOTIFY();
	bool removed = (NULL == notify->whence);
	notify->release();
	if (removed) {
		ret = gIOServiceNullNotifier;
	}
	UNLOCKNOTIFY();

	return ret;
}

```

This implementation closes the ordinary gap between checking the existing set and installing future-event interest by doing both under the notification lock. It does not make replay an immutable snapshot of each service's future activity: a retained service can become inactive after it is selected. The explicit inactive check before replay is evidence of that distinction. Nor should callback order across independently executing service threads be inferred from the ordered notifier set alone. [`installation/snapshot`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L6527-L6538), [`replay`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L6632-L6640).

Matching dictionary ownership depends on the entry point. `setNotification()` adds its own reference, and removal releases it. The compatibility `addNotification()` wrapper additionally releases the caller's matching dictionary on successful installation; the newer `addMatchingNotification()` body does not do that extra caller release. Reading one wrapper's ownership convention into all overloads produces leaks or premature releases. [`dictionary retain`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L6463-L6466), [`compatibility wrapper`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L6591-L6611), [`remove`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L7209-L7230).

### The existing set comes from the class-instance index

`copyExistingServices()` has a direct `IOResources` special case, then normally enumerates published service instances through `OSMetaClass::applyToInstancesOfClassName()` or the IOService metaclass tree. `instanceMatch()` checks required state and inactivity, applies the internal matching predicates, and builds a retained `OSSet` or an early single result. If some matching conditions remain, `copyExistingServices()` runs `matchPassive()` over the candidate set afterward. It normally wraps the result set in an `OSCollectionIterator`, whose retained collection keeps the candidates alive. The registry-walk implementation later in the function is under `MATCH_DEBUG`; it is not the normal lookup algorithm. [`instanceMatch`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L6209-L6250), [`existing-service algorithm`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L6254-L6394), [instance index](object-runtime-and-collections.md).

That result iterator is a snapshot container iterator, unlike the live recursive registry cursor. Its objects remain retained even if the service graph changes, but their active/matched state is not frozen. The type's default state mask also matters: publish and matched notifications represent distinct states and are not interchangeable with “property exists.” [`state masks`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L6513-L6524), [`iterator conversion`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L6384-L6391), [registry iterator distinctions](registry-planes-and-properties.md), [boot/resource integration](bootstrap-and-bsd-integration.md).

### What each notification actually observes

| Notification | Registration-time selection | Later event represented |
|---|---|---|
| Publish | Registered services | A matching pass entered after explicit registration; publish notifiers are mixed into the ordered candidate set. A generation-only retry does not re-add them unless re-registration also occurred. |
| First publish | Services with `FirstPublishState` | First publication bookkeeping, before ordinary candidate probing. “First” does not prevent a newly installed notifier from replaying an already published service. |
| Matched | Services with `MatchedState` | Completion of a matching operation while active and not module-stalled; this does not imply that some driver candidate successfully started. |
| First match | Services with `FirstMatchState` | The first such completed match for the service, with the same registration-time replay distinction. |
| Terminated | No current-service replay | Phase 1 has made a victim inactive; final stop, detach and storage release can still be pending. |
| Will terminate | No current-service replay | Selected termination callbacks in the later termination processing; the name alone does not mean it precedes the phase-1 terminated notification. |

The first four masks come from [`doInstallNotification`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L6513-L6534). Publication and matched delivery are in [`doServiceMatch`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L5523-L5613); termination selection is in [`phase 1`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L2634-L2687) and [`will-terminate processing`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L3259-L3284). In particular, `MatchedState` is set even when the candidate set was empty or all attempted starts failed, provided the final active/not-stalled test succeeds. It records completion of matching, not a live child count.

Publish notifier priority participates in `matches` together with personalities; matched notifier arrays have their own selection order. Neither order serializes callbacks for **different services** across configuration threads. `invokeNotifier()` calls the handler directly on the invoking thread; replay uses the registration caller, live matching uses the selected synchronous caller or configuration worker, and termination uses its caller/worker path. There is no universal notification thread or automatic workloop gate. [`publish insertion`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L5548-L5564), [`ordered object priority`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L3660-L3738), [`direct call`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L3779-L3817), [matching dispatch](service-matching-and-termination.md#2-publication-records-work-before-invoking-matching).

## 3. Event selection and callback invocation have separate lifetimes

`copyNotifiers()` takes arbitration, then the notification lock, selects enabled notifiers whose dictionaries pass `matchPassive()`, retains them in an array, and updates the service state before releasing the locks. It allows termination notifications even when the service is inactive. `invokeNotifiers()` consumes the array pointer, sets the caller's pointer to null, invokes every retained notifier, combines Boolean results with `&=`, and finally releases the array. A false callback result does not short-circuit the rest of that array. [`selection/state update`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L6858-L6899), [`array consumption`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L3820-L3843).

The matching worker illustrates this split: it records first-publication state and selects its callbacks under arbitration, then unlocks before invocation; after matching it selects matched/first-match notifications, clears `ConfigRunning`, unlocks, invokes callbacks, and only then clears `ConfigState` and resumes pending termination work. Those two configuration bits are intentionally not cleared at the same point. [`doServiceMatch`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L5526-L5568), [`post-match callbacks`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L5590-L5624), [termination coordination](service-matching-and-termination.md).

`invokeNotifier()` rechecks enabled state under the notification lock even if an earlier selection retained it. If enabled, it inserts a stack invocation record containing `current_thread()`, unlocks, calls the handler, then relocks to remove the record and wake removal/disable waiters. If disabled by then, it simply skips the callback. A retained snapshot supplies object lifetime; the enabled recheck supplies cancellation of callbacks not yet started. They solve different races. [`invokeNotifier`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L3779-L3817).

```mermaid
sequenceDiagram
    participant E as Event thread
    participant N as Notification mutex
    participant C as Callback
    participant R as Removing thread
    E->>N: select and retain notifier in array
    E->>N: recheck enabled#59; add invocation(thread)
    E->>C: invoke with notification mutex released
    R->>N: unlink notifier#59; clear enabled
    R->>N: wait while other-thread invocation exists
    C-->>E: return
    E->>N: remove invocation#59; wake waiters
    N-->>R: callback drain complete
    R->>R: release registration owner
    E->>E: release retained invocation array
```

`deliverNotification()` is not an alternate working shortcut in this checkout: its body panics. Follow `copyNotifiers()` and `invokeNotifiers()` rather than assuming the method name implies a valid generic delivery path. [`deliverNotification`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L6849-L6855).

### Worked event orders: retained does not mean still eligible

Assume notifier `N` matches services `A` and `B`, and all allocations succeed. Each row describes a possible source-level order, not an observed trace:

| Event order | Outcome and reason |
|---|---|
| Registration installs `N` and snapshots `A`; then `A` becomes inactive before replay reaches it | The snapshot still owns `A`, but replay skips its inactive state. Storage lifetime and event eligibility are separate. |
| An event retains `N` in an array; another thread disables it before `invokeNotifier()` checks enabled | The array remains valid; invocation skips the handler and the array later releases `N`. Selection does not make delivery irrevocable. |
| Invocation records itself first; another thread removes `N` | Removal clears membership/enabled state and waits for the recorded other-thread invocation to return. It cannot cancel an already executing callback. |
| Replay callback for `A` removes `N`, and `B` remains in the replay iterator | The extra install reference protects `N`; later replay calls skip its cleared enabled bit. Registration ultimately returns the null-notifier sentinel. |
| Replay for `A` and a live event for `B` reach `N` concurrently | Both can have invocation records and run outside the notification mutex. Callback context needs its own synchronization; the invocation queue tracks concurrency rather than forbidding it. |

The replay checks are in [`addMatchingNotification`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L6632-L6648); live cancellation and entry are in [`invokeNotifier`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L3794-L3813); removal/drain is in [`remove/wait`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L7175-L7228). No active-service recheck occurs *inside* `invokeNotifier()` after the caller's event selection. A service can change state after the replay caller's inactive check; retaining the service does not promise that it remains usable throughout the callback.

```mermaid
sequenceDiagram
    participant R as Registration caller
    participant N as Notifier N
    participant A as Service A callback
    participant B as Live event for service B
    R->>N: install#59; hold extra reference#59; snapshot A
    R->>N: replay enters invocation on registration thread
    N->>A: handler with notification mutex released
    B->>N: enabled check#59; second invocation record
    N->>B: handler on B event thread
    B-->>N: return#59; remove B invocation
    A->>N: remove self#59; unlink and disable
    N-->>A: no other invocation left to drain
    A-->>R: return#59; remove A invocation
    R->>N: release extra install reference
    N-->>R: registration returns null-notifier sentinel
```

The diagram deliberately lets `B` finish before self-removal. If its invocation is still active, `A`'s `remove()` waits for `B`; only invocations on `A`'s current thread are exempt. A recursive invocation on that same thread is also exempt because the test compares thread identities, not one particular stack record. This is why callbacks must not use a self-removal return as proof that their own context is no longer in use.

## 4. Removal waits for other threads, with a self-callback exception

Matching notifier `remove()` unlinks the notifier from `whence`, clears that pointer, releases its matching dictionary, clears enabled state, waits, unlocks, and releases the registration owner. `disable()` clears enabled and waits only if it was previously enabled; it returns the previous state, which `enable(was)` can restore. These methods do not destroy a notifier still retained by a dispatch snapshot. `free()` asserts that the invocation queue is empty. [`matching removal/disable/enable`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L7197-L7260).

Both matching and interest `wait()` implementations scan active invocations and sleep only for records belonging to another thread. The current thread is excluded so a callback can disable/remove itself without waiting for its own return. That does **not** authorize destruction while its callback body still runs: the caller's replay/snapshot reference is what makes the self-removal case safe. It also does not prove a callback is absent merely because `remove()` returned to that same callback. [`matching wait`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L7175-L7194), [`interest wait`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L2412-L2431), [`replay protection`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L6580-L6585), [`array protection`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L6876-L6883).

The exact condition is the critical part of the drain protocol: [`_IOServiceNotifier::wait`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L7180-L7193).

<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L7180-L7193 -->
```cpp
	do {
		doWait = false;
		queue_iterate( &handlerInvocations, next,
		    _IOServiceNotifierInvocation *, link) {
			if (next->thread != current_thread()) {
				doWait = true;
				break;
			}
		}
		if (doWait) {
			state |= kIOServiceNotifyWaiter;
			SLEEPNOTIFY(this);
		}
	} while (doWait);
```

The wait uses `IORecursiveLockSleep` with `THREAD_UNINT`, and callback exit clears the waiter bit and wakes all notification waiters. Removing a notifier from within a callback therefore requires preserving any callback-owned context until that body is finished; clearing a raw target pointer or freeing shared context solely because self-removal returned would not be justified by this protocol. [`sleep/wake macros`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L308-L313), [`callback completion`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L3806-L3813), [`raw target/ref fields`](../../../platydoc-data/xnu/iokit/Kernel/IOServicePrivate.h#L105-L110).

### Disable is a reversible bit change, not unregister-and-replay

`disable()` returns whether enabled was set when it acquired the lock; it calls `wait()` only when that previous state was true. This qualification matters with concurrent callers. Thread D1 can clear enabled and sleep waiting for a running handler; D2 then sees enabled already false and returns from `disable()` without joining D1's drain. D2's false return does not establish that the handler has finished. The caller must coordinate its own ownership of this transition. [`disable`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L7232-L7247).

Restoring the prior state only changes the flag. It does not reinstall a removed notifier, enumerate current services, replay missed events, or provide a nesting counter. [`enable`, lines 7250–7258](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L7250-L7258).

<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L7250-L7258 -->
```cpp
_IOServiceNotifier::enable( bool was )
{
	LOCKWRITENOTIFY();
	if (was) {
		state |= kIOServiceNotifyEnable;
	} else {
		state &= ~kIOServiceNotifyEnable;
	}
	UNLOCKNOTIFY();
```

An event selected into a retained snapshot *before* disable can still be invoked if another caller re-enables the notifier before that snapshot's enabled check; events never selected while disabled have no saved replay queue here. The protocol's state is registration membership, an enabled bit and current invocations, not a history of service events. Ordinary callers should treat `remove()` as consuming the registration owner's reference. Having a borrowed pointer in a callback or a separately retained snapshot does not turn repeated `remove()` into an idempotent owner operation: the body unconditionally releases an owner reference at the end. [`selection`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L6875-L6888), [`invoke-time check`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L3794-L3804), [`terminal release`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L7209-L7228).

## 5. Interest messages attach to one service

`registerInterestForNotifier()` validates notifier type and handler, accepts a specific set of interest symbols, then takes service arbitration. An inactive service returns `kIOReturnNotReady`. For an active service it enables the notifier, takes the notification lock, locates or creates an `IOCommand` chain head stored in the corresponding registry property, enqueues the notifier and takes a list reference. Unsupported interest types return `kIOReturnBadArgument`. The visible body leaves `rc` as success if chain-head creation/property installation fails, so this path should not be documented as having a complete allocation-failure error return for every list-creation failure. [`registration`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L2291-L2355).

`applyToInterestNotifiers()` copies the chain's notifiers into an `OSArray` under the notification lock, then invokes its applier after unlocking; the array retains the notifiers. `applyToInterested(gIOGeneralInterest, ...)` additionally visits attached service clients. `messageClient()` dispatches directly to a service's virtual `message()` or, for an interest notifier, performs the same enabled-check/invocation-record/callback/drain sequence. `messageClients()` continues through recipients and keeps a non-success result if one is returned. [`interest snapshot`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L2148-L2185), [`general-interest routing`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L2188-L2196), [`message dispatch`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L2101-L2145), [`message aggregation`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L2206-L2235).

Interest removal removes the chain membership and list reference, disables, drains other-thread callbacks, then drops the registration owner. `unregisterAllInterest()` is different: it drains list nodes from the known interest properties and drops their list references through `cleanInterestList()`. It does not call each notifier's public `remove()` or perform that method's enabled/drain sequence. This matters when reading service teardown: the service's surrounding lifecycle and retained callback snapshots still participate in lifetime. [`interest remove`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L2446-L2463), [`bulk list cleanup`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L2359-L2401).

The resulting ownership ledger is useful when comparing interest callbacks to matching callbacks:

| Reference or borrowed field | Matching notifier | Interest notifier |
|---|---|---|
| Registration owner | Initial notifier allocation, consumed by `remove()` | Initial allocation, consumed by `remove()` |
| Membership owner | `OSOrderedSet` retains the notifier | Explicit retain after queue insertion |
| Temporary delivery owner | Candidate set, callback array, or extra install/replay retain | Snapshot `OSArray` retains each copied notifier |
| Callback state | Stack invocation record under notification mutex; it is not itself an object retain | Same distinction |
| Target/refcon | Raw pointers, except copied blocks | Raw pointers, except copied blocks |
| Provider/service passed to callback | Supplied by the matching caller or retained existing-service snapshot | Supplied by the message caller; notifier membership does not itself retain its provider |

See [`matching installation`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L6454-L6494), [`interest installation`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L2291-L2355), [`interest snapshot`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L2148-L2185), and [`interest fields and cleanup`](../../../platydoc-data/xnu/iokit/Kernel/IOServicePrivate.h#L115-L139). Holding an iterator or notifier can preserve selected objects without preserving the registry relationship that caused their selection. Public interest registration also has no automatic existing-state replay equivalent to `addMatchingNotification()`; callers needing a current property/state sample must use that state's own synchronization protocol.

## 6. A synchronous match wait is a temporary notification

`waitForMatchingServiceWithToken()` optionally installs a DriverKit check-in-token cancellation handler, then under the notification lock looks for an already matched service with `kIONotifyOnce`. If none exists and cancellation has not occurred, it creates a matched notifier whose refcon points to its local result slot and sleeps on that slot, with an absolute deadline for finite timeouts. The synchronous handler retains the first service, stores it, and wakes the waiter while holding the same lock. The cancellation handler wakes the same event and records cancellation. [`wait setup and lookup`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L6709-L6795), [`result handler`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L6692-L6706), [`cancellation`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L6681-L6689).

After wakeup the waiter unlocks, unregisters the cancellation handler, removes its notifier (including the invocation drain), releases the cancellation-handler object and returns the retained result or null. The visible body sleeps once inside a `do ... while (false)` block, rather than implementing a generic repeated predicate wait. Cleanup before leaving is especially important because the callback refcon points to stack state. The legacy `waitForService()` wrapper consumes the matching dictionary and releases the returned service before returning a borrowed pointer, unlike `waitForMatchingService()`. [`wait cleanup`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L6796-L6819), [`wrappers`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L6822-L6846).

## 7. Arbitration tracks owners and breaks only permitted deadlocks

`lockForArbitration(isSuccessRequired)` obtains a global queue lock and prepares a queue element recording current thread, service, recursion count, required flag and aborted state. It searches the active queue for an owner. An unlocked service becomes active immediately; recursion by the same thread increments the owner's count. If another thread owns the service, the code follows that owner's waiting dependency through the active/waiting queues to detect a cycle. [`acquisition setup`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L1666-L1736), [`dependency walk`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L1737-L1814).

On a detected cycle, a non-required originating request fails. A required request can instead abort another waiting request encountered with `required == false`, remove that victim from the waiting queue and wake it. If every participant requires success, the implementation panics with an unrecoverable-deadlock diagnostic. This is a narrow, explicit deadlock response; it is not a claim that arbitrary lock combinations across workloops, registry locks and driver mutexes are automatically detected. [`cycle resolution`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L1764-L1801).

Waiting enqueues the request and calls `IOLockSleepWithInheritor()` using the current owner's thread as inheritor and `LCK_SLEEP_UNLOCK`. Required requests wait uninterruptibly; optional requests can return interrupted and remove themselves if still queued. A woken request distinguishes an aborted floating queue element from one already moved to the active queue. Thus a successful wake represents ownership transfer, not merely a signal to race all other contenders for an unlocked flag. [`sleep and interruption`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L1816-L1894), [runtime wait/inheritance mechanisms](../runtime/wait-and-turnstile-protocols.md).

The inheritor and interruptibility are visible at the wait call: [`arbitration sleep`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L1822-L1826).

<!-- source-excerpt: ../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L1822-L1826 -->
```cpp
				wait_result = IOLockSleepWithInheritor(gArbitrationLockQueueLock,
				    LCK_SLEEP_UNLOCK,
				    &element->service->__machPortHoldDestroy,     // event
				    owner->thread,
				    element->required ? THREAD_UNINT : THREAD_INTERRUPTIBLE, TIMEOUT_WAIT_FOREVER);
```

`unlockForArbitration()` decrements a recursive count or removes the owner from the active queue. It calls `wakeup_one_with_inheritor`, uses the returned thread to find the matching waiting element, moves that element to the active queue while still holding the global queue lock, and drops the returned thread reference. Although requests are appended to a waiting queue, the selected successor comes from the inheritor-aware wake primitive; describing this as unconditional FIFO ownership would overstate the body. [`unlock/handoff`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L1932-L2008).

## 8. Open/close serialize service policy and cooperate with termination

`open()` first sends the general-interest “attempting open” message, then tries optional arbitration. Deadlock avoidance can therefore return false before `handleOpen()`. Once locked, an inactive service fails; a DriverKit client first performs `userServer->serviceOpen`, then the provider's virtual `handleOpen`. If that latter step fails, it rolls back the DriverKit bookkeeping using `serviceClose`. Arbitration is released before returning. [`IOService::open`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L3522-L3559).

The default `handleOpen()` permits one `__owner`. If already owned and `kIOServiceSeize` is supplied, it asks the current owner to close and succeeds only if the message succeeds **and** `__owner` became null. An acknowledgment alone does not forcibly erase ownership. Subclasses can implement a different policy in their handle methods while keeping the public arbitration wrapper. [`default open policy`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L3616-L3640).

`close()` uses required arbitration, checks whether this client is open, calls `handleClose`, snapshots whether termination phase 3 is waiting, and updates DriverKit open bookkeeping. After unlocking, it schedules stop on the closing client when termination is waiting; otherwise it broadcasts “was closed” if a real open was closed. This avoids running the later stop scheduling or general-interest broadcast as part of the locked owner update. `isOpen()` also uses arbitration around the virtual predicate. [`close/isOpen`](../../../platydoc-data/xnu/iokit/Kernel/IOService.cpp#L3562-L3613), [termination phase 3](service-matching-and-termination.md), [DriverKit connection lifetime](user-client-and-driverkit-lifetime.md).

## 9. Local examples and limits of the test evidence

`IOServiceTest()` demonstrates a registration-time callback rather than merely looking up a class name. It installs a block notifier for already matched `IOPlatformExpert`, asserts that the callback populated `found` before registration returns, explicitly retains that service in the callback, removes the matching notifier, then registers/removes a busy-interest block and releases the service. That extra service retain is needed because neither the stack variable nor the callback argument owns the snapshot's eventual lifetime. [`test body`](../../../platydoc-data/xnu/iokit/Tests/Tests.cpp#L1402-L1444).

[`IOServiceMatchingSharedPtrTests`](../../../platydoc-data/xnu/iokit/Tests/Tests.cpp#L1647-L1764) checks that matching-dictionary helpers preserve shared-pointer ownership when filling or reusing tables. Those assertions concern dictionary references, not callback cancellation. [`IOUserNotificationTests`](../../../platydoc-data/xnu/iokit/Tests/Tests.cpp#L1567-L1644) creates ten kernel threads which repeatedly replace/clear one `IOUserNotification`'s underlying matching notifier. This is evidence of a concurrent ownership exercise, not a complete live-callback removal regression: it uses will-terminate interest in the root path, its handler does no work, and the visible harness does not initialize `threadsCompleted` before the wait. No result from executing that harness is claimed here.

These routines are in development/debug test code, reached through the local test dispatch. The matching test's synthetic provider creation block is separately `#if 0`, so it should not be described as executed setup. [`test guard`](../../../platydoc-data/xnu/iokit/Tests/Tests.cpp#L191-L198), [`disabled setup`](../../../platydoc-data/xnu/iokit/Tests/Tests.cpp#L1409-L1416), [`dispatch cases`](../../../platydoc-data/xnu/iokit/Tests/Tests.cpp#L2098-L2135). For shared-buffer publication and asynchronous result messages, continue with the [shared-queue chapter](shared-data-queues-and-notifications.md). User-facing matching-notification iterator arming is a separate protocol not traced by those queue examples; registration, callback completion and message receipt remain different events.

## Reading route and source-review limits

Read the notifier structures and lock macros, then `installNotification/addMatchingNotification`, `invokeNotifier`, and `remove/wait`. Compare matching and interest snapshots. Finally trace `lockForArbitration/unlockForArbitration` and one `open/close` pair; keep the registry/property locks distinct throughout.

| Sources inspected | Depth | Limits |
|---|---|---|
| Matching notifier setup, existing-instance snapshot and replay | Full selected registration, callback and cleanup path; event-type semantics and worked replay/live interleavings | Every passive matching predicate and notifier client is not reviewed |
| Interest list setup, message snapshots and removal | Enabled-state, list/snapshot ownership and invocation drain | Device-specific interest semantics and all teardown callers remain outside scope |
| Synchronous matched wait and token cancellation | Stack-refcon lifetime, result reference, timeout cleanup | No timeout/cancellation race test was run |
| Arbitration queue/deadlock/handoff and open/close | Full selected owner-transfer and rollback path | Not a proof of global driver lock-order correctness |
| `doServiceMatch` callback boundaries | State ordering around notification delivery and late re-registration; reversible disable versus terminal removal | Candidate probing and termination are covered in the companion lifecycle chapter |
| Development/debug fixtures | Matching replay and retained result, matching-helper reference counts, notification-owner replacement exercise | Source inspected only; no race, deadlock or kernel test was executed |

Compare these callback lifetimes with [shared data queues and notifications](shared-data-queues-and-notifications.md), whose buffer publication, wakeups and asynchronous results have distinct ownership rules. No callback race or deadlock was executed during this source review.

<!-- BEGIN PLATYDOC DOCUMENTATION LICENSE -->
Original Platydoc text and diagrams are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Quoted source code and third-party material retain their respective licenses.
<!-- END PLATYDOC DOCUMENTATION LICENSE -->
