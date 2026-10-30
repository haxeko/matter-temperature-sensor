/*
 * Boot guard decision logic (pure C, unit tested on the host).
 *
 * Why it exists: near end of life the coin cell can power the idle chip but
 * collapse during radio bursts. The 3V3 supervisor (TPS3839) then pulls EN low,
 * which is a full power-on reset: RTC memory is lost and the reset reason reads
 * "power-on". Without persistent state the device would boot, attach, brown
 * out and repeat, draining the cell. The state below is kept in NVS:
 *
 *   unstable_boots  run attempts that did not reach "stable" (default 10 min)
 *   last_best_mv    cell voltage recorded at the last attempt (name from Rev A,
 *                   two cells: the higher of the two)
 *
 * Rules (gp_decide):
 *   1. A software restart (factory reset, console reboot) clears the count.
 *   2. A cell reading >= last_best_mv + recovery_mv means a new cell: clear.
 *   3. Cell below boot_min_mv: count an attempt and sleep (backoff).
 *   4. Count > 0 and this is not the wake from a guard sleep: sleep (backoff).
 *   5. Otherwise run, counting this boot as an attempt until marked stable.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    GP_RESET_POWER_ON,     /* power-on, EN pin (supervisor), brown-out, unknown */
    GP_RESET_SOFTWARE,     /* esp_restart() */
    GP_RESET_SLEEP_WAKE,   /* wake from the guard's own deep sleep (timer or button) */
    GP_RESET_FAULT,        /* panic / watchdog: counted like a power-on */
} gp_reset_t;

typedef struct {
    uint8_t unstable_boots;
    uint16_t last_best_mv;
} gp_state_t;

typedef struct {
    uint16_t boot_min_mv;
    uint16_t recovery_mv;
    uint32_t backoff_min_s;
    uint32_t backoff_max_s;
} gp_config_t;

typedef enum {
    GP_RUN = 0,
    GP_SLEEP_LOW_BATTERY,
    GP_SLEEP_UNSTABLE,
} gp_action_t;

typedef struct {
    gp_action_t action;
    uint32_t sleep_s;      /* valid for the sleep actions */
    bool cleared;          /* rule 1 or 2 cleared the count */
} gp_decision_t;

/* Updates *st (caller persists it when it changed). */
gp_decision_t gp_decide(gp_state_t *st, const gp_config_t *cfg, gp_reset_t reset, uint16_t best_mv);

/* Call once the device has run for the stable period. Returns true if *st changed. */
bool gp_mark_stable(gp_state_t *st);

#ifdef __cplusplus
}
#endif
