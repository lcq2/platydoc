#!/usr/bin/env python3
"""Rebuild the all-slot Mach trap catalog from this checkout, preserving conditionals.

Curated purpose text is intentionally separate from extracted table/ABI/source data.
This is a documentation extractor, not a C preprocessor or an ABI conformance test.
"""
from pathlib import Path
import argparse
import re
import os

from paths import DOCS, SOURCE_ROOT, require_source
from doc_license import with_license_notice

OUT = DOCS / 'interfaces/mach-traps.md'
START = '<!-- BEGIN GENERATED MACH TRAP CATALOG -->'
END = '<!-- END GENERATED MACH TRAP CATALOG -->'
PURPOSE = {
10: 'Allocate an anonymous region in the current task via mach_vm_allocate_external; address is copied in/out.',
11: 'Get or change current-task purgeable state via mach_vm_purgable_control; GET accepts the current-task read capability.',
12: 'Remove a current-task virtual range via mach_vm_deallocate_external.',
13: 'Copy active dyld notifier send-right names into the current task; capacity/count and failure cleanup are explicit.',
14: 'Change current-task region protections via mach_vm_protect.',
15: 'Restricted anonymous mapping via mach_vm_map_external with null object, zero object offset, no copy, maximum ALL, default inheritance.',
16: 'Allocate a named right in the current IPC space via mach_port_allocate; copy out its name.',
18: 'Drop a user reference through mach_port_deallocate in the current IPC space.',
19: 'Adjust selected right user-reference count via mach_port_mod_refs.',
20: 'Move a receive right between port sets via mach_port_move_member.',
21: 'Insert a right; same-name MAKE_SEND/COPY_SEND has a fast path, otherwise copy in a right and destroy it if insertion fails.',
22: 'Add receive-right membership to a port set via mach_port_insert_member.',
23: 'Remove receive-right membership from a port set via mach_port_extract_member.',
24: 'Copy in options, construct a port with context, and copy out its name.',
25: 'Destruct a port with send-reference delta and guard through mach_port_destruct.',
26: 'Allocate a receive right in the current space; return its name directly or MACH_PORT_NULL.',
27: 'Obtain the current thread self send right and install/copy it out with immovable-right support.',
28: 'Obtain the current task self send right and install/copy it out with immovable-right support.',
29: 'Copy a send right for the current task\'s host port into its IPC space.',
31: 'Legacy combined message send/receive; sets rcv_msg to zero before the overwrite implementation.',
32: 'Legacy message send/receive with separate receive buffer; IPC_HAS_LEGACY_MACH_MSG_TRAP body, otherwise KERN_NOT_SUPPORTED.',
33: 'Signal one semaphore waiter or increment availability through semaphore_signal_internal_trap.',
34: 'Wake all eligible semaphore waiters; semaphore object reference is released after the operation.',
35: 'Signal a semaphore with a selected thread target; resolves both names and drops references.',
36: 'Wait on a semaphore; blocking completion may return through a continuation.',
37: 'Wait on one semaphore while signaling another; coordinated wait/signal internal path.',
38: 'Semaphore wait with relative seconds/nanoseconds timeout converted to a deadline.',
39: 'Timed wait plus signal, using the same semaphore wait/signal internal machinery.',
40: 'Read current-task port attributes; clamp count to generated reply capacity, zero temporary storage, copy count/data out.',
41: 'Guard a current-space port with a 64-bit context and strictness policy.',
42: 'Unguard a current-space port after guard validation.',
43: 'Reserve one or more globally allocated activity IDs; validates count and copies the first ID out.',
44: 'Resolve PID to a task-name capability with BSD process/credential/MAC checks.',
45: 'Resolve PID to a task-control capability with process, credential, MAC, and task-access policy checks.',
46: 'Convert a task port to its PID and copy the PID to userspace.',
47: 'Current packed 64-bit message ABI; decode packed header/scalar fields and dispatch send/receive with message policy.',
48: 'Retained ABI stub: returns ENOTSUP; does not create a swap file in this checkout.',
49: 'Retained ABI stub: returns ENOTSUP; does not remove a swap file in this checkout.',
50: 'Unbind any prior user special reply port, allocate a new receive+send right, bind it to the thread, return name.',
51: 'Only compaction enable/disable flags reach macx_backing_store_compaction; other requests return ENOTSUP.',
52: 'Retained ABI stub: returns ENOTSUP.',
53: 'Retained ABI stub: returns ENOTSUP.',
58: 'No-op success body; pending AST work is picked up on kernel exit from the preemption-free region.',
59: 'Yield with temporary priority depression; the historical priority argument is unused and table argc is zero.',
60: 'Yield if scheduler policy says useful; boolean result reports whether yielding remains appropriate.',
61: 'Scheduler-directed switch/yield with optional depression/wait and a thread hint; continuation path can discard the stack.',
62: 'Clock-port sleep with absolute/relative clock time and wakeup-time copyout.',
63: 'Current-task deferred-reclamation accounting update; CONFIG_DEFERRED_RECLAIM body or KERN_NOT_SUPPORTED.',
70: 'Copy raw recipes, create a voucher, export its send right, and copy its name to userspace.',
72: 'Resolve a voucher, extract one raw attribute recipe into bounded temporary storage, then copy bytes/count out.',
76: 'Return current-space right type bits through mach_port_type and copyout.',
77: 'Register/change a notification using a send-once disposition; copy previous notification right back into the namespace.',
88: 'Exclaves operation multiplexer: privilege/config checks then resource, IPC, sensor, notification, and boot operations; disabled body returns KERN_NOT_SUPPORTED.',
89: 'Copy the absolute-time conversion numerator/denominator to userspace.',
90: 'Wait until an absolute-time deadline through assert_wait_deadline/thread_block; interruption maps to a Mach result.',
91: 'Allocate a timer object and receive-right port; return the name or MACH_PORT_NULL.',
92: 'Destroy the named timer port with timer-object validation.',
93: 'Arm a timer at an absolute deadline through mk_timer_arm_trap_internal.',
94: 'Cancel timer delivery and optionally copy out its previous deadline.',
95: 'Arm a timer with flags and leeway through mk_timer_arm_trap_internal.',
96: 'Obtain a task debug-control capability subject to process/credential/entitlement restrictions.',
100: 'Dispatch an IOKit user-client trap or DriverKit uext trap from a tagged reference; index and six scalars reach the selected target.',
}

def link(label, path, line):
    return f'[{label}]({os.path.relpath(SOURCE_ROOT / path, OUT.parent)}#L{line})'

def generate():
    table_path = Path('osfmk/kern/syscall_sw.c')
    src = (SOURCE_ROOT / table_path).read_text()
    table = src.split('const char * const mach_syscall_name_table')[0]
    rows = {}
    for m in re.finditer(r'/\*\s*(\d+)\s*\*/\s*MACH_TRAP\((\w+),\s*(\d+),\s*(\d+),\s*(\w+)([^\n]*)', table):
        slot, name, argc, words, munge, rest = m.groups()
        rows.setdefault(int(slot), []).append((name, argc, words, munge, 'returns_port = 1' in rest, table[:m.start()].count('\n')+1))
    assert set(rows) == set(range(128)), 'Trap slot inventory changed'
    assert {i for i, rs in rows.items() if len(rs) > 1} == {47, 63}, 'Conditional trap layout changed'
    assert '#if defined(__LP64__) || defined(__arm64__)\n/* 47 */' in table
    assert '#if __LP64__\n/* 63 */' in table
    named = {i: next(r for r in rs if r[0] != 'kern_invalid') for i, rs in rows.items() if any(r[0] != 'kern_invalid' for r in rs)}
    assert set(named) == set(PURPOSE), 'Update curated operation descriptions'
    names = {r[0] for r in named.values()}
    # Read each implementation once. A line-leading symbol followed by a parameter list
    # is enough for this known catalog; assertions below reject missing/ambiguous matches.
    definitions = {}
    pattern = re.compile(r'^('+'|'.join(map(re.escape, sorted(names)))+r')\s*\(', re.M)
    for top in ['osfmk', 'bsd', 'iokit']:
        for p in sorted((SOURCE_ROOT / top).rglob('*')):
            if p.suffix not in {'.c','.cpp'}: continue
            text = p.read_text(errors='replace')
            for m in pattern.finditer(text):
                definitions.setdefault(m.group(1), []).append((p.relative_to(SOURCE_ROOT), text[:m.start()].count('\n')+1))
    header_path = Path('osfmk/mach/mach_traps.h')
    header = (SOURCE_ROOT / header_path).read_text()
    structs = {}
    for m in re.finditer(r'struct\s+(\w+)\s*\{(.*?)\n\};',header,re.S):
        fields = re.findall(r'PAD_ARG_\(\s*([^,]+),\s*(\w+)\)',m.group(2))
        structs[m.group(1)] = (fields, header[:m.start()].count('\n')+1)
    signatures = dict(re.findall(r'\b(\w+)\s*\(\s*struct\s+(\w+)\s*\*args\s*\)',header))
    output = [START, '', '## Complete table: all 128 slots', '',
      'The **ABI** column is `argument count / 32-bit word count / munger suffix` exactly as stored in the table; `—` means no munger. `port` marks the table’s direct port-name return flag. Argument declarations below are kernel argument-structure fields, in order; a `user_addr_t` is a userspace pointer value, not a kernel pointer. Source links on slot numbers identify the exact table entries. Conditional alternatives are preserved rather than evaluated for this host.', '']
    for lo in range(0,128,32):
        output += [f'### Slots {lo}–{lo+31}', '', '| Slot | Handler and availability | ABI | Kernel argument fields | Purpose and first implementation boundary |', '| ---: | --- | --- | --- | --- |']
        for i in range(lo,lo+32):
            rs=rows[i]
            r=named.get(i,rs[0]); name,argc,words,munge,port,line=r
            slotlink=link(str(i),table_path,line)
            if name=='kern_invalid':
                reason='No operation assigned; dispatch rejects this slot.'
                if i<=9: reason='Reserved low numbers; not a Mach operation.'
                if 101<=i<=107: reason='Reserved for IOKit; currently invalid.'
                if i==108: reason='Invalid despite the historical thread_set_x86_64_compat userspace stub.'
                if i>=109: reason='Explicitly unused table slot.'
                output.append(f'| {slotlink} | `kern_invalid` | `0 / 0 / —` | none | {reason} |')
                continue
            hits=definitions.get(name,[])
            assert len(hits)==1,(name,hits)
            path,implline=hits[0]
            target=link('`'+name+'`',path,implline)
            condition=''
            if i==47: condition=r'; `__LP64__ \|\| __arm64__`, otherwise '+link('invalid',table_path,rs[1][-1])
            if i==63: condition='; `__LP64__`, otherwise '+link('invalid',table_path,rs[1][-1])
            typename=signatures[name]
            fields,argline=structs[typename]
            # Field-bearing but unconsumed swtch_pri is deliberately retained in the ABI display.
            args=', '.join(f'`{t.strip()} {n}`' for t,n in fields) or 'no consumed fields'
            args += ' ('+link('structure',header_path,argline)+')'
            abi=f'`{argc} / {words} / {munge.removeprefix("munge_") if munge!="NULL" else "—"}`'
            if port:abi+='; port'
            output.append(f'| {slotlink} | {target}{condition} | {abi} | {args} | {PURPOSE[i]} |')
        output.append('')
    output += [END]
    return '\n'.join(output)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check', action='store_true')
    args=ap.parse_args()
    require_source()
    generated=generate()
    old=OUT.read_text()
    assert START in old and END in old
    new=with_license_notice(old[:old.index(START)]+generated+old[old.index(END)+len(END):])
    if args.check:
        if old!=new:raise SystemExit('Mach trap catalog is stale')
        print('Mach trap catalog matches source: 128 slots, 62 potentially named, 66 always invalid')
    else:
        OUT.write_text(new)
        print('Updated Mach trap catalog: 128 slots')
if __name__=='__main__':main()
