"""Sensor platform for Pawsync devices."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfMass,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import pawsync
from .const import DOMAIN, PAWSYNC_COORDINATOR

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class PawsyncSensorEntityDescription(SensorEntityDescription):
    """Class describing Pawsync sensor entities."""

    value_fn: Callable[[pawsync.Device], Any] | None = None


SENSOR_TYPES: tuple[PawsyncSensorEntityDescription, ...] = (
    PawsyncSensorEntityDescription(
        key="primary",
        name=None,
        value_fn=lambda device: device.deviceProp.get("connectionStatus"),
    ),
    PawsyncSensorEntityDescription(
        key="content_in_pot",
        name="Food in pot",
        native_unit_of_measurement=UnitOfMass.GRAMS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:bowl-mix",
        value_fn=lambda device: device.deviceProp.get("contentInPot"),
    ),
    PawsyncSensorEntityDescription(
        key="bucket_surplus",
        name="Bucket surplus",
        native_unit_of_measurement=UnitOfMass.GRAMS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:database",
        value_fn=lambda device: device.deviceProp.get("petFood", {}).get(
            "bucketSurplus"
        ),
    ),
    PawsyncSensorEntityDescription(
        key="last_feeding_amount",
        name="Last feeding amount",
        native_unit_of_measurement=UnitOfMass.GRAMS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:shaker",
        value_fn=lambda device: device.deviceProp.get("petFood", {}).get(
            "lastFeedingAmount"
        ),
    ),
    PawsyncSensorEntityDescription(
        key="content_remain_time",
        name="Remaining food time",
        native_unit_of_measurement=UnitOfTime.DAYS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:calendar-clock",
        value_fn=lambda device: device.deviceProp.get("petFood", {}).get(
            "contentRemainTime"
        ),
    ),
    PawsyncSensorEntityDescription(
        key="battery_percent",
        name="Battery level",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: device.deviceProp.get("batteryPercent"),
    ),
    PawsyncSensorEntityDescription(
        key="wifi_rssi",
        name="WiFi signal strength",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda device: device.deviceProp.get("wifiRssi"),
    ),
    PawsyncSensorEntityDescription(
        key="alert_count",
        name="Alert count",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:alert-circle",
        value_fn=lambda device: device.deviceProp.get("alertCount"),
    ),
    PawsyncSensorEntityDescription(
        key="main_fw_version",
        name="Main firmware version",
        icon="mdi:chip",
        value_fn=lambda device: next(
            (
                fw["version"]
                for fw in device.deviceProp.get("firmwareInfos", [])
                if fw.get("isMainFw")
            ),
            None,
        ),
    ),
    PawsyncSensorEntityDescription(
        key="mcu_fw_version",
        name="MCU firmware version",
        icon="mdi:cpu-64-bit",
        value_fn=lambda device: next(
            (
                fw["version"]
                for fw in device.deviceProp.get("firmwareInfos", [])
                if fw.get("pluginName") == "mcuFw"
            ),
            None,
        ),
    ),
)


@dataclass(frozen=True)
class PawsyncLogSensorEntityDescription(SensorEntityDescription):
    """Class describing Pawsync log sensor entities."""

    log_fn: Callable[[list], Any] | None = None


LOG_SENSOR_TYPES: tuple[PawsyncLogSensorEntityDescription, ...] = (
    PawsyncLogSensorEntityDescription(
        key="last_dispensed_time",
        name="Last dispensed time",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:clock-check",
        log_fn=lambda logs: next(
            (
                datetime.fromtimestamp(e["timestamp"], tz=UTC)
                for e in logs
                if e["logType"] in ("planFeeding", "manualFeeding")
            ),
            None,
        ),
    ),
    PawsyncLogSensorEntityDescription(
        key="last_dispensed_amount",
        name="Last dispensed amount",
        native_unit_of_measurement=UnitOfMass.GRAMS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:shaker-outline",
        log_fn=lambda logs: next(
            (
                e["value"]
                for e in logs
                if e["logType"] in ("planFeeding", "manualFeeding")
                and e.get("value") is not None
            ),
            None,
        ),
    ),
    PawsyncLogSensorEntityDescription(
        key="last_eaten_time",
        name="Last eaten time",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:cat",
        log_fn=lambda logs: next(
            (
                datetime.fromtimestamp(e["timestamp"], tz=UTC)
                for e in logs
                if e["logType"] == "takeFood"
            ),
            None,
        ),
    ),
    PawsyncLogSensorEntityDescription(
        key="last_eaten_amount",
        name="Last eaten amount",
        native_unit_of_measurement=UnitOfMass.GRAMS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:food-variant",
        log_fn=lambda logs: next(
            (
                e["value"]
                for e in logs
                if e["logType"] == "takeFood" and e.get("value") is not None
            ),
            None,
        ),
    ),
    PawsyncLogSensorEntityDescription(
        key="last_eating_duration",
        name="Last eating duration",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:timer",
        log_fn=lambda logs: next(
            (
                e["durationInS"]
                for e in logs
                if e["logType"] == "takeFood" and e.get("durationInS", -1) > 0
            ),
            None,
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pawsync sensor entities from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id][PAWSYNC_COORDINATOR]

    entities = []
    devices = (coordinator.data or {}).get("devices", [])
    pet_logs = (coordinator.data or {}).get("pet_logs", {})

    for device in devices:
        for description in SENSOR_TYPES:
            entities.append(PawsyncDeviceSensor(coordinator, device, description))

    for device in devices:
        logs = pet_logs.get(device.deviceId, [])
        for description in LOG_SENSOR_TYPES:
            entities.append(PawsyncLogSensor(coordinator, device, description, logs))

    async_add_entities(entities)


class PawsyncDeviceSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Pawsync device as a sensor."""

    entity_description: PawsyncSensorEntityDescription

    def __init__(
        self,
        coordinator,
        device: pawsync.Device,
        description: PawsyncSensorEntityDescription,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.device = device
        self.entity_description = description
        self._attr_unique_id = f"pawsync_{device.deviceId}_{description.key}"

        if description.name is None:
            self._attr_name = device.deviceName
            self._attr_entity_picture = device.deviceImg
            self._attr_extra_state_attributes = {
                "device_id": device.deviceId,
                "device_name": device.deviceName,
                "device_model": device.deviceModel,
                "device_image": device.deviceImg,
                "connection_type": device.connectionType,
                "secondary_category": device.secondaryCategory,
                "config_model": device.configModel,
                "biz_id": device.bizId,
                "pet_id": device.petId,
                "device_prop": device.deviceProp,
                "terminal_id": device.terminalId,
            }
        else:
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
                # If primary, refresh all attributes
                if self.entity_description.key == "primary":
                    self._attr_extra_state_attributes = {
                        "device_id": device.deviceId,
                        "device_name": device.deviceName,
                        "device_model": device.deviceModel,
                        "device_image": device.deviceImg,
                        "connection_type": device.connectionType,
                        "secondary_category": device.secondaryCategory,
                        "config_model": device.configModel,
                        "biz_id": device.bizId,
                        "pet_id": device.petId,
                        "device_prop": device.deviceProp,
                        "terminal_id": device.terminalId,
                    }
                break
        super()._handle_coordinator_update()

    @property
    def native_value(self) -> Any:  # pyright: ignore[reportIncompatibleVariableOverride]
        """Return the state of the sensor."""
        if self.entity_description.value_fn:
            return self.entity_description.value_fn(self.device)
        return None


class PawsyncLogSensor(CoordinatorEntity, SensorEntity):
    """Representation of Pawsync pet log activity as a sensor."""

    entity_description: PawsyncLogSensorEntityDescription

    def __init__(
        self,
        coordinator,
        device: pawsync.Device,
        description: PawsyncLogSensorEntityDescription,
        logs: list,
    ):
        """Initialize the log sensor."""
        super().__init__(coordinator)
        self._device_id = device.deviceId
        self._logs = logs
        self.entity_description = description
        self._attr_unique_id = f"pawsync_{device.deviceId}_{description.key}"
        self._attr_name = f"{device.deviceName} {description.name}"
        self._attr_extra_state_attributes = {"device_id": device.deviceId}
        self._attr_native_unit_of_measurement = description.native_unit_of_measurement

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._logs = (
            (self.coordinator.data or {}).get("pet_logs", {}).get(self._device_id, [])
        )
        super()._handle_coordinator_update()

    @property
    def available(self) -> bool:  # pyright: ignore[reportIncompatibleVariableOverride]
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def device_info(self):  # pyright: ignore[reportIncompatibleVariableOverride]
        """Return device information."""
        devices = (self.coordinator.data or {}).get("devices", [])
        d = next((d for d in devices if d.deviceId == self._device_id), None)
        if d is None:
            return None
        return {
            "identifiers": {(DOMAIN, d.deviceId)},
            "name": d.deviceName,
            "model": d.deviceModel,
            "manufacturer": "Pawsync",
            "hw_version": d.configModel,
        }

    @property
    def native_value(self) -> Any:  # pyright: ignore[reportIncompatibleVariableOverride]
        """Return the state of the sensor."""
        if not self.entity_description.log_fn:
            return None
        return self.entity_description.log_fn(self._logs)
