/*
 * Battery state estimation for one CR2450 behind one TPS63900 (pure C).
 *
 * What is measured: the cell's terminal voltage (VBAT) through a switched
 * divider while the chip is awake for the measurement. The cell carries that
 * load through the converter, so it reads below its rest voltage by the load
 * current times its internal resistance, which grows with age and with cold.
 * The estimate below is therefore an indication, not a fuel gauge, and its
 * thresholds are bring-up tunables (Kconfig).
 *
 * Li-MnO2 coin cells have a flat voltage curve; end of life under radio
 * bursts is set by internal resistance (TI SWRA349), which a voltage reading
 * does not see. The power model (docs/power_budget.md) predicts that reports
 * start to fail while a large part of the capacity is still left, so the
 * Warning/Critical thresholds are deliberately high.
 *
 * The logic keeps per-position arrays (BAT_CELL_COUNT; Rev A had two cells).
 * With one cell the pack is that cell.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define BAT_CELL_COUNT 1

/* Values match Matter PowerSource BatChargeLevelEnum. */
typedef enum {
    BAT_LEVEL_OK = 0,
    BAT_LEVEL_WARNING = 1,
    BAT_LEVEL_CRITICAL = 2,
} bat_level_t;

typedef struct {
    uint16_t present_mv;       /* a cell is present above this voltage */
    uint8_t warn_enter_half;   /* pack charge (half-percent) below which -> WARNING */
    uint8_t warn_exit_half;    /* back to OK at/above this (and every cell present) */
    uint8_t crit_enter_half;   /* pack charge below which -> CRITICAL */
    uint8_t crit_exit_half;    /* CRITICAL -> WARNING at/above this */
    uint16_t crit_cell_mv;     /* best cell below this -> CRITICAL regardless of charge */
    uint16_t crit_cell_exit_mv;
} bat_policy_t;

/* warn/crit in percent; exit thresholds add 5 % / 50 mV of hysteresis. */
#define BAT_POLICY_INIT(present, warn_pct, crit_pct)                                         \
    { .present_mv = (present), .warn_enter_half = (uint8_t)((warn_pct) * 2),               \
      .warn_exit_half = (uint8_t)((warn_pct) * 2 + 10), .crit_enter_half = (uint8_t)((crit_pct) * 2), \
      .crit_exit_half = (uint8_t)((crit_pct) * 2 + 10), .crit_cell_mv = 2600, .crit_cell_exit_mv = 2650 }

typedef struct {
    uint16_t cell_mv[BAT_CELL_COUNT];
    bool present[BAT_CELL_COUNT];
    uint8_t cell_half_pct[BAT_CELL_COUNT];
    uint8_t cells_present;
    uint16_t best_mv;          /* highest present cell, 0 if none */
    uint8_t pack_half_pct;     /* mean over all positions, an empty position counts 0 */
} bat_pack_t;

typedef struct {
    bool initialized;
    bat_level_t level;
} bat_state_t;

/* Piece-wise rest-voltage table, result in Matter half-percent units (0..200). */
uint8_t bat_half_percent_from_cell_mv(uint32_t cell_mv);

/* Hysteresis on downward/upward percentage changes (jitter suppression). */
uint8_t bat_filter_half_percent(bool have_last, uint8_t last, uint8_t fresh);

/* Per-cell presence and percentage, pack aggregate. */
void bat_pack_from_cells(bat_pack_t *out, const uint32_t cell_mv[BAT_CELL_COUNT], uint16_t present_mv);

/* Charge level of the pack with hysteresis; the first call classifies directly.
 * No cell present is CRITICAL; with BAT_CELL_COUNT > 1 a missing cell is at least
 * WARNING. With one cell and no other supply, "no cell" while running means the
 * reading is wrong (divider, switch or ADC fault), which CRITICAL also flags. */
bat_level_t bat_pack_update(bat_state_t *st, const bat_policy_t *pol, const bat_pack_t *pack);

#ifdef __cplusplus
}
#endif
