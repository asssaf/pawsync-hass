"""Sensor platform for Pawsync devices."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import pawsync
from .const import DOMAIN, PAWSYNC_COORDINATOR

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pawsync sensor entities from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id][PAWSYNC_COORDINATOR]
    
    entities = []
    for device in coordinator.data or []:
        entities.append(PawsyncDeviceSensor(coordinator, device))
    
    async_add_entities(entities)


class PawsyncDeviceSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Pawsync device as a sensor."""

    def __init__(self, coordinator, device: pawsync.Device):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.device = device
        self._attr_unique_id = f"pawsync_{device.deviceId}"
        self._attr_name = device.deviceName
        self._attr_native_unit_of_measurement = None

    @property
    def available(self) -> bool: # pyright: ignore[reportIncompatibleVariableOverride]
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def device_info(self): # pyright: ignore[reportIncompatibleVariableOverride]
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self.device.deviceId)},
            "name": self.device.deviceName,
            "model": self.device.deviceModel,
            "manufacturer": "Pawsync",
            "hw_version": self.device.configModel,
        }

    @property
    def extra_state_attributes(self) -> dict[str, Any]: # pyright: ignore[reportIncompatibleVariableOverride]
        """Return the state attributes."""
        return {
            "device_id": self.device.deviceId,
            "device_name": self.device.deviceName,
            "device_model": self.device.deviceModel,
            "device_image": self.device.deviceImg,
            "connection_type": self.device.connectionType,
            "secondary_category": self.device.secondaryCategory,
            "config_model": self.device.configModel,
            "biz_id": self.device.bizId,
            "pet_id": self.device.petId,
            "device_prop": self.device.deviceProp,
        }
        
    @property
    def entity_picture(self) -> str: # pyright: ignore[reportIncompatibleVariableOverride]
        """Return the entity picture to use in the frontend, if any."""
        return self.device.deviceImg

    @property
    def native_value(self) -> int: # pyright: ignore[reportIncompatibleVariableOverride]
        """Return the state of the sensor."""
        return  int(self.device.deviceProp['contentInPot'])
