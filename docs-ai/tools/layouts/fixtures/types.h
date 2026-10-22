/* SPDX-License-Identifier: GPL-2.0-only */
#ifndef LAYOUT_FIXTURE_TYPES_H
#define LAYOUT_FIXTURE_TYPES_H
_Static_assert(sizeof(unsigned int) == 4, "fixture requires 32-bit int");
_Static_assert(sizeof(unsigned long) == 8, "fixture requires 64-bit long");
_Static_assert(sizeof(void *) == 8, "fixture requires 64-bit pointers");
#endif
