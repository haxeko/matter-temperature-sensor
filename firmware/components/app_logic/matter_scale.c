#include "matter_scale.h"

int32_t mx_milli_to_centi(int32_t milli)
{
    return (milli >= 0) ? (milli + 5) / 10 : -((-milli + 5) / 10);
}

static int32_t clamp_i32(int32_t v, int32_t lo, int32_t hi)
{
    return v < lo ? lo : (v > hi ? hi : v);
}

mx_nullable_i16_t mx_temperature(bool valid, int32_t temp_milli_c, int16_t offset_centi_c)
{
    mx_nullable_i16_t r = {.is_null = true, .value = 0};
    if (!valid) {
        return r;
    }
    int32_t centi = mx_milli_to_centi(temp_milli_c) + offset_centi_c;
    r.is_null = false;
    r.value = (int16_t)clamp_i32(centi, MX_TEMP_MIN_CENTI, MX_TEMP_MAX_CENTI);
    return r;
}

mx_nullable_u16_t mx_humidity(bool valid, int32_t rh_milli_pct, int16_t offset_centi_pct)
{
    mx_nullable_u16_t r = {.is_null = true, .value = 0};
    if (!valid) {
        return r;
    }
    int32_t centi = mx_milli_to_centi(rh_milli_pct) + offset_centi_pct;
    r.is_null = false;
    r.value = (uint16_t)clamp_i32(centi, MX_RH_MIN_CENTI, MX_RH_MAX_CENTI);
    return r;
}
