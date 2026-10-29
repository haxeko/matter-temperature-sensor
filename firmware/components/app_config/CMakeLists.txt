idf_component_register(SRCS "app_config.c"
                       INCLUDE_DIRS "include"
                       REQUIRES app_logic
                       PRIV_REQUIRES nvs_flash log)
