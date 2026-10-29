/*
 * SHT40 protocol helpers (pure C). See sht40_proto.h for the datasheet references.
 */
#include "sht40_proto.h"

uint8_t sht40_crc8(const uint8_t *data, size_t len)
{
    uint8_t crc = 0xFF;
    for (size_t i = 0; i < len; i++) {
        crc ^= data[i];
        for (int bit = 0; bit < 8; bit++) {
            crc = (crc & 0x80) ? (uint8_t)((crc << 1) ^ 0x31) : (uint8_t)(crc << 1);
        }
    }
    return crc;
}

/* (scale * ticks) / 65535 rounded to nearest; numerator is never negative. */
static int32_t scale_ticks(uint32_t scale, uint16_t ticks)
{
    uint64_t num = (uint64_t)scale * ticks;
    return (int32_t)((num * 2 + 65535) / (2 * 65535ULL));
}

int32_t sht40_ticks_to_milli_c(uint16_t ticks)
{
    return -45000 + scale_ticks(175000, ticks);
}

int32_t sht40_ticks_to_milli_rh(uint16_t ticks)
{
    return -6000 + scale_ticks(125000, ticks);
}

sht40_decode_t sht40_decode(const uint8_t rx[6], sht40_sample_t *out)
{
    if (!rx || !out) {
        return SHT40_DECODE_BAD_ARG;
    }
    if (sht40_crc8(&rx[0], 2) != rx[2]) {
        return SHT40_DECODE_CRC_T;
    }
    if (sht40_crc8(&rx[3], 2) != rx[5]) {
        return SHT40_DECODE_CRC_RH;
    }
    uint16_t raw_t = (uint16_t)((rx[0] << 8) | rx[1]);
    uint16_t raw_rh = (uint16_t)((rx[3] << 8) | rx[4]);
    int32_t t = sht40_ticks_to_milli_c(raw_t);
    if (t < SHT40_T_MIN_MILLI_C || t > SHT40_T_MAX_MILLI_C) {
        return SHT40_DECODE_T_OUT_OF_RANGE;
    }
    int32_t rh_raw = sht40_ticks_to_milli_rh(raw_rh);
    int32_t rh = rh_raw;
    if (rh < 0) {
        rh = 0;
    } else if (rh > 100000) {
        rh = 100000;
    }
    out->raw_t = raw_t;
    out->raw_rh = raw_rh;
    out->temp_milli_c = t;
    out->rh_milli_pct = rh;
    out->rh_milli_pct_raw = rh_raw;
    return SHT40_DECODE_OK;
}

bool sht40_decode_serial(const uint8_t rx[6], uint32_t *serial)
{
    if (!rx || !serial) {
        return false;
    }
    if (sht40_crc8(&rx[0], 2) != rx[2] || sht40_crc8(&rx[3], 2) != rx[5]) {
        return false;
    }
    *serial = ((uint32_t)rx[0] << 24) | ((uint32_t)rx[1] << 16) | ((uint32_t)rx[3] << 8) | rx[4];
    return true;
}

const char *sht40_decode_str(sht40_decode_t code)
{
    switch (code) {
    case SHT40_DECODE_OK: return "ok";
    case SHT40_DECODE_BAD_ARG: return "bad argument";
    case SHT40_DECODE_CRC_T: return "temperature CRC mismatch";
    case SHT40_DECODE_CRC_RH: return "humidity CRC mismatch";
    case SHT40_DECODE_T_OUT_OF_RANGE: return "temperature out of range";
    }
    return "unknown";
}
