import time
from datetime import UTC, datetime, timedelta
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
    PAWSYNC_COORDINATOR,
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


@pytest.mark.asyncio
async def test_handle_feed_fast_polling():
    hass = MagicMock()

    mock_coord = MagicMock()
    mock_coord.data = {"devices": [MagicMock(deviceId="device_123")]}
    mock_coord.async_request_refresh = AsyncMock()
    mock_coord.fast_polling_until = None
    mock_coord.update_interval = timedelta(minutes=15)

    hass.data = {
        DOMAIN: {
            "entry_1": {
                "re_login": AsyncMock(),
                PAWSYNC_COORDINATOR: mock_coord,
            }
        }
    }

    await async_setup(hass, {})
    handle_feed = hass.services.async_register.call_args[0][2]

    mock_entity = MagicMock()
    mock_entity.attributes = {"device_id": "device_123"}
    hass.states.get = MagicMock(return_value=mock_entity)

    mock_device = MagicMock()
    mock_session = MagicMock()

    mock_resp_success = MagicMock()
    mock_resp_success.json = AsyncMock(return_value={"code": 0})
    mock_device.requestFeed = AsyncMock(return_value=mock_resp_success)

    all_devices["device_123"] = mock_device
    sessions["device_123"] = mock_session

    call = MagicMock()
    call.data = {"entity_id": "sensor.my_feeder", "amount": 10}

    try:
        await handle_feed(call)

        assert mock_coord.fast_polling_until is not None
        assert mock_coord.fast_polling_until > time.time() + 290
        assert mock_coord.update_interval == timedelta(seconds=15)
        mock_coord.async_request_refresh.assert_called_once()
        hass.async_create_task.assert_called_once()
        # Close the unawaited coroutine mock to avoid RuntimeWarning
        coro = hass.async_create_task.call_args[0][0]
        coro.close()
    finally:
        all_devices.clear()
        sessions.clear()


@pytest.mark.asyncio
async def test_async_update_fast_polling_revert():
    hass = MagicMock()
    hass.data = {}
    hass.config_entries.async_forward_entry_setups = AsyncMock()

    entry = MagicMock()
    entry.entry_id = "entry_1"
    entry.data = {"username": "test@example.com", "password": "password123"}
    entry.options = {}

    with (
        patch("custom_components.pawsync.pawsync.login", new_callable=AsyncMock),
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

        # Setup entry
        await async_setup_entry(hass, entry)

        # Retrieve the actual async_update function passed to DataUpdateCoordinator
        async_update = mock_coordinator_cls.call_args[1]["update_method"]

        # Test case 1: Not in fast polling mode
        mock_coord.fast_polling_until = None
        mock_coord.update_interval = timedelta(minutes=15)

        with patch(
            "custom_components.pawsync.pawsync.getPetLogList",
            new_callable=AsyncMock,
        ) as mock_logs:
            mock_logs.return_value = []
            await async_update()

            assert mock_coord.update_interval == timedelta(minutes=15)
            assert mock_coord.fast_polling_until is None

        # Test case 2: Fast polling active, not expired
        mock_coord.fast_polling_until = time.time() + 300
        mock_coord.update_interval = timedelta(seconds=15)

        with patch(
            "custom_components.pawsync.pawsync.getPetLogList",
            new_callable=AsyncMock,
        ) as mock_logs:
            mock_logs.return_value = []
            await async_update()

            assert mock_coord.update_interval == timedelta(seconds=15)
            assert mock_coord.fast_polling_until is not None

        # Test case 3: Fast polling active and expired
        mock_coord.fast_polling_until = time.time() - 10
        mock_coord.update_interval = timedelta(seconds=15)

        with patch(
            "custom_components.pawsync.pawsync.getPetLogList",
            new_callable=AsyncMock,
        ) as mock_logs:
            mock_logs.return_value = []
            await async_update()

            assert mock_coord.update_interval == timedelta(minutes=15)
            assert mock_coord.fast_polling_until is None


@pytest.mark.asyncio
async def test_async_update_scheduled_feed_timer():
    hass = MagicMock()
    hass.data = {}
    hass.config_entries.async_forward_entry_setups = AsyncMock()

    entry = MagicMock()
    entry.entry_id = "entry_1"
    entry.data = {"username": "test@example.com", "password": "password123"}
    entry.options = {}
    entry.async_on_unload = MagicMock()

    with (
        patch("custom_components.pawsync.pawsync.login", new_callable=AsyncMock),
        patch(
            "custom_components.pawsync.pawsync.getDeviceList",
            new_callable=AsyncMock,
        ) as mock_devices,
        patch(
            "custom_components.pawsync.DataUpdateCoordinator"
        ) as mock_coordinator_cls,
        patch("homeassistant.util.dt.now") as mock_now,
        patch(
            "custom_components.pawsync.async_track_point_in_utc_time"
        ) as mock_track_time,
    ):
        mock_coord = MagicMock()
        mock_coord.async_config_entry_first_refresh = AsyncMock()
        mock_coord.async_request_refresh = AsyncMock()
        mock_coordinator_cls.return_value = mock_coord

        mock_devices.return_value = []
        mock_unsub = MagicMock()
        mock_track_time.return_value = mock_unsub

        await async_setup_entry(hass, entry)
        async_update = mock_coordinator_cls.call_args[1]["update_method"]

        # Monday 10:00:00 (timestamp = 0 sec of hour)
        monday_dt = datetime(2026, 8, 17, 10, 0, 0, tzinfo=UTC)
        mock_now.return_value = monday_dt

        device = MagicMock()
        device.deviceId = "dev_1"
        device.getStatus = AsyncMock(return_value={})
        mock_devices.return_value = [device]

        with patch(
            "custom_components.pawsync.pawsync.getPetLogList",
            new_callable=AsyncMock,
            return_value=[],
        ):
            # Case 1: Schedule info available -> registers track_point_in_utc_time
            device.deviceProp = {
                "scheduleInfo": {
                    "planId": 1,
                    "repeat": 254,
                    "nextDay": 2,
                    "nextTime": 36300,  # 10:05:00
                    "nextMount": 10,
                }
            }
            mock_coord.fast_polling_until = None
            await async_update()

            # Polling interval stays at 15 minutes
            assert mock_coord.update_interval == timedelta(minutes=15)
            assert mock_coord.fast_polling_until is None

            # Timer was registered for 10:05:00 UTC
            mock_track_time.assert_called_once()
            call_args = mock_track_time.call_args[0]
            assert call_args[0] == hass
            callback_func = call_args[1]
            assert call_args[2] == datetime(2026, 8, 17, 10, 5, 0, tzinfo=UTC)

            # Case 2: Config entry unload cancels an active timer
            entry.async_on_unload.assert_called_once()
            cancel_callback = entry.async_on_unload.call_args[0][0]
            cancel_callback()
            mock_unsub.assert_called_once()

            # Case 3: When callback fires, fast polling is triggered
            callback_func(datetime(2026, 8, 17, 10, 5, 0, tzinfo=UTC))
            assert mock_coord.fast_polling_until is not None
            assert mock_coord.fast_polling_until > time.time() + 290
            assert mock_coord.update_interval == timedelta(seconds=15)
            mock_coord.async_request_refresh.assert_called_once()
            hass.async_create_task.assert_called_once()
            coro = hass.async_create_task.call_args[0][0]
            coro.close()


@pytest.mark.asyncio
async def test_async_update_scheduled_feed_preempted_by_refresh():
    """Test when an update runs right as scheduled feed time passes before timer fires."""
    hass = MagicMock()
    hass.data = {}
    hass.config_entries.async_forward_entry_setups = AsyncMock()

    entry = MagicMock()
    entry.entry_id = "entry_1"
    entry.data = {"username": "test@example.com", "password": "password123"}
    entry.options = {}
    entry.async_on_unload = MagicMock()

    with (
        patch("custom_components.pawsync.pawsync.login", new_callable=AsyncMock),
        patch(
            "custom_components.pawsync.pawsync.getDeviceList",
            new_callable=AsyncMock,
        ) as mock_devices,
        patch(
            "custom_components.pawsync.DataUpdateCoordinator"
        ) as mock_coordinator_cls,
        patch("homeassistant.util.dt.now") as mock_now,
        patch(
            "custom_components.pawsync.async_track_point_in_utc_time"
        ) as mock_track_time,
    ):
        mock_coord = MagicMock()
        mock_coord.async_config_entry_first_refresh = AsyncMock()
        mock_coord.async_request_refresh = AsyncMock()
        mock_coordinator_cls.return_value = mock_coord

        mock_devices.return_value = []
        mock_unsub = MagicMock()
        mock_track_time.return_value = mock_unsub

        await async_setup_entry(hass, entry)
        async_update = mock_coordinator_cls.call_args[1]["update_method"]

        # Step 1: Monday 10:00:00 - Next meal in 5 minutes (10:05:00 = 36300 sec)
        mock_now.return_value = datetime(2026, 8, 17, 10, 0, 0, tzinfo=UTC)

        device = MagicMock()
        device.deviceId = "dev_1"
        device.getStatus = AsyncMock(return_value={})
        mock_devices.return_value = [device]

        with patch(
            "custom_components.pawsync.pawsync.getPetLogList",
            new_callable=AsyncMock,
            return_value=[],
        ):
            device.deviceProp = {
                "scheduleInfo": {
                    "planId": 1,
                    "repeat": 254,
                    "nextDay": 2,
                    "nextTime": 36300,  # 10:05:00
                    "nextMount": 10,
                }
            }
            mock_coord.fast_polling_until = None
            await async_update()

            assert mock_track_time.call_count == 1
            assert mock_coord.update_interval == timedelta(minutes=15)
            assert mock_coord.fast_polling_until is None

            # Step 2: An update runs at 10:05:01 (1s past feed time) before callback
            # Device rolled over scheduleInfo to 14:00:00 (50400 sec)
            mock_now.return_value = datetime(2026, 8, 17, 10, 5, 1, tzinfo=UTC)
            device.deviceProp = {
                "scheduleInfo": {
                    "planId": 1,
                    "repeat": 254,
                    "nextDay": 2,
                    "nextTime": 50400,  # 14:00:00
                    "nextMount": 10,
                }
            }
            await async_update()

            # Fast polling was latched because previous scheduled time was reached
            assert mock_coord.fast_polling_until is not None
            assert mock_coord.fast_polling_until > time.time() + 290
            assert mock_coord.update_interval == timedelta(seconds=15)

            # Old timer was unsubscribed and new timer registered for 14:00:00
            mock_unsub.assert_called_once()
            assert mock_track_time.call_count == 2
            assert mock_track_time.call_args[0][2] == datetime(
                2026, 8, 17, 14, 0, 0, tzinfo=UTC
            )


@pytest.mark.asyncio
async def test_async_update_failure_raises_update_failed():
    """Test that API errors during update raise UpdateFailed."""
    from homeassistant.helpers.update_coordinator import UpdateFailed

    hass = MagicMock()
    hass.data = {}
    hass.config_entries.async_forward_entry_setups = AsyncMock()

    entry = MagicMock()
    entry.entry_id = "entry_1"
    entry.data = {"username": "test@example.com", "password": "password123"}
    entry.options = {}

    with (
        patch("custom_components.pawsync.pawsync.login", new_callable=AsyncMock),
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
        await async_setup_entry(hass, entry)
        async_update = mock_coordinator_cls.call_args[1]["update_method"]

        # Case 1: getDeviceList returns None and retry also returns None -> UpdateFailed
        mock_devices.return_value = None
        with pytest.raises(
            UpdateFailed, match="Failed to fetch device list from Pawsync API"
        ):
            await async_update()

        # Case 2: Exception raised during fetch -> UpdateFailed
        mock_devices.side_effect = ConnectionError("Network unreachable")
        with pytest.raises(UpdateFailed, match="Error communicating with Pawsync API"):
            await async_update()
