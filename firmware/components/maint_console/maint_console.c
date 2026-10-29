/*
 * Maintenance console commands.
 */
#include "maint_console.h"

#include <stdlib.h>
#include <string.h>
#include "esp_console.h"
#include "esp_log.h"
#include "esp_system.h"
#include "sdkconfig.h"

static const char *TAG = "console";
static maint_console_ops_t s_ops;

static bool parse_i32(const char *s, int32_t *out)
{
    char *end = NULL;
    long v = strtol(s, &end, 10);
    if (!s[0] || *end != '\0') {
        return false;
    }
    *out = (int32_t)v;
    return true;
}

static int cmd_status(int argc, char **argv)
{
    s_ops.print_status();
    return 0;
}

static int cmd_measure(int argc, char **argv)
{
    s_ops.request_measure();
    printf("measurement requested\n");
    return 0;
}

static int cmd_battery(int argc, char **argv)
{
    s_ops.request_battery();
    printf("battery measurement requested\n");
    return 0;
}

static int cmd_config(int argc, char **argv)
{
    if (argc == 1 || (argc == 2 && strcmp(argv[1], "show") == 0)) {
        s_ops.print_config();
        return 0;
    }
    int32_t v;
    if (argc == 4 && strcmp(argv[1], "set") == 0 && parse_i32(argv[3], &v)) {
        esp_err_t err = s_ops.config_set(argv[2], v);
        if (err == ESP_OK) {
            printf("ok\n");
            return 0;
        }
        printf("rejected: %s\n", esp_err_to_name(err));
        return 1;
    }
    printf("usage: config [show]\n"
           "       config set <key> <value>\n"
           "keys:  temp_offset (0.01 degC, -500..500), rh_offset (0.01 %%RH, -1000..1000),\n"
           "       meas_interval (s, 10..3600), bat_interval (s, 600..86400),\n"
           "       temp_deadband (0.01 degC, 0..200), rh_deadband (0.01 %%RH, 0..1000),\n"
           "       led (0/1), tx_power (dBm, -24..8)\n");
    return 1;
}

static int cmd_heater(int argc, char **argv)
{
    int32_t mw = 0, ms = 0;
    if (argc != 3 || !parse_i32(argv[1], &mw) || !parse_i32(argv[2], &ms)) {
        printf("usage: heater <20|110> <100|1000>\n"
               "Runs one SHT40 heater pulse (maintenance, e.g. after condensation).\n"
               "The heated reading is printed but never published; scheduled\n"
               "publishing is suspended until the sensor has cooled down.\n");
        return 1;
    }
    esp_err_t err = s_ops.heater(mw, ms);
    if (err != ESP_OK) {
        printf("heater: %s\n", esp_err_to_name(err));
        return 1;
    }
    return 0;
}

static int cmd_window(int argc, char **argv)
{
    s_ops.open_window();
    printf("commissioning window requested\n");
    return 0;
}

static int cmd_factory_reset(int argc, char **argv)
{
    if (argc != 2 || strcmp(argv[1], "confirm") != 0) {
        printf("usage: factory_reset confirm\n"
               "Erases fabrics, Thread dataset, Matter KVS and app settings.\n"
               "Factory provisioning data (fctry / esp_secure_cert) is kept.\n");
        return 1;
    }
    s_ops.factory_reset();
    return 0;
}

static int cmd_reboot(int argc, char **argv)
{
    esp_restart();
    return 0;
}

esp_err_t maint_console_start(const maint_console_ops_t *ops)
{
    if (!ops) {
        return ESP_ERR_INVALID_ARG;
    }
    s_ops = *ops;

    esp_console_repl_t *repl = NULL;
    esp_console_repl_config_t repl_cfg = ESP_CONSOLE_REPL_CONFIG_DEFAULT();
    repl_cfg.prompt = "th-sensor>";
    repl_cfg.max_cmdline_length = 128;
    repl_cfg.task_stack_size = 4096;

    esp_err_t err;
#if CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG
    esp_console_dev_usb_serial_jtag_config_t hw_cfg = ESP_CONSOLE_DEV_USB_SERIAL_JTAG_CONFIG_DEFAULT();
    err = esp_console_new_repl_usb_serial_jtag(&hw_cfg, &repl_cfg, &repl);
#elif CONFIG_ESP_CONSOLE_UART_DEFAULT || CONFIG_ESP_CONSOLE_UART_CUSTOM
    esp_console_dev_uart_config_t hw_cfg = ESP_CONSOLE_DEV_UART_CONFIG_DEFAULT();
    err = esp_console_new_repl_uart(&hw_cfg, &repl_cfg, &repl);
#else
    ESP_LOGW(TAG, "no console device configured");
    return ESP_ERR_NOT_SUPPORTED;
#endif
    if (err != ESP_OK) {
        return err;
    }

    const esp_console_cmd_t cmds[] = {
        {.command = "status", .help = "Show sensor, battery, Matter and power-guard status", .func = cmd_status},
        {.command = "measure", .help = "Take a measurement now", .func = cmd_measure},
        {.command = "battery", .help = "Measure the battery voltage now", .func = cmd_battery},
        {.command = "config", .help = "Show or change settings (config set <key> <value>)", .func = cmd_config},
        {.command = "heater", .help = "Maintenance SHT40 heater pulse: heater <mW> <ms>", .func = cmd_heater},
        {.command = "window", .help = "Open a commissioning window", .func = cmd_window},
        {.command = "factory_reset", .help = "factory_reset confirm", .func = cmd_factory_reset},
        {.command = "reboot", .help = "Restart the chip", .func = cmd_reboot},
    };
    for (size_t i = 0; i < sizeof(cmds) / sizeof(cmds[0]); i++) {
        esp_console_cmd_register(&cmds[i]);
    }
    err = esp_console_start_repl(repl);
    if (err == ESP_OK) {
        ESP_LOGI(TAG, "maintenance console started (type 'help')");
    }
    return err;
}
