/*
 * Board support implementation.
 *
 * The LED runs in a small task so that patterns keep exact timing: a PM lock
 * (ESP_PM_NO_LIGHT_SLEEP) is held only while a pattern is active, otherwise
 * automatic light sleep could stretch or cut the pulses.
 */
#include "board.h"

#include "driver/gpio.h"
#include "esp_log.h"
#include "esp_pm.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/task.h"

static const char *TAG = "board";

typedef struct {
    uint8_t count;      /* number of on-pulses */
    uint16_t on_ms;
    uint16_t off_ms;
    bool hold_on;       /* stay on until the next request */
    bool always;        /* shown even when LED feedback is disabled */
} led_pattern_def_t;

static const led_pattern_def_t k_patterns[] = {
    [BOARD_LED_ACK]           = {1, 40, 0, false, false},
    [BOARD_LED_ERROR]         = {2, 150, 150, false, false},
    [BOARD_LED_WINDOW_OPEN]   = {3, 80, 120, false, false},
    [BOARD_LED_COMMISSIONED]  = {2, 300, 200, false, false},
    [BOARD_LED_IDENTIFY]      = {6, 250, 250, false, true},
    [BOARD_LED_RESET_ARMED]   = {0, 0, 0, true, true},
    [BOARD_LED_RESET_GO]      = {8, 60, 60, false, true},
    [BOARD_LED_OFF]           = {0, 0, 0, false, true},
};

static QueueHandle_t s_led_queue;
static volatile bool s_led_enabled = true;
#if CONFIG_PM_ENABLE
static esp_pm_lock_handle_t s_led_pm_lock;
#endif

static void led_write(bool on)
{
    gpio_set_level(BOARD_GPIO_LED, on ? BOARD_LED_ACTIVE : !BOARD_LED_ACTIVE);
}

static void led_pm_hold(bool hold)
{
#if CONFIG_PM_ENABLE
    static bool held;
    if (hold && !held) {
        esp_pm_lock_acquire(s_led_pm_lock);
        held = true;
    } else if (!hold && held) {
        esp_pm_lock_release(s_led_pm_lock);
        held = false;
    }
#else
    (void)hold;
#endif
}

/* Wait for `ms`, returning true (and the new request) if one arrives. */
static bool led_wait(uint32_t ms, board_led_pattern_t *next)
{
    return xQueueReceive(s_led_queue, next, pdMS_TO_TICKS(ms)) == pdTRUE;
}

static void led_task(void *arg)
{
    (void)arg;
    board_led_pattern_t req;
    for (;;) {
        if (xQueueReceive(s_led_queue, &req, portMAX_DELAY) != pdTRUE) {
            continue;
        }
restart:
        if ((unsigned)req >= sizeof(k_patterns) / sizeof(k_patterns[0])) {
            continue;
        }
        const led_pattern_def_t *p = &k_patterns[req];
        if (!p->always && !s_led_enabled) {
            led_write(false);
            led_pm_hold(false);
            continue;
        }
        if (p->hold_on) {
            led_pm_hold(true);
            led_write(true);
            /* Stay on until something else is requested. */
            if (xQueueReceive(s_led_queue, &req, portMAX_DELAY) == pdTRUE) {
                led_write(false);
                goto restart;
            }
            continue;
        }
        if (p->count == 0) { /* BOARD_LED_OFF */
            led_write(false);
            led_pm_hold(false);
            continue;
        }
        led_pm_hold(true);
        for (uint8_t i = 0; i < p->count; i++) {
            led_write(true);
            if (led_wait(p->on_ms, &req)) {
                led_write(false);
                goto restart;
            }
            led_write(false);
            if (p->off_ms && led_wait(p->off_ms, &req)) {
                goto restart;
            }
        }
        led_pm_hold(false);
    }
}

void board_vbat_sense_enable(bool on)
{
    gpio_set_level(BOARD_GPIO_VBAT_MEAS_EN, on ? 1 : 0);
}

esp_err_t board_init(void)
{
    esp_err_t err;

    /* Outputs: LED off, sense switch off. */
    const gpio_config_t out_cfg = {
        .pin_bit_mask = (1ULL << BOARD_GPIO_LED) | (1ULL << BOARD_GPIO_VBAT_MEAS_EN),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    gpio_set_level(BOARD_GPIO_LED, !BOARD_LED_ACTIVE);
    gpio_set_level(BOARD_GPIO_VBAT_MEAS_EN, 0);
    err = gpio_config(&out_cfg);
    if (err != ESP_OK) {
        return err;
    }

    /* GPIO8 is a strapping pin held high externally; keep its input buffer off. */
    const gpio_config_t strap_cfg = {
        .pin_bit_mask = 1ULL << BOARD_GPIO_STRAP8,
        .mode = GPIO_MODE_DISABLE,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    err = gpio_config(&strap_cfg);
    if (err != ESP_OK) {
        return err;
    }

    /* Unconnected pins: input buffer disabled + pull-down, never floating. */
    static const int unused[] = BOARD_UNUSED_GPIO_LIST;
    uint64_t mask = 0;
    for (size_t i = 0; i < sizeof(unused) / sizeof(unused[0]); i++) {
        mask |= 1ULL << unused[i];
    }
    const gpio_config_t unused_cfg = {
        .pin_bit_mask = mask,
        .mode = GPIO_MODE_DISABLE,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_ENABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    err = gpio_config(&unused_cfg);
    if (err != ESP_OK) {
        return err;
    }

#if CONFIG_PM_ENABLE
    err = esp_pm_lock_create(ESP_PM_NO_LIGHT_SLEEP, 0, "led", &s_led_pm_lock);
    if (err != ESP_OK) {
        return err;
    }
#endif
    s_led_queue = xQueueCreate(4, sizeof(board_led_pattern_t));
    if (!s_led_queue) {
        return ESP_ERR_NO_MEM;
    }
    if (xTaskCreate(led_task, "led", 2048, NULL, 3, NULL) != pdPASS) {
        return ESP_ERR_NO_MEM;
    }
    ESP_LOGI(TAG, "board init done (LED GPIO%d, cell sense enable GPIO%d, ADC GPIO%d/GPIO%d)",
             BOARD_GPIO_LED, BOARD_GPIO_VBAT_MEAS_EN, BOARD_GPIO_VBAT1_SENSE, BOARD_GPIO_VBAT2_SENSE);
    return ESP_OK;
}

void board_led_set_enabled(bool enabled)
{
    s_led_enabled = enabled;
}

bool board_led_get_enabled(void)
{
    return s_led_enabled;
}

void board_led_show(board_led_pattern_t pattern)
{
    if (!s_led_queue) {
        return;
    }
    /* Never block the caller; drop the request if the queue is full. */
    xQueueSend(s_led_queue, &pattern, 0);
}
