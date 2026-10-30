# ESP-IDF project: Matter-over-Thread temperature/humidity sensor (ESP32-H2, 1x CR2450).
# ESP-Matter is consumed as a managed component (see main/idf_component.yml), so no
# ESP_MATTER_PATH checkout is needed to build.
cmake_minimum_required(VERSION 3.16)

set(PROJECT_VER "0.1.0")
set(PROJECT_VER_NUMBER 1)

include($ENV{IDF_PATH}/tools/cmake/project.cmake)

project(th_sensor)

# Same compile options as the ESP-Matter examples of the locked release.
idf_build_set_property(CXX_COMPILE_OPTIONS "-std=gnu++17;-Os;-DCHIP_HAVE_CONFIG_H;-Wno-overloaded-virtual" APPEND)
idf_build_set_property(C_COMPILE_OPTIONS "-Os" APPEND)
idf_build_set_property(COMPILE_OPTIONS "-Wno-format-nonliteral;-Wno-format-security" APPEND)
