# SPDX-License-Identifier: GPL-2.0-only
"""Independent source fixtures for dependency evidence, not generated from traces."""
from copy import deepcopy


SOURCE = r'''#include "support.h"
struct Direct {
 char head;
#ifdef DEFINED_FLAG
 int present_when_defined;
#endif
 char tail;
};
struct Interacting {
 char head;
#if FLAG_A
#if FLAG_B
 long combined;
#endif
#endif
 char tail;
};
struct Leaf {
 char tag;
#if LEAF_EXTRA
 long payload;
#endif
};
typedef struct Leaf LeafAlias;
struct Embedded { char lead; LeafAlias items[COUNT]; };
struct PointerOnly { struct Leaf *link; };
#if TYPE_WIDE
typedef long Word;
#else
typedef int Word;
#endif
typedef Word WordAlias;
struct Aliased { WordAlias value; };
#if MACRO_WIDE
#define GENERATED_FIELD long generated;
#else
#define GENERATED_FIELD char generated;
#endif
struct Generated { GENERATED_FIELD };
enum Slots {
 FIRST,
#if ENUM_EXTRA
 EXTRA,
#endif
 SLOT_COUNT
};
struct EnumBound { int slots[SLOT_COUNT]; };
#if PACKED
#pragma pack(push, 1)
#else
#pragma pack(push, 8)
#endif
struct Packing { char head; long payload; };
#pragma pack(pop)
struct Alignment { char head; _Alignas(ALIGNMENT) char value; };
struct Width { unsigned value : WIDTH; unsigned tail : 1; };
struct NoEffect {
#if NOOP
#define UNUSED_INSIDE 1
#else
#define UNUSED_INSIDE 0
#endif
 int value;
};
struct Inactive {
 int live;
#if NEVER_ENABLED
 long unseen;
#endif
};
struct MissingBranch {
 int live;
#if NEED_MISSING_HEADER
#include "not-supplied.h"
 MissingType unavailable;
#endif
};
struct Unrelated { int value; };
/* The following are comments, not directives or declarations.
#if COMMENT_FLAG
struct Unrelated { long false_field; };
#endif
*/
static const char *comment_like = "#if STRING_FLAG";
static int unrelated_function(void) {
#if FUNCTION_ONLY
 return 1;
#else
 return 0;
#endif
}
'''

SUPPORT = r'''#ifndef DEPENDENCY_SUPPORT_H
#define DEPENDENCY_SUPPORT_H
/* A continued condition whose second flag is not evaluated with FIRST_GATE=0. */
#if FIRST_GATE && \
    SECOND_GATE
#define SUPPORT_VALUE 8
#elif FALLBACK_GATE
#define SUPPORT_VALUE 4
#else
#define SUPPORT_VALUE 2
#endif
struct DerivedBound { char values[SUPPORT_VALUE]; };
#endif
'''

BASE_MACROS = {
    'DEFINED_FLAG': None, 'FLAG_A': '0', 'FLAG_B': '0', 'LEAF_EXTRA': '0',
    'COUNT': '2', 'TYPE_WIDE': '0', 'MACRO_WIDE': '0', 'ENUM_EXTRA': '0',
    'PACKED': '0', 'ALIGNMENT': '1', 'WIDTH': '1', 'NOOP': '0',
    'NEVER_ENABLED': '0', 'NEED_MISSING_HEADER': '0', 'FUNCTION_ONLY': '0',
    'FIRST_GATE': '0', 'SECOND_GATE': '0', 'FALLBACK_GATE': '0',
}
ROOTS = [
    'Direct', 'Interacting', 'Embedded', 'PointerOnly', 'Aliased', 'Generated',
    'EnumBound', 'Packing', 'Alignment', 'Width', 'NoEffect', 'Inactive',
    'MissingBranch', 'Unrelated', 'DerivedBound',
]


def request(overrides=None):
    return {
        'target': 'aarch64-apple-darwin', 'main': '/inputs/dependencies.c',
        'files': {'/inputs/dependencies.c': SOURCE, '/inputs/support.h': SUPPORT},
        'macros': {**BASE_MACROS, **(overrides or {})}, 'records': ROOTS[:],
        'trace_files': True, 'trace_dependencies': True,
    }


def cases():
    variations = [
        ('dep-base', {}), ('dep-defined-zero', {'DEFINED_FLAG': '0'}),
        ('dep-defined-one', {'DEFINED_FLAG': '1'}),
        ('dep-a', {'FLAG_A': '1'}), ('dep-b', {'FLAG_B': '1'}),
        ('dep-ab', {'FLAG_A': '1', 'FLAG_B': '1'}),
        ('dep-leaf', {'LEAF_EXTRA': '1'}), ('dep-count', {'COUNT': '3'}),
        ('dep-alias', {'TYPE_WIDE': '1'}), ('dep-generated', {'MACRO_WIDE': '1'}),
        ('dep-enum', {'ENUM_EXTRA': '1'}), ('dep-packed', {'PACKED': '1'}),
        ('dep-aligned', {'ALIGNMENT': '16'}), ('dep-width', {'WIDTH': '9'}),
        ('dep-noop', {'NOOP': '1'}), ('dep-function', {'FUNCTION_ONLY': '1'}),
        ('dep-first', {'FIRST_GATE': '1'}), ('dep-second', {'SECOND_GATE': '1'}),
        ('dep-both-gates', {'FIRST_GATE': '1', 'SECOND_GATE': '1'}),
        ('dep-fallback', {'FALLBACK_GATE': '1'}),
        ('dep-missing', {'NEED_MISSING_HEADER': '1'}),
    ]
    result = [(name, request(overrides)) for name, overrides in variations]
    # Different macro insertion order must not affect evidence or identities.
    reordered = request()
    reordered['macros'] = dict(reversed(list(reordered['macros'].items())))
    result.append(('dep-reordered', reordered))
    # A pointer-only selection must not inherit its referent's storage controls.
    for name, value in [('dep-pointer-base', '0'), ('dep-pointer-leaf', '1')]:
        pointer = request({'LEAF_EXTRA': value})
        pointer['records'] = ['PointerOnly']
        result.append((name, pointer))
    return deepcopy(result)


# Byte size, byte alignment and field offsets in bits. These are independently
# derived from the ARM64 Darwin ABI and the source above, not compiler traces.
BASE_LAYOUTS = {
    'Direct': (2, 1, [0, 8]), 'Interacting': (2, 1, [0, 8]),
    'Leaf': (1, 1, [0]), 'Embedded': (3, 1, [0, 8]),
    'PointerOnly': (8, 8, [0]), 'Aliased': (4, 4, [0]),
    'Generated': (1, 1, [0]), 'EnumBound': (4, 4, [0]),
    'Packing': (16, 8, [0, 64]), 'Alignment': (2, 1, [0, 8]),
    'Width': (4, 4, [0, 1]), 'NoEffect': (4, 4, [0]),
    'Inactive': (4, 4, [0]), 'MissingBranch': (4, 4, [0]),
    'Unrelated': (4, 4, [0]), 'DerivedBound': (2, 1, [0]),
}
CHANGED_LAYOUTS = {
    'dep-defined-zero': {'Direct': (12, 4, [0, 32, 64])},
    'dep-defined-one': {'Direct': (12, 4, [0, 32, 64])},
    'dep-ab': {'Interacting': (24, 8, [0, 64, 128])},
    'dep-leaf': {'Leaf': (16, 8, [0, 64]), 'Embedded': (40, 8, [0, 64])},
    'dep-count': {'Embedded': (4, 1, [0, 8])},
    'dep-alias': {'Aliased': (8, 8, [0])},
    'dep-generated': {'Generated': (8, 8, [0])},
    'dep-enum': {'EnumBound': (8, 4, [0])},
    'dep-packed': {'Packing': (9, 1, [0, 8])},
    'dep-aligned': {'Alignment': (32, 16, [0, 128])},
    'dep-width': {'Width': (4, 4, [0, 9])},
    'dep-both-gates': {'DerivedBound': (8, 1, [0])},
    'dep-fallback': {'DerivedBound': (4, 1, [0])},
}


def validate(name, result):
    if name == 'dep-missing':
        assert result['status'] == 'error' and not result['records'], result
        assert any('not-supplied.h' in d['message'] for d in result['diagnostics'])
        return
    assert result['status'] == 'ok' and not result['diagnostics'], (name, result.get('diagnostics'))
    layouts = {**BASE_LAYOUTS, **CHANGED_LAYOUTS.get(name, {})}
    if name.startswith('dep-pointer-'):
        layouts = {'PointerOnly': BASE_LAYOUTS['PointerOnly']}
    records = {record['name']: record for record in result['records']}
    assert records.keys() == layouts.keys(), (name, records.keys(), layouts.keys())
    for record_name, (size, alignment, offsets) in layouts.items():
        record = records[record_name]
        assert (record['size_bytes'], record['alignment_bytes'], [field['offset_bits'] for field in record['fields']]) == (size, alignment, offsets), (name, record_name, record)
