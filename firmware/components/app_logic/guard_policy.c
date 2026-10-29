#include "guard_policy.h"

#include "backoff.h"

static uint8_t sat_inc(uint8_t v)
{
    return v == UINT8_MAX ? v : (uint8_t)(v + 1);
}

gp_decision_t gp_decide(gp_state_t *st, const gp_config_t *cfg, gp_reset_t reset, uint16_t best_mv)
{
    gp_decision_t d = {.action = GP_RUN, .sleep_s = 0, .cleared = false};

    if (st->unstable_boots && reset == GP_RESET_SOFTWARE) {
        st->unstable_boots = 0;
        d.cleared = true;
    }
    if (st->unstable_boots && (uint32_t)best_mv >= (uint32_t)st->last_best_mv + cfg->recovery_mv) {
        st->unstable_boots = 0;
        d.cleared = true;
    }
    if (best_mv < cfg->boot_min_mv) {
        st->unstable_boots = sat_inc(st->unstable_boots);
        st->last_best_mv = best_mv;
        d.action = GP_SLEEP_LOW_BATTERY;
        d.sleep_s = backoff_for_attempt(cfg->backoff_min_s, cfg->backoff_max_s, st->unstable_boots);
        return d;
    }
    if (st->unstable_boots && reset != GP_RESET_SLEEP_WAKE) {
        d.action = GP_SLEEP_UNSTABLE;
        d.sleep_s = backoff_for_attempt(cfg->backoff_min_s, cfg->backoff_max_s, st->unstable_boots);
        return d;
    }
    st->unstable_boots = sat_inc(st->unstable_boots);
    st->last_best_mv = best_mv;
    return d;
}

bool gp_mark_stable(gp_state_t *st)
{
    if (!st->unstable_boots) {
        return false;
    }
    st->unstable_boots = 0;
    return true;
}
