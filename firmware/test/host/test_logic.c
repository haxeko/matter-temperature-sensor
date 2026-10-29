/*
 * Tests for app_logic: Matter scaling/null, publish policy, configuration
 * limits, backoff.
 */
#include "app_config_limits.h"
#include "backoff.h"
#include "guard_policy.h"
#include "matter_scale.h"
#include "report_policy.h"
#include "test_harness.h"

/* ------------------------------------------------------------ matter_scale */

static void test_milli_to_centi_rounding(void)
{
    CHECK_EQ_INT(mx_milli_to_centi(25004), 2500);
    CHECK_EQ_INT(mx_milli_to_centi(25005), 2501);     /* half away from zero */
    CHECK_EQ_INT(mx_milli_to_centi(-25004), -2500);
    CHECK_EQ_INT(mx_milli_to_centi(-25005), -2501);
    CHECK_EQ_INT(mx_milli_to_centi(0), 0);
    CHECK_EQ_INT(mx_milli_to_centi(-4), 0);
    CHECK_EQ_INT(mx_milli_to_centi(-5), -1);
}

static void test_temperature_null_and_signed(void)
{
    mx_nullable_i16_t v = mx_temperature(false, 21000, 0);
    CHECK(v.is_null);                                  /* invalid sample -> null, never 0 */
    v = mx_temperature(true, -12345, 0);               /* -12.345 C */
    CHECK(!v.is_null);
    CHECK_EQ_INT(v.value, -1235);
    v = mx_temperature(true, 21000, -150);             /* offset -1.50 C */
    CHECK_EQ_INT(v.value, 1950);
}

static void test_temperature_clamped_to_advertised_range(void)
{
    mx_nullable_i16_t v = mx_temperature(true, 124900, 500);
    CHECK_EQ_INT(v.value, MX_TEMP_MAX_CENTI);
    v = mx_temperature(true, -39900, -500);
    CHECK_EQ_INT(v.value, MX_TEMP_MIN_CENTI);
}

static void test_humidity_null_and_clamp(void)
{
    mx_nullable_u16_t v = mx_humidity(false, 50000, 0);
    CHECK(v.is_null);
    v = mx_humidity(true, 45678, 0);
    CHECK_EQ_INT(v.value, 4568);
    v = mx_humidity(true, 99500, 1000);                /* +10 %RH offset -> 100 % max */
    CHECK_EQ_INT(v.value, 10000);
    v = mx_humidity(true, 3000, -1000);                /* -10 %RH offset -> 0 % min */
    CHECK_EQ_INT(v.value, 0);
}

/* ---------------------------------------------------------- report_policy */

static void test_policy_deadband(void)
{
    rp_channel_t ch;
    rp_init(&ch, 10, 3);
    CHECK_EQ_INT(rp_on_sample(&ch, true, 2000, false), RP_VALUE);   /* first value always */
    CHECK_EQ_INT(rp_on_sample(&ch, true, 2009, false), RP_NONE);    /* < deadband */
    CHECK_EQ_INT(rp_on_sample(&ch, true, 1991, false), RP_NONE);
    CHECK_EQ_INT(rp_on_sample(&ch, true, 2010, false), RP_VALUE);   /* = deadband */
    CHECK_EQ_INT(ch.last_published, 2010);
    /* slow drift accumulates against the last *published* value */
    CHECK_EQ_INT(rp_on_sample(&ch, true, 2015, false), RP_NONE);
    CHECK_EQ_INT(rp_on_sample(&ch, true, 2019, false), RP_NONE);
    CHECK_EQ_INT(rp_on_sample(&ch, true, 2020, false), RP_VALUE);
    /* user request forces a publish inside the deadband */
    CHECK_EQ_INT(rp_on_sample(&ch, true, 2021, true), RP_VALUE);
}

static void test_policy_failures_publish_null_once(void)
{
    rp_channel_t ch;
    rp_init(&ch, 10, 3);
    CHECK_EQ_INT(rp_on_sample(&ch, true, 2000, false), RP_VALUE);
    CHECK_EQ_INT(rp_on_sample(&ch, false, 0, false), RP_NONE);
    CHECK_EQ_INT(rp_on_sample(&ch, false, 0, false), RP_NONE);
    CHECK_EQ_INT(rp_on_sample(&ch, false, 0, false), RP_NULL);      /* 3rd failure */
    CHECK_EQ_INT(rp_on_sample(&ch, false, 0, false), RP_NONE);      /* already null */
    /* recovery: publish even if equal to the value before the outage */
    CHECK_EQ_INT(rp_on_sample(&ch, true, 2000, false), RP_VALUE);
    CHECK(!ch.published_null);
}

static void test_policy_null_before_first_value(void)
{
    rp_channel_t ch;
    rp_init(&ch, 10, 1);
    CHECK_EQ_INT(rp_on_sample(&ch, false, 0, false), RP_NULL);
    CHECK_EQ_INT(rp_on_sample(&ch, false, 0, false), RP_NONE);
    CHECK_EQ_INT(rp_on_sample(&ch, true, -500, false), RP_VALUE);
}

static void test_policy_single_success_resets_failures(void)
{
    rp_channel_t ch;
    rp_init(&ch, 10, 3);
    rp_on_sample(&ch, true, 100, false);
    rp_on_sample(&ch, false, 0, false);
    rp_on_sample(&ch, false, 0, false);
    rp_on_sample(&ch, true, 101, false);                           /* resets the counter */
    CHECK_EQ_INT(rp_on_sample(&ch, false, 0, false), RP_NONE);
    CHECK_EQ_INT(rp_on_sample(&ch, false, 0, false), RP_NONE);
    CHECK_EQ_INT(rp_on_sample(&ch, false, 0, false), RP_NULL);
}

/* ------------------------------------------------------------------ config */

static const app_cfg_defaults_t k_def = {
    .meas_interval_s = 60, .bat_interval_s = 21600, .temp_deadband_centi = 10,
    .rh_deadband_centi = 100, .led_enabled = true, .tx_power_dbm = 5,
};

static void test_config_defaults_valid(void)
{
    app_cfg_t c;
    app_cfg_set_defaults(&c, &k_def);
    const char *bad = "x";
    CHECK(app_cfg_is_valid(&c, &bad));
    CHECK(bad == NULL);
    CHECK_EQ_INT(c.temp_offset_centi, 0);              /* offsets default to zero */
    CHECK_EQ_INT(c.rh_offset_centi, 0);
}

static void test_config_offset_limits(void)
{
    app_cfg_t c;
    app_cfg_set_defaults(&c, &k_def);
    CHECK(app_cfg_set_temp_offset(&c, 500));
    CHECK(app_cfg_set_temp_offset(&c, -500));
    CHECK(!app_cfg_set_temp_offset(&c, 501));
    CHECK(!app_cfg_set_temp_offset(&c, -501));
    CHECK_EQ_INT(c.temp_offset_centi, -500);           /* rejected input leaves value unchanged */
    CHECK(!app_cfg_set_temp_offset(&c, 70000));        /* would overflow int16 */
    CHECK(app_cfg_set_rh_offset(&c, 1000));
    CHECK(!app_cfg_set_rh_offset(&c, 1001));
    CHECK_EQ_INT(c.rh_offset_centi, 1000);
}

static void test_config_other_limits(void)
{
    app_cfg_t c;
    app_cfg_set_defaults(&c, &k_def);
    CHECK(!app_cfg_set_meas_interval(&c, 9));
    CHECK(app_cfg_set_meas_interval(&c, 10));
    CHECK(!app_cfg_set_meas_interval(&c, 3601));
    CHECK(!app_cfg_set_bat_interval(&c, 599));
    CHECK(app_cfg_set_bat_interval(&c, 86400));
    CHECK(!app_cfg_set_tx_power(&c, 9));               /* power-path limit */
    CHECK(app_cfg_set_tx_power(&c, 8));
    CHECK(!app_cfg_set_tx_power(&c, -25));
    CHECK(!app_cfg_set_temp_deadband(&c, -1));
    CHECK(!app_cfg_set_rh_deadband(&c, 1001));
    const char *bad = NULL;
    c.tx_power_dbm = 20;                                /* corrupted value from storage */
    CHECK(!app_cfg_is_valid(&c, &bad));
    CHECK(bad != NULL);
}

static void test_config_equal_detects_changes(void)
{
    app_cfg_t a, b;
    app_cfg_set_defaults(&a, &k_def);
    b = a;
    CHECK(app_cfg_equal(&a, &b));
    b.led_enabled = !b.led_enabled;
    CHECK(!app_cfg_equal(&a, &b));
    b = a;
    b.rh_offset_centi = 1;
    CHECK(!app_cfg_equal(&a, &b));
}

/* ----------------------------------------------------------------- backoff */

static void test_backoff_sequence(void)
{
    backoff_t b;
    backoff_init(&b, 2000, 60000);
    CHECK_EQ_INT(backoff_next(&b), 2000);
    CHECK_EQ_INT(backoff_next(&b), 4000);
    CHECK_EQ_INT(backoff_next(&b), 8000);
    CHECK_EQ_INT(backoff_next(&b), 16000);
    CHECK_EQ_INT(backoff_next(&b), 32000);
    CHECK_EQ_INT(backoff_next(&b), 60000);             /* saturates */
    CHECK_EQ_INT(backoff_next(&b), 60000);
    backoff_reset(&b);
    CHECK_EQ_INT(backoff_next(&b), 2000);
}

static void test_backoff_for_attempt(void)
{
    CHECK_EQ_INT(backoff_for_attempt(300, 14400, 1), 300);
    CHECK_EQ_INT(backoff_for_attempt(300, 14400, 2), 600);
    CHECK_EQ_INT(backoff_for_attempt(300, 14400, 6), 9600);
    CHECK_EQ_INT(backoff_for_attempt(300, 14400, 7), 14400);
    CHECK_EQ_INT(backoff_for_attempt(300, 14400, 1000), 14400);  /* no overflow */
    CHECK_EQ_INT(backoff_for_attempt(0, 0, 3), 1);               /* degenerate input */
}

/* ----------------------------------------------------------------- boot guard */

static const gp_config_t k_gp = {.boot_min_mv = 2400, .recovery_mv = 150, .backoff_min_s = 300,
                                 .backoff_max_s = 14400};

static void test_guard_normal_boots(void)
{
    gp_state_t st = {0};
    gp_decision_t d = gp_decide(&st, &k_gp, GP_RESET_POWER_ON, 3050);   /* fresh cells */
    CHECK_EQ_INT(d.action, GP_RUN);
    CHECK_EQ_INT(st.unstable_boots, 1);          /* attempt counted until stable */
    CHECK_EQ_INT(st.last_best_mv, 3050);
    CHECK(gp_mark_stable(&st));
    CHECK_EQ_INT(st.unstable_boots, 0);
    CHECK(!gp_mark_stable(&st));                 /* no NVS write when nothing changed */
    d = gp_decide(&st, &k_gp, GP_RESET_SOFTWARE, 3000);
    CHECK_EQ_INT(d.action, GP_RUN);
}

static void test_guard_brownout_loop_backs_off(void)
{
    gp_state_t st = {0};
    CHECK_EQ_INT(gp_decide(&st, &k_gp, GP_RESET_POWER_ON, 2900).action, GP_RUN);
    /* supervisor reset before "stable": looks like power-on */
    gp_decision_t d = gp_decide(&st, &k_gp, GP_RESET_POWER_ON, 2900);
    CHECK_EQ_INT(d.action, GP_SLEEP_UNSTABLE);
    CHECK_EQ_INT(d.sleep_s, 300);
    d = gp_decide(&st, &k_gp, GP_RESET_SLEEP_WAKE, 2910);              /* retry after sleep */
    CHECK_EQ_INT(d.action, GP_RUN);
    CHECK_EQ_INT(st.unstable_boots, 2);
    d = gp_decide(&st, &k_gp, GP_RESET_POWER_ON, 2900);                 /* failed again */
    CHECK_EQ_INT(d.action, GP_SLEEP_UNSTABLE);
    CHECK_EQ_INT(d.sleep_s, 600);
    for (int i = 0; i < 20; i++) {
        gp_decide(&st, &k_gp, GP_RESET_SLEEP_WAKE, 2900);
        d = gp_decide(&st, &k_gp, GP_RESET_FAULT, 2900);
    }
    CHECK_EQ_INT(d.action, GP_SLEEP_UNSTABLE);
    CHECK_EQ_INT(d.sleep_s, 14400);              /* capped */
}

static void test_guard_new_cells_clear(void)
{
    gp_state_t st = {.unstable_boots = 5, .last_best_mv = 2700};
    gp_decision_t d = gp_decide(&st, &k_gp, GP_RESET_POWER_ON, 2849);  /* +149 mV: not enough */
    CHECK_EQ_INT(d.action, GP_SLEEP_UNSTABLE);
    CHECK(!d.cleared);
    d = gp_decide(&st, &k_gp, GP_RESET_POWER_ON, 2850);                 /* +150 mV: new cells */
    CHECK(d.cleared);
    CHECK_EQ_INT(d.action, GP_RUN);
    CHECK_EQ_INT(st.unstable_boots, 1);
    gp_state_t s2 = {.unstable_boots = 3, .last_best_mv = 3000};
    d = gp_decide(&s2, &k_gp, GP_RESET_SOFTWARE, 3000);                 /* factory reset / reboot */
    CHECK(d.cleared);
    CHECK_EQ_INT(d.action, GP_RUN);
}

static void test_guard_low_battery(void)
{
    gp_state_t st = {0};
    gp_decision_t d = gp_decide(&st, &k_gp, GP_RESET_POWER_ON, 2399);
    CHECK_EQ_INT(d.action, GP_SLEEP_LOW_BATTERY);
    CHECK_EQ_INT(d.sleep_s, 300);
    d = gp_decide(&st, &k_gp, GP_RESET_SLEEP_WAKE, 2380);
    CHECK_EQ_INT(d.action, GP_SLEEP_LOW_BATTERY);
    CHECK_EQ_INT(d.sleep_s, 600);
    d = gp_decide(&st, &k_gp, GP_RESET_SLEEP_WAKE, 2390);
    CHECK_EQ_INT(d.sleep_s, 1200);
    d = gp_decide(&st, &k_gp, GP_RESET_POWER_ON, 3100);                 /* cells replaced */
    CHECK_EQ_INT(d.action, GP_RUN);
    CHECK(d.cleared);
    gp_state_t sat = {.unstable_boots = 255, .last_best_mv = 2000};
    d = gp_decide(&sat, &k_gp, GP_RESET_POWER_ON, 1000);
    CHECK_EQ_INT(sat.unstable_boots, 255);       /* saturates, no wrap to 0 */
    CHECK_EQ_INT(d.sleep_s, 14400);
}

void test_matter_scale_all(void)
{
    run_test("scale: milli->centi rounding", test_milli_to_centi_rounding);
    run_test("scale: temperature null/signed/offset", test_temperature_null_and_signed);
    run_test("scale: temperature clamp to Min/Max", test_temperature_clamped_to_advertised_range);
    run_test("scale: humidity null/clamp", test_humidity_null_and_clamp);
}

void test_report_policy_all(void)
{
    run_test("policy: deadband and forced publish", test_policy_deadband);
    run_test("policy: failures -> null once", test_policy_failures_publish_null_once);
    run_test("policy: null before first value", test_policy_null_before_first_value);
    run_test("policy: success resets failure count", test_policy_single_success_resets_failures);
}

void test_config_all(void)
{
    run_test("config: defaults valid, offsets zero", test_config_defaults_valid);
    run_test("config: offset limits", test_config_offset_limits);
    run_test("config: interval/tx/deadband limits", test_config_other_limits);
    run_test("config: change detection", test_config_equal_detects_changes);
}

void test_backoff_all(void)
{
    run_test("backoff: doubling and saturation", test_backoff_sequence);
    run_test("backoff: n-th attempt", test_backoff_for_attempt);
    run_test("guard: normal boots and stable mark", test_guard_normal_boots);
    run_test("guard: brown-out loop backs off", test_guard_brownout_loop_backs_off);
    run_test("guard: new cells / restart clear", test_guard_new_cells_clear);
    run_test("guard: low battery backoff", test_guard_low_battery);
}
