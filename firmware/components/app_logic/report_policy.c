#include "report_policy.h"

void rp_init(rp_channel_t *ch, uint32_t deadband, uint32_t fail_threshold)
{
    ch->deadband = deadband;
    ch->fail_threshold = fail_threshold ? fail_threshold : 1;
    ch->has_published = false;
    ch->published_null = false;
    ch->last_published = 0;
    ch->consecutive_failures = 0;
}

static uint32_t abs_diff(int32_t a, int32_t b)
{
    return (a > b) ? (uint32_t)((int64_t)a - b) : (uint32_t)((int64_t)b - a);
}

rp_action_t rp_on_sample(rp_channel_t *ch, bool valid, int32_t value, bool force)
{
    if (!valid) {
        if (ch->consecutive_failures < UINT32_MAX) {
            ch->consecutive_failures++;
        }
        if (ch->consecutive_failures >= ch->fail_threshold &&
            !(ch->has_published && ch->published_null)) {
            ch->has_published = true;
            ch->published_null = true;
            return RP_NULL;
        }
        return RP_NONE;
    }

    ch->consecutive_failures = 0;
    if (!ch->has_published || ch->published_null || force ||
        abs_diff(value, ch->last_published) >= ch->deadband) {
        ch->has_published = true;
        ch->published_null = false;
        ch->last_published = value;
        return RP_VALUE;
    }
    return RP_NONE;
}
