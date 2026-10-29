idf_component_register(SRCS "user_button.c"
                       INCLUDE_DIRS "include"
                       REQUIRES app_logic
                       PRIV_REQUIRES board esp_timer log)
