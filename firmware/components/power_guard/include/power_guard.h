/*
 * Boot-time protection against brown-out reset loops and against starting the
 * radio on exhausted cells (decision logic: app_logic/guard_policy.h).
 *
 * A CR2450 near end of life, or a cold one, can power the idle chip but
 * collapses during radio bursts. The TPS3839 supervisor then resets the module
 * through EN, which is a full power-on reset (RTC memory is lost, the reset
 * reason reads "power-on"), so the guard keeps its state in NVS. Unstable or
 * low-battery boots back off with exponentially growing deep sleep (timer, or
 * the USER button wakes the device earlier).
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>
#include "esp_system.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    esp_reset_reason_t reset_reason;
    uint32_t boot_count;         /* boots since the last power-on reset (RTC) */
    uint8_t unstable_boots;      /* run attempts not yet marked stable (NVS) */
    uint16_t last_best_mv;       /* best-cell voltage at the last attempt (NVS) */
    bool nvs_ok;
} power_guard_info_t;

/* Call right after nvs_flash_init(): reads the reset reason and NVS state. */
void power_guard_init(void);

/* Decide whether this boot may start the radio. have_mv = false when the
 * battery measurement failed (only the unstable-boot rule is applied then).
 * May not return (deep sleep). */
void power_guard_check(bool have_mv, uint32_t best_cell_mv);

/* Call after the device has run stably (APP_STABLE_AFTER_S). */
void power_guard_mark_stable(void);

void power_guard_get_info(power_guard_info_t *out);
const char *power_guard_reset_reason_str(esp_reset_reason_t r);

#ifdef __cplusplus
}
#endif
