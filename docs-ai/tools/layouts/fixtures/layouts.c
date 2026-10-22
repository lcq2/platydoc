/* SPDX-License-Identifier: GPL-2.0-only */
#include "types.h"

struct Conditional {
    char head;
#ifdef FLAG
    unsigned int present_when_defined;
#endif
#if FLAG
    unsigned long present_when_nonzero;
#endif
    char tail;
};

struct Inner { unsigned short value; unsigned char tag; };
union Payload { unsigned long wide; unsigned char bytes[9]; };
struct Outer {
    char lead;
    struct Inner rows[2][3];
    union Payload payload;
    void *opaque;
};

struct __attribute__((packed)) Packed {
    char prefix;
    unsigned int value;
};
struct __attribute__((packed, aligned(8))) PackedAligned {
    char prefix;
    unsigned int value;
};
#pragma pack(push, 2)
struct PragmaPacked { char prefix; unsigned int value; unsigned short tail; };
#pragma pack(pop)
struct ExplicitAligned { char first; unsigned int value __attribute__((aligned(16))); char tail; };

struct Anonymous {
    char lead;
    union { unsigned int word; unsigned char bytes[4]; };
    struct { unsigned short low; unsigned short high; };
    char tail;
};

struct Bits {
    unsigned int low : 3;
    unsigned int : 2;
    unsigned int high : 5;
    unsigned int : 0;
    unsigned int next : 9;
    unsigned char tail;
};
struct __attribute__((packed)) PackedBits {
    unsigned int low : 3;
    unsigned int high : 7;
    unsigned char tail;
};
struct Flexible { unsigned int length; unsigned char bytes[]; };

/* Distinct declarations from one expansion need distinct record identities. */
#define RECORD_PAIR struct MacroFirst { int first; }; struct MacroSecond { long second; };
RECORD_PAIR
