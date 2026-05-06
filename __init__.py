from __future__ import annotations

from datetime import timedelta
import logging
import uuid

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, Platform
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from . import pawsync
from .const import DOMAIN, PAWSYNC_COORDINATOR, PLATFORMS

logger = logging.getLogger(__name__)

STORE_VERSION = 1
STORAGE_KEY = "pawsync_terminal_id"

async def async_get_or_create_terminal_id(hass: HomeAssistant, entry_id: str) -> str:
    store = Store(hass, STORE_VERSION, STORAGE_KEY)
    data = await store.async_load()
    if data is None:
        data = {}

    terminal_id = data.get(entry_id)
    if terminal_id is None:
        terminal_id = str(uuid.uuid1()).replace('-', '')[-33:]
        data[entry_id] = terminal_id
        await store.async_save(data)

    return terminal_id

# Validation of the user's configuration
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
            })
    },
    extra=vol.ALLOW_EXTRA
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
        await device.requestFeed(session, amount)

    # Service schema: accept an entity id (a Pawsync device entity) and amount
    SERVICE_FEED_SCHEMA = vol.Schema({
        vol.Required("entity_id"): cv.entity_id,
        vol.Required("amount"): vol.All(vol.Coerce(int), vol.Range(min=1)),
    })

    hass.services.async_register(DOMAIN, "feed", handle_feed, schema=SERVICE_FEED_SCHEMA)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    
    session = async_get_clientsession(hass)
    terminal_id = await async_get_or_create_terminal_id(hass, entry.entry_id)

    await pawsync.login(session, username, password, terminal_id=terminal_id)
    
    async def async_update():
        devices = await pawsync.getDeviceList(session, logger)
        
        if not devices:
            await pawsync.login(session, username, password, terminal_id=terminal_id)
            devices = await pawsync.getDeviceList(session, logger)
            
            if not devices:
                devices = []
        
        for d in devices:
            sessions[d.deviceId] = session
            all_devices[d.deviceId] = d
        
        return devices
        
    coordinator = DataUpdateCoordinator(
        hass,
        logger,
        name="pawsync-update",
        update_interval=timedelta(minutes=15),
        update_method=async_update,
        config_entry=entry,
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        PAWSYNC_COORDINATOR: coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok

