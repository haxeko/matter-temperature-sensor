idf_component_register(SRCS "battery.c"
                       INCLUDE_DIRS "include"
                       PRIV_REQUIRES board esp_adc esp_pm freertos log)
