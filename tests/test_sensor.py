from datetime import UTC, datetime
from unittest.mock import MagicMock

from custom_components.pawsync.pawsync import Device
from custom_components.pawsync.sensor import (
    LOG_SENSOR_TYPES,
    SENSOR_TYPES,
    PawsyncDeviceSensor,
    PawsyncLogSensor,
)


def test_sensors():
    device_data = {
        "deviceName": "Feeder 1",
        "deviceImg": "img_url",
        "deviceDefaultImg": "default_url",
        "deviceId": "id123",
        "connectionType": "wifi",
        "secondaryCategory": "feeder",
        "deviceModel": "model_x",
        "configModel": "config_y",
        "bizId": "biz123",
        "petId": "pet123",
        "deviceProp": {
            "connectionStatus": "online",
            "contentInPot": 250,
            "bowlWeight": 5,
            "petFood": {
                "bucketSurplus": 1500,
                "lastFeedingAmount": 12,
                "contentRemainTime": 5,
            },
            "batteryPercent": 85,
            "wifiRssi": -60,
            "alertCount": 0,
            "firmwareInfos": [
                {"version": "1.0.85", "isMainFw": True},
                {"version": "mcu_1.0", "pluginName": "mcuFw"},
            ],
        },
    }
    device = Device(device_data)
    coordinator = MagicMock()
    coordinator.last_update_success = True

    sensors = [PawsyncDeviceSensor(coordinator, device, desc) for desc in SENSOR_TYPES]

    assert sensors[0].native_value == "online"
    assert sensors[1].native_value == 250
    assert sensors[2].native_value == 5
    assert sensors[3].native_value == 1500
    assert sensors[4].native_value == 12
    assert sensors[5].native_value == 5
    assert sensors[6].native_value == 85
    assert sensors[7].native_value == -60
    assert sensors[8].native_value == 0
    assert sensors[9].native_value == "1.0.85"
    assert sensors[10].native_value == "mcu_1.0"

    assert sensors[0]._attr_extra_state_attributes["device_id"] == "id123"
    assert sensors[0]._attr_extra_state_attributes["device_name"] == "Feeder 1"

    assert sensors[0].available is True
    coordinator.last_update_success = False
    assert sensors[0].available is False


def test_log_sensors():
    device_data = {
        "deviceName": "Feeder 1",
        "deviceImg": "img_url",
        "deviceDefaultImg": "default_url",
        "deviceId": "id123",
        "connectionType": "wifi",
        "secondaryCategory": "feeder",
        "deviceModel": "model_x",
        "configModel": "config_y",
        "bizId": "biz123",
        "petId": "pet123",
        "deviceProp": {},
    }
    device = Device(device_data)
    coordinator = MagicMock()
    coordinator.last_update_success = True
    coordinator.config_entry.options = {}

    logs = [
        {"timestamp": 1713600000, "logType": "planFeeding", "value": 11},
        {
            "timestamp": 1713610000,
            "logType": "takeFood",
            "value": 8,
            "durationInS": 120,
        },
    ]

    sensors = [
        PawsyncLogSensor(coordinator, device, desc, logs) for desc in LOG_SENSOR_TYPES
    ]

    assert sensors[0].native_value == datetime.fromtimestamp(1713600000, tz=UTC)
    assert sensors[1].native_value == 11
    assert sensors[2].native_value == datetime.fromtimestamp(1713610000, tz=UTC)
    assert sensors[3].native_value == 8
    assert sensors[4].native_value == 120
