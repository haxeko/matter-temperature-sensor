/*
 * Maintenance console (esp_console REPL on the primary console, normally
 * USB Serial/JTAG). Advanced parameters are only changeable here; there is
 * no Wi-Fi AP, web page or custom BLE protocol on this device.
 *
 * While a USB host is connected, ESP-IDF keeps the chip out of automatic
 * light sleep (CONFIG_USJ_NO_AUTO_LS_ON_CONNECTION) so the console stays
 * responsive; on batteries with nothing connected it costs nothing.
 */
#pragma once

#include <stdint.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    void (*print_status)(void);
    void (*print_config)(void);
    void (*request_measure)(void);
    void (*request_battery)(void);
    esp_err_t (*config_set)(const char *key, int32_t value);
    esp_err_t (*heater)(int milliwatt, int duration_ms);
    void (*open_window)(void);
    void (*factory_reset)(void);
} maint_console_ops_t;

esp_err_t maint_console_start(const maint_console_ops_t *ops);

#ifdef __cplusplus
}
#endif
