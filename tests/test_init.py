from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from custom_components.pawsync import (
    all_devices,
    async_setup,
    async_setup_entry,
    sessions,
)
from custom_components.pawsync.const import (
    DOMAIN,
    TOKEN_INVALID_CODE,
)


@pytest.mark.asyncio
async def test_async_setup():
    hass = MagicMock()
    hass.data = {}

    config = {DOMAIN: {"username": "test@example.com", "password": "password123"}}

    res = await async_setup(hass, config)
    assert res is True
    hass.services.async_register.assert_called_once()
    assert hass.services.async_register.call_args[0][0] == DOMAIN
    assert hass.services.async_register.call_args[0][1] == "feed"


@pytest.mark.asyncio
async def test_handle_feed_token_expired():
    hass = MagicMock()
    hass.data = {DOMAIN: {"entry_1": {"re_login": AsyncMock()}}}

    await async_setup(hass, {})
    handle_feed = hass.services.async_register.call_args[0][2]

    # Mock state and device/session
    mock_entity = MagicMock()
    mock_entity.attributes = {"device_id": "device_123"}
    hass.states.get = MagicMock(return_value=mock_entity)

    mock_device = MagicMock()
    mock_session = MagicMock()

    # Mock response returning TOKEN_INVALID_CODE on first call, 0 on second call
    mock_resp_invalid = MagicMock()
    mock_resp_invalid.json = AsyncMock(return_value={"code": TOKEN_INVALID_CODE})

    mock_resp_success = MagicMock()
    mock_resp_success.json = AsyncMock(return_value={"code": 0})

    mock_device.requestFeed = AsyncMock(
        side_effect=[mock_resp_invalid, mock_resp_success]
    )

    all_devices["device_123"] = mock_device
    sessions["device_123"] = mock_session

    call = MagicMock()
    call.data = {"entity_id": "sensor.my_feeder", "amount": 10}

    try:
        await handle_feed(call)

        # Verify it fetched state, called requestFeed twice, called re_login once
        hass.states.get.assert_called_once_with("sensor.my_feeder")
        assert mock_device.requestFeed.call_count == 2
        hass.data[DOMAIN]["entry_1"]["re_login"].assert_called_once()
    finally:
        # Clean up global registries
        all_devices.clear()
        sessions.clear()


@pytest.mark.asyncio
async def test_async_setup_entry():
    hass = MagicMock()
    hass.data = {}
    hass.config_entries.async_forward_entry_setups = AsyncMock()

    entry = MagicMock()
    entry.entry_id = "entry_1"
    entry.data = {"username": "test@example.com", "password": "password123"}
    entry.options = {}

    with (
        patch(
            "custom_components.pawsync.pawsync.login", new_callable=AsyncMock
        ) as mock_login,
        patch(
            "custom_components.pawsync.pawsync.getDeviceList",
            new_callable=AsyncMock,
        ) as mock_devices,
        patch(
            "custom_components.pawsync.DataUpdateCoordinator"
        ) as mock_coordinator_cls,
    ):
        mock_coord = MagicMock()
        mock_coord.async_config_entry_first_refresh = AsyncMock()
        mock_coordinator_cls.return_value = mock_coord

        mock_devices.return_value = []
        res = await async_setup_entry(hass, entry)

        import homeassistant.helpers.aiohttp_client as aiohttp_client

        assert res is True
        mock_login.assert_called_once_with(
            aiohttp_client.async_get_clientsession.return_value,
            "test@example.com",
            "password123",
        )

        # Check re_login callback is registered in hass.data
        assert "re_login" in hass.data[DOMAIN]["entry_1"]
        re_login_cb = hass.data[DOMAIN]["entry_1"]["re_login"]
        await re_login_cb()
        # Should call login again
        assert mock_login.call_count == 2
