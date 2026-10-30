/*
 * Cell voltage measurement: VBAT (ADC1_CH4) through a switched 470k/470k
 * divider (switch on GPIO12). Rev B has one CR2450; the reading structure keeps
 * a per-cell array so that the battery model stays independent of the count.
 */
#pragma once

#include <stdint.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

#define BATTERY_CELLS 1

typedef struct {
    uint32_t cell_mv[BATTERY_CELLS];   /* reconstructed cell voltage (divider ratio applied) */
    uint32_t sense_mv[BATTERY_CELLS];  /* calibrated voltage at the ADC pins */
    uint16_t samples;                  /* averaged conversions per channel */
} battery_reading_t;

/*
 * Blocks for ~40 ms (divider settling + conversions) with light sleep held off,
 * so the switch stays closed.
 * Returns ESP_ERR_NOT_SUPPORTED if no ADC calibration scheme can be created
 * (no uncalibrated value is ever reported).
 */
esp_err_t battery_measure(battery_reading_t *out);

/* Highest cell reading (with one cell: that cell). */
uint32_t battery_best_cell_mv(const battery_reading_t *r);

#ifdef __cplusplus
}
#endif
