idf_component_register(SRCS "power_guard.c"
                       INCLUDE_DIRS "include"
                       REQUIRES esp_system
                       PRIV_REQUIRES app_logic board esp_hw_support log nvs_flash)
