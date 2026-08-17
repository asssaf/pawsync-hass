from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from custom_components.pawsync.pawsync import Device
from custom_components.pawsync.sensor import (
    LOG_SENSOR_TYPES,
    SENSOR_TYPES,
    PawsyncDeviceSensor,
    PawsyncLogSensor,
    _get_next_scheduled_feeding_time,
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
            "scheduleInfo": {
                "planId": 3,
                "repeat": 254,
                "nextDay": 2,
                "nextTime": 75600,
                "nextMount": 16,
                "count": 3,
                "totalMealG": 32,
            },
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
    assert sensors[11].native_value is not None
    assert sensors[12].native_value == 16

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


def test_next_scheduled_feeding_time():
    with patch("homeassistant.util.dt.now") as mock_now:
        # Simulate Monday at 10:00:00 (weekday() == 0)
        monday_dt = datetime(2026, 8, 17, 10, 0, 0, tzinfo=UTC)
        mock_now.return_value = monday_dt

        # Case 1: Next meal later today (21:00 = 75600 sec, nextDay=2 for Monday)
        device = Device(
            {
                "deviceName": "Feeder",
                "deviceImg": "",
                "deviceDefaultImg": "",
                "deviceId": "id1",
                "connectionType": "wifi",
                "secondaryCategory": "feeder",
                "deviceModel": "m",
                "configModel": "c",
                "bizId": "b",
                "petId": "p",
                "deviceProp": {
                    "scheduleInfo": {
                        "nextTime": 75600,
                        "nextDay": 2,
                        "nextMount": 16,
                    }
                },
            }
        )
        assert _get_next_scheduled_feeding_time(device) == datetime(
            2026, 8, 17, 21, 0, 0, tzinfo=UTC
        )

        # Case 2: Next meal was earlier today, rolls to next week same day (nextDay=2)
        device.deviceProp["scheduleInfo"]["nextTime"] = 28800  # 08:00
        assert _get_next_scheduled_feeding_time(device) == datetime(
            2026, 8, 24, 8, 0, 0, tzinfo=UTC
        )

        # Case 3: Next meal on Wednesday (nextDay=4, nextTime=08:00)
        device.deviceProp["scheduleInfo"]["nextDay"] = 4
        device.deviceProp["scheduleInfo"]["nextTime"] = 28800
        assert _get_next_scheduled_feeding_time(device) == datetime(
            2026, 8, 19, 8, 0, 0, tzinfo=UTC
        )

        # Case 4: No nextDay specified, earlier today -> rolls to tomorrow
        device.deviceProp["scheduleInfo"] = {
            "planId": 1,
            "repeat": 254,
            "nextTime": 28800,
        }
        assert _get_next_scheduled_feeding_time(device) == datetime(
            2026, 8, 18, 8, 0, 0, tzinfo=UTC
        )

        # Case 5: Nothing scheduled (all zeros)
        device.deviceProp["scheduleInfo"] = {
            "planId": 0,
            "repeat": 0,
            "nextDay": 0,
            "nextTime": 0,
            "nextMount": 0,
            "count": 3,
            "totalMealG": 0,
        }
        assert _get_next_scheduled_feeding_time(device) is None

        # Case 6: No scheduleInfo or empty -> returns None
        device.deviceProp["scheduleInfo"] = {}
        assert _get_next_scheduled_feeding_time(device) is None
        device.deviceProp.pop("scheduleInfo")
        assert _get_next_scheduled_feeding_time(device) is None


def test_next_scheduled_feeding_amount():
    coordinator = MagicMock()
    coordinator.last_update_success = True

    amount_desc = next(
        desc for desc in SENSOR_TYPES if desc.key == "next_scheduled_feeding_amount"
    )

    device_data = {
        "deviceName": "Feeder",
        "deviceImg": "",
        "deviceDefaultImg": "",
        "deviceId": "id1",
        "connectionType": "wifi",
        "secondaryCategory": "feeder",
        "deviceModel": "m",
        "configModel": "c",
        "bizId": "b",
        "petId": "p",
        "deviceProp": {
            "scheduleInfo": {
                "planId": 3,
                "repeat": 254,
                "nextDay": 2,
                "nextTime": 75600,
                "nextMount": 16,
            }
        },
    }
    device = Device(device_data)
    sensor = PawsyncDeviceSensor(coordinator, device, amount_desc)
    assert sensor.native_value == 16

    # Test nothing scheduled (all zeros) -> None
    device.deviceProp["scheduleInfo"] = {
        "planId": 0,
        "repeat": 0,
        "nextDay": 0,
        "nextTime": 0,
        "nextMount": 0,
        "count": 3,
        "totalMealG": 0,
    }
    assert sensor.native_value is None

    # Test missing scheduleInfo -> None
    device.deviceProp.pop("scheduleInfo")
    assert sensor.native_value is None
