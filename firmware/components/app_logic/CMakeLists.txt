# Pure application logic: no ESP-IDF API calls, built unchanged by the host
# unit tests in test/host.
idf_component_register(SRCS "matter_scale.c" "report_policy.c" "backoff.c"
                            "button_gesture.c" "battery_model.c" "app_config_limits.c"
                            "guard_policy.c"
                       INCLUDE_DIRS "include")
