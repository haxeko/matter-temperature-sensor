/*
 * Application-side publish policy for one measured quantity (pure C).
 *
 * Matter subscriptions report every attribute change (subject to the
 * subscriber's MinInterval). Publishing each 0.01 unit of sensor noise would
 * wake the radio every measurement, so the application only writes a new
 * value to the data model when it moved by at least `deadband` from the last
 * published one (or on an explicit user request). Slow drifts below the
 * deadband accumulate relative to the last published value and are still
 * published once they exceed it.
 *
 * After `fail_threshold` consecutive invalid samples the value is published
 * as null so that a controller never shows an old value as current.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    RP_NONE = 0,      /* nothing to publish */
    RP_VALUE,         /* publish `value` */
    RP_NULL,          /* publish null */
} rp_action_t;

typedef struct {
    uint32_t deadband;          /* in the same unit as the values (e.g. centi-degC) */
    uint32_t fail_threshold;    /* consecutive failures before publishing null (>= 1) */
    bool has_published;         /* false until the first publish */
    bool published_null;
    int32_t last_published;
    uint32_t consecutive_failures;
} rp_channel_t;

void rp_init(rp_channel_t *ch, uint32_t deadband, uint32_t fail_threshold);

/* Feed one sample. `force` publishes a valid value even inside the deadband. */
rp_action_t rp_on_sample(rp_channel_t *ch, bool valid, int32_t value, bool force);

#ifdef __cplusplus
}
#endif
