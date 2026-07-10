"""Device registry for Pawsync."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from . import pawsync
from .const import DOMAIN


async def async_setup_devices(
    hass: HomeAssistant,
    entry_id: str,
    devices: list[pawsync.Device],
    username: str,
) -> None:
    """Set up devices in the device registry."""
    device_registry = dr.async_get(hass)

    for device in devices:
        device_registry.async_get_or_create(
            config_entry_id=entry_id,
            identifiers={(DOMAIN, device.deviceId)},
            name=device.deviceName,
            model=device.deviceModel,
            manufacturer="Pawsync",
            hw_version=device.configModel,
        )


async def async_setup_entity(
    hass: HomeAssistant,
    entry_id: str,
    device_id: str,
    entity_id: str,
    device_name: str,
) -> None:
    """Set up an entity for a device."""
    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)

    # Get the device
    device_entry = device_registry.async_get_device({(DOMAIN, device_id)})

    if device_entry:
        entity_registry.async_get_or_create(
            "sensor",
            DOMAIN,
            entity_id,
            suggested_object_id=device_name,
            device_id=device_entry.id,
        )
