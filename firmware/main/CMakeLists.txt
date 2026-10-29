idf_component_register(SRCS "app_main.cpp" "app_controller.c"
                       INCLUDE_DIRS "."
                       PRIV_REQUIRES app_config app_logic battery board maint_console matter_bridge
                                     power_guard sht40 user_button
                                     esp_pm esp_timer esp_hw_support nvs_flash freertos log)
