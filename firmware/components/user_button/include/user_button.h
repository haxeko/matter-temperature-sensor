/*
 * USER/BOOT button (GPIO9) -> gesture events.
 *
 * Uses the Espressif `button` component (GPIO wake-up from light sleep, debounce)
 * and the pure gesture recognizer from app_logic/button_gesture.h.
 * The callback runs in the esp_timer task: keep it short and non-blocking.
 */
#pragma once

#include "esp_err.h"
#include "button_gesture.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef void (*user_button_cb_t)(bg_event_t event, void *ctx);

esp_err_t user_button_init(user_button_cb_t cb, void *ctx);

#ifdef __cplusplus
}
#endif
