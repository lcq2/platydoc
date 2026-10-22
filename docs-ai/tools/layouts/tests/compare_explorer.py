#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Native geometry evidence and focused live-explorer semantic checks."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import hashlib
sys.dont_write_bytecode = True
SOURCE = '''struct Leaf { short code; char tag; };
union Choice { unsigned long whole; struct Leaf leaf; };
struct Node { int n; struct Node *next; };
struct Bits { unsigned a:3; unsigned :0; unsigned b:2; };
struct Flex { int n; char tag; unsigned short tail[]; };
struct Root {
 char head;
#if EXTRA
 long optional;
#endif
 struct Leaf leaf;
 union Choice choice;
 struct Node *link;
 unsigned short grid[2][3];
};
struct __attribute__((packed, aligned(8))) Packed { char tag; unsigned bits:3; unsigned rest:5; short value; };
struct __attribute__((aligned(16))) Aligned { char value; };
struct Edge {
 char prefix;
 struct Packed packets[2];
 union { struct { short small; char last; } detail; unsigned long whole; };
 struct Aligned cells[2];
};
struct __attribute__((aligned(16))) FlexAligned { int n; char tag; unsigned short data[]; };
struct Zero { int n; char values[0]; };
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--wasm', type=Path, help='Also require exact Wasm geometry/transport parity for these model fixtures')
    args = parser.parse_args()
    entries = []
    for name, extra, source in [('base', '0', SOURCE), ('extra', '1', SOURCE), ('changed-source', '0', SOURCE.replace('short code', 'int code'))]:
        request = dict(target='aarch64-apple-darwin', main='/inputs/explorer.c', files={'/inputs/explorer.c': source},
                       macros={'EXTRA': extra}, records=['Root', 'Node', 'Bits', 'Flex', 'Edge', 'FlexAligned', 'Zero'], trace_files=True)
        result = subprocess.run([str(args.native.resolve())], input=json.dumps(request), text=True, capture_output=True, check=True, timeout=30)
        result = json.loads(result.stdout)
        assert result['status'] == 'ok' and not result['diagnostics'], result.get('diagnostics')
        records = {record['name']: record for record in result['records']}
        if name != 'changed-source':
            assert records['Root']['size_bytes'] == (40 if extra == '0' else 56)
            assert records['Flex']['size_bytes'] == 8
            assert records['Flex']['fields'][-1]['offset_bits'] == 48
            assert [field['offset_bits'] for field in records['Bits']['fields']] == [0, 32, 32]
            assert records['Packed']['size_bytes'] == 8 and records['Packed']['alignment_bytes'] == 8
            assert [field['offset_bits'] for field in records['Packed']['fields']] == [0, 8, 11, 16]
            assert records['Edge']['size_bytes'] == 64 and records['Edge']['alignment_bytes'] == 16
            assert [field['offset_bits'] for field in records['Edge']['fields']] == [0, 64, 192, 256]
            assert records['FlexAligned']['size_bytes'] == 16 and records['FlexAligned']['fields'][-1]['offset_bits'] == 48
            assert records['Zero']['size_bytes'] == 4
        entries.append(dict(name=name, request=request, result=result))
    with tempfile.TemporaryDirectory(prefix='layout-explorer-') as temporary:
        evidence = Path(temporary) / 'evidence.json'
        evidence.write_text(json.dumps(entries))
        wasm_metrics = None
        if args.wasm:
            requests = Path(temporary) / 'requests.json'
            requests.write_text(json.dumps([entry['request'] for entry in entries]))
            process = subprocess.run(['node', str(Path(__file__).with_name('run_wasm.cjs')), str(args.wasm.resolve()), str(requests)], capture_output=True, text=True, check=True, timeout=120)
            wasm = json.loads(process.stdout)
            assert wasm['results'] == [entry['result'] for entry in entries], 'Native/Wasm model fixture outputs differ'
            wasm_metrics = wasm['metrics']
        with evidence.open() as stream:
            raw = subprocess.run(['node', str(Path(__file__).with_name('explorer.test.cjs'))], stdin=stream, capture_output=True, text=True, timeout=60)
            if raw.returncode:
                raise RuntimeError(raw.stderr)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    report = json.loads(raw.stdout)
    report.update(native_sha256=hashlib.sha256(args.native.read_bytes()).hexdigest(), wasm_parity='passed' if args.wasm else 'not-run')
    if args.wasm:
        report.update(wasm_factory_sha256=hashlib.sha256(args.wasm.read_bytes()).hexdigest(), wasm_sha256=hashlib.sha256(args.wasm.with_suffix('.wasm').read_bytes()).hexdigest(), wasm_metrics=wasm_metrics)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print('Explorer model checks passed: ' + str(args.output))


if __name__ == '__main__':
    main()
