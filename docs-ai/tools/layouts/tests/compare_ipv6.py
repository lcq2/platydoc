#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Fixed source-derived geometry and PAC checks for the thread/IPv6 expansion.

Consumes the exact native/Wasm report, not copied browser geometry. Constants
come from original wire/address definitions and explicit ARM64 C field widths;
external pinned-Clang assertions independently cover the complete named roots.
"""
import argparse
import json
from pathlib import Path
from compare_catalog import read, result_hash, validate_pac_context

BASES = ('release-t8103', 'development-t8103', 'release-vmapple', 'development-vmapple')
# sizeof/alignment; field offsets are bits, including the actual bitfields.
FACTS = {
 'in6_addr': (16, 4, {}),
 'sockaddr_in6': (28, 4, {'sin6_addr': 64, 'sin6_scope_id': 192}),
 'ip6_hdr': (40, 1, {'ip6_src': 64, 'ip6_dst': 192}),
 'ip6_hbh': (2, 1, {'ip6h_nxt': 0, 'ip6h_len': 8}),
 'ip6_dest': (2, 1, {'ip6d_nxt': 0, 'ip6d_len': 8}),
 'ip6_rthdr': (4, 1, {'ip6r_type': 16, 'ip6r_segleft': 24}),
 'ip6_frag': (8, 1, {'ip6f_offlg': 16, 'ip6f_ident': 32}),
 'route_in6': (48, 8, {'ro_rt': 0, 'ro_srcia': 64, 'ro_flags': 128, 'ro_dst': 160}),
 'ip6_pktopts': (152, 8, {'ip6po_minmtu': 32, 'ip6po_prefer_tempaddr': 35, 'ip6po_flags': 38,
                        'ip6po_pktinfo': 64, 'ip6po_nhinfo': 128, 'ip6po_hbh': 576,
                        'ip6po_dest1': 640, 'ip6po_rhinfo': 704, 'ip6po_dest2': 1152}),
 'arm_saved_state64': (296, 8, {'fp': 1856, 'lr': 1920, 'sp': 1984, 'pc': 2048, 'cpsr': 2112,
                              'far': 2176, 'esr': 2240, 'jophash': 2304}),
}
FAMILIES = {'ipv6-wire': ('in6_addr','sockaddr_in6','ip6_hdr','ip6_hbh','ip6_dest','ip6_rthdr','ip6_frag'),
 'ipv6-options': ('ip6_pktopts','ip6_exthdrs','ip6_out_args','ip6q','ip6_moptions'),
 'ipv6-address': ('route_in6','in6_multi','in6_mfilter'),
 'ipv6-neighbor': ('nd_ifinfo','nd_defrouter','nd_prefix','llinfo_nd6'),
 'ipv6-mld': ('mld_ifinfo',), 'thread': ('machine_thread','arm_saved_state64')}


def check(results, requests):
    assertions = 0
    def expect(value, message):
        nonlocal assertions
        if not value: raise ValueError(message)
        assertions += 1
    for base in BASES:
        for family, names in FAMILIES.items():
            name = base + '--' + family; result = results[name]
            expect(result['status'] == 'ok' and not result['diagnostics'], name + ': not a clean success')
            validate_pac_context(requests[name], result)
            records = {r['name']: r for r in result['records'] if r['name']}
            for tag in names:
                expect(tag in records, name + ': missing ' + tag)
                if tag not in FACTS: continue
                record = records[tag]; size, alignment, offsets = FACTS[tag]
                expect((record['size_bytes'], record['alignment_bytes']) == (size, alignment), tag + ': size/alignment')
                fields = {f['name']: f for f in record['fields']}
                for field, offset in offsets.items(): expect(fields[field]['offset_bits'] == offset, tag + '.' + field + ': bit offset')
            if family == 'ipv6-options':
                fields = {f['name']: f for f in records['ip6_pktopts']['fields']}
                for field, width in [('ip6po_minmtu', 3), ('ip6po_prefer_tempaddr', 3), ('ip6po_flags', 2)]:
                    expect(fields[field]['bit_width'] == width, field + ': width')
                fragment = {f['name']: f for f in records['ip6q']['fields']}
                expect(fragment['ip6q_down']['type']['kind'] == 'pointer', 'Fragment queue reference must remain a pointer boundary')
            if family == 'thread':
                fields = {f['name']: f for f in records['machine_thread']['fields']}
                for field in ('rop_pid','jop_pid','upcb','uNeon','kstackptr'):
                    expect(field in fields and fields[field]['type']['size_bits'] == 64, 'Missing/changed PAC-preserved machine field ' + field)
                expect(records['machine_thread']['size_bytes'] == (392 if base.startswith('development') else 256) + (8 if base.endswith('vmapple') else 0), 'Machine debug/SME variant')
    return assertions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundles', type=Path, required=True)
    parser.add_argument('--comparison', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    from compare_catalog import load_cases
    cases = load_cases(args.bundles); report = read(args.comparison)
    from compare_catalog import requests_hash
    if report['wasm_parity'] != 'passed' or report['cases'] != [n for n, _ in cases] or report['requests_sha256'] != requests_hash(cases):
        raise ValueError('A complete matching native/Wasm comparison is required')
    for name, result in zip(report['cases'], report['results'], strict=True):
        if result_hash(result) != report['case_evidence'][name]['compact_result_sha256']: raise ValueError('Changed comparison result')
    assertions = check(dict(zip(report['cases'], report['results'], strict=True)), dict(cases))
    args.output.write_text(json.dumps({'kind': 'thread-ipv6-fixed-geometry', 'assertions': assertions, 'profiles': list(BASES),
        'comparison_sha256': __import__('hashlib').sha256(args.comparison.read_bytes()).hexdigest(), 'passed': True}, indent=2) + '\n')
    print(assertions, 'fixed geometry/PAC assertions passed')


if __name__ == '__main__': main()
