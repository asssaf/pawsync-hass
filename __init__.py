from __future__ import annotations

import logging
import time
from datetime import timedelta

import aiohttp
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)

from . import pawsync
from .const import DOMAIN, PAWSYNC_COORDINATOR, PLATFORMS, TOKEN_INVALID_CODE

logger = logging.getLogger(__name__)


# Validation of the user's configuration
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

all_devices: dict[str, pawsync.Device] = {}
sessions: dict[str, aiohttp.ClientSession] = {}


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Pawsync component (legacy YAML support)."""
    hass.data.setdefault(DOMAIN, {})

    # Import YAML config if present
    if DOMAIN in config:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": "import"},
                data=config[DOMAIN],
            )
        )

    async def handle_feed(call: ServiceCall):
        entity_id = call.data.get("entity_id")
        if entity_id is None:
            return
        entity = hass.states.get(entity_id)
        if entity is None:
            return
        device_id = entity.attributes.get("device_id")
        if device_id is None:
            return

        logger.warning(f"Requesting feed for entity {entity_id} => device {device_id}")

        device = all_devices.get(device_id)
        if device is None:
            return

        session = sessions.get(device_id)
        if session is None:
            return

        amount = call.data.get("amount")
        response = await device.requestFeed(session, amount)
        resp_json = await response.json()
        if resp_json.get("code") == TOKEN_INVALID_CODE:
            logger.warning("Feed service: token expired, re-authenticating")
            re_login = next(
                (
                    v["re_login"]
                    for v in hass.data.get(DOMAIN, {}).values()
                    if isinstance(v, dict) and "re_login" in v
                ),
                None,
            )
            if re_login:
                await re_login()
            response = await device.requestFeed(session, amount)
            resp_json = await response.json()
        if resp_json.get("code") != 0:
            logger.error(f"Feed failed for device {device_id}: {resp_json}")
        else:
            for entry_data in hass.data.get(DOMAIN, {}).values():
                if isinstance(entry_data, dict) and PAWSYNC_COORDINATOR in entry_data:
                    coord = entry_data[PAWSYNC_COORDINATOR]
                    devices = (coord.data or {}).get("devices", [])
                    if any(d.deviceId == device_id for d in devices):
                        coord.fast_polling_until = time.time() + 600
                        coord.update_interval = timedelta(seconds=30)
                        hass.async_create_task(coord.async_request_refresh())
                        break

    # Service schema: accept an entity id (a Pawsync device entity) and amount
    SERVICE_FEED_SCHEMA = vol.Schema(
        {
            vol.Required("entity_id"): cv.entity_id,
            vol.Required("amount"): vol.All(vol.Coerce(int), vol.Range(min=1)),
        }
    )

    hass.services.async_register(
        DOMAIN, "feed", handle_feed, schema=SERVICE_FEED_SCHEMA
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    session = async_get_clientsession(hass)

    await pawsync.login(session, username, password)

    async def async_update():
        if (
            coordinator.fast_polling_until is not None
            and time.time() > coordinator.fast_polling_until
        ):
            coordinator.update_interval = timedelta(minutes=15)
            coordinator.fast_polling_until = None

        devices = await pawsync.getDeviceList(session, logger)

        if not devices:
            await pawsync.login(session, username, password)
            devices = await pawsync.getDeviceList(session, logger)

            if not devices:
                devices = []

        for d in devices:
            sessions[d.deviceId] = session
            all_devices[d.deviceId] = d

        for d in devices:
            status = await d.getStatus(session, logger)
            if status:
                d.deviceProp.update(status)

        pet_logs = {}
        for d in devices:
            pet_logs[d.deviceId] = await pawsync.getPetLogList(
                session, d.deviceId, logger
            )

        return {"devices": devices, "pet_logs": pet_logs}

    coordinator = DataUpdateCoordinator(
        hass,
        logger,
        name="pawsync-update",
        update_interval=timedelta(minutes=15),
        update_method=async_update,
        config_entry=entry,
    )
    coordinator.fast_polling_until = None
    await coordinator.async_config_entry_first_refresh()

    async def re_login():
        await pawsync.login(session, username, password)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        PAWSYNC_COORDINATOR: coordinator,
        "re_login": re_login,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
