/* SPDX-License-Identifier: GPL-2.0-only
 * Independently authored syntax/layout aid, NOT an Apple CoreEntitlements header.
 * Public XNU uses CEContext_t by value in unselected pmap code-signing types.
 * This one-byte stand-in does not describe its real extent, alignment or ABI.
 * Production guards prohibit exposing any dependent declaration or layout.
 */
#ifndef PLATYDOC_COREENTITLEMENTS_LAYOUT_ONLY_API
#define PLATYDOC_COREENTITLEMENTS_LAYOUT_ONLY_API
#include <CoreEntitlements/CoreEntitlements.h>
typedef struct PlatydocUnavailableCEContext {
    unsigned char unavailable_storage[1];
} CEContext_t;
typedef struct PlatydocOpaqueCEKernelAPI CEKernelAPI_t;
#endif
