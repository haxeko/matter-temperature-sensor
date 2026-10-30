/*
 * Application controller (see app_controller.h).
 */
#include "app_controller.h"

#include <inttypes.h>
#include <stdio.h>
#include <string.h>

#include "app_config.h"
#include "backoff.h"
#include "battery_model.h"
#include "board.h"
#include "esp_log.h"
#include "esp_system.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/semphr.h"
#include "freertos/task.h"
#include "matter_scale.h"
#include "power_guard.h"
#include "report_policy.h"
#include "sdkconfig.h"
#include "sht40.h"

static const char *TAG = "app";

typedef enum {
    EV_MEASURE,          /* a = 1: console (no rate limit), 0: button */
    EV_BATTERY,
    EV_BUTTON,           /* a = bg_event_t */
    EV_MATTER,           /* a = mb_event_t */
    EV_HEATER,           /* a = sht40_heater_t */
    EV_FACTORY_RESET,
    EV_RESCHEDULE,       /* configuration changed */
} ev_type_t;

typedef struct {
    ev_type_t type;
    int32_t a;
} app_ev_t;

typedef struct {
    bool have_sample;
    int64_t t_us;
    sht40_sample_t sample;
    esp_err_t last_err;
    sht40_diag_t last_diag;
    uint32_t ok_count;
    uint32_t fail_count;
    mx_nullable_i16_t published_t;
    mx_nullable_u16_t published_rh;
    bool any_published;
} meas_state_t;

typedef struct {
    bool have_reading;
    int64_t t_us;
    battery_reading_t reading;
    bat_pack_t pack;
    uint8_t half_pct;            /* filtered pack charge, as published */
    bool have_reported_pct;
    esp_err_t last_err;
} batt_state_t;

static QueueHandle_t s_queue;
static SemaphoreHandle_t s_lock;            /* protects everything below */
static app_cfg_t s_cfg;
static meas_state_t s_meas;
static batt_state_t s_batt;
static bat_state_t s_bat_model;
static rp_channel_t s_ch_t;
static rp_channel_t s_ch_rh;
static backoff_t s_retry;
static int64_t s_next_meas_us;
static int64_t s_next_bat_us;
static int64_t s_heater_holdoff_until_us;
static int64_t s_last_manual_us = INT64_MIN / 2;
static int64_t s_stable_at_us;
static bool s_stable_marked;

_Static_assert(BAT_CELL_COUNT == 1, "logging and status print one cell (Rev B)");
static const bat_policy_t k_bat_policy =
    BAT_POLICY_INIT(CONFIG_APP_BAT_CELL_PRESENT_MV, CONFIG_APP_BAT_WARN_PCT, CONFIG_APP_BAT_CRIT_PCT);

#define LOCK()   xSemaphoreTake(s_lock, portMAX_DELAY)
#define UNLOCK() xSemaphoreGive(s_lock)

static int64_t now_us(void)
{
    return esp_timer_get_time();
}

static bool post(ev_type_t type, int32_t a)
{
    if (!s_queue) {
        return false;
    }
    app_ev_t ev = {.type = type, .a = a};
    if (xQueueSend(s_queue, &ev, 0) != pdTRUE) {
        ESP_LOGW(TAG, "event queue full, dropped event %d", type);
        return false;
    }
    return true;
}

/* ---------------------------------------------------------------- measure */

static void do_measure(bool manual)
{
    int64_t t = now_us();
    if (t < s_heater_holdoff_until_us) {
        ESP_LOGW(TAG, "heater recovery hold-off: measurement not published");
        s_next_meas_us = s_heater_holdoff_until_us;
        return;
    }

    sht40_sample_t smp = {0};
    sht40_diag_t diag = {0};
    esp_err_t err = sht40_measure(&smp, &diag);
    const bool valid = (err == ESP_OK);

    LOCK();
    const app_cfg_t cfg = s_cfg;
    s_ch_t.deadband = cfg.temp_deadband_centi;
    s_ch_rh.deadband = cfg.rh_deadband_centi;
    mx_nullable_i16_t vt = mx_temperature(valid, smp.temp_milli_c, cfg.temp_offset_centi);
    mx_nullable_u16_t vh = mx_humidity(valid, smp.rh_milli_pct, cfg.rh_offset_centi);
    rp_action_t at = rp_on_sample(&s_ch_t, valid, vt.value, manual);
    rp_action_t ah = rp_on_sample(&s_ch_rh, valid, vh.value, manual);

    s_meas.last_err = err;
    s_meas.last_diag = diag;
    if (valid) {
        s_meas.have_sample = true;
        s_meas.t_us = t;
        s_meas.sample = smp;
        s_meas.ok_count++;
    } else {
        s_meas.fail_count++;
    }
    if (at != RP_NONE) {
        s_meas.published_t = vt;
        s_meas.any_published = true;
    }
    if (ah != RP_NONE) {
        s_meas.published_rh = vh;
        s_meas.any_published = true;
    }
    UNLOCK();

    if (at == RP_VALUE) {
        mb_publish_temperature(false, vt.value);
    } else if (at == RP_NULL) {
        mb_publish_temperature(true, 0);
    }
    if (ah == RP_VALUE) {
        mb_publish_humidity(false, vh.value);
    } else if (ah == RP_NULL) {
        mb_publish_humidity(true, 0);
    }

    if (valid) {
        ESP_LOGI(TAG, "T %.2f C  RH %.2f %%%s%s", vt.value / 100.0, vh.value / 100.0,
                 at == RP_VALUE ? "  [T published]" : "", ah == RP_VALUE ? "  [RH published]" : "");
        backoff_reset(&s_retry);
        s_next_meas_us = t + (int64_t)cfg.meas_interval_s * 1000000;
    } else {
        uint32_t delay_ms = backoff_next(&s_retry);
        uint32_t cap_ms = (uint32_t)cfg.meas_interval_s * 1000u;
        if (delay_ms > cap_ms) {
            delay_ms = cap_ms;
        }
        ESP_LOGW(TAG, "sensor read failed (%s), retry in %" PRIu32 " ms%s", esp_err_to_name(err), delay_ms,
                 (at == RP_NULL || ah == RP_NULL) ? ", value now null" : "");
        s_next_meas_us = t + (int64_t)delay_ms * 1000;
    }
    if (manual) {
        board_led_show(valid ? BOARD_LED_ACK : BOARD_LED_ERROR);
    }
}

/* ---------------------------------------------------------------- battery */

static void do_battery(void)
{
    battery_reading_t r = {0};
    esp_err_t err = battery_measure(&r);
    mb_battery_t pub = {0};

    LOCK();
    s_batt.last_err = err;
    if (err == ESP_OK) {
        bat_pack_t pack;
        bat_pack_from_cells(&pack, r.cell_mv, k_bat_policy.present_mv);
        bat_level_t prev = s_bat_model.initialized ? s_bat_model.level : BAT_LEVEL_OK;
        bat_level_t level = bat_pack_update(&s_bat_model, &k_bat_policy, &pack);
        uint8_t half = bat_filter_half_percent(s_batt.have_reported_pct, s_batt.half_pct, pack.pack_half_pct);
        s_batt.have_reading = true;
        s_batt.t_us = now_us();
        s_batt.reading = r;
        s_batt.pack = pack;
        s_batt.half_pct = half;
        s_batt.have_reported_pct = true;
        pub.present = pack.cells_present > 0;
        pub.voltage_valid = pack.cells_present > 0;
        pub.voltage_mv = pack.best_mv;  /* BatVoltage = cell voltage under the awake load */
        pub.percent_valid = true;
        pub.percent_half = half;
        pub.charge_level = (uint8_t)level;
        pub.replacement_needed = (level != BAT_LEVEL_OK);
        if (level != prev) {
            ESP_LOGW(TAG, "battery level %d -> %d (VBAT %u mV, %u.%u %%)", prev, level, pack.cell_mv[0],
                     pack.pack_half_pct / 2, (pack.pack_half_pct % 2) * 5);
        }
        if (pack.cells_present == 0) {
            /* the board has no other supply: the reading, not the cell, is missing */
            ESP_LOGW(TAG, "VBAT reads %u mV (< %u mV) while running: check divider R31/R32, Q3, GPIO5",
                     pack.cell_mv[0], k_bat_policy.present_mv);
        }
    } else {
        /* No fresh value: voltage/percent become null, level keeps its last state. */
        pub.present = true;
        pub.voltage_valid = false;
        pub.percent_valid = false;
        pub.charge_level = (uint8_t)(s_bat_model.initialized ? s_bat_model.level : BAT_LEVEL_OK);
        pub.replacement_needed = s_bat_model.initialized && s_bat_model.level != BAT_LEVEL_OK;
    }
    const uint32_t interval_s = s_cfg.bat_interval_s;
    UNLOCK();

    mb_publish_battery(&pub);
    s_next_bat_us = now_us() + (int64_t)interval_s * 1000000;
}

/* ---------------------------------------------------------------- events */

static void factory_reset(void)
{
    ESP_LOGW(TAG, "factory reset requested");
    board_led_show(BOARD_LED_RESET_GO);
    vTaskDelay(pdMS_TO_TICKS(1000));            /* let the LED pattern play */
    esp_err_t err = app_config_erase();         /* application settings */
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "app config erase: %s", esp_err_to_name(err));
    }
    mb_factory_reset();                         /* fabrics, Thread, KVS; reboots */
}

static void handle_button(bg_event_t ev)
{
    switch (ev) {
    case BG_EVT_SHORT: {
        int64_t t = now_us();
        if (t - s_last_manual_us < (int64_t)CONFIG_APP_MANUAL_MEASURE_MIN_INTERVAL_MS * 1000) {
            ESP_LOGI(TAG, "manual measurement rate-limited");
            break;
        }
        s_last_manual_us = t;
        do_measure(true);
        break;
    }
    case BG_EVT_TRIPLE:
        mb_open_commissioning_window();     /* LED feedback on the Matter event */
        break;
    case BG_EVT_LONG_ARMED:
        board_led_show(BOARD_LED_RESET_ARMED);
        ESP_LOGW(TAG, "release now to factory reset");
        break;
    case BG_EVT_LONG_RELEASED:
        factory_reset();
        break;
    case BG_EVT_LONG_CANCELLED:
        board_led_show(BOARD_LED_OFF);
        ESP_LOGW(TAG, "button held too long: treated as stuck, reset cancelled");
        break;
    default:
        break;
    }
}

static void handle_matter(mb_event_t ev)
{
    switch (ev) {
    case MB_EVT_SERVER_READY:
        /* Publish fresh values as soon as the data model is live. */
        s_next_meas_us = now_us();
        break;
    case MB_EVT_COMMISSIONED:
        board_led_show(BOARD_LED_COMMISSIONED);
        s_next_meas_us = now_us();
        s_next_bat_us = now_us();
        break;
    case MB_EVT_WINDOW_OPENED:
        board_led_show(BOARD_LED_WINDOW_OPEN);
        break;
    case MB_EVT_WINDOW_FAILED:
        board_led_show(BOARD_LED_ERROR);
        break;
    case MB_EVT_WINDOW_CLOSED:
        ESP_LOGI(TAG, "commissioning window closed");
        break;
    case MB_EVT_FABRIC_REMOVED:
        ESP_LOGI(TAG, "fabric removed");
        break;
    case MB_EVT_THREAD_ATTACHED:
        ESP_LOGI(TAG, "Thread attached");
        s_next_meas_us = now_us();          /* publish a current value after reconnect */
        break;
    case MB_EVT_THREAD_DETACHED:
        /* Measurement continues; OpenThread handles re-attach with its own
         * backoff. No fabric reset and no automatic BLE window here. */
        ESP_LOGW(TAG, "Thread detached, measurements continue");
        break;
    case MB_EVT_IDENTIFY_START:
        board_led_show(BOARD_LED_IDENTIFY);
        break;
    case MB_EVT_IDENTIFY_STOP:
        board_led_show(BOARD_LED_OFF);
        break;
    }
}

static void handle_heater(sht40_heater_t heater)
{
    sht40_sample_t hot = {0};
    esp_err_t err = sht40_heater_pulse(heater, &hot);
    s_heater_holdoff_until_us = now_us() + (int64_t)CONFIG_APP_HEATER_HOLDOFF_S * 1000000;
    s_next_meas_us = s_heater_holdoff_until_us;
    if (err == ESP_OK) {
        printf("heater pulse done: T %.2f C RH %.2f %% (heated, NOT published); publishing resumes in %d s\n",
               hot.temp_milli_c / 1000.0, hot.rh_milli_pct / 1000.0, CONFIG_APP_HEATER_HOLDOFF_S);
    } else {
        printf("heater pulse failed: %s\n", esp_err_to_name(err));
    }
}

static void controller_task(void *arg)
{
    (void)arg;
    for (;;) {
        int64_t t = now_us();
        int64_t next = s_next_meas_us < s_next_bat_us ? s_next_meas_us : s_next_bat_us;
        if (!s_stable_marked && s_stable_at_us < next) {
            next = s_stable_at_us;
        }
        TickType_t wait = 0;
        if (next > t) {
            int64_t ms = (next - t + 999) / 1000;
            wait = pdMS_TO_TICKS(ms > 86400000 ? 86400000 : ms);
            if (wait == 0) {
                wait = 1;
            }
        }
        app_ev_t ev;
        if (xQueueReceive(s_queue, &ev, wait) == pdTRUE) {
            switch (ev.type) {
            case EV_MEASURE:
                if (ev.a == 0) {
                    handle_button(BG_EVT_SHORT);
                } else {
                    do_measure(true);
                }
                break;
            case EV_BATTERY:
                do_battery();
                break;
            case EV_BUTTON:
                handle_button((bg_event_t)ev.a);
                break;
            case EV_MATTER:
                handle_matter((mb_event_t)ev.a);
                break;
            case EV_HEATER:
                handle_heater((sht40_heater_t)ev.a);
                break;
            case EV_FACTORY_RESET:
                factory_reset();
                break;
            case EV_RESCHEDULE:
                break;
            }
        }
        t = now_us();
        if (t >= s_next_meas_us) {
            do_measure(false);
        }
        if (t >= s_next_bat_us) {
            do_battery();
        }
        if (!s_stable_marked && t >= s_stable_at_us) {
            power_guard_mark_stable();
            s_stable_marked = true;
        }
    }
}

/* ---------------------------------------------------------------- public */

esp_err_t app_controller_init(const app_cfg_t *cfg, const battery_reading_t *boot_battery)
{
    s_lock = xSemaphoreCreateMutex();
    s_queue = xQueueCreate(16, sizeof(app_ev_t));
    if (!s_lock || !s_queue) {
        return ESP_ERR_NO_MEM;
    }
    s_cfg = *cfg;
    rp_init(&s_ch_t, cfg->temp_deadband_centi, CONFIG_APP_SENSOR_FAIL_THRESHOLD);
    rp_init(&s_ch_rh, cfg->rh_deadband_centi, CONFIG_APP_SENSOR_FAIL_THRESHOLD);
    backoff_init(&s_retry, CONFIG_APP_SENSOR_RETRY_MIN_MS, (uint32_t)cfg->meas_interval_s * 1000u);
    memset(&s_meas, 0, sizeof(s_meas));
    memset(&s_batt, 0, sizeof(s_batt));
    s_meas.published_t.is_null = true;
    s_meas.published_rh.is_null = true;
    int64_t t = now_us();
    s_next_meas_us = t;                          /* first sample right away */
    s_next_bat_us = t;                           /* publish battery right after start */
    s_stable_at_us = t + (int64_t)CONFIG_APP_STABLE_AFTER_S * 1000000;
    (void)boot_battery;
    return ESP_OK;
}

esp_err_t app_controller_start(void)
{
    return xTaskCreate(controller_task, "app_ctrl", 4096, NULL, 4, NULL) == pdPASS ? ESP_OK : ESP_ERR_NO_MEM;
}

void app_controller_on_button(bg_event_t ev, void *ctx)
{
    (void)ctx;
    post(EV_BUTTON, (int32_t)ev);
}

void app_controller_on_matter(mb_event_t ev, void *ctx)
{
    (void)ctx;
    post(EV_MATTER, (int32_t)ev);
}

/* ---------------------------------------------------------------- console */

static void print_status(void)
{
    LOCK();
    const meas_state_t m = s_meas;
    const batt_state_t b = s_batt;
    const bat_state_t bm = s_bat_model;
    UNLOCK();
    mb_status_t ms;
    mb_get_status(&ms);
    power_guard_info_t pg;
    power_guard_get_info(&pg);
    int64_t t = now_us();

    printf("uptime            : %lld s\n", (long long)(t / 1000000));
    if (m.have_sample) {
        printf("last valid sample : T %.3f C, RH %.3f %% (raw RH %.3f %%), %lld s ago\n",
               m.sample.temp_milli_c / 1000.0, m.sample.rh_milli_pct / 1000.0,
               m.sample.rh_milli_pct_raw / 1000.0, (long long)((t - m.t_us) / 1000000));
    } else {
        printf("last valid sample : none\n");
    }
    printf("published         : T %s%.2f, RH %s%.2f\n", m.published_t.is_null ? "null " : "",
           m.published_t.value / 100.0, m.published_rh.is_null ? "null " : "", m.published_rh.value / 100.0);
    printf("sensor            : ok %" PRIu32 ", failed %" PRIu32 ", last %s (decode: %s, attempts %u)\n",
           m.ok_count, m.fail_count, esp_err_to_name(m.last_err), sht40_decode_str(m.last_diag.decode),
           m.last_diag.attempts);
    if (b.have_reading) {
        printf("battery           : VBAT %u mV%s, %u.%u %% (published %u.%u %%), level %d, %lld s ago\n",
               b.pack.cell_mv[0], b.pack.present[0] ? "" : " (below present threshold)",
               b.pack.pack_half_pct / 2, (b.pack.pack_half_pct % 2) * 5, b.half_pct / 2, (b.half_pct % 2) * 5,
               bm.level, (long long)((t - b.t_us) / 1000000));
    } else {
        printf("battery           : no reading (%s)\n", esp_err_to_name(b.last_err));
    }
    printf("matter            : server %s, fabrics %u, window %s, thread %s\n",
           ms.server_ready ? "ready" : "not ready", ms.fabric_count, ms.window_open ? "open" : "closed",
           ms.thread_attached ? "attached" : "detached");
    printf("power guard       : reset %s, boot #%" PRIu32 ", unstable boots %u (last cell reading %u mV)%s\n",
           power_guard_reset_reason_str(pg.reset_reason), pg.boot_count, pg.unstable_boots, pg.last_best_mv,
           pg.nvs_ok ? "" : ", NVS unavailable");
    printf("heap              : free %" PRIu32 " B, minimum since boot %" PRIu32 " B\n", esp_get_free_heap_size(),
           esp_get_minimum_free_heap_size());
}

static void print_config(void)
{
    LOCK();
    const app_cfg_t c = s_cfg;
    UNLOCK();
    printf("temp_offset   %d (0.01 C)\n", c.temp_offset_centi);
    printf("rh_offset     %d (0.01 %%RH)\n", c.rh_offset_centi);
    printf("meas_interval %u s\n", c.meas_interval_s);
    printf("bat_interval  %" PRIu32 " s\n", c.bat_interval_s);
    printf("temp_deadband %u (0.01 C)\n", c.temp_deadband_centi);
    printf("rh_deadband   %u (0.01 %%RH)\n", c.rh_deadband_centi);
    printf("led           %d\n", c.led_enabled);
    printf("tx_power      %d dBm\n", c.tx_power_dbm);
}

static esp_err_t config_set(const char *key, int32_t value)
{
    LOCK();
    app_cfg_t c = s_cfg;
    bool ok;
    if (strcmp(key, "temp_offset") == 0) {
        ok = app_cfg_set_temp_offset(&c, value);
    } else if (strcmp(key, "rh_offset") == 0) {
        ok = app_cfg_set_rh_offset(&c, value);
    } else if (strcmp(key, "meas_interval") == 0) {
        ok = app_cfg_set_meas_interval(&c, value);
    } else if (strcmp(key, "bat_interval") == 0) {
        ok = app_cfg_set_bat_interval(&c, value);
    } else if (strcmp(key, "temp_deadband") == 0) {
        ok = app_cfg_set_temp_deadband(&c, value);
    } else if (strcmp(key, "rh_deadband") == 0) {
        ok = app_cfg_set_rh_deadband(&c, value);
    } else if (strcmp(key, "led") == 0) {
        ok = (value == 0 || value == 1);
        c.led_enabled = (value == 1);
    } else if (strcmp(key, "tx_power") == 0) {
        ok = app_cfg_set_tx_power(&c, value);
    } else {
        UNLOCK();
        return ESP_ERR_NOT_FOUND;
    }
    if (!ok) {
        UNLOCK();
        return ESP_ERR_INVALID_ARG;
    }
    bool written = false;
    esp_err_t err = app_config_save(&c, &written);   /* writes flash only if changed */
    if (err == ESP_OK) {
        const bool tx_changed = c.tx_power_dbm != s_cfg.tx_power_dbm;
        s_cfg = c;
        board_led_set_enabled(c.led_enabled);
        s_retry.max = (uint32_t)c.meas_interval_s * 1000u;
        UNLOCK();
        if (tx_changed) {
            mb_set_tx_power(c.tx_power_dbm);
        }
        ESP_LOGI(TAG, "config %s = %ld (%s)", key, (long)value, written ? "saved" : "unchanged");
        post(EV_RESCHEDULE, 0);
        return ESP_OK;
    }
    UNLOCK();
    return err;
}

static void req_measure(void)
{
    post(EV_MEASURE, 1);
}

static void req_battery(void)
{
    post(EV_BATTERY, 0);
}

static esp_err_t req_heater(int mw, int ms)
{
    sht40_heater_t h;
    if (mw == 20 && ms == 100) {
        h = SHT40_HEATER_20MW_100MS;
    } else if (mw == 20 && ms == 1000) {
        h = SHT40_HEATER_20MW_1S;
    } else if (mw == 110 && ms == 100) {
        h = SHT40_HEATER_110MW_100MS;
    } else if (mw == 110 && ms == 1000) {
        h = SHT40_HEATER_110MW_1S;
    } else {
        return ESP_ERR_INVALID_ARG;
    }
    return post(EV_HEATER, (int32_t)h) ? ESP_OK : ESP_FAIL;
}

static void req_window(void)
{
    mb_open_commissioning_window();
}

static void req_factory_reset(void)
{
    post(EV_FACTORY_RESET, 0);
}

void app_controller_console_ops(maint_console_ops_t *ops)
{
    ops->print_status = print_status;
    ops->print_config = print_config;
    ops->request_measure = req_measure;
    ops->request_battery = req_battery;
    ops->config_set = config_set;
    ops->heater = req_heater;
    ops->open_window = req_window;
    ops->factory_reset = req_factory_reset;
}
