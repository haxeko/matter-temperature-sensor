/*
 * Saturating exponential backoff (pure C).
 * Used for sensor read retries and for the brownout/low-battery boot guard.
 */
#pragma once

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    uint32_t base;      /* first delay */
    uint32_t max;       /* saturation value */
    uint32_t next;      /* delay returned by the next call */
    uint32_t attempts;  /* calls since the last reset */
} backoff_t;

void backoff_init(backoff_t *b, uint32_t base, uint32_t max);

/* Return the current delay and double it for the next call (saturating). */
uint32_t backoff_next(backoff_t *b);

void backoff_reset(backoff_t *b);

/* Stateless form: delay for the n-th consecutive event (n >= 1). */
uint32_t backoff_for_attempt(uint32_t base, uint32_t max, uint32_t n);

#ifdef __cplusplus
}
#endif
