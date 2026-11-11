idf_component_register(SRCS "matter_bridge.cpp"
                       INCLUDE_DIRS "include"
                       PRIV_REQUIRES espressif__esp_matter openthread esp_system nvs_flash log)

target_compile_options(${COMPONENT_LIB} PRIVATE "-DCHIP_HAVE_CONFIG_H")
