/*
 * Board support: GPIO setup, status LED patterns and the battery-sense switch.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>
#include "esp_err.h"
#include "board_pins.h"

#ifdef __cplusplus
extern "C" {
#endif

/* LED feedback patterns. All are short and bounded; there is no heartbeat. */
typedef enum {
    BOARD_LED_ACK = 0,          /* 1 x 40 ms: request accepted / measurement ok */
    BOARD_LED_ERROR,            /* 2 x 150 ms: sensor or operation error */
    BOARD_LED_WINDOW_OPEN,      /* 3 x 80 ms: commissioning window opened */
    BOARD_LED_COMMISSIONED,     /* 2 x 300 ms: commissioning complete */
    BOARD_LED_IDENTIFY,         /* 6 x 250 ms: Matter Identify */
    BOARD_LED_RESET_ARMED,      /* LED on until cleared: long press >= 10 s */
    BOARD_LED_RESET_GO,         /* 8 x 60 ms: factory reset accepted */
    BOARD_LED_OFF,              /* stop any pattern */
} board_led_pattern_t;

/* Configure all board GPIOs (LED, sense switch, unused pins). Call first. */
esp_err_t board_init(void);

/* Enable/disable LED feedback. RESET_ARMED / RESET_GO / IDENTIFY are shown
 * even when disabled because they confirm an explicit user/admin action. */
void board_led_set_enabled(bool enabled);
bool board_led_get_enabled(void);

/* Start a pattern (non-blocking). A new pattern replaces the running one.
 * Light sleep is blocked only while a pattern is running. */
void board_led_show(board_led_pattern_t pattern);

/* Battery sense divider switches (GPIO12 -> NMOS gates). */
void board_vbat_sense_enable(bool on);

#ifdef __cplusplus
}
#endif
