/*
 * SHT40 driver on the ESP-IDF I2C master driver (driver/i2c_master.h).
 *
 * The I2C bus is created for each transaction session and deleted afterwards,
 * so nothing has to survive automatic light sleep between measurements.
 * The heater is never used by sht40_measure(); see sht40_heater_pulse().
 */
#pragma once

#include <stdint.h>
#include "esp_err.h"
#include "sht40_proto.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    esp_err_t i2c_err;          /* last I2C driver error (ESP_OK if none) */
    sht40_decode_t decode;      /* decode result of the last frame */
    uint8_t attempts;           /* I2C attempts used (1 = first try worked) */
    bool bus_recovered;         /* a bus reset / soft reset was performed */
} sht40_diag_t;

/* Validate wiring by reading the serial number once. Safe to call again. */
esp_err_t sht40_init(uint32_t *serial_out);

/*
 * High-repeatability T/RH measurement.
 * Returns ESP_OK and fills `out` only for a CRC-valid, in-range frame.
 * Errors: ESP_ERR_TIMEOUT / ESP_ERR_INVALID_STATE (I2C, NACK),
 *         ESP_ERR_INVALID_CRC (checksum), ESP_ERR_INVALID_RESPONSE (range).
 * `diag` (optional) always receives the details.
 */
esp_err_t sht40_measure(sht40_sample_t *out, sht40_diag_t *diag);

/* Soft reset (0x94); also used during error recovery. */
esp_err_t sht40_soft_reset(void);

typedef enum {
    SHT40_HEATER_20MW_100MS = SHT40_CMD_HEATER_20MW_100MS,
    SHT40_HEATER_20MW_1S = SHT40_CMD_HEATER_20MW_1S,
    SHT40_HEATER_110MW_100MS = SHT40_CMD_HEATER_110MW_100MS,
    SHT40_HEATER_110MW_1S = SHT40_CMD_HEATER_110MW_1S,
} sht40_heater_t;

/*
 * Maintenance only: run one heater pulse. The returned sample was taken with
 * the heater on and MUST NOT be published as room temperature. The 200 mW
 * settings are deliberately not offered: they draw up to 100 mA (datasheet
 * table 4), more than the coin-cell power path is designed for.
 */
esp_err_t sht40_heater_pulse(sht40_heater_t heater, sht40_sample_t *heated_sample);

#ifdef __cplusplus
}
#endif
