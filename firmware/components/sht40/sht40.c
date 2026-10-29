/*
 * SHT40 driver (ESP-IDF I2C master).
 */
#include "sht40.h"

#include <inttypes.h>
#include <string.h>
#include "board_pins.h"
#include "driver/i2c_master.h"
#include "esp_check.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "soc/soc_caps.h"

static const char *TAG = "sht40";

#define XFER_TIMEOUT_MS     20
#define READ_RETRIES        3   /* sensor NACKs the read header while busy */
#define READ_RETRY_GAP_MS   2

typedef struct {
    i2c_master_bus_handle_t bus;
    i2c_master_dev_handle_t dev;
} session_t;

static void delay_ms(uint32_t ms)
{
    /* Round up to whole ticks so the wait is never shorter than requested. */
    TickType_t ticks = (ms + portTICK_PERIOD_MS - 1) / portTICK_PERIOD_MS;
    vTaskDelay(ticks ? ticks : 1);
}

static esp_err_t session_begin(session_t *s)
{
    memset(s, 0, sizeof(*s));
    i2c_master_bus_config_t bus_cfg = {
        .i2c_port = BOARD_I2C_PORT,
        .sda_io_num = BOARD_GPIO_I2C_SDA,
        .scl_io_num = BOARD_GPIO_I2C_SCL,
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .glitch_ignore_cnt = 7,
        .flags = {
            .enable_internal_pullup = false, /* 10k external pull-ups (R7/R8) */
#if SOC_I2C_SUPPORT_SLEEP_RETENTION
            .allow_pd = true,
#endif
        },
    };
    ESP_RETURN_ON_ERROR(i2c_new_master_bus(&bus_cfg, &s->bus), TAG, "bus create");
    i2c_device_config_t dev_cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = SHT40_I2C_ADDR,
        .scl_speed_hz = BOARD_I2C_FREQ_HZ,
    };
    esp_err_t err = i2c_master_bus_add_device(s->bus, &dev_cfg, &s->dev);
    if (err != ESP_OK) {
        i2c_del_master_bus(s->bus);
        s->bus = NULL;
    }
    return err;
}

static void session_end(session_t *s)
{
    if (s->dev) {
        i2c_master_bus_rm_device(s->dev);
    }
    if (s->bus) {
        i2c_del_master_bus(s->bus);
    }
    memset(s, 0, sizeof(*s));
}

static esp_err_t send_cmd(session_t *s, uint8_t cmd)
{
    return i2c_master_transmit(s->dev, &cmd, 1, XFER_TIMEOUT_MS);
}

/* Read 6 bytes, tolerating "busy" NACKs for a few milliseconds. */
static esp_err_t read6(session_t *s, uint8_t rx[6], uint8_t *attempts)
{
    esp_err_t err = ESP_FAIL;
    for (int i = 0; i < READ_RETRIES; i++) {
        if (attempts) {
            (*attempts)++;
        }
        err = i2c_master_receive(s->dev, rx, 6, XFER_TIMEOUT_MS);
        if (err == ESP_OK) {
            return ESP_OK;
        }
        delay_ms(READ_RETRY_GAP_MS);
    }
    return err;
}

/* Clock out a stuck slave and reset the sensor's state machine. */
static void recover(session_t *s)
{
    i2c_master_bus_reset(s->bus);
    if (send_cmd(s, SHT40_CMD_SOFT_RESET) == ESP_OK) {
        delay_ms(SHT40_SOFT_RESET_MAX_MS + 1);
    }
}

static esp_err_t map_decode(sht40_decode_t d)
{
    switch (d) {
    case SHT40_DECODE_OK: return ESP_OK;
    case SHT40_DECODE_CRC_T:
    case SHT40_DECODE_CRC_RH: return ESP_ERR_INVALID_CRC;
    case SHT40_DECODE_T_OUT_OF_RANGE: return ESP_ERR_INVALID_RESPONSE;
    default: return ESP_FAIL;
    }
}

esp_err_t sht40_measure(sht40_sample_t *out, sht40_diag_t *diag)
{
    sht40_diag_t d = {.i2c_err = ESP_OK, .decode = SHT40_DECODE_BAD_ARG};
    if (!out) {
        return ESP_ERR_INVALID_ARG;
    }
    session_t s;
    esp_err_t err = session_begin(&s);
    if (err != ESP_OK) {
        d.i2c_err = err;
        goto done;
    }
    uint8_t rx[6];
    for (int pass = 0; pass < 2; pass++) {
        d.attempts++;
        err = send_cmd(&s, SHT40_CMD_MEASURE_HIGH);
        if (err == ESP_OK) {
            delay_ms(SHT40_MEAS_HIGH_MAX_MS);
            err = read6(&s, rx, &d.attempts);
        }
        if (err == ESP_OK) {
            d.decode = sht40_decode(rx, out);
            err = map_decode(d.decode);
            if (err == ESP_OK || pass == 1) {
                break;
            }
        } else {
            d.i2c_err = err;
        }
        /* First pass failed: recover the bus/sensor and try once more. */
        recover(&s);
        d.bus_recovered = true;
    }
    session_end(&s);
done:
    if (diag) {
        *diag = d;
    }
    if (err != ESP_OK) {
        ESP_LOGW(TAG, "measure failed: %s (i2c %s, decode %s)", esp_err_to_name(err),
                 esp_err_to_name(d.i2c_err), sht40_decode_str(d.decode));
    }
    return err;
}

esp_err_t sht40_soft_reset(void)
{
    session_t s;
    ESP_RETURN_ON_ERROR(session_begin(&s), TAG, "session");
    esp_err_t err = send_cmd(&s, SHT40_CMD_SOFT_RESET);
    delay_ms(SHT40_SOFT_RESET_MAX_MS + 1);
    session_end(&s);
    return err;
}

esp_err_t sht40_init(uint32_t *serial_out)
{
    delay_ms(SHT40_POWER_UP_MAX_MS);
    session_t s;
    ESP_RETURN_ON_ERROR(session_begin(&s), TAG, "session");
    uint8_t rx[6];
    esp_err_t err = send_cmd(&s, SHT40_CMD_READ_SERIAL);
    if (err == ESP_OK) {
        delay_ms(1);
        err = read6(&s, rx, NULL);
    }
    if (err != ESP_OK) {
        recover(&s);
    }
    session_end(&s);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "no response at 0x%02X: %s", SHT40_I2C_ADDR, esp_err_to_name(err));
        return err;
    }
    uint32_t serial;
    if (!sht40_decode_serial(rx, &serial)) {
        ESP_LOGE(TAG, "serial number CRC mismatch");
        return ESP_ERR_INVALID_CRC;
    }
    ESP_LOGI(TAG, "SHT40 serial 0x%08" PRIX32, serial);
    if (serial_out) {
        *serial_out = serial;
    }
    return ESP_OK;
}

esp_err_t sht40_heater_pulse(sht40_heater_t heater, sht40_sample_t *heated_sample)
{
    uint32_t wait_ms;
    switch (heater) {
    case SHT40_HEATER_20MW_100MS:
    case SHT40_HEATER_110MW_100MS:
        wait_ms = 110 + SHT40_MEAS_HIGH_MAX_MS;
        break;
    case SHT40_HEATER_20MW_1S:
    case SHT40_HEATER_110MW_1S:
        wait_ms = 1100 + SHT40_MEAS_HIGH_MAX_MS;
        break;
    default:
        return ESP_ERR_INVALID_ARG;
    }
    session_t s;
    ESP_RETURN_ON_ERROR(session_begin(&s), TAG, "session");
    uint8_t rx[6];
    esp_err_t err = send_cmd(&s, (uint8_t)heater);
    if (err == ESP_OK) {
        delay_ms(wait_ms);
        err = read6(&s, rx, NULL);
    }
    session_end(&s);
    if (err == ESP_OK && heated_sample) {
        err = map_decode(sht40_decode(rx, heated_sample));
    }
    return err;
}
