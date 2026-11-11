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
 *   1. A software restart (factory reset, console reboot, flashing) clears the
 *      count.
 *   2. A reading in the new-cell range (>= fresh_mv) that is also at least
 *      recovery_mv above the last recorded attempt means the cell was replaced:
 *      clear. Both conditions are needed: Li-MnO2 has a flat curve, so a rise
 *      alone is what a worn cell shows after resting, and a high reading alone
 *      is what a new but cold cell shows on every boot of a brown-out loop.
 *   3. Cell below boot_min_mv: count an attempt and sleep (backoff).
 *   4. free_boots or more attempts did not reach "stable" and this is not the
 *      wake from a guard sleep: sleep (backoff). The first free_boots - 1
 *      early resets run normally: re-seating the cell, a reset button or a
 *      programmer reset look exactly like a supervisor reset.
 *   5. Otherwise run, counting this boot as an attempt until marked stable.
 * Without a cell reading (ADC or sense-path fault) rules 2 and 3 are skipped and
 * the recorded voltage is kept.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    GP_RESET_POWER_ON,     /* power-on, EN pin (supervisor), brown-out, unknown */
    GP_RESET_SOFTWARE,     /* esp_restart(), or a reset from the USB/JTAG host */
    GP_RESET_SLEEP_WAKE,   /* wake from the guard's own deep sleep (timer or button) */
    GP_RESET_FAULT,        /* panic / watchdog: counted like a power-on */
} gp_reset_t;

typedef struct {
    uint8_t unstable_boots;
    uint16_t last_best_mv;
} gp_state_t;

typedef struct {
    uint16_t boot_min_mv;
    uint16_t fresh_mv;     /* readings at or above this are in the new-cell range */
    uint16_t recovery_mv;  /* ... and must exceed the last attempt by this much */
    uint8_t free_boots;    /* attempts allowed before rule 4 backs off (>= 1) */
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

/* Updates *st (caller persists it when it changed). have_mv = false: no cell
 * reading is available, best_mv is ignored. */
gp_decision_t gp_decide(gp_state_t *st, const gp_config_t *cfg, gp_reset_t reset, bool have_mv, uint16_t best_mv);

/* Call once the device has run for the stable period. Returns true if *st changed. */
bool gp_mark_stable(gp_state_t *st);

#ifdef __cplusplus
}
#endif
