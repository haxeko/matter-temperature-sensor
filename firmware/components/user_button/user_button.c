/*
 * USER button glue: espressif/button press/release -> button_gesture.
 */
#include "user_button.h"

#include "board_pins.h"
#include "button_gpio.h"
#include "esp_check.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "iot_button.h"

static const char *TAG = "user_btn";

static bg_state_t s_gesture;
static user_button_cb_t s_cb;
static void *s_ctx;
static esp_timer_handle_t s_deadline_timer;

static uint32_t now_ms(void)
{
    return (uint32_t)(esp_timer_get_time() / 1000);
}

static void emit(bg_event_t ev)
{
    if (ev == BG_EVT_NONE) {
        return;
    }
    ESP_LOGI(TAG, "gesture: %s", bg_event_str(ev));
    if (s_cb) {
        s_cb(ev, s_ctx);
    }
}

/* Arm the one-shot timer for the next gesture deadline, if any. */
static void rearm(void)
{
    esp_timer_stop(s_deadline_timer);
    uint32_t deadline;
    if (bg_next_deadline(&s_gesture, &deadline)) {
        int32_t delta = (int32_t)(deadline - now_ms());
        if (delta < 1) {
            delta = 1;
        }
        esp_timer_start_once(s_deadline_timer, (uint64_t)delta * 1000);
    }
}

static void deadline_cb(void *arg)
{
    (void)arg;
    emit(bg_on_tick(&s_gesture, now_ms()));
    rearm();
}

static void press_cb(void *handle, void *usr)
{
    (void)handle;
    (void)usr;
    emit(bg_on_press(&s_gesture, now_ms()));
    rearm();
}

static void release_cb(void *handle, void *usr)
{
    (void)handle;
    (void)usr;
    emit(bg_on_release(&s_gesture, now_ms()));
    rearm();
}

esp_err_t user_button_init(user_button_cb_t cb, void *ctx)
{
    s_cb = cb;
    s_ctx = ctx;
    bg_init(&s_gesture, NULL);

    const esp_timer_create_args_t targs = {
        .callback = deadline_cb,
        .dispatch_method = ESP_TIMER_TASK,
        .name = "btn_deadline",
        .skip_unhandled_events = true,
    };
    ESP_RETURN_ON_ERROR(esp_timer_create(&targs, &s_deadline_timer), TAG, "timer");

    const button_config_t btn_cfg = {0};
    const button_gpio_config_t gpio_cfg = {
        .gpio_num = BOARD_GPIO_USER_BUTTON,
        .active_level = BOARD_USER_BUTTON_ACTIVE,
        .enable_power_save = true,   /* GPIO wake-up from light sleep */
        .disable_pull = true,        /* external 10k pull-up (R4) */
    };
    button_handle_t btn = NULL;
    ESP_RETURN_ON_ERROR(iot_button_new_gpio_device(&btn_cfg, &gpio_cfg, &btn), TAG, "button");
    ESP_RETURN_ON_ERROR(iot_button_register_cb(btn, BUTTON_PRESS_DOWN, NULL, press_cb, NULL), TAG, "cb");
    ESP_RETURN_ON_ERROR(iot_button_register_cb(btn, BUTTON_PRESS_UP, NULL, release_cb, NULL), TAG, "cb");
    ESP_LOGI(TAG, "USER button on GPIO%d", BOARD_GPIO_USER_BUTTON);
    return ESP_OK;
}
