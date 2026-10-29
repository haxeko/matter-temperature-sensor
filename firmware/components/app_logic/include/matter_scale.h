/*
 * Conversion of sensor samples to Matter attribute values (pure C).
 *
 * Matter Application Cluster spec:
 *  - Temperature Measurement MeasuredValue: nullable int16, unit 0.01 degC,
 *    must lie within MinMeasuredValue..MaxMeasuredValue or be null.
 *  - Relative Humidity Measurement MeasuredValue: nullable uint16,
 *    unit 0.01 %RH, 0..10000, or null.
 * Null is used whenever no valid recent sample exists; a stale or fake value
 * (e.g. 0) is never substituted.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* MinMeasuredValue / MaxMeasuredValue advertised by this device (SHT40 range). */
#define MX_TEMP_MIN_CENTI   (-4000)
#define MX_TEMP_MAX_CENTI   12500
#define MX_RH_MIN_CENTI     0
#define MX_RH_MAX_CENTI     10000

typedef struct {
    bool is_null;
    int16_t value;
} mx_nullable_i16_t;

typedef struct {
    bool is_null;
    uint16_t value;
} mx_nullable_u16_t;

/* milli-units -> centi-units, rounding half away from zero. */
int32_t mx_milli_to_centi(int32_t milli);

/* Apply the calibration offset and clamp into the advertised range. */
mx_nullable_i16_t mx_temperature(bool valid, int32_t temp_milli_c, int16_t offset_centi_c);
mx_nullable_u16_t mx_humidity(bool valid, int32_t rh_milli_pct, int16_t offset_centi_pct);

#ifdef __cplusplus
}
#endif
