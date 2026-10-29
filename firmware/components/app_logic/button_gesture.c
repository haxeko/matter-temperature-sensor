#include "button_gesture.h"

#include <string.h>

/* All time arithmetic is modulo 2^32 so a wrapping millisecond counter works. */
static uint32_t elapsed(uint32_t now, uint32_t then)
{
    return now - then;
}

void bg_init(bg_state_t *s, const bg_config_t *cfg)
{
    static const bg_config_t def = BG_CONFIG_DEFAULT;
    memset(s, 0, sizeof(*s));
    s->cfg = cfg ? *cfg : def;
}

/* A click group ends when no new press follows within click_gap_ms. The
 * 2 s triple window is checked on the third release, so three slow clicks
 * are ignored as a whole instead of turning the last one into a short press. */
static bool group_expired(const bg_state_t *s, uint32_t now)
{
    return s->clicks > 0 && !s->pressed && elapsed(now, s->last_release) >= s->cfg.click_gap_ms;
}

static bg_event_t finalize_group(bg_state_t *s)
{
    uint8_t clicks = s->clicks;
    s->clicks = 0;
    if (clicks == 0) {
        return BG_EVT_NONE;
    }
    return (clicks == 1) ? BG_EVT_SHORT : BG_EVT_IGNORED;
}

bg_event_t bg_on_press(bg_state_t *s, uint32_t now_ms)
{
    if (s->pressed) {
        return BG_EVT_NONE;
    }
    bg_event_t ev = BG_EVT_NONE;
    if (group_expired(s, now_ms)) {
        ev = finalize_group(s);   /* caller missed the tick: resolve now */
    }
    s->pressed = true;
    s->press_t = now_ms;
    s->long_armed = false;
    s->long_cancelled = false;
    if (s->clicks == 0) {
        s->group_start = now_ms;
    }
    return ev;
}

bg_event_t bg_on_release(bg_state_t *s, uint32_t now_ms)
{
    if (!s->pressed) {
        return BG_EVT_NONE;
    }
    s->pressed = false;
    uint32_t dur = elapsed(now_ms, s->press_t);

    if (s->long_cancelled) {           /* already reported as stuck */
        s->long_cancelled = false;
        s->clicks = 0;
        return BG_EVT_NONE;
    }
    if (dur >= s->cfg.stuck_ms) {      /* no tick arrived during a stuck press */
        s->long_armed = false;
        s->clicks = 0;
        return BG_EVT_LONG_CANCELLED;
    }
    if (s->long_armed || dur >= s->cfg.long_ms) {
        s->long_armed = false;
        s->clicks = 0;
        return BG_EVT_LONG_RELEASED;
    }
    if (dur < s->cfg.min_press_ms) {
        return BG_EVT_NONE;            /* glitch, not counted */
    }
    if (dur > s->cfg.click_max_ms) {
        s->clicks = 0;
        return BG_EVT_IGNORED;         /* medium press: no action */
    }
    s->clicks++;
    s->last_release = now_ms;
    if (s->clicks >= 3) {
        bool in_window = elapsed(now_ms, s->group_start) <= s->cfg.triple_window_ms;
        s->clicks = 0;
        return in_window ? BG_EVT_TRIPLE : BG_EVT_IGNORED;
    }
    return BG_EVT_NONE;
}

bg_event_t bg_on_tick(bg_state_t *s, uint32_t now_ms)
{
    if (s->pressed) {
        uint32_t dur = elapsed(now_ms, s->press_t);
        if (!s->long_cancelled && dur >= s->cfg.stuck_ms) {
            s->long_cancelled = true;
            s->long_armed = false;
            s->clicks = 0;
            return BG_EVT_LONG_CANCELLED;
        }
        if (!s->long_armed && !s->long_cancelled && dur >= s->cfg.long_ms) {
            s->long_armed = true;
            s->clicks = 0;
            return BG_EVT_LONG_ARMED;
        }
        return BG_EVT_NONE;
    }
    if (group_expired(s, now_ms)) {
        return finalize_group(s);
    }
    return BG_EVT_NONE;
}

bool bg_next_deadline(const bg_state_t *s, uint32_t *deadline_ms)
{
    if (s->pressed) {
        if (s->long_cancelled) {
            return false;
        }
        *deadline_ms = s->press_t + (s->long_armed ? s->cfg.stuck_ms : s->cfg.long_ms);
        return true;
    }
    if (s->clicks > 0) {
        *deadline_ms = s->last_release + s->cfg.click_gap_ms;
        return true;
    }
    return false;
}

const char *bg_event_str(bg_event_t e)
{
    switch (e) {
    case BG_EVT_NONE: return "none";
    case BG_EVT_SHORT: return "short";
    case BG_EVT_TRIPLE: return "triple";
    case BG_EVT_LONG_ARMED: return "long-armed";
    case BG_EVT_LONG_RELEASED: return "long-released";
    case BG_EVT_LONG_CANCELLED: return "long-cancelled";
    case BG_EVT_IGNORED: return "ignored";
    }
    return "?";
}
