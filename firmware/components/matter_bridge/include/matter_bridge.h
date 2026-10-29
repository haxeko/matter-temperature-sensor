/*
 * C interface between the application controller and ESP-Matter.
 *
 * All publish/command functions may be called from any task: they copy their
 * arguments and schedule the actual data-model access on the Matter thread.
 * Event callbacks are invoked on the Matter thread; they must not block.
 *
 * Data model:
 *   EP0 Root Node + Power Source (battery, replaceable, EndpointList {0,1,2})
 *       + ICD Management (SIT, from Kconfig)
 *   EP1 Temperature Sensor  (Temperature Measurement, Identify)
 *   EP2 Humidity Sensor     (Relative Humidity Measurement, Identify)
 * Endpoint IDs are created in a fixed order and are therefore stable across
 * reboots and firmware updates of this application.
 */
#pragma once

#include <stdbool.h>
#include <stdint.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

#define MB_ENDPOINT_ROOT         0
#define MB_ENDPOINT_TEMPERATURE  1
#define MB_ENDPOINT_HUMIDITY     2

typedef enum {
    MB_EVT_SERVER_READY,
    MB_EVT_COMMISSIONED,
    MB_EVT_WINDOW_OPENED,
    MB_EVT_WINDOW_CLOSED,
    MB_EVT_WINDOW_FAILED,
    MB_EVT_FABRIC_REMOVED,
    MB_EVT_THREAD_ATTACHED,
    MB_EVT_THREAD_DETACHED,
    MB_EVT_IDENTIFY_START,
    MB_EVT_IDENTIFY_STOP,
} mb_event_t;

typedef void (*mb_event_cb_t)(mb_event_t event, void *ctx);

typedef struct {
    mb_event_cb_t cb;
    void *ctx;
    int8_t thread_tx_power_dbm;       /* applied once OpenThread is up */
    uint16_t commissioning_window_s;  /* window length for user-opened windows */
} mb_config_t;

typedef struct {
    bool present;                     /* BatPresent: at least one cell detected */
    bool voltage_valid;
    uint32_t voltage_mv;              /* BatVoltage: highest cell voltage */
    bool percent_valid;
    uint8_t percent_half;             /* BatPercentRemaining, 0..200 */
    uint8_t charge_level;             /* BatChargeLevelEnum */
    bool replacement_needed;
} mb_battery_t;

typedef struct {
    uint8_t fabric_count;
    bool window_open;
    bool thread_attached;
    bool server_ready;
} mb_status_t;

/* Build the data model. Must be called once before mb_start(). */
esp_err_t mb_init(const mb_config_t *cfg);

/* esp_matter::start(); OpenThread and BLE commissioning start here. */
esp_err_t mb_start(void);

void mb_publish_temperature(bool is_null, int16_t centi_c);
void mb_publish_humidity(bool is_null, uint16_t centi_pct);
void mb_publish_battery(const mb_battery_t *battery);

/*
 * Open a commissioning window using the standard Matter API:
 *  - no fabric yet : Basic Commissioning Window, BLE + DNS-SD
 *  - fabric(s) exist: Basic Commissioning Window, DNS-SD (on-network) only;
 *                     existing fabrics are kept (multi-admin).
 */
void mb_open_commissioning_window(void);

void mb_set_tx_power(int8_t dbm);

/* Matter/Thread factory reset (SDK procedure); reboots. */
void mb_factory_reset(void);

void mb_get_status(mb_status_t *out);

#ifdef __cplusplus
}
#endif
