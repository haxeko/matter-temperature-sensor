/*
 * ESP-Matter integration (ESP-Matter 1.6.0~1 managed component, legacy data model).
 *
 * Threading rule: the data model is only touched on the Matter thread.
 * Publishing from the application task goes through
 * SystemLayer().ScheduleLambda(), as in the ESP-Matter "sensors" example;
 * commissioning-window and status work goes through PlatformMgr().ScheduleWork().
 */
#include "matter_bridge.h"

#include <atomic>
#include <cstring>

#include <esp_log.h>
#include <esp_matter.h>
#include <esp_matter_core.h>

#include <app/clusters/power-source-server/power-source-server.h>
#include <app/server/CommissioningWindowManager.h>
#include <app/server/Server.h>
#include <platform/CHIPDeviceLayer.h>

#if CHIP_DEVICE_CONFIG_ENABLE_THREAD
#include <esp_openthread.h>
#include <esp_openthread_types.h>
#include <openthread/platform/radio.h>
#include <platform/ESP32/OpenthreadLauncher.h>
#include <platform/ThreadStackManager.h>
#endif

static const char *TAG = "matter_bridge";

using namespace esp_matter;
using namespace chip::app::Clusters;
using chip::DeviceLayer::ChipDeviceEvent;

namespace {

mb_config_t s_cfg;
std::atomic<uint8_t> s_fabric_count{0};
std::atomic<bool> s_window_open{false};
std::atomic<bool> s_thread_attached{false};
std::atomic<bool> s_server_ready{false};
std::atomic<int8_t> s_tx_power{0};

constexpr uint16_t kTempToleranceCenti = 20;    /* SHT40 typ. accuracy 0.2 degC (DS v7.3 table 2) */
constexpr uint16_t kRhToleranceCenti = 180;     /* SHT40 typ. accuracy 1.8 %RH (DS v7.3 table 1) */
constexpr uint32_t kBatCapacityMah = 620;       /* CR2450 nominal (Panasonic datasheet, Feb 2026) */

void notify(mb_event_t ev)
{
    if (s_cfg.cb) {
        s_cfg.cb(ev, s_cfg.ctx);
    }
}

/* Runs on the Matter thread. */
void apply_tx_power()
{
#if CHIP_DEVICE_CONFIG_ENABLE_THREAD
    otInstance *ot = esp_openthread_get_instance();
    if (!ot) {
        return;
    }
    chip::DeviceLayer::ThreadStackMgr().LockThreadStack();
    otPlatRadioSetTransmitPower(ot, s_tx_power.load());
    int8_t now = 0;
    otPlatRadioGetTransmitPower(ot, &now);
    chip::DeviceLayer::ThreadStackMgr().UnlockThreadStack();
    ESP_LOGI(TAG, "802.15.4 TX power set to %d dBm", now);
#endif
}

void refresh_fabric_count()
{
    s_fabric_count = static_cast<uint8_t>(chip::Server::GetInstance().GetFabricTable().FabricCount());
}

void set_power_source_endpoint_list()
{
    chip::EndpointId eps[] = {MB_ENDPOINT_ROOT, MB_ENDPOINT_TEMPERATURE, MB_ENDPOINT_HUMIDITY};
    CHIP_ERROR err = PowerSourceServer::Instance().SetEndpointList(MB_ENDPOINT_ROOT, chip::Span<chip::EndpointId>(eps));
    if (err != CHIP_NO_ERROR) {
        ESP_LOGE(TAG, "PowerSource EndpointList: %" CHIP_ERROR_FORMAT, err.Format());
    }
}

void app_event_cb(const ChipDeviceEvent *event, intptr_t arg)
{
    (void)arg;
    namespace DeviceEventType = chip::DeviceLayer::DeviceEventType;
    switch (event->Type) {
    case DeviceEventType::kServerReady:
        refresh_fabric_count();
        set_power_source_endpoint_list();
        apply_tx_power();
        s_server_ready = true;
        ESP_LOGI(TAG, "server ready, %u fabric(s)", s_fabric_count.load());
        notify(MB_EVT_SERVER_READY);
        break;
    case DeviceEventType::kCommissioningComplete:
        refresh_fabric_count();
        ESP_LOGI(TAG, "commissioning complete");
        notify(MB_EVT_COMMISSIONED);
        break;
    case DeviceEventType::kCommissioningWindowOpened:
        s_window_open = true;
        notify(MB_EVT_WINDOW_OPENED);
        break;
    case DeviceEventType::kCommissioningWindowClosed:
        s_window_open = false;
        notify(MB_EVT_WINDOW_CLOSED);
        break;
    case DeviceEventType::kFailSafeTimerExpired:
        ESP_LOGW(TAG, "commissioning failed: fail-safe expired");
        break;
    case DeviceEventType::kFabricRemoved: {
        refresh_fabric_count();
        ESP_LOGI(TAG, "fabric removed, %u left", s_fabric_count.load());
        /* Same policy as the ESP-Matter examples: after the last fabric is
         * removed the Thread credentials are still present, so offer one
         * on-network (DNS-SD) window; BLE is not re-enabled automatically. */
        auto &mgr = chip::Server::GetInstance().GetCommissioningWindowManager();
        if (s_fabric_count == 0 && !mgr.IsCommissioningWindowOpen()) {
            CHIP_ERROR err = mgr.OpenBasicCommissioningWindow(
                chip::System::Clock::Seconds16(s_cfg.commissioning_window_s),
                chip::CommissioningWindowAdvertisement::kDnssdOnly);
            if (err != CHIP_NO_ERROR) {
                ESP_LOGE(TAG, "open window after fabric removal: %" CHIP_ERROR_FORMAT, err.Format());
            }
        }
        notify(MB_EVT_FABRIC_REMOVED);
        break;
    }
#if CHIP_DEVICE_CONFIG_ENABLE_THREAD
    case DeviceEventType::kThreadConnectivityChange:
        if (event->ThreadConnectivityChange.Result == chip::DeviceLayer::kConnectivity_Established) {
            s_thread_attached = true;
            notify(MB_EVT_THREAD_ATTACHED);
        } else if (event->ThreadConnectivityChange.Result == chip::DeviceLayer::kConnectivity_Lost) {
            s_thread_attached = false;
            notify(MB_EVT_THREAD_DETACHED);
        }
        break;
    case DeviceEventType::kThreadStateChange:
        /* The radio PIB is re-initialised to the maximum table power when the
         * 802.15.4 driver is (re)enabled; re-apply the configured value. */
        apply_tx_power();
        break;
#endif
    case DeviceEventType::kBLEDeinitialized:
        ESP_LOGI(TAG, "BLE deinitialized (commissioning-only BLE)");
        break;
    default:
        break;
    }
}

esp_err_t identification_cb(identification::callback_type_t type, uint16_t endpoint_id, uint8_t effect_id,
                            uint8_t effect_variant, void *priv_data)
{
    (void)endpoint_id;
    (void)effect_id;
    (void)effect_variant;
    (void)priv_data;
    if (type == identification::callback_type_t::START || type == identification::callback_type_t::EFFECT) {
        notify(MB_EVT_IDENTIFY_START);
    } else if (type == identification::callback_type_t::STOP) {
        notify(MB_EVT_IDENTIFY_STOP);
    }
    return ESP_OK;
}

esp_err_t attribute_update_cb(attribute::callback_type_t type, uint16_t endpoint_id, uint32_t cluster_id,
                              uint32_t attribute_id, esp_matter_attr_val_t *val, void *priv_data)
{
    /* Sensor device: no writable application attributes. */
    return ESP_OK;
}

esp_err_t add_power_source(node_t *node)
{
    endpoint_t *root = endpoint::get(node, MB_ENDPOINT_ROOT);
    if (!root) {
        return ESP_ERR_INVALID_STATE;
    }
    endpoint::power_source::config_t ps;
    ps.power_source.status = chip::to_underlying(PowerSource::PowerSourceStatusEnum::kActive);
    ps.power_source.order = 0;
    strncpy(ps.power_source.description, "1x CR2450, buck-boost 3.3 V",
            sizeof(ps.power_source.description) - 1);
    ps.power_source.feature_flags = cluster::power_source::feature::battery::get_id() |
                                    cluster::power_source::feature::replaceable::get_id();
    ps.power_source.features.battery.bat_charge_level = chip::to_underlying(PowerSource::BatChargeLevelEnum::kOk);
    ps.power_source.features.battery.bat_replacement_needed = false;
    ps.power_source.features.battery.bat_replaceability =
        chip::to_underlying(PowerSource::BatReplaceabilityEnum::kUserReplaceable);
    strncpy(ps.power_source.features.replaceable.bat_replacement_description,
            "Replace with a new CR2450 (primary lithium, never recharge)",
            sizeof(ps.power_source.features.replaceable.bat_replacement_description) - 1);
    ps.power_source.features.replaceable.bat_quantity = 1;
    esp_err_t err = endpoint::power_source::add(root, &ps);
    if (err != ESP_OK) {
        return err;
    }
    cluster_t *c = cluster::get(root, PowerSource::Id);
    if (!c) {
        return ESP_ERR_INVALID_STATE;
    }
    namespace psa = cluster::power_source::attribute;
    psa::create_bat_voltage(c, nullable<uint32_t>(), nullable<uint32_t>(0), nullable<uint32_t>(6000));
    psa::create_bat_percent_remaining(c, nullable<uint8_t>(), nullable<uint8_t>(0), nullable<uint8_t>(200));
    psa::create_bat_present(c, true);
    psa::create_bat_iec_designation(c, "CR2450", strlen("CR2450"));
    psa::create_bat_approved_chemistry(c, chip::to_underlying(PowerSource::BatApprovedChemistryEnum::kLithiumManganeseDioxide),
                                       0, 0xFF);
    psa::create_bat_capacity(c, kBatCapacityMah, 0, UINT32_MAX);
    return ESP_OK;
}

} // namespace

extern "C" esp_err_t mb_init(const mb_config_t *cfg)
{
    if (!cfg) {
        return ESP_ERR_INVALID_ARG;
    }
    s_cfg = *cfg;
    s_tx_power = cfg->thread_tx_power_dbm;

    node::config_t node_config;
    node_t *node = node::create(&node_config, attribute_update_cb, identification_cb);
    if (!node) {
        ESP_LOGE(TAG, "node create failed");
        return ESP_FAIL;
    }

    endpoint::temperature_sensor::config_t tcfg;
    tcfg.temperature_measurement.measured_value = nullable<int16_t>();
    tcfg.temperature_measurement.min_measured_value = nullable<int16_t>(-4000);
    tcfg.temperature_measurement.max_measured_value = nullable<int16_t>(12500);
    endpoint_t *t_ep = endpoint::temperature_sensor::create(node, &tcfg, ENDPOINT_FLAG_NONE, nullptr);
    endpoint::humidity_sensor::config_t hcfg;
    hcfg.relative_humidity_measurement.measured_value = nullable<uint16_t>();
    hcfg.relative_humidity_measurement.min_measured_value = nullable<uint16_t>(0);
    hcfg.relative_humidity_measurement.max_measured_value = nullable<uint16_t>(10000);
    endpoint_t *h_ep = endpoint::humidity_sensor::create(node, &hcfg, ENDPOINT_FLAG_NONE, nullptr);
    if (!t_ep || !h_ep) {
        ESP_LOGE(TAG, "sensor endpoint create failed");
        return ESP_FAIL;
    }
    if (endpoint::get_id(t_ep) != MB_ENDPOINT_TEMPERATURE || endpoint::get_id(h_ep) != MB_ENDPOINT_HUMIDITY) {
        ESP_LOGE(TAG, "unexpected endpoint ids %u/%u", endpoint::get_id(t_ep), endpoint::get_id(h_ep));
        return ESP_ERR_INVALID_STATE;
    }
    cluster::temperature_measurement::attribute::create_tolerance(
        cluster::get(t_ep, TemperatureMeasurement::Id), kTempToleranceCenti);
    cluster::relative_humidity_measurement::attribute::create_tolerance(
        cluster::get(h_ep, RelativeHumidityMeasurement::Id), kRhToleranceCenti);

    esp_err_t err = add_power_source(node);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "power source: %s", esp_err_to_name(err));
        return err;
    }

#if CHIP_DEVICE_CONFIG_ENABLE_THREAD
    static esp_openthread_platform_config_t ot_cfg = {};
    ot_cfg.radio_config.radio_mode = RADIO_MODE_NATIVE;
    ot_cfg.host_config.host_connection_mode = HOST_CONNECTION_MODE_NONE;
    ot_cfg.port_config.storage_partition_name = "nvs";
    ot_cfg.port_config.netif_queue_size = 10;
    ot_cfg.port_config.task_queue_size = 10;
    set_openthread_platform_config(&ot_cfg);
#endif
    return ESP_OK;
}

extern "C" esp_err_t mb_start(void)
{
    return esp_matter::start(app_event_cb);
}

extern "C" void mb_publish_temperature(bool is_null, int16_t centi_c)
{
    chip::DeviceLayer::SystemLayer().ScheduleLambda([is_null, centi_c]() {
        esp_matter_attr_val_t val = is_null ? esp_matter_nullable_int16(nullable<int16_t>())
                                            : esp_matter_nullable_int16(nullable<int16_t>(centi_c));
        attribute::update(MB_ENDPOINT_TEMPERATURE, TemperatureMeasurement::Id,
                          TemperatureMeasurement::Attributes::MeasuredValue::Id, &val);
    });
}

extern "C" void mb_publish_humidity(bool is_null, uint16_t centi_pct)
{
    chip::DeviceLayer::SystemLayer().ScheduleLambda([is_null, centi_pct]() {
        esp_matter_attr_val_t val = is_null ? esp_matter_nullable_uint16(nullable<uint16_t>())
                                            : esp_matter_nullable_uint16(nullable<uint16_t>(centi_pct));
        attribute::update(MB_ENDPOINT_HUMIDITY, RelativeHumidityMeasurement::Id,
                          RelativeHumidityMeasurement::Attributes::MeasuredValue::Id, &val);
    });
}

extern "C" void mb_publish_battery(const mb_battery_t *battery)
{
    if (!battery) {
        return;
    }
    const mb_battery_t b = *battery;
    chip::DeviceLayer::SystemLayer().ScheduleLambda([b]() {
        esp_matter_attr_val_t v = b.voltage_valid ? esp_matter_nullable_uint32(nullable<uint32_t>(b.voltage_mv))
                                                  : esp_matter_nullable_uint32(nullable<uint32_t>());
        attribute::update(MB_ENDPOINT_ROOT, PowerSource::Id, PowerSource::Attributes::BatVoltage::Id, &v);
        v = b.percent_valid ? esp_matter_nullable_uint8(nullable<uint8_t>(b.percent_half))
                            : esp_matter_nullable_uint8(nullable<uint8_t>());
        attribute::update(MB_ENDPOINT_ROOT, PowerSource::Id, PowerSource::Attributes::BatPercentRemaining::Id, &v);
        v = esp_matter_enum8(b.charge_level);
        attribute::update(MB_ENDPOINT_ROOT, PowerSource::Id, PowerSource::Attributes::BatChargeLevel::Id, &v);
        v = esp_matter_bool(b.replacement_needed);
        attribute::update(MB_ENDPOINT_ROOT, PowerSource::Id, PowerSource::Attributes::BatReplacementNeeded::Id, &v);
        v = esp_matter_bool(b.present);
        attribute::update(MB_ENDPOINT_ROOT, PowerSource::Id, PowerSource::Attributes::BatPresent::Id, &v);
    });
}

extern "C" void mb_open_commissioning_window(void)
{
    CHIP_ERROR sched = chip::DeviceLayer::PlatformMgr().ScheduleWork([](intptr_t) {
        auto &server = chip::Server::GetInstance();
        auto &mgr = server.GetCommissioningWindowManager();
        if (mgr.IsCommissioningWindowOpen()) {
            ESP_LOGI(TAG, "commissioning window already open");
            notify(MB_EVT_WINDOW_OPENED);
            return;
        }
        const bool has_fabric = server.GetFabricTable().FabricCount() > 0;
        const auto adv = has_fabric ? chip::CommissioningWindowAdvertisement::kDnssdOnly
                                    : chip::CommissioningWindowAdvertisement::kAllSupported;
        CHIP_ERROR err = mgr.OpenBasicCommissioningWindow(
            chip::System::Clock::Seconds16(s_cfg.commissioning_window_s), adv);
        if (err != CHIP_NO_ERROR) {
            ESP_LOGE(TAG, "open commissioning window: %" CHIP_ERROR_FORMAT, err.Format());
            notify(MB_EVT_WINDOW_FAILED);
        } else {
            ESP_LOGI(TAG, "commissioning window open for %u s (%s)", s_cfg.commissioning_window_s,
                     has_fabric ? "on-network, existing fabrics kept" : "BLE + on-network");
        }
    });
    if (sched != CHIP_NO_ERROR) {
        ESP_LOGE(TAG, "schedule commissioning window: %" CHIP_ERROR_FORMAT, sched.Format());
        notify(MB_EVT_WINDOW_FAILED);
    }
}

extern "C" void mb_set_tx_power(int8_t dbm)
{
    s_tx_power = dbm;
    CHIP_ERROR err = chip::DeviceLayer::PlatformMgr().ScheduleWork([](intptr_t) { apply_tx_power(); });
    if (err != CHIP_NO_ERROR) {
        ESP_LOGE(TAG, "schedule TX power update: %" CHIP_ERROR_FORMAT, err.Format());
    }
}

extern "C" void mb_factory_reset(void)
{
    ESP_LOGW(TAG, "factory reset: clearing fabrics, Thread dataset and Matter KVS");
    esp_matter::factory_reset();
}

extern "C" void mb_get_status(mb_status_t *out)
{
    if (!out) {
        return;
    }
    out->fabric_count = s_fabric_count;
    out->window_open = s_window_open;
    out->thread_attached = s_thread_attached;
    out->server_ready = s_server_ready;
}
