/*
 * SHT40 protocol helpers — pure C, no ESP-IDF dependency (host unit tested).
 *
 * Source: Sensirion "Datasheet SHT4x" version 7.3 (June 2026):
 *   - CRC-8, polynomial 0x31, init 0xFF, no reflection, no final XOR,
 *     CRC(0xBEEF) = 0x92 (section 4.4)
 *   - RH = -6 + 125 * S_RH / (2^16 - 1)   [%RH]   (eq. 1)
 *   - T  = -45 + 175 * S_T / (2^16 - 1)   [degC]  (eq. 2)
 *   - specified range: T -40..125 degC, RH 0..100 %RH (crop advised)
 */
#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define SHT40_I2C_ADDR                 0x44  /* SHT40-AD1B */

#define SHT40_CMD_MEASURE_HIGH         0xFD
#define SHT40_CMD_MEASURE_MEDIUM       0xF6
#define SHT40_CMD_MEASURE_LOW          0xE0
#define SHT40_CMD_READ_SERIAL          0x89
#define SHT40_CMD_SOFT_RESET           0x94
#define SHT40_CMD_HEATER_20MW_100MS    0x15
#define SHT40_CMD_HEATER_20MW_1S       0x1E
#define SHT40_CMD_HEATER_110MW_100MS   0x24
#define SHT40_CMD_HEATER_110MW_1S      0x2F
#define SHT40_CMD_HEATER_200MW_100MS   0x32
#define SHT40_CMD_HEATER_200MW_1S      0x39

/* Max durations from datasheet table 5 (at -40 degC, 1.08 V), plus margin. */
#define SHT40_MEAS_HIGH_MAX_MS         9   /* 8.3 ms max */
#define SHT40_MEAS_MEDIUM_MAX_MS       5   /* 4.5 ms max */
#define SHT40_SOFT_RESET_MAX_MS        1
#define SHT40_POWER_UP_MAX_MS          1

/* Specified operating range used for plausibility checks. */
#define SHT40_T_MIN_MILLI_C            (-40000)
#define SHT40_T_MAX_MILLI_C            125000

typedef enum {
    SHT40_DECODE_OK = 0,
    SHT40_DECODE_BAD_ARG,
    SHT40_DECODE_CRC_T,         /* checksum of temperature word wrong */
    SHT40_DECODE_CRC_RH,        /* checksum of humidity word wrong */
    SHT40_DECODE_T_OUT_OF_RANGE,/* converted temperature outside -40..125 degC */
} sht40_decode_t;

typedef struct {
    uint16_t raw_t;
    uint16_t raw_rh;
    int32_t temp_milli_c;       /* milli-degC */
    int32_t rh_milli_pct;       /* milli-%RH, cropped to 0..100000 */
    int32_t rh_milli_pct_raw;   /* milli-%RH before cropping (diagnostics) */
} sht40_sample_t;

/* CRC-8 as defined by the datasheet (poly 0x31, init 0xFF). */
uint8_t sht40_crc8(const uint8_t *data, size_t len);

/* Integer conversions with round-half-away-from-zero, exact to 1 milli-unit. */
int32_t sht40_ticks_to_milli_c(uint16_t ticks);
int32_t sht40_ticks_to_milli_rh(uint16_t ticks);

/*
 * Decode a 6-byte measurement response [T_msb T_lsb CRC RH_msb RH_lsb CRC].
 * On any error `out` is left untouched. A CRC error on either word rejects
 * the whole sample: T and RH are never published from a half-valid frame.
 */
sht40_decode_t sht40_decode(const uint8_t rx[6], sht40_sample_t *out);

/* Decode the 6-byte serial-number response. Returns false on CRC error. */
bool sht40_decode_serial(const uint8_t rx[6], uint32_t *serial);

const char *sht40_decode_str(sht40_decode_t code);

#ifdef __cplusplus
}
#endif
