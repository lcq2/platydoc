#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Focused pasted-token identity regression; no compiler is downloaded/built."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

SOURCE = '''#define CAT_(a,b) a##b
#define CAT(a,b) CAT_(a,b)
#if EXTRA
struct CAT(Unused,Record) { int ignored; };
#endif
#define POINTERS(name) typedef struct name *CAT(name,_one); typedef struct name *CAT(name,_two);
struct Leaf { int value; };
POINTERS(Leaf)
struct Root { struct Leaf embedded; Leaf_one a; Leaf_two b; int stable; };
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True); parser.add_argument('--wasm', type=Path, required=True)
    parser.add_argument('--previous-native', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); here = Path(__file__).resolve().parent
    cases = [{'target':'aarch64-apple-darwin','main':'/inputs/main.c','files':{'/inputs/main.c':SOURCE},'records':['Root'],'macros':{'EXTRA':str(flag)}} for flag in (0,1)]
    # Physical declarations keep precisely their previous IDs.
    ordinary = {'target':'aarch64-apple-darwin','main':'/inputs/ordinary.c','files':{'/inputs/ordinary.c':'struct Ordinary { int x; long y; };'}}
    cases.append(ordinary)
    cases.append({'target':'aarch64-apple-darwin','main':'/inputs/main.c','files':{
        '/inputs/main.c':'#define CAT(a,b) a##b\n#define MAKE(name) struct { int CAT(va,lue); } name;\nstruct Outer {\n#define FIELD a\n#include "repeat.h"\n#undef FIELD\n#define FIELD b\n#include "repeat.h"\n};',
        '/inputs/repeat.h':'MAKE(FIELD)\n'},'records':['Outer']})
    native = [json.loads(subprocess.run([str(args.native.resolve())],input=json.dumps(request),capture_output=True,text=True,check=True,timeout=30).stdout) for request in cases]
    with tempfile.TemporaryDirectory(prefix='pasted-identity-') as tmp:
        requests = Path(tmp)/'requests.json'; requests.write_text(json.dumps(cases))
        result = subprocess.run(['node',str(here/'run_wasm.cjs'),str(args.wasm.resolve()),str(requests)],capture_output=True,text=True,check=True,timeout=60)
    assert json.loads(result.stdout)['results'] == native, 'Native/Wasm responses differ'
    for result in native: assert result['status']=='ok' and not result['diagnostics']
    if args.previous_native:
        previous=json.loads(subprocess.run([str(args.previous_native.resolve())],input=json.dumps(ordinary),capture_output=True,text=True,check=True,timeout=30).stdout)
        assert previous['declarations']==native[2]['declarations'] and previous['records']==native[2]['records']
    repeated=[d for d in native[3]['declarations'] if d['kind']=='field' and d['name']=='value']
    assert len(repeated)==2 and repeated[0]['id']!=repeated[1]['id']
    declarations = [{d['name']:d for d in r['declarations']} for r in native[:2]]
    for name in ('Root','Leaf','Leaf_one','Leaf_two','embedded','a','b','stable'):
        assert declarations[0][name]['id']==declarations[1][name]['id'],name
    assert declarations[0]['Leaf_one']['id']!=declarations[0]['Leaf_two']['id']
    for name in ('Leaf_one','Leaf_two'):
        anchor=declarations[0][name]['source'];assert anchor['generated_token']==name
        assert anchor['spelling']['file']=='/inputs/main.c'
        assert anchor['expansions']
    # Shared contract normalization validates/recomputes every physical ID.
    entries=[{'profile':str(i),'request':r,'result':n} for i,(r,n) in enumerate(zip(cases,native))]
    source={'release':'synthetic','revision':'synthetic'}
    with tempfile.TemporaryFile() as stream:
        stream.write(json.dumps({'entries':entries,'source':source,'mapping':{'contract':'platydoc.layout-chapters','version':1,'source':source,'entries':[]},'partial':True}).encode());stream.seek(0)
        normalized=subprocess.run(['node',str(here.parent/'catalog_contracts.cjs')],stdin=stream,capture_output=True,text=True,check=True,timeout=30)
    assert len(json.loads(normalized.stdout)['documents'])==4
    args.output.write_text(json.dumps({'passed':True,'cases':4,'native_wasm':'equal','paste_ids_stable':True,'distinct_generated_aliases':True,'contracts':'passed'},indent=2)+'\n')
    print('Four focused identity cases passed native/Wasm and shared contracts')


if __name__=='__main__':main()
