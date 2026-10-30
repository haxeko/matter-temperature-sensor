/*
 * TH-SENSOR-H2: Matter-over-Thread temperature/humidity sensor
 * (ESP32-H2-MINI-1, SHT40, 1 x CR2450, one TPS63900 buck-boost).
 *
 * Boot sequence:
 *   1. NVS, power guard state (reset reason, unstable-boot count)
 *   2. board GPIO, persisted configuration
 *   3. power management (automatic light sleep, tickless idle)
 *   4. cell voltage, guard decision before any radio activity (may deep-sleep)
 *   5. SHT40 presence check (a missing sensor only yields null values)
 *   6. controller queue, USER button, Matter data model, Matter start
 *   7. controller task, maintenance console
 */
#include <esp_err.h>
#include <esp_log.h>
#include <esp_pm.h>
#include <nvs_flash.h>
#include <soc/rtc.h>

#include "app_config.h"
#include "app_controller.h"
#include "battery.h"
#include "board.h"
#include "maint_console.h"
#include "matter_bridge.h"
#include "power_guard.h"
#include "sht40.h"
#include "user_button.h"

static const char *TAG = "app_main";

static void configure_power_management(void)
{
#if CONFIG_PM_ENABLE
    /* Same settings as the ESP-Matter icd_app example: fixed CPU frequency,
     * automatic light sleep when all tasks are blocked. */
    esp_pm_config_t pm = {};
    pm.max_freq_mhz = CONFIG_ESP_DEFAULT_CPU_FREQ_MHZ;
    pm.min_freq_mhz = CONFIG_ESP_DEFAULT_CPU_FREQ_MHZ;
#if CONFIG_FREERTOS_USE_TICKLESS_IDLE
    pm.light_sleep_enable = true;
#endif
    esp_err_t err = esp_pm_configure(&pm);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "esp_pm_configure: %s", esp_err_to_name(err));
    }
#endif
    if (rtc_clk_slow_src_get() == SOC_RTC_SLOW_CLK_SRC_XTAL32K) {
        ESP_LOGI(TAG, "RTC slow clock: external 32.768 kHz crystal");
    } else {
        ESP_LOGW(TAG, "RTC slow clock: internal RC (32 kHz crystal not running?)");
    }
}

extern "C" void app_main(void)
{
    /* No automatic erase on NVS errors: that would silently drop fabrics. */
    esp_err_t err = nvs_flash_init();
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "nvs_flash_init: %s", esp_err_to_name(err));
    }
    power_guard_init();

    ESP_ERROR_CHECK(board_init());

    app_cfg_t cfg;
    if (app_config_load(&cfg) != ESP_OK) {
        app_config_defaults(&cfg);
    }
    board_led_set_enabled(cfg.led_enabled);

    configure_power_management();

    battery_reading_t boot_bat = {};
    if (battery_measure(&boot_bat) == ESP_OK) {
        power_guard_check(true, battery_best_cell_mv(&boot_bat));
    } else {
        ESP_LOGW(TAG, "boot battery check without a reading (ADC error)");
        power_guard_check(false, 0);
    }

    if (sht40_init(nullptr) != ESP_OK) {
        ESP_LOGE(TAG, "SHT40 not responding; values will be published as null until it recovers");
    }

    ESP_ERROR_CHECK(app_controller_init(&cfg, &boot_bat));

    err = user_button_init(app_controller_on_button, nullptr);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "button init: %s", esp_err_to_name(err));
    }

    mb_config_t mcfg = {};
    mcfg.cb = app_controller_on_matter;
    mcfg.ctx = nullptr;
    mcfg.thread_tx_power_dbm = cfg.tx_power_dbm;
    mcfg.commissioning_window_s = CONFIG_APP_COMMISSIONING_WINDOW_S;
    err = mb_init(&mcfg);
    if (err == ESP_OK) {
        err = mb_start();
    }
    if (err != ESP_OK) {
        /* Keep sensor, console and factory-reset gesture usable. */
        ESP_LOGE(TAG, "Matter start failed: %s", esp_err_to_name(err));
        board_led_show(BOARD_LED_ERROR);
    }

    ESP_ERROR_CHECK(app_controller_start());

#if CONFIG_APP_CONSOLE_ENABLE
    maint_console_ops_t ops = {};
    app_controller_console_ops(&ops);
    err = maint_console_start(&ops);
    if (err != ESP_OK) {
        ESP_LOGW(TAG, "console not started: %s", esp_err_to_name(err));
    }
#endif
}
