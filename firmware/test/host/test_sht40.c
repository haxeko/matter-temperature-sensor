/*
 * SHT40 protocol tests. Reference values come from the datasheet (v7.3):
 * CRC(0xBEEF) = 0x92, conversion formulas (1) and (2).
 */
#include <string.h>
#include "sht40_proto.h"
#include "test_harness.h"

/* Independent table-free reference CRC written from the spec text, used to
 * build test frames (so the decoder is not tested against itself only). */
static uint8_t ref_crc(uint8_t msb, uint8_t lsb)
{
    uint16_t reg = 0xFF;
    uint8_t bytes[2] = {msb, lsb};
    for (int i = 0; i < 2; i++) {
        reg ^= bytes[i];
        for (int b = 0; b < 8; b++) {
            reg = (reg & 0x80) ? ((reg << 1) ^ 0x131) : (reg << 1);
        }
    }
    return (uint8_t)reg;
}

static void frame(uint8_t rx[6], uint16_t t, uint16_t rh)
{
    rx[0] = t >> 8;
    rx[1] = t & 0xFF;
    rx[2] = ref_crc(rx[0], rx[1]);
    rx[3] = rh >> 8;
    rx[4] = rh & 0xFF;
    rx[5] = ref_crc(rx[3], rx[4]);
}

static void test_crc_datasheet_example(void)
{
    const uint8_t beef[2] = {0xBE, 0xEF};
    CHECK_EQ_INT(sht40_crc8(beef, 2), 0x92);
    CHECK_EQ_INT(ref_crc(0xBE, 0xEF), 0x92);
}

static void test_conversion_endpoints(void)
{
    CHECK_EQ_INT(sht40_ticks_to_milli_c(0), -45000);
    CHECK_EQ_INT(sht40_ticks_to_milli_c(65535), 130000);
    CHECK_EQ_INT(sht40_ticks_to_milli_rh(0), -6000);
    CHECK_EQ_INT(sht40_ticks_to_milli_rh(65535), 119000);
    /* 26214/65535 = 0.40000: T = -45 + 70.000 = 25.000 C, RH = -6 + 50.000 = 44.000 % */
    CHECK_EQ_INT(sht40_ticks_to_milli_c(26214), 25000);
    CHECK_EQ_INT(sht40_ticks_to_milli_rh(26214), 44000);
}

static void test_conversion_matches_float_formula(void)
{
    /* Exhaustive check against the datasheet formula, rounded to 1 milli-unit. */
    int worst = 0;
    for (uint32_t t = 0; t <= 65535; t++) {
        double ft = (-45.0 + 175.0 * t / 65535.0) * 1000.0;
        double fr = (-6.0 + 125.0 * t / 65535.0) * 1000.0;
        long et = (long)(ft >= 0 ? ft + 0.5 : ft - 0.5);
        long er = (long)(fr >= 0 ? fr + 0.5 : fr - 0.5);
        int dt = (int)labs(et - sht40_ticks_to_milli_c((uint16_t)t));
        int dr = (int)labs(er - sht40_ticks_to_milli_rh((uint16_t)t));
        if (dt > worst) worst = dt;
        if (dr > worst) worst = dr;
    }
    CHECK(worst <= 1);
}

static void test_decode_valid(void)
{
    uint8_t rx[6];
    sht40_sample_t s;
    frame(rx, 26214, 26214);
    CHECK_EQ_INT(sht40_decode(rx, &s), SHT40_DECODE_OK);
    CHECK_EQ_INT(s.temp_milli_c, 25000);
    CHECK_EQ_INT(s.rh_milli_pct, 44000);
    CHECK_EQ_INT(s.raw_t, 26214);
}

static void test_decode_rejects_crc_errors(void)
{
    uint8_t rx[6];
    sht40_sample_t s;
    memset(&s, 0x5A, sizeof(s));
    sht40_sample_t untouched = s;

    frame(rx, 26214, 30000);
    rx[2] ^= 0x01;
    CHECK_EQ_INT(sht40_decode(rx, &s), SHT40_DECODE_CRC_T);
    CHECK(memcmp(&s, &untouched, sizeof(s)) == 0);

    frame(rx, 26214, 30000);
    rx[4] ^= 0x80;                    /* corrupt humidity data, keep its CRC */
    CHECK_EQ_INT(sht40_decode(rx, &s), SHT40_DECODE_CRC_RH);
    CHECK(memcmp(&s, &untouched, sizeof(s)) == 0);

    /* Every single-bit error in the 6-byte frame must be caught. */
    int caught = 0;
    for (int byte = 0; byte < 6; byte++) {
        for (int bit = 0; bit < 8; bit++) {
            frame(rx, 26214, 30000);
            rx[byte] ^= (uint8_t)(1u << bit);
            if (sht40_decode(rx, &s) != SHT40_DECODE_OK) {
                caught++;
            }
        }
    }
    CHECK_EQ_INT(caught, 48);
}

static void test_decode_bus_stuck_patterns(void)
{
    sht40_sample_t s;
    uint8_t ones[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};   /* SDA stuck high / no device */
    uint8_t zeros[6] = {0};                                   /* SDA stuck low */
    CHECK(sht40_decode(ones, &s) != SHT40_DECODE_OK);
    CHECK(sht40_decode(zeros, &s) != SHT40_DECODE_OK);
}

static void test_decode_range_and_crop(void)
{
    uint8_t rx[6];
    sht40_sample_t s;
    frame(rx, 0, 26214);              /* -45 C: outside the -40..125 C specification */
    CHECK_EQ_INT(sht40_decode(rx, &s), SHT40_DECODE_T_OUT_OF_RANGE);
    frame(rx, 65535, 26214);          /* +130 C */
    CHECK_EQ_INT(sht40_decode(rx, &s), SHT40_DECODE_T_OUT_OF_RANGE);

    frame(rx, 26214, 65535);          /* RH 119 %: cropped to 100 % */
    CHECK_EQ_INT(sht40_decode(rx, &s), SHT40_DECODE_OK);
    CHECK_EQ_INT(s.rh_milli_pct, 100000);
    CHECK_EQ_INT(s.rh_milli_pct_raw, 119000);
    frame(rx, 26214, 0);              /* RH -6 %: cropped to 0 % */
    CHECK_EQ_INT(sht40_decode(rx, &s), SHT40_DECODE_OK);
    CHECK_EQ_INT(s.rh_milli_pct, 0);
}

static void test_serial(void)
{
    uint8_t rx[6];
    uint32_t serial = 0;
    frame(rx, 0x1234, 0x5678);
    CHECK(sht40_decode_serial(rx, &serial));
    CHECK_EQ_INT(serial, 0x12345678);
    rx[5] ^= 1;
    CHECK(!sht40_decode_serial(rx, &serial));
}

void test_sht40_all(void)
{
    run_test("sht40: CRC datasheet example", test_crc_datasheet_example);
    run_test("sht40: conversion endpoints", test_conversion_endpoints);
    run_test("sht40: conversion == formula (all ticks)", test_conversion_matches_float_formula);
    run_test("sht40: decode valid frame", test_decode_valid);
    run_test("sht40: CRC errors rejected (all 1-bit)", test_decode_rejects_crc_errors);
    run_test("sht40: stuck bus patterns rejected", test_decode_bus_stuck_patterns);
    run_test("sht40: T range check, RH crop", test_decode_range_and_crop);
    run_test("sht40: serial number", test_serial);
}
