/*
 * Application controller: one task, one event queue, all scheduling.
 *
 *  - periodic SHT40 measurement (default 60 s) with retry/backoff
 *  - periodic battery measurement (default 6 h)
 *  - USER button gestures, Matter events, maintenance console requests
 * Waiting is done with xQueueReceive() timeouts, so the idle task (and thus
 * automatic light sleep) runs whenever nothing is due.
 */
#pragma once

#include "app_config_limits.h"
#include "battery.h"
#include "button_gesture.h"
#include "maint_console.h"
#include "matter_bridge.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Create the queue and state. `boot_battery` may be NULL. */
esp_err_t app_controller_init(const app_cfg_t *cfg, const battery_reading_t *boot_battery);

/* Start the controller task (after Matter has been started). */
esp_err_t app_controller_start(void);

/* Event sinks (non-blocking, callable from any task). */
void app_controller_on_button(bg_event_t ev, void *ctx);
void app_controller_on_matter(mb_event_t ev, void *ctx);

/* Console operations implemented by the controller. */
void app_controller_console_ops(maint_console_ops_t *ops);

#ifdef __cplusplus
}
#endif
