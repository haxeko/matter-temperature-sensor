#include "app_config_limits.h"

#include <stddef.h>

static bool in_range(int32_t v, int32_t lo, int32_t hi)
{
    return v >= lo && v <= hi;
}

void app_cfg_set_defaults(app_cfg_t *c, const app_cfg_defaults_t *d)
{
    c->temp_offset_centi = 0;
    c->rh_offset_centi = 0;
    c->meas_interval_s = d->meas_interval_s;
    c->bat_interval_s = d->bat_interval_s;
    c->temp_deadband_centi = d->temp_deadband_centi;
    c->rh_deadband_centi = d->rh_deadband_centi;
    c->led_enabled = d->led_enabled;
    c->tx_power_dbm = d->tx_power_dbm;
}

bool app_cfg_is_valid(const app_cfg_t *c, const char **bad)
{
    const char *b = NULL;
    if (!in_range(c->temp_offset_centi, CFG_TEMP_OFFSET_MIN_CENTI, CFG_TEMP_OFFSET_MAX_CENTI)) {
        b = "temp_offset";
    } else if (!in_range(c->rh_offset_centi, CFG_RH_OFFSET_MIN_CENTI, CFG_RH_OFFSET_MAX_CENTI)) {
        b = "rh_offset";
    } else if (!in_range(c->meas_interval_s, CFG_MEAS_INTERVAL_MIN_S, CFG_MEAS_INTERVAL_MAX_S)) {
        b = "meas_interval";
    } else if (c->bat_interval_s < CFG_BAT_INTERVAL_MIN_S || c->bat_interval_s > CFG_BAT_INTERVAL_MAX_S) {
        b = "bat_interval";
    } else if (c->temp_deadband_centi > CFG_TEMP_DEADBAND_MAX_CENTI) {
        b = "temp_deadband";
    } else if (c->rh_deadband_centi > CFG_RH_DEADBAND_MAX_CENTI) {
        b = "rh_deadband";
    } else if (!in_range(c->tx_power_dbm, CFG_TX_POWER_MIN_DBM, CFG_TX_POWER_MAX_DBM)) {
        b = "tx_power";
    }
    if (bad) {
        *bad = b;
    }
    return b == NULL;
}

bool app_cfg_set_temp_offset(app_cfg_t *c, int32_t centi)
{
    if (!in_range(centi, CFG_TEMP_OFFSET_MIN_CENTI, CFG_TEMP_OFFSET_MAX_CENTI)) {
        return false;
    }
    c->temp_offset_centi = (int16_t)centi;
    return true;
}

bool app_cfg_set_rh_offset(app_cfg_t *c, int32_t centi)
{
    if (!in_range(centi, CFG_RH_OFFSET_MIN_CENTI, CFG_RH_OFFSET_MAX_CENTI)) {
        return false;
    }
    c->rh_offset_centi = (int16_t)centi;
    return true;
}

bool app_cfg_set_meas_interval(app_cfg_t *c, int32_t seconds)
{
    if (!in_range(seconds, CFG_MEAS_INTERVAL_MIN_S, CFG_MEAS_INTERVAL_MAX_S)) {
        return false;
    }
    c->meas_interval_s = (uint16_t)seconds;
    return true;
}

bool app_cfg_set_bat_interval(app_cfg_t *c, int32_t seconds)
{
    if (!in_range(seconds, CFG_BAT_INTERVAL_MIN_S, CFG_BAT_INTERVAL_MAX_S)) {
        return false;
    }
    c->bat_interval_s = (uint32_t)seconds;
    return true;
}

bool app_cfg_set_temp_deadband(app_cfg_t *c, int32_t centi)
{
    if (!in_range(centi, 0, CFG_TEMP_DEADBAND_MAX_CENTI)) {
        return false;
    }
    c->temp_deadband_centi = (uint16_t)centi;
    return true;
}

bool app_cfg_set_rh_deadband(app_cfg_t *c, int32_t centi)
{
    if (!in_range(centi, 0, CFG_RH_DEADBAND_MAX_CENTI)) {
        return false;
    }
    c->rh_deadband_centi = (uint16_t)centi;
    return true;
}

bool app_cfg_set_tx_power(app_cfg_t *c, int32_t dbm)
{
    if (!in_range(dbm, CFG_TX_POWER_MIN_DBM, CFG_TX_POWER_MAX_DBM)) {
        return false;
    }
    c->tx_power_dbm = (int8_t)dbm;
    return true;
}

bool app_cfg_equal(const app_cfg_t *a, const app_cfg_t *b)
{
    return a->temp_offset_centi == b->temp_offset_centi &&
           a->rh_offset_centi == b->rh_offset_centi &&
           a->meas_interval_s == b->meas_interval_s &&
           a->bat_interval_s == b->bat_interval_s &&
           a->temp_deadband_centi == b->temp_deadband_centi &&
           a->rh_deadband_centi == b->rh_deadband_centi &&
           a->led_enabled == b->led_enabled &&
           a->tx_power_dbm == b->tx_power_dbm;
}
