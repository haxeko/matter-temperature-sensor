/*
 * NVS persistence for app_cfg_t. One key per field so that adding a field in
 * a later firmware keeps older stored values readable.
 */
#include "app_config.h"

#include "esp_check.h"
#include "esp_log.h"
#include "nvs.h"
#include "sdkconfig.h"

static const char *TAG = "app_cfg";
static const char *NS = "app_cfg";

void app_config_defaults(app_cfg_t *out)
{
    const app_cfg_defaults_t d = {
        .meas_interval_s = CONFIG_APP_MEASURE_INTERVAL_S,
        .bat_interval_s = CONFIG_APP_BATTERY_INTERVAL_S,
        .temp_deadband_centi = CONFIG_APP_TEMP_DEADBAND_CENTI,
        .rh_deadband_centi = CONFIG_APP_RH_DEADBAND_CENTI,
#if CONFIG_APP_LED_DEFAULT_ENABLED
        .led_enabled = true,
#else
        .led_enabled = false,
#endif
        .tx_power_dbm = CONFIG_APP_THREAD_TX_POWER_DBM,
    };
    app_cfg_set_defaults(out, &d);
}

esp_err_t app_config_load(app_cfg_t *out)
{
    app_config_defaults(out);
    nvs_handle_t h;
    esp_err_t err = nvs_open(NS, NVS_READONLY, &h);
    if (err == ESP_ERR_NVS_NOT_FOUND) {
        ESP_LOGI(TAG, "no stored config, using defaults");
        return ESP_OK;
    }
    ESP_RETURN_ON_ERROR(err, TAG, "nvs_open");

    int16_t i16;
    uint16_t u16;
    uint32_t u32;
    uint8_t u8;
    int8_t i8;
    if (nvs_get_i16(h, "t_off", &i16) == ESP_OK && !app_cfg_set_temp_offset(out, i16)) {
        ESP_LOGW(TAG, "stored temp offset %d out of range, ignored", i16);
    }
    if (nvs_get_i16(h, "rh_off", &i16) == ESP_OK && !app_cfg_set_rh_offset(out, i16)) {
        ESP_LOGW(TAG, "stored RH offset %d out of range, ignored", i16);
    }
    if (nvs_get_u16(h, "meas_s", &u16) == ESP_OK && !app_cfg_set_meas_interval(out, u16)) {
        ESP_LOGW(TAG, "stored measurement interval %u out of range, ignored", u16);
    }
    if (nvs_get_u32(h, "bat_s", &u32) == ESP_OK && !app_cfg_set_bat_interval(out, (int32_t)u32)) {
        ESP_LOGW(TAG, "stored battery interval %lu out of range, ignored", (unsigned long)u32);
    }
    if (nvs_get_u16(h, "db_t", &u16) == ESP_OK && !app_cfg_set_temp_deadband(out, u16)) {
        ESP_LOGW(TAG, "stored temp deadband %u out of range, ignored", u16);
    }
    if (nvs_get_u16(h, "db_rh", &u16) == ESP_OK && !app_cfg_set_rh_deadband(out, u16)) {
        ESP_LOGW(TAG, "stored RH deadband %u out of range, ignored", u16);
    }
    if (nvs_get_u8(h, "led", &u8) == ESP_OK) {
        out->led_enabled = (u8 != 0);
    }
    if (nvs_get_i8(h, "txp", &i8) == ESP_OK && !app_cfg_set_tx_power(out, i8)) {
        ESP_LOGW(TAG, "stored TX power %d out of range, ignored", i8);
    }
    nvs_close(h);
    return ESP_OK;
}

esp_err_t app_config_save(const app_cfg_t *cfg, bool *written)
{
    const char *bad = NULL;
    if (written) {
        *written = false;
    }
    ESP_RETURN_ON_FALSE(app_cfg_is_valid(cfg, &bad), ESP_ERR_INVALID_ARG, TAG, "invalid field %s", bad);

    app_cfg_t stored;
    ESP_RETURN_ON_ERROR(app_config_load(&stored), TAG, "load");
    if (app_cfg_equal(&stored, cfg)) {
        return ESP_OK;  /* nothing changed: no flash write */
    }

    nvs_handle_t h;
    ESP_RETURN_ON_ERROR(nvs_open(NS, NVS_READWRITE, &h), TAG, "nvs_open");
    esp_err_t err = ESP_OK;
    if (stored.temp_offset_centi != cfg->temp_offset_centi) {
        err |= nvs_set_i16(h, "t_off", cfg->temp_offset_centi);
    }
    if (stored.rh_offset_centi != cfg->rh_offset_centi) {
        err |= nvs_set_i16(h, "rh_off", cfg->rh_offset_centi);
    }
    if (stored.meas_interval_s != cfg->meas_interval_s) {
        err |= nvs_set_u16(h, "meas_s", cfg->meas_interval_s);
    }
    if (stored.bat_interval_s != cfg->bat_interval_s) {
        err |= nvs_set_u32(h, "bat_s", cfg->bat_interval_s);
    }
    if (stored.temp_deadband_centi != cfg->temp_deadband_centi) {
        err |= nvs_set_u16(h, "db_t", cfg->temp_deadband_centi);
    }
    if (stored.rh_deadband_centi != cfg->rh_deadband_centi) {
        err |= nvs_set_u16(h, "db_rh", cfg->rh_deadband_centi);
    }
    if (stored.led_enabled != cfg->led_enabled) {
        err |= nvs_set_u8(h, "led", cfg->led_enabled ? 1 : 0);
    }
    if (stored.tx_power_dbm != cfg->tx_power_dbm) {
        err |= nvs_set_i8(h, "txp", cfg->tx_power_dbm);
    }
    if (err == ESP_OK) {
        err = nvs_commit(h);
    } else {
        err = ESP_FAIL;
    }
    nvs_close(h);
    if (err == ESP_OK && written) {
        *written = true;
    }
    return err;
}

esp_err_t app_config_erase(void)
{
    nvs_handle_t h;
    esp_err_t err = nvs_open(NS, NVS_READWRITE, &h);
    if (err == ESP_ERR_NVS_NOT_FOUND) {
        return ESP_OK;
    }
    ESP_RETURN_ON_ERROR(err, TAG, "nvs_open");
    err = nvs_erase_all(h);
    if (err == ESP_OK) {
        err = nvs_commit(h);
    }
    nvs_close(h);
    return err;
}
