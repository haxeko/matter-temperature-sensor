/*
 * Brown-out / low-battery boot guard (state in NVS, see power_guard.h).
 */
#include "power_guard.h"

#include "board_pins.h"
#include "esp_attr.h"
#include "esp_log.h"
#include "esp_sleep.h"
#include "guard_policy.h"
#include "nvs.h"
#include "sdkconfig.h"
#include "soc/soc_caps.h"

static const char *TAG = "power_guard";

#define GUARD_MAGIC 0x50475244u /* "PGRD" */
#define NVS_NS      "pguard"
#define KEY_UNST    "unst"
#define KEY_LASTMV  "lastmv"

typedef struct {
    uint32_t magic;
    uint32_t boots;
} guard_rtc_t;

static RTC_NOINIT_ATTR guard_rtc_t s_rtc;
static esp_reset_reason_t s_reason = ESP_RST_UNKNOWN;
static gp_state_t s_state;
static gp_state_t s_saved;
static bool s_nvs_ok;

const char *power_guard_reset_reason_str(esp_reset_reason_t r)
{
    switch (r) {
    case ESP_RST_POWERON: return "power-on / EN (supervisor)";
    case ESP_RST_EXT: return "external pin";
    case ESP_RST_SW: return "software";
    case ESP_RST_PANIC: return "panic";
    case ESP_RST_INT_WDT: return "interrupt watchdog";
    case ESP_RST_TASK_WDT: return "task watchdog";
    case ESP_RST_WDT: return "other watchdog";
    case ESP_RST_DEEPSLEEP: return "deep-sleep wake";
    case ESP_RST_BROWNOUT: return "brown-out";
    case ESP_RST_SDIO: return "sdio";
    default: return "other";
    }
}

#if CONFIG_APP_POWER_GUARD_ENABLE
static gp_reset_t classify(esp_reset_reason_t r)
{
    switch (r) {
    case ESP_RST_SW: return GP_RESET_SOFTWARE;
    case ESP_RST_DEEPSLEEP: return GP_RESET_SLEEP_WAKE;   /* the guard is the only deep-sleep user */
    case ESP_RST_PANIC:
    case ESP_RST_INT_WDT:
    case ESP_RST_TASK_WDT:
    case ESP_RST_WDT: return GP_RESET_FAULT;
    default: return GP_RESET_POWER_ON;                    /* incl. EN from the supervisor, brown-out */
    }
}
#endif /* CONFIG_APP_POWER_GUARD_ENABLE */

static void state_save(void)
{
    if (!s_nvs_ok || (s_state.unstable_boots == s_saved.unstable_boots &&
                      s_state.last_best_mv == s_saved.last_best_mv)) {
        return;
    }
    nvs_handle_t h;
    esp_err_t err = nvs_open(NVS_NS, NVS_READWRITE, &h);
    if (err == ESP_OK) {
        if (s_state.unstable_boots != s_saved.unstable_boots) {
            err = nvs_set_u8(h, KEY_UNST, s_state.unstable_boots);
        }
        if (err == ESP_OK && s_state.last_best_mv != s_saved.last_best_mv) {
            err = nvs_set_u16(h, KEY_LASTMV, s_state.last_best_mv);
        }
        if (err == ESP_OK) {
            err = nvs_commit(h);
        }
        nvs_close(h);
    }
    if (err == ESP_OK) {
        s_saved = s_state;
    } else {
        ESP_LOGE(TAG, "state save: %s", esp_err_to_name(err));
    }
}

#if CONFIG_APP_POWER_GUARD_ENABLE
static void guard_sleep(uint32_t seconds, const char *why)
{
    ESP_LOGW(TAG, "%s: deep sleep for %lu s (USER button wakes earlier)", why, (unsigned long)seconds);
    esp_sleep_enable_timer_wakeup((uint64_t)seconds * 1000000ULL);
#if SOC_PM_SUPPORT_EXT1_WAKEUP
    /* GPIO9 is an LP IO on ESP32-H2 (GPIO7..14); 10k external pull-up. */
    esp_sleep_enable_ext1_wakeup_io(1ULL << BOARD_GPIO_USER_BUTTON, ESP_EXT1_WAKEUP_ANY_LOW);
#endif
    esp_deep_sleep_start();
}
#endif /* CONFIG_APP_POWER_GUARD_ENABLE */

void power_guard_init(void)
{
    s_reason = esp_reset_reason();
    if (s_rtc.magic != GUARD_MAGIC || s_reason == ESP_RST_POWERON) {
        s_rtc.magic = GUARD_MAGIC;
        s_rtc.boots = 0;
    }
    s_rtc.boots++;

    nvs_handle_t h;
    esp_err_t err = nvs_open(NVS_NS, NVS_READWRITE, &h);
    if (err == ESP_OK) {
        uint8_t u = 0;
        uint16_t mv = 0;
        if (nvs_get_u8(h, KEY_UNST, &u) == ESP_OK) {
            s_state.unstable_boots = u;
        }
        if (nvs_get_u16(h, KEY_LASTMV, &mv) == ESP_OK) {
            s_state.last_best_mv = mv;
        }
        nvs_close(h);
        s_saved = s_state;
        s_nvs_ok = true;
    } else {
        ESP_LOGE(TAG, "NVS unavailable (%s): boot guard disabled for this boot", esp_err_to_name(err));
    }
    ESP_LOGI(TAG, "reset reason: %s, boot #%lu, unstable boots %u (last cell reading %u mV)",
             power_guard_reset_reason_str(s_reason), (unsigned long)s_rtc.boots, s_state.unstable_boots,
             s_state.last_best_mv);
}

void power_guard_check(bool have_mv, uint32_t best_cell_mv)
{
#if CONFIG_APP_POWER_GUARD_ENABLE
    if (!s_nvs_ok) {
        return;
    }
    const gp_config_t cfg = {
        .boot_min_mv = CONFIG_APP_BOOT_MIN_CELL_MV,
        .recovery_mv = CONFIG_APP_GUARD_RECOVERY_MV,
        .backoff_min_s = CONFIG_APP_GUARD_BACKOFF_MIN_S,
        .backoff_max_s = CONFIG_APP_GUARD_BACKOFF_MAX_S,
    };
    /* Without a reading, use the last recorded value: rule 2 cannot fire and
     * rule 3 keeps its previous outcome only if the cells were already low. */
    uint16_t mv = have_mv ? (uint16_t)(best_cell_mv > 0xFFFFu ? 0xFFFFu : best_cell_mv)
                          : (s_state.last_best_mv ? s_state.last_best_mv : 0xFFFFu);
    const uint16_t prev_mv = s_state.last_best_mv;
    gp_decision_t d = gp_decide(&s_state, &cfg, classify(s_reason), mv);
    if (!have_mv) {
        s_state.last_best_mv = prev_mv;   /* never record a substitute as a measurement */
    }
    if (d.cleared) {
        ESP_LOGI(TAG, "unstable-boot count cleared (%s)",
                 classify(s_reason) == GP_RESET_SOFTWARE ? "software restart" : "new cells detected");
    }
    state_save();
    switch (d.action) {
    case GP_SLEEP_LOW_BATTERY:
        ESP_LOGW(TAG, "cell %u mV < %d mV", mv, CONFIG_APP_BOOT_MIN_CELL_MV);
        guard_sleep(d.sleep_s, "battery too low to start the radio");
        break;
    case GP_SLEEP_UNSTABLE:
        guard_sleep(d.sleep_s, "previous run reset before it was stable");
        break;
    case GP_RUN:
    default:
        break;
    }
#else
    (void)have_mv;
    (void)best_cell_mv;
#endif
}

void power_guard_mark_stable(void)
{
    if (gp_mark_stable(&s_state)) {
        ESP_LOGI(TAG, "stable operation, clearing the unstable-boot count");
        state_save();
    }
}

void power_guard_get_info(power_guard_info_t *out)
{
    out->reset_reason = s_reason;
    out->boot_count = s_rtc.boots;
    out->unstable_boots = s_state.unstable_boots;
    out->last_best_mv = s_state.last_best_mv;
    out->nvs_ok = s_nvs_ok;
}
