from unittest.mock import MagicMock

from custom_components.pawsync.binary_sensor import (
    BINARY_SENSOR_TYPES,
    PawsyncDeviceBinarySensor,
)
from custom_components.pawsync.pawsync import Device


def test_binary_sensors():
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
            "powerAdapter": 1,
            "intelligentFeedingSwitch": 0,
            "slowFeedSwitch": 1,
            "accurateFeeding": 0,
        },
    }
    device = Device(device_data)
    coordinator = MagicMock()
    coordinator.last_update_success = True

    sensors = [
        PawsyncDeviceBinarySensor(coordinator, device, desc)
        for desc in BINARY_SENSOR_TYPES
    ]

    assert sensors[0].is_on is True
    assert sensors[1].is_on is False
    assert sensors[2].is_on is True
    assert sensors[3].is_on is False
