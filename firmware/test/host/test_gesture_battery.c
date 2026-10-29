/*
 * Tests for the USER button gestures (short / triple / long-press reset)
 * and for the battery level model.
 */
#include "battery_model.h"
#include "button_gesture.h"
#include "test_harness.h"

/* Drive the recognizer like the firmware does: tick at every deadline. */
typedef struct {
    bg_state_t s;
    uint32_t t;
    bg_event_t log[16];
    int n;
} sim_t;

static void sim_init(sim_t *m, uint32_t start)
{
    bg_init(&m->s, NULL);
    m->t = start;
    m->n = 0;
}

static void record(sim_t *m, bg_event_t e)
{
    if (e != BG_EVT_NONE && m->n < 16) {
        m->log[m->n++] = e;
    }
}

/* Advance time to t_target, firing ticks at each deadline on the way. */
static void advance(sim_t *m, uint32_t dt)
{
    uint32_t target = m->t + dt;
    uint32_t d;
    while (bg_next_deadline(&m->s, &d) && (int32_t)(d - target) <= 0) {
        if ((int32_t)(d - m->t) > 0) {
            m->t = d;
        }
        record(m, bg_on_tick(&m->s, m->t));
    }
    m->t = target;
}

static void press(sim_t *m) { record(m, bg_on_press(&m->s, m->t)); }
static void release(sim_t *m) { record(m, bg_on_release(&m->s, m->t)); }

static void click(sim_t *m, uint32_t hold, uint32_t gap)
{
    press(m);
    advance(m, hold);
    release(m);
    advance(m, gap);
}

static void test_short_press(void)
{
    sim_t m;
    sim_init(&m, 1000);
    click(&m, 120, 2000);
    CHECK_EQ_INT(m.n, 1);
    CHECK_EQ_INT(m.log[0], BG_EVT_SHORT);
}

static void test_triple_press(void)
{
    sim_t m;
    sim_init(&m, 5000);
    click(&m, 100, 250);
    click(&m, 100, 250);
    press(&m);
    advance(&m, 100);
    release(&m);                                   /* 3rd release at +800 ms */
    advance(&m, 3000);
    CHECK_EQ_INT(m.n, 1);
    CHECK_EQ_INT(m.log[0], BG_EVT_TRIPLE);         /* no extra SHORT afterwards */
}

static void test_triple_too_slow_is_ignored(void)
{
    sim_t m;
    sim_init(&m, 0);
    click(&m, 400, 700);
    click(&m, 400, 700);
    press(&m);
    advance(&m, 400);
    release(&m);                                   /* 3rd release at 2.6 s > 2 s */
    advance(&m, 3000);
    CHECK_EQ_INT(m.n, 1);
    CHECK_EQ_INT(m.log[0], BG_EVT_IGNORED);
}

static void test_double_click_is_not_a_short_press(void)
{
    sim_t m;
    sim_init(&m, 0);
    click(&m, 100, 200);
    click(&m, 100, 3000);
    CHECK_EQ_INT(m.n, 1);
    CHECK_EQ_INT(m.log[0], BG_EVT_IGNORED);
}

static void test_long_press_reset_on_release(void)
{
    sim_t m;
    sim_init(&m, 100);
    press(&m);
    advance(&m, 9999);
    CHECK_EQ_INT(m.n, 0);                          /* nothing before 10 s */
    advance(&m, 1);
    CHECK_EQ_INT(m.n, 1);
    CHECK_EQ_INT(m.log[0], BG_EVT_LONG_ARMED);     /* feedback, no reset yet */
    advance(&m, 2000);
    release(&m);
    CHECK_EQ_INT(m.n, 2);
    CHECK_EQ_INT(m.log[1], BG_EVT_LONG_RELEASED);  /* reset only on release */
}

static void test_stuck_button_never_resets(void)
{
    sim_t m;
    sim_init(&m, 0);
    press(&m);
    advance(&m, 61000);
    release(&m);
    advance(&m, 5000);
    CHECK_EQ_INT(m.n, 2);
    CHECK_EQ_INT(m.log[0], BG_EVT_LONG_ARMED);
    CHECK_EQ_INT(m.log[1], BG_EVT_LONG_CANCELLED);
}

static void test_long_release_without_ticks(void)
{
    bg_state_t s;
    bg_init(&s, NULL);
    CHECK_EQ_INT(bg_on_press(&s, 0), BG_EVT_NONE);
    CHECK_EQ_INT(bg_on_release(&s, 10500), BG_EVT_LONG_RELEASED);
    CHECK_EQ_INT(bg_on_press(&s, 20000), BG_EVT_NONE);
    CHECK_EQ_INT(bg_on_release(&s, 90000), BG_EVT_LONG_CANCELLED);
}

static void test_medium_press_and_glitch(void)
{
    sim_t m;
    sim_init(&m, 0);
    click(&m, 3000, 2000);                         /* 3 s: neither click nor reset */
    CHECK_EQ_INT(m.n, 1);
    CHECK_EQ_INT(m.log[0], BG_EVT_IGNORED);
    sim_init(&m, 0);
    click(&m, 10, 2000);                           /* 10 ms glitch: dropped */
    CHECK_EQ_INT(m.n, 0);
}

static void test_click_then_long_press_is_reset_only(void)
{
    sim_t m;
    sim_init(&m, 0);
    click(&m, 100, 300);
    press(&m);
    advance(&m, 10500);
    release(&m);
    CHECK_EQ_INT(m.n, 2);
    CHECK_EQ_INT(m.log[0], BG_EVT_LONG_ARMED);
    CHECK_EQ_INT(m.log[1], BG_EVT_LONG_RELEASED);
}

static void test_counter_wraparound(void)
{
    sim_t m;
    sim_init(&m, 0xFFFFFF00u);                     /* ms counter wraps during the gesture */
    click(&m, 100, 250);
    click(&m, 100, 250);
    click(&m, 100, 3000);
    CHECK_EQ_INT(m.n, 1);
    CHECK_EQ_INT(m.log[0], BG_EVT_TRIPLE);
}

/* ----------------------------------------------------------------- battery */

static void test_percent_table(void)
{
    CHECK_EQ_INT(bat_half_percent_from_cell_mv(3300), 200);
    CHECK_EQ_INT(bat_half_percent_from_cell_mv(3050), 200);
    CHECK_EQ_INT(bat_half_percent_from_cell_mv(2900), 100);
    CHECK_EQ_INT(bat_half_percent_from_cell_mv(2300), 0);
    CHECK_EQ_INT(bat_half_percent_from_cell_mv(1800), 0);
    CHECK_EQ_INT(bat_half_percent_from_cell_mv(2925), 120);   /* midway 50..70 % */
    uint8_t prev = 255;
    int monotonic = 1;
    for (uint32_t mv = 2200; mv <= 3200; mv += 5) {
        uint8_t p = bat_half_percent_from_cell_mv(mv);
        if (prev != 255 && p < prev) {
            monotonic = 0;
        }
        prev = p;
    }
    CHECK(monotonic);
}

static bat_pack_t pack_of(uint32_t mv1, uint32_t mv2)
{
    const uint32_t mv[BAT_CELL_COUNT] = {mv1, mv2};
    bat_pack_t p;
    bat_pack_from_cells(&p, mv, 1500);
    return p;
}

static void test_pack_aggregate(void)
{
    bat_pack_t p = pack_of(3050, 2900);          /* 100 % and 50 % */
    CHECK_EQ_INT(p.cells_present, 2);
    CHECK_EQ_INT(p.best_mv, 3050);
    CHECK_EQ_INT(p.cell_half_pct[0], 200);
    CHECK_EQ_INT(p.cell_half_pct[1], 100);
    CHECK_EQ_INT(p.pack_half_pct, 150);          /* 75 % */
    p = pack_of(0, 3050);                        /* empty holder counts as 0 % */
    CHECK_EQ_INT(p.cells_present, 1);
    CHECK(!p.present[0] && p.present[1]);
    CHECK_EQ_INT(p.best_mv, 3050);
    CHECK_EQ_INT(p.pack_half_pct, 100);
    p = pack_of(1499, 1200);
    CHECK_EQ_INT(p.cells_present, 0);
    CHECK_EQ_INT(p.best_mv, 0);
    CHECK_EQ_INT(p.pack_half_pct, 0);
    p = pack_of(70000, 3000);                    /* out-of-range reading saturates */
    CHECK_EQ_INT(p.cell_mv[0], 0xFFFF);
}

static void test_pack_level(void)
{
    const bat_policy_t pol = BAT_POLICY_INIT(1500, 40, 20);
    bat_state_t st = {0};
    bat_pack_t p = pack_of(3050, 3050);
    CHECK_EQ_INT(bat_pack_update(&st, &pol, &p), BAT_LEVEL_OK);
    p = pack_of(2850, 2850);                     /* 35 % < 40 % */
    CHECK_EQ_INT(bat_pack_update(&st, &pol, &p), BAT_LEVEL_WARNING);
    p = pack_of(2875, 2875);                     /* 42.5 %: inside hysteresis */
    CHECK_EQ_INT(bat_pack_update(&st, &pol, &p), BAT_LEVEL_WARNING);
    p = pack_of(2900, 2900);                     /* 50 % >= 45 % exit */
    CHECK_EQ_INT(bat_pack_update(&st, &pol, &p), BAT_LEVEL_OK);
    p = pack_of(0, 3050);                        /* one cell removed */
    CHECK_EQ_INT(bat_pack_update(&st, &pol, &p), BAT_LEVEL_WARNING);
    p = pack_of(2700, 2650);                     /* best cell 2700 mV, pack ~10.5 % < 20 % */
    CHECK_EQ_INT(bat_pack_update(&st, &pol, &p), BAT_LEVEL_CRITICAL);
    p = pack_of(2400, 2590);                     /* best cell below 2600 mV */
    CHECK_EQ_INT(bat_pack_update(&st, &pol, &p), BAT_LEVEL_CRITICAL);
    p = pack_of(2850, 2900);                     /* recovered above the exits: WARNING */
    CHECK_EQ_INT(bat_pack_update(&st, &pol, &p), BAT_LEVEL_WARNING);
    p = pack_of(3100, 3100);                     /* new cells */
    CHECK_EQ_INT(bat_pack_update(&st, &pol, &p), BAT_LEVEL_OK);
    bat_state_t st2 = {0};
    p = pack_of(0, 0);                           /* no cells (debug supply only) */
    CHECK_EQ_INT(bat_pack_update(&st2, &pol, &p), BAT_LEVEL_CRITICAL);
    p = pack_of(3100, 3100);
    CHECK_EQ_INT(bat_pack_update(&st2, &pol, &p), BAT_LEVEL_OK);
    bat_state_t st3 = {0};
    p = pack_of(3100, 0);                        /* first reading with one cell: WARNING */
    CHECK_EQ_INT(bat_pack_update(&st3, &pol, &p), BAT_LEVEL_WARNING);
}

static void test_percent_filter(void)
{
    CHECK_EQ_INT(bat_filter_half_percent(false, 0, 150), 150);
    CHECK_EQ_INT(bat_filter_half_percent(true, 150, 147), 150);   /* -1.5 %: suppressed */
    CHECK_EQ_INT(bat_filter_half_percent(true, 150, 146), 146);   /* -2 %: reported */
    CHECK_EQ_INT(bat_filter_half_percent(true, 100, 115), 100);   /* +7.5 %: temperature drift */
    CHECK_EQ_INT(bat_filter_half_percent(true, 100, 120), 120);   /* +10 %: new cells */
}

void test_gesture_all(void)
{
    run_test("button: short press", test_short_press);
    run_test("button: triple press within 2 s", test_triple_press);
    run_test("button: slow triple ignored", test_triple_too_slow_is_ignored);
    run_test("button: double click ignored", test_double_click_is_not_a_short_press);
    run_test("button: >=10 s hold resets on release", test_long_press_reset_on_release);
    run_test("button: stuck button cancels reset", test_stuck_button_never_resets);
    run_test("button: long release without ticks", test_long_release_without_ticks);
    run_test("button: medium press / glitch", test_medium_press_and_glitch);
    run_test("button: click then long press", test_click_then_long_press_is_reset_only);
    run_test("button: ms counter wrap-around", test_counter_wraparound);
}

void test_battery_all(void)
{
    run_test("battery: percent table monotonic", test_percent_table);
    run_test("battery: pack aggregate / missing cell", test_pack_aggregate);
    run_test("battery: pack charge level hysteresis", test_pack_level);
    run_test("battery: percent jitter filter", test_percent_filter);
}
