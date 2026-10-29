/*
 * Board pin map — single source of truth for firmware.
 *
 * Board: TH-SENSOR-H2 Rev A (hardware/th_sensor_h2.kicad_sch)
 * Module: ESP32-H2-MINI-1-H4S (datasheet v1.6, Table 3 "Pin Definitions").
 *
 * Every assignment below must match docs/pinmap.md and the net names in the
 * KiCad schematic. tools/check_pinmap.py cross-checks this file against the
 * exported KiCad netlist; run it after any change on either side.
 *
 * Module pad numbers are given for traceability (MINI-1 pad, not chip pin).
 */
#pragma once

/* ---- Strapping / boot ---------------------------------------------------
 * GPIO9: BOOT strap, weak pull-up inside, external 10k pull-up on the board.
 *        Low at reset (with GPIO8 high) = Joint Download Boot.
 *        Re-used as the single USER button after boot (active low).
 * GPIO8: strap, floating inside; external 10k pull-up so that GPIO9 low at
 *        reset selects download mode. Not used by the application.
 * GPIO25: JTAG-source strap only when EFUSE_STRAP_JTAG_SEL_ENABLE=1 (not
 *        burnt by default). Left unconnected.
 */
#define BOARD_GPIO_USER_BUTTON      9   /* module pad 23, net BTN_USER, active low */
#define BOARD_USER_BUTTON_ACTIVE    0
#define BOARD_GPIO_STRAP8           8   /* module pad 22, net STRAP_GPIO8 (10k to 3V3) */

/* ---- SHT40 on I2C (external 10k pull-ups to 3V3) ------------------------ */
#define BOARD_GPIO_I2C_SDA          10  /* module pad 20, net I2C_SDA */
#define BOARD_GPIO_I2C_SCL          11  /* module pad 21, net I2C_SCL */
#define BOARD_I2C_PORT              0
#define BOARD_I2C_FREQ_HZ           100000

/* ---- Status LED (active high, 0603 red LED + 1k to GND) ----------------- */
#define BOARD_GPIO_LED              12  /* module pad 16, net LED */
#define BOARD_LED_ACTIVE            1

/* ---- Cell voltage sense (one switched 470k/470k divider per cell) --------
 * Power path (docs/architecture.md): each CR2032 feeds its own TPS63900, so
 * there is no common VBAT_OR node; VBAT1/VBAT2 are the holder terminals.
 * GPIO0 drives both gates of the low-side NMOS pair (Q4A/Q4B) that connect the
 * divider bottoms to GND (1M gate pull-down keeps them off in reset/sleep).
 * Divider mid-points have 22 nF to GND: tau = 235 kOhm * 22 nF = 5.2 ms.
 */
#define BOARD_GPIO_VBAT_MEAS_EN     0   /* module pad 9,  net VBAT_MEAS_EN */
#define BOARD_GPIO_VBAT1_SENSE      1   /* module pad 10, net VBAT1_SENSE, ADC1_CH0 */
#define BOARD_GPIO_VBAT2_SENSE      4   /* module pad 18, net VBAT2_SENSE, ADC1_CH3 */
#define BOARD_VBAT_ADC_UNIT         0   /* ADC_UNIT_1 */
#define BOARD_VBAT1_ADC_CHANNEL     0   /* ADC_CHANNEL_0 */
#define BOARD_VBAT2_ADC_CHANNEL     3   /* ADC_CHANNEL_3 */
#define BOARD_VBAT_DIVIDER_NUM      2   /* V_cell = V_sense * NUM / DEN */
#define BOARD_VBAT_DIVIDER_DEN      1
#define BOARD_VBAT_SETTLE_MS        30  /* > 5 tau */

/* ---- 32.768 kHz crystal (RTC slow clock) -------------------------------- */
#define BOARD_GPIO_XTAL32K_P        13  /* module pad 12 */
#define BOARD_GPIO_XTAL32K_N        14  /* module pad 13 */

/* ---- Debug interfaces (test pads / pogo header J1) ---------------------- */
#define BOARD_GPIO_UART0_RX         23  /* module pad 30 (RXD0) */
#define BOARD_GPIO_UART0_TX         24  /* module pad 31 (TXD0) */
#define BOARD_GPIO_USB_DM           26  /* module pad 26 (22R series) */
#define BOARD_GPIO_USB_DP           27  /* module pad 27 (22R series) */

/* ---- Pins with no connection on Rev A -------------------------------------
 * Configured by board_init() as input-disabled with pull-down so that they
 * cannot float (ESP32-H2 HW design guidelines, section "GPIO").
 * GPIO25 has no internal pulls; input is disabled instead.
 */
#define BOARD_UNUSED_GPIO_LIST      { 2, 3, 5, 22, 25 }
