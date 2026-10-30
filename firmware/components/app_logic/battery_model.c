#include "battery_model.h"

#include <stddef.h>

/* Rest-voltage (mV) to remaining-capacity (%) points for a Li-MnO2 coin cell at
 * light load, derived from the shape of the Panasonic CR2032 discharge curve
 * (datasheet Feb-2026, 15 kOhm, 20 degC). Rev B applies it to the CR2450 on the
 * assumption that the same chemistry gives the same voltage-vs-fraction shape;
 * not checked against a CR2450 curve. Indicative only. */
static const struct {
    uint16_t mv;
    uint8_t pct;
} k_curve[] = {
    {3050, 100}, {3000, 90}, {2950, 70}, {2900, 50}, {2850, 35},
    {2800, 25},  {2700, 12}, {2600, 6},  {2500, 3},  {2400, 1}, {2300, 0},
};

uint8_t bat_half_percent_from_cell_mv(uint32_t cell_mv)
{
    const size_t n = sizeof(k_curve) / sizeof(k_curve[0]);
    if (cell_mv >= k_curve[0].mv) {
        return 200;
    }
    if (cell_mv <= k_curve[n - 1].mv) {
        return 0;
    }
    for (size_t i = 1; i < n; i++) {
        if (cell_mv >= k_curve[i].mv) {
            /* Linear interpolation between point i (lower) and i-1 (upper). */
            uint32_t v0 = k_curve[i].mv, v1 = k_curve[i - 1].mv;
            uint32_t p0 = k_curve[i].pct * 2u, p1 = k_curve[i - 1].pct * 2u;
            uint32_t half = p0 + ((cell_mv - v0) * (p1 - p0) + (v1 - v0) / 2) / (v1 - v0);
            return (uint8_t)(half > 200 ? 200 : half);
        }
    }
    return 0;
}

uint8_t bat_filter_half_percent(bool have_last, uint8_t last, uint8_t fresh)
{
    if (!have_last) {
        return fresh;
    }
    if (fresh < last) {
        return (last - fresh >= 4) ? fresh : last;     /* report drops of >= 2 % */
    }
    return (fresh - last >= 20) ? fresh : last;        /* rises only >= 10 % (new cells) */
}

void bat_pack_from_cells(bat_pack_t *out, const uint32_t cell_mv[BAT_CELL_COUNT], uint16_t present_mv)
{
    uint32_t sum = 0;
    out->cells_present = 0;
    out->best_mv = 0;
    for (int i = 0; i < BAT_CELL_COUNT; i++) {
        uint32_t mv = cell_mv[i] > 0xFFFFu ? 0xFFFFu : cell_mv[i];
        out->cell_mv[i] = (uint16_t)mv;
        out->present[i] = mv >= present_mv;
        out->cell_half_pct[i] = out->present[i] ? bat_half_percent_from_cell_mv(mv) : 0;
        if (out->present[i]) {
            out->cells_present++;
            if (mv > out->best_mv) {
                out->best_mv = (uint16_t)mv;
            }
        }
        sum += out->cell_half_pct[i];
    }
    out->pack_half_pct = (uint8_t)((sum + BAT_CELL_COUNT / 2) / BAT_CELL_COUNT);
}

static bool critical_now(const bat_policy_t *pol, const bat_pack_t *p)
{
    return p->cells_present == 0 || p->best_mv < pol->crit_cell_mv || p->pack_half_pct < pol->crit_enter_half;
}

static bat_level_t classify(const bat_policy_t *pol, const bat_pack_t *p)
{
    if (critical_now(pol, p)) {
        return BAT_LEVEL_CRITICAL;
    }
    if (p->cells_present < BAT_CELL_COUNT || p->pack_half_pct < pol->warn_enter_half) {
        return BAT_LEVEL_WARNING;
    }
    return BAT_LEVEL_OK;
}

bat_level_t bat_pack_update(bat_state_t *st, const bat_policy_t *pol, const bat_pack_t *p)
{
    if (!st->initialized) {
        st->initialized = true;
        st->level = classify(pol, p);
        return st->level;
    }
    const bool all_present = p->cells_present == BAT_CELL_COUNT;
    const bool ok_again = all_present && p->pack_half_pct >= pol->warn_exit_half;
    switch (st->level) {
    case BAT_LEVEL_OK:
        st->level = classify(pol, p);
        break;
    case BAT_LEVEL_WARNING:
        if (critical_now(pol, p)) {
            st->level = BAT_LEVEL_CRITICAL;
        } else if (ok_again) {
            st->level = BAT_LEVEL_OK;
        }
        break;
    case BAT_LEVEL_CRITICAL:
        if (ok_again && p->best_mv >= pol->crit_cell_exit_mv) {
            st->level = BAT_LEVEL_OK;          /* fresh cells inserted */
        } else if (p->cells_present > 0 && p->best_mv >= pol->crit_cell_exit_mv &&
                   p->pack_half_pct >= pol->crit_exit_half) {
            st->level = BAT_LEVEL_WARNING;
        }
        break;
    }
    return st->level;
}
