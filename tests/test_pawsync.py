import pytest
import importlib.util
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Load pawsync.py directly to bypass package __init__.py which requires Home Assistant
spec = importlib.util.spec_from_file_location(
    "pawsync_standalone", Path(__file__).parent.parent / "pawsync.py"
)
pawsync = importlib.util.module_from_spec(spec)
sys.modules["pawsync_standalone"] = pawsync
spec.loader.exec_module(pawsync)

login = pawsync.login
getDeviceList = pawsync.getDeviceList
Device = pawsync.Device
context = pawsync.context


@pytest.mark.asyncio
async def test_login_success():
    # Mock response
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(
        return_value={
            "code": 0,
            "result": {"accountId": "test_account_123", "token": "test_token_456"},
        }
    )

    mock_session = MagicMock()
    mock_session.post = AsyncMock(return_value=mock_response)

    # Reset context before test
    context.pop("accountID", None)
    context.pop("token", None)

    await login(mock_session, "test@example.com", "password123")

    assert context["accountID"] == "test_account_123"
    assert context["token"] == "test_token_456"
    assert context["terminalId"] is not None


@pytest.mark.asyncio
async def test_login_failure(caplog):
    # Mock response with error
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(return_value={"code": 1001, "result": None})

    mock_session = MagicMock()
    mock_session.post = AsyncMock(return_value=mock_response)

    # Reset context
    context.pop("accountID", None)
    context.pop("token", None)

    await login(mock_session, "test@example.com", "password123")

    assert "accountID" not in context
    assert "token" not in context


@pytest.mark.asyncio
async def test_get_device_list():
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(
        return_value={
            "code": 0,
            "result": {
                "list": [
                    {
                        "deviceName": "Feeder 1",
                        "deviceImg": "img_url",
                        "deviceDefaultImg": "default_img_url",
                        "deviceId": "device_123",
                        "connectionType": "wifi",
                        "secondaryCategory": "feeder",
                        "deviceModel": "model_abc",
                        "configModel": "config_xyz",
                        "bizId": "biz_1",
                        "petId": "pet_1",
                        "deviceProp": {"feedStatus": "ok"},
                    }
                ]
            },
        }
    )

    mock_session = MagicMock()
    mock_session.post = AsyncMock(return_value=mock_response)

    logger = MagicMock()
    devices = await getDeviceList(mock_session, logger)

    assert devices is not None
    assert len(devices) == 1
    assert devices[0].deviceId == "device_123"
    assert devices[0].deviceName == "Feeder 1"


@pytest.mark.asyncio
async def test_device_request_feed():
    device_data = {
        "deviceName": "Feeder 1",
        "deviceImg": "img_url",
        "deviceDefaultImg": "default_img_url",
        "deviceId": "device_123",
        "connectionType": "wifi",
        "secondaryCategory": "feeder",
        "deviceModel": "model_abc",
        "configModel": "config_xyz",
        "bizId": "biz_1",
        "petId": "pet_1",
        "deviceProp": {"feedStatus": "ok"},
    }

    device = Device(device_data)

    mock_response = AsyncMock()
    mock_session = MagicMock()
    mock_session.post = AsyncMock(return_value=mock_response)

    # Initialize some dummy context variables
    context["accountID"] = "test_account_123"
    context["token"] = "test_token_456"
    context["clientVersion"] = "Pawsync 1.0.85"
    context["debugMode"] = "false"
    context["osInfo"] = "Android 15"
    context["timeZone"] = "America/Los_Angeles"
    context["traceId"] = "trace_abc"

    response = await device.requestFeed(mock_session, 15)

    assert response == mock_response
    mock_session.post.assert_called_once()

    # Verify post args
    args, kwargs = mock_session.post.call_args
    assert args[0] == "https://smartapi.pawsync.com/pet/api/deviceManaged/v1/bypassV2"

    payload = kwargs["json"]
    assert payload["cid"] == "device_123"
    assert payload["payload"]["method"] == "manualFeeding"
    assert payload["payload"]["data"]["serving1"] == 15
