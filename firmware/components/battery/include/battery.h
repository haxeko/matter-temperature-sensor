/*
 * Per-cell voltage measurement: VBAT1 (ADC1_CH4) and VBAT2 (ADC1_CH3), each
 * through its own switched 470k/470k divider (both switches on GPIO12).
 */
#pragma once

#include <stdint.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

#define BATTERY_CELLS 2

typedef struct {
    uint32_t cell_mv[BATTERY_CELLS];   /* reconstructed cell voltage (divider ratio applied) */
    uint32_t sense_mv[BATTERY_CELLS];  /* calibrated voltage at the ADC pins */
    uint16_t samples;                  /* averaged conversions per channel */
} battery_reading_t;

/*
 * Blocks for ~40 ms (divider settling + conversions) with light sleep held off,
 * so the switches stay closed. Both cells are read in one session.
 * Returns ESP_ERR_NOT_SUPPORTED if no ADC calibration scheme can be created
 * (no uncalibrated value is ever reported).
 */
esp_err_t battery_measure(battery_reading_t *out);

/* Highest of the two readings (the cell that currently sustains the rail). */
uint32_t battery_best_cell_mv(const battery_reading_t *r);

#ifdef __cplusplus
}
#endif
