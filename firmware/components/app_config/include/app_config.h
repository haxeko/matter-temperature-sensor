/*
 * Persistent application configuration (NVS namespace "app_cfg").
 *
 * Flash is written only when a value actually changes (console command),
 * never per measurement. A factory reset clears this namespace; Matter
 * fabrics/Thread data are cleared by the SDK and the factory partition
 * ("fctry", esp_secure_cert) is never touched by the application.
 */
#pragma once

#include "esp_err.h"
#include "app_config_limits.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Load from NVS; missing or invalid entries fall back to Kconfig defaults. */
esp_err_t app_config_load(app_cfg_t *out);

/* Persist `cfg` if it differs from the stored copy. *written tells which. */
esp_err_t app_config_save(const app_cfg_t *cfg, bool *written);

/* Erase the namespace (used by factory reset). */
esp_err_t app_config_erase(void);

/* Kconfig-derived defaults. */
void app_config_defaults(app_cfg_t *out);

#ifdef __cplusplus
}
#endif
