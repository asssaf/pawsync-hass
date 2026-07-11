import hashlib
import logging
from unittest.mock import AsyncMock, MagicMock

import pytest
from custom_components.pawsync.pawsync import (
    Device,
    context,
    getDeviceList,
    getPetLogList,
    login,
)


@pytest.fixture(autouse=True)
def reset_context():
    # Reset context variables to clean state before each test
    context.pop("accountID", None)
    context.pop("token", None)


def test_device_init():
    data = {
        "deviceName": "Feeder",
        "deviceImg": "img_url",
        "deviceDefaultImg": "default_url",
        "deviceId": "id123",
        "connectionType": "wifi",
        "secondaryCategory": "feeder",
        "deviceModel": "model_x",
        "configModel": "config_y",
        "bizId": "biz123",
        "petId": "pet123",
        "deviceProp": {"level": 100},
    }
    context["terminalId"] = "term123"
    device = Device(data)
    assert device.deviceName == "Feeder"
    assert device.deviceId == "id123"
    assert device.deviceProp == {"level": 100}
    assert device.terminalId == "term123"


@pytest.mark.asyncio
async def test_login_success():
    session = MagicMock()
    mock_response = MagicMock()
    mock_response.json = AsyncMock(
        return_value={
            "code": 0,
            "result": {"accountId": "acc_123", "token": "token_abc"},
        }
    )
    session.post = AsyncMock(return_value=mock_response)

    await login(session, "test@example.com", "password123")
    assert context["accountID"] == "acc_123"
    assert context["token"] == "token_abc"


@pytest.mark.asyncio
async def test_login_failed():
    session = MagicMock()
    mock_response = MagicMock()
    mock_response.json = AsyncMock(return_value={"code": 1, "result": None})
    session.post = AsyncMock(return_value=mock_response)

    res = await login(session, "test@example.com", "password123")
    assert res is None
    assert "accountID" not in context
    assert "token" not in context


@pytest.mark.asyncio
async def test_login_stable_terminal_id():
    session = MagicMock()
    mock_response = MagicMock()
    mock_response.json = AsyncMock(
        return_value={
            "code": 0,
            "result": {"accountId": "acc_123", "token": "token_abc"},
        }
    )
    session.post = AsyncMock(return_value=mock_response)

    original_terminal_id = context.get("terminalId")
    try:
        await login(session, "test@example.com", "password123")
        expected_terminal_id = hashlib.sha256(b"test@example.com").hexdigest()[:32]
        assert context["terminalId"] == expected_terminal_id
    finally:
        if original_terminal_id is not None:
            context["terminalId"] = original_terminal_id


@pytest.mark.asyncio
async def test_get_device_list_success():
    session = MagicMock()
    mock_response = MagicMock()
    mock_response.json = AsyncMock(
        return_value={
            "code": 0,
            "result": {
                "list": [
                    {
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
                        "deviceProp": {"level": 100},
                    }
                ]
            },
        }
    )
    session.post = AsyncMock(return_value=mock_response)
    logger = logging.getLogger("test_logger")

    devices = await getDeviceList(session, logger)
    assert devices is not None
    assert len(devices) == 1
    assert devices[0].deviceName == "Feeder 1"
    assert devices[0].deviceId == "id123"


@pytest.mark.asyncio
async def test_get_device_list_failed():
    session = MagicMock()
    mock_response = MagicMock()
    mock_response.json = AsyncMock(return_value={"code": -1, "result": None})
    session.post = AsyncMock(return_value=mock_response)
    logger = logging.getLogger("test_logger")

    devices = await getDeviceList(session, logger)
    assert devices is None


@pytest.mark.asyncio
async def test_device_request_feed():
    session = MagicMock()
    mock_response = MagicMock()
    session.post = AsyncMock(return_value=mock_response)

    data = {
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
        "deviceProp": {"level": 100},
    }
    context["accountID"] = "acc_123"
    context["token"] = "token_abc"

    device = Device(data)
    res = await device.requestFeed(session, 15)
    assert res == mock_response
    session.post.assert_called_once()


@pytest.mark.asyncio
async def test_get_pet_log_list_success():
    session = MagicMock()
    mock_response = MagicMock()
    mock_response.json = AsyncMock(
        return_value={
            "code": 0,
            "result": {
                "petLogList": [
                    {"timestamp": 1234567890, "logType": "planFeeding", "value": 11}
                ]
            },
        }
    )
    session.post = AsyncMock(return_value=mock_response)
    logger = logging.getLogger("test_logger")

    logs = await getPetLogList(session, "device_123", logger)
    assert len(logs) == 1
    assert logs[0]["logType"] == "planFeeding"
    assert logs[0]["value"] == 11


@pytest.mark.asyncio
async def test_get_pet_log_list_failed():
    session = MagicMock()
    mock_response = MagicMock()
    mock_response.json = AsyncMock(return_value={"code": -1, "result": None})
    session.post = AsyncMock(return_value=mock_response)
    logger = logging.getLogger("test_logger")

    logs = await getPetLogList(session, "device_123", logger)
    assert logs == []
