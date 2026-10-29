/*
 * USER button gesture recognizer (pure C, time is passed in by the caller).
 *
 *  - short press   : one click (press <= click_max_ms) not followed by another
 *                    click within click_gap_ms                -> BG_EVT_SHORT
 *  - triple press  : three clicks, first press to third release
 *                    within triple_window_ms (2 s)            -> BG_EVT_TRIPLE
 *  - long press    : held >= long_ms (10 s)                   -> BG_EVT_LONG_ARMED
 *                    then released                            -> BG_EVT_LONG_RELEASED
 *                    (factory reset happens only on release)
 *  - stuck button  : held >= stuck_ms                         -> BG_EVT_LONG_CANCELLED
 *                    (release afterwards does nothing)
 *  - anything else (double click, 1.5..10 s press, slow
 *    triple)                                                  -> BG_EVT_IGNORED
 * Contact bounce is filtered by the GPIO button driver; presses shorter than
 * min_press_ms are additionally dropped as glitches.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    BG_EVT_NONE = 0,
    BG_EVT_SHORT,
    BG_EVT_TRIPLE,
    BG_EVT_LONG_ARMED,
    BG_EVT_LONG_RELEASED,
    BG_EVT_LONG_CANCELLED,
    BG_EVT_IGNORED,
} bg_event_t;

typedef struct {
    uint32_t min_press_ms;
    uint32_t click_max_ms;
    uint32_t click_gap_ms;
    uint32_t triple_window_ms;
    uint32_t long_ms;
    uint32_t stuck_ms;
} bg_config_t;

#define BG_CONFIG_DEFAULT { \
    .min_press_ms = 30, .click_max_ms = 1500, .click_gap_ms = 800, \
    .triple_window_ms = 2000, .long_ms = 10000, .stuck_ms = 60000 }

typedef struct {
    bg_config_t cfg;
    bool pressed;
    uint32_t press_t;
    uint8_t clicks;
    uint32_t group_start;
    uint32_t last_release;
    bool long_armed;
    bool long_cancelled;
} bg_state_t;

void bg_init(bg_state_t *s, const bg_config_t *cfg);
bg_event_t bg_on_press(bg_state_t *s, uint32_t now_ms);
bg_event_t bg_on_release(bg_state_t *s, uint32_t now_ms);
/* Resolve time-outs. Call at (or after) the deadline from bg_next_deadline(). */
bg_event_t bg_on_tick(bg_state_t *s, uint32_t now_ms);
/* True if a tick is needed; *deadline_ms is an absolute time. */
bool bg_next_deadline(const bg_state_t *s, uint32_t *deadline_ms);
const char *bg_event_str(bg_event_t e);

#ifdef __cplusplus
}
#endif
