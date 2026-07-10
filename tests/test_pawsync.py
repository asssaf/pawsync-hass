import aiohttp
import pytest

from pawsync import PawsyncClient


@pytest.mark.asyncio
async def test_login_success(aresponses):
    aresponses.add(
        "smartapi.pawsync.com",
        "/pet/api/userManaged/v1/login",
        "POST",
        aresponses.Response(
            status=200,
            content_type="application/json",
            text='{"code": 0, "result": {"accountId": "test_account", "token": "test_token"}}',
        ),
    )

    async with aiohttp.ClientSession() as session:
        client = PawsyncClient(session)
        success = await client.login("test@example.com", "password")
        assert success is True
        assert client.context["accountID"] == "test_account"
        assert client.context["token"] == "test_token"


@pytest.mark.asyncio
async def test_login_failure(aresponses):
    aresponses.add(
        "smartapi.pawsync.com",
        "/pet/api/userManaged/v1/login",
        "POST",
        aresponses.Response(
            status=200,
            content_type="application/json",
            text='{"code": 1, "message": "fail"}',
        ),
    )

    async with aiohttp.ClientSession() as session:
        client = PawsyncClient(session)
        success = await client.login("test@example.com", "password")
        assert success is False


@pytest.mark.asyncio
async def test_get_device_list(aresponses):
    aresponses.add(
        "smartapi.pawsync.com",
        "/pet/api/deviceManaged/v1/deviceList4Pet",
        "POST",
        aresponses.Response(
            status=200,
            content_type="application/json",
            text='{"code": 0, "result": {"list": [{"deviceName": "Feeder", "deviceImg": "img", "deviceDefaultImg": "dimg", "deviceId": "123", "connectionType": 1, "secondaryCategory": "cat", "deviceModel": "model", "configModel": "conf", "bizId": "biz", "petId": "pet", "deviceProp": {}}]}}',
        ),
    )

    async with aiohttp.ClientSession() as session:
        client = PawsyncClient(session)
        devices = await client.get_device_list()
        assert len(devices) == 1
        assert devices[0].deviceName == "Feeder"
        assert devices[0].deviceId == "123"


@pytest.mark.asyncio
async def test_request_feed(aresponses):
    aresponses.add(
        "smartapi.pawsync.com",
        "/pet/api/deviceManaged/v1/bypassV2",
        "POST",
        aresponses.Response(
            status=200,
            content_type="application/json",
            text='{"code": 0, "result": "ok"}',
        ),
    )

    async with aiohttp.ClientSession() as session:
        client = PawsyncClient(session)
        client.context["accountID"] = "test_account"
        client.context["token"] = "test_token"

        device_data = {
            "deviceName": "Feeder",
            "deviceImg": "img",
            "deviceDefaultImg": "dimg",
            "deviceId": "123",
            "connectionType": 1,
            "secondaryCategory": "cat",
            "deviceModel": "model",
            "configModel": "conf",
            "bizId": "biz",
            "petId": "pet",
            "deviceProp": {},
        }
        from pawsync import Device

        device = Device(client, device_data)

        response = await device.requestFeed(12)
        assert response.status == 200
        json_resp = await response.json()
        assert json_resp["code"] == 0
