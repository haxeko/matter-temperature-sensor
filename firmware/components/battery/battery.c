/*
 * Cell voltage measurement (ADC oneshot + calibration).
 */
#include "battery.h"

#include "board.h"
#include "esp_adc/adc_cali.h"
#include "esp_adc/adc_cali_scheme.h"
#include "esp_adc/adc_oneshot.h"
#include "esp_check.h"
#include "esp_log.h"
#include "esp_pm.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "battery";

#define VBAT_ADC_UNIT     ADC_UNIT_1
#define VBAT_ADC_ATTEN    ADC_ATTEN_DB_6  /* 0..~1.9 V, enough for 3.6 V / 2 */
#define VBAT_SAMPLES      8

static const adc_channel_t k_channels[BATTERY_CELLS] = {ADC_CHANNEL_4};

_Static_assert(BOARD_GPIO_VBAT_SENSE == 5 && BOARD_VBAT_ADC_CHANNEL == 4, "GPIO5 = ADC1_CH4");

static esp_err_t cali_create(adc_channel_t chan, adc_cali_handle_t *out)
{
#if ADC_CALI_SCHEME_CURVE_FITTING_SUPPORTED
    adc_cali_curve_fitting_config_t cfg = {
        .unit_id = VBAT_ADC_UNIT,
        .chan = chan,
        .atten = VBAT_ADC_ATTEN,
        .bitwidth = ADC_BITWIDTH_DEFAULT,
    };
    return adc_cali_create_scheme_curve_fitting(&cfg, out);
#elif ADC_CALI_SCHEME_LINE_FITTING_SUPPORTED
    (void)chan;
    adc_cali_line_fitting_config_t cfg = {
        .unit_id = VBAT_ADC_UNIT,
        .atten = VBAT_ADC_ATTEN,
        .bitwidth = ADC_BITWIDTH_DEFAULT,
    };
    return adc_cali_create_scheme_line_fitting(&cfg, out);
#else
    (void)chan;
    (void)out;
    return ESP_ERR_NOT_SUPPORTED;
#endif
}

static void cali_delete(adc_cali_handle_t h)
{
#if ADC_CALI_SCHEME_CURVE_FITTING_SUPPORTED
    adc_cali_delete_scheme_curve_fitting(h);
#elif ADC_CALI_SCHEME_LINE_FITTING_SUPPORTED
    adc_cali_delete_scheme_line_fitting(h);
#else
    (void)h;
#endif
}

static esp_err_t read_channel(adc_oneshot_unit_handle_t unit, adc_channel_t chan, uint32_t *mv_out,
                              uint16_t *samples)
{
    const adc_oneshot_chan_cfg_t ch_cfg = {
        .atten = VBAT_ADC_ATTEN,
        .bitwidth = ADC_BITWIDTH_DEFAULT,
    };
    ESP_RETURN_ON_ERROR(adc_oneshot_config_channel(unit, chan, &ch_cfg), TAG, "channel %d", chan);
    adc_cali_handle_t cali = NULL;
    esp_err_t err = cali_create(chan, &cali);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "no ADC calibration scheme (%s); battery value not reported", esp_err_to_name(err));
        return ESP_ERR_NOT_SUPPORTED;
    }
    int32_t sum = 0;
    int n = 0;
    for (int i = 0; i < VBAT_SAMPLES; i++) {
        int mv = 0;
        if (adc_oneshot_get_calibrated_result(unit, cali, chan, &mv) == ESP_OK) {
            sum += mv;
            n++;
        }
    }
    cali_delete(cali);
    if (n == 0) {
        return ESP_FAIL;
    }
    *mv_out = (uint32_t)((sum + n / 2) / n);
    *samples = (uint16_t)n;
    return ESP_OK;
}

esp_err_t battery_measure(battery_reading_t *out)
{
    ESP_RETURN_ON_FALSE(out, ESP_ERR_INVALID_ARG, TAG, "null out");
    esp_err_t err = ESP_OK;
    adc_oneshot_unit_handle_t unit = NULL;

#if CONFIG_PM_ENABLE
    static esp_pm_lock_handle_t s_lock;
    if (!s_lock) {
        ESP_RETURN_ON_ERROR(esp_pm_lock_create(ESP_PM_NO_LIGHT_SLEEP, 0, "vbat", &s_lock), TAG, "pm lock");
    }
    esp_pm_lock_acquire(s_lock);
#endif

    board_vbat_sense_enable(true);
    vTaskDelay(pdMS_TO_TICKS(BOARD_VBAT_SETTLE_MS));

    const adc_oneshot_unit_init_cfg_t unit_cfg = {
        .unit_id = VBAT_ADC_UNIT,
        .ulp_mode = ADC_ULP_MODE_DISABLE,
    };
    err = adc_oneshot_new_unit(&unit_cfg, &unit);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "adc unit: %s", esp_err_to_name(err));
        unit = NULL;
        goto out;
    }
    for (int c = 0; c < BATTERY_CELLS && err == ESP_OK; c++) {
        err = read_channel(unit, k_channels[c], &out->sense_mv[c], &out->samples);
        if (err == ESP_OK) {
            out->cell_mv[c] = out->sense_mv[c] * BOARD_VBAT_DIVIDER_NUM / BOARD_VBAT_DIVIDER_DEN;
        }
    }
    if (err == ESP_OK) {
        ESP_LOGI(TAG, "VBAT %lu mV (%u samples)", (unsigned long)out->cell_mv[0], out->samples);
    }

out:
    if (unit) {
        adc_oneshot_del_unit(unit);
    }
    board_vbat_sense_enable(false);
#if CONFIG_PM_ENABLE
    esp_pm_lock_release(s_lock);
#endif
    return err;
}

uint32_t battery_best_cell_mv(const battery_reading_t *r)
{
    uint32_t best = 0;
    for (int c = 0; c < BATTERY_CELLS; c++) {
        if (r->cell_mv[c] > best) {
            best = r->cell_mv[c];
        }
    }
    return best;
}
