/*
 * User/maintenance configuration model and its limits (pure C).
 * Persistence lives in components/app_config (NVS); this file only defines
 * the values, defaults and validation so they can be unit tested on the host.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Calibration offsets (added to the sensor value before publishing). */
#define CFG_TEMP_OFFSET_MIN_CENTI   (-500)    /* -5.00 degC */
#define CFG_TEMP_OFFSET_MAX_CENTI   500       /* +5.00 degC */
#define CFG_RH_OFFSET_MIN_CENTI     (-1000)   /* -10.00 %RH */
#define CFG_RH_OFFSET_MAX_CENTI     1000      /* +10.00 %RH */

#define CFG_MEAS_INTERVAL_MIN_S     10
#define CFG_MEAS_INTERVAL_MAX_S     3600
#define CFG_BAT_INTERVAL_MIN_S      600
#define CFG_BAT_INTERVAL_MAX_S      86400

#define CFG_TEMP_DEADBAND_MAX_CENTI 200       /* 2.00 degC */
#define CFG_RH_DEADBAND_MAX_CENTI   1000      /* 10.00 %RH */

/* 802.15.4 TX power. The upper bound is a power-path limit, not a radio
 * limit: above ~+8 dBm the ESP32-H2 draws more than the TPS63900 100 mA input
 * limit can supply from discharged cells (docs/power_budget.md). */
#define CFG_TX_POWER_MIN_DBM        (-24)
#define CFG_TX_POWER_MAX_DBM        8

typedef struct {
    int16_t temp_offset_centi;
    int16_t rh_offset_centi;
    uint16_t meas_interval_s;
    uint32_t bat_interval_s;
    uint16_t temp_deadband_centi;
    uint16_t rh_deadband_centi;
    bool led_enabled;
    int8_t tx_power_dbm;
} app_cfg_t;

typedef struct {
    uint16_t meas_interval_s;
    uint32_t bat_interval_s;
    uint16_t temp_deadband_centi;
    uint16_t rh_deadband_centi;
    bool led_enabled;
    int8_t tx_power_dbm;
} app_cfg_defaults_t;

void app_cfg_set_defaults(app_cfg_t *c, const app_cfg_defaults_t *d);

/* Return true if every field is inside its limits; else *bad names the field. */
bool app_cfg_is_valid(const app_cfg_t *c, const char **bad);

/* Setters return false (and leave the config unchanged) for out-of-range input. */
bool app_cfg_set_temp_offset(app_cfg_t *c, int32_t centi);
bool app_cfg_set_rh_offset(app_cfg_t *c, int32_t centi);
bool app_cfg_set_meas_interval(app_cfg_t *c, int32_t seconds);
bool app_cfg_set_bat_interval(app_cfg_t *c, int32_t seconds);
bool app_cfg_set_temp_deadband(app_cfg_t *c, int32_t centi);
bool app_cfg_set_rh_deadband(app_cfg_t *c, int32_t centi);
bool app_cfg_set_tx_power(app_cfg_t *c, int32_t dbm);

bool app_cfg_equal(const app_cfg_t *a, const app_cfg_t *b);

#ifdef __cplusplus
}
#endif
