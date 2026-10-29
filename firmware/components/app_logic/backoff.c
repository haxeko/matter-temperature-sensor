#include "backoff.h"

void backoff_init(backoff_t *b, uint32_t base, uint32_t max)
{
    b->base = base ? base : 1;
    b->max = (max < b->base) ? b->base : max;
    b->next = b->base;
    b->attempts = 0;
}

uint32_t backoff_next(backoff_t *b)
{
    uint32_t d = b->next;
    b->attempts++;
    b->next = (b->next > b->max / 2) ? b->max : b->next * 2;
    return d;
}

void backoff_reset(backoff_t *b)
{
    b->next = b->base;
    b->attempts = 0;
}

uint32_t backoff_for_attempt(uint32_t base, uint32_t max, uint32_t n)
{
    backoff_t b;
    backoff_init(&b, base, max);
    uint32_t d = b.base;
    for (uint32_t i = 0; i < n && i < 32; i++) {
        d = backoff_next(&b);
    }
    return d;
}
