# SPDX-License-Identifier: GPL-2.0-only
"""Source-identity and policy cases; no external compiler tool is downloaded."""
from fixtures import request


def cases():
    source = '''typedef __typeof__(TYPE_VALUE) Value;
typedef Value Alias;
struct Node;
typedef struct Node *NodeRef;
struct Node {
#if FLAG
 int conditional;
#endif
 Alias fixed;
 NodeRef next;
 int stable;
};
'''
    result = []
    for name, value, flag in [('narrow-undefined', '1', None), ('narrow-zero', '1', '0'), ('wide-one', '1LL', '1')]:
        r = request(source, macros={'TYPE_VALUE': value, 'FLAG': flag})
        r['trace_files'] = True
        result.append((name, r))
    result.extend([
        ('repeated-include', {'target': 'aarch64-apple-darwin', 'main': '/inputs/main.c', 'trace_files': True,
          'files': {'/inputs/main.c': 'struct A {\n#define FIELD a\n#include "repeat.h"\n#undef FIELD\n#define FIELD b\n#include "repeat.h"\n};',
                    '/inputs/repeat.h': 'struct { int x; } FIELD;'}}),
        ('scoped-records', request('void f(void) { struct Same { int x; }; } void g(void) { struct Same { char y; }; }')),
        ('ambiguous-selection', request('void f(void) { struct Same { int x; }; } void g(void) { struct Same { char y; }; }', records=['Same'])),
        ('anonymous-alias', request('typedef struct { int x; } Anonymous; typedef Anonymous Alias; struct Root { Alias values[2]; };')),
        ('token-paste', request('#define CAT_(a,b) a##b\n#define CAT(a,b) CAT_(a,b)\nstruct CAT(Rec,ord) { int x; };')),
        ('command-line-origin', request('struct Root { int FIELD; };', macros={'FIELD': 'renamed', 'UNRELATED': '0'})),
        ('implicit-alias', request('struct Root { __builtin_va_list args; };')),
        ('aligned-array-alias', request('typedef int A[2] __attribute__((aligned(16))); struct Root { A a; };')),
        ('aligned-record-alias', request('struct S { int x; }; typedef struct S A __attribute__((aligned(16))); struct Root { A a; };')),
        ('unicode-path', {'target': 'aarch64-apple-darwin', 'main': '/inputs/данные.c',
                          'files': {'/inputs/данные.c': 'struct Unicode { int value; };'}}),
    ])
    for flag in ['0', '1']:
        result.append(('macro-include-' + flag, {
            'target': 'aarch64-apple-darwin', 'main': '/inputs/main.c', 'trace_files': True,
            'macros': {'WHICH': flag}, 'files': {
                '/inputs/main.c': '#define DECL(name) struct {int x;} name;\nstruct Root {\n#if WHICH\n#include "repeat.h"\n#else\n#include "repeat.h"\n#endif\n};',
                '/inputs/repeat.h': 'DECL(item)'}}))
    return result
