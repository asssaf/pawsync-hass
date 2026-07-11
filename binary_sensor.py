"""Binary sensor platform for Pawsync devices."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import pawsync
from .const import DOMAIN, PAWSYNC_COORDINATOR

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class PawsyncBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Class describing Pawsync binary sensor entities."""

    value_fn: Callable[[pawsync.Device], Any] | None = None


BINARY_SENSOR_TYPES: tuple[PawsyncBinarySensorEntityDescription, ...] = (
    PawsyncBinarySensorEntityDescription(
        key="power_adapter",
        name="Power adapter",
        device_class=BinarySensorDeviceClass.POWER,
        value_fn=lambda device: device.deviceProp.get("powerAdapter") == 1,
    ),
    PawsyncBinarySensorEntityDescription(
        key="intelligent_feeding",
        name="Intelligent feeding",
        icon="mdi:robot-pet",
        value_fn=lambda device: device.deviceProp.get("intelligentFeedingSwitch") == 1,
    ),
    PawsyncBinarySensorEntityDescription(
        key="slow_feed",
        name="Slow feed",
        icon="mdi:speedometer-slow",
        value_fn=lambda device: device.deviceProp.get("slowFeedSwitch") == 1,
    ),
    PawsyncBinarySensorEntityDescription(
        key="accurate_feeding",
        name="Accurate feeding",
        icon="mdi:target",
        value_fn=lambda device: device.deviceProp.get("accurateFeeding") == 1,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pawsync binary sensor entities from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id][PAWSYNC_COORDINATOR]

    entities = []
    devices = (coordinator.data or {}).get("devices", [])
    for device in devices:
        for description in BINARY_SENSOR_TYPES:
            entities.append(PawsyncDeviceBinarySensor(coordinator, device, description))

    async_add_entities(entities)


class PawsyncDeviceBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Pawsync device binary sensor."""

    entity_description: PawsyncBinarySensorEntityDescription

    def __init__(
        self,
        coordinator,
        device: pawsync.Device,
        description: PawsyncBinarySensorEntityDescription,
    ):
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.device = device
        self.entity_description = description
        self._attr_unique_id = f"pawsync_{device.deviceId}_{description.key}"
        self._attr_name = f"{device.deviceName} {description.name}"

        # Keep device_id in attributes for the feed service
        self._attr_extra_state_attributes = {
            "device_id": device.deviceId,
        }

    @property
    def available(self) -> bool:  # pyright: ignore[reportIncompatibleVariableOverride]
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def device_info(self):  # pyright: ignore[reportIncompatibleVariableOverride]
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self.device.deviceId)},
            "name": self.device.deviceName,
            "model": self.device.deviceModel,
            "manufacturer": "Pawsync",
            "hw_version": self.device.configModel,
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        devices = (self.coordinator.data or {}).get("devices", [])
        for device in devices:
            if device.deviceId == self.device.deviceId:
                self.device = device
                break
        super()._handle_coordinator_update()

    @property
    def is_on(self) -> bool | None:  # pyright: ignore[reportIncompatibleVariableOverride]
        """Return true if the binary sensor is on."""
        if self.entity_description.value_fn:
            return self.entity_description.value_fn(self.device)
        return None
