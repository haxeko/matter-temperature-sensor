# Host unit tests for the hardware-independent firmware modules.
#   cmake -S firmware/test/host -B build/host-tests && cmake --build build/host-tests
#   ctest --test-dir build/host-tests --output-on-failure
cmake_minimum_required(VERSION 3.16)
project(th_sensor_host_tests C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(FW ${CMAKE_CURRENT_LIST_DIR}/../..)

add_executable(host_tests
    test_main.c
    test_sht40.c
    test_logic.c
    test_gesture_battery.c
    ${FW}/components/sht40/sht40_proto.c
    ${FW}/components/app_logic/matter_scale.c
    ${FW}/components/app_logic/report_policy.c
    ${FW}/components/app_logic/backoff.c
    ${FW}/components/app_logic/button_gesture.c
    ${FW}/components/app_logic/battery_model.c
    ${FW}/components/app_logic/app_config_limits.c
    ${FW}/components/app_logic/guard_policy.c)

target_include_directories(host_tests PRIVATE
    ${CMAKE_CURRENT_LIST_DIR}
    ${FW}/components/sht40/include
    ${FW}/components/app_logic/include)

target_compile_options(host_tests PRIVATE -Wall -Wextra -Werror -Wno-unused-parameter
                       -fsanitize=address,undefined -fno-omit-frame-pointer)
target_link_options(host_tests PRIVATE -fsanitize=address,undefined)
target_link_libraries(host_tests PRIVATE m)

enable_testing()
add_test(NAME host_tests COMMAND host_tests)
