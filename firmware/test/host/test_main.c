#include "test_harness.h"

int g_failures = 0;
int g_checks = 0;

void run_test(const char *name, test_fn_t fn)
{
    int before = g_failures;
    fn();
    printf("%-48s %s\n", name, g_failures == before ? "ok" : "FAILED");
}

void test_sht40_all(void);
void test_matter_scale_all(void);
void test_report_policy_all(void);
void test_config_all(void);
void test_gesture_all(void);
void test_battery_all(void);
void test_backoff_all(void);

int main(void)
{
    test_sht40_all();
    test_matter_scale_all();
    test_report_policy_all();
    test_config_all();
    test_gesture_all();
    test_battery_all();
    test_backoff_all();
    printf("\n%d checks, %d failures\n", g_checks, g_failures);
    return g_failures ? 1 : 0;
}
