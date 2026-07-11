import importlib.util
import os
import sys
import types
from dataclasses import dataclass
from unittest.mock import MagicMock


# Mock homeassistant modules to prevent import errors during testing
class MockModule(MagicMock):
    @property
    def __file__(self):
        return "mock"


# Create custom_components namespace as a real package module
cc_module = types.ModuleType("custom_components")
cc_module.__path__ = []
sys.modules["custom_components"] = cc_module

# Create homeassistant structure as real package modules so subpackages resolve correctly
ha_module = types.ModuleType("homeassistant")
ha_module.__path__ = []
sys.modules["homeassistant"] = ha_module

helpers_module = types.ModuleType("homeassistant.helpers")
helpers_module.__path__ = []
sys.modules["homeassistant.helpers"] = helpers_module

components_module = types.ModuleType("homeassistant.components")
components_module.__path__ = []
sys.modules["homeassistant.components"] = components_module

# Mock helpers subpackages
sys.modules["homeassistant.helpers.config_validation"] = MockModule()
sys.modules["homeassistant.helpers.typing"] = MockModule()
sys.modules["homeassistant.helpers.entity_platform"] = MockModule()

# Mock config_entries
config_entries = MockModule()


class ConfigFlow:
    @classmethod
    def __init_subclass__(cls, **kwargs):
        pass


config_entries.ConfigFlow = ConfigFlow
sys.modules["homeassistant.config_entries"] = config_entries

# Mock const
const_mod = MockModule()
const_mod.CONF_PASSWORD = "password"
const_mod.CONF_USERNAME = "username"
const_mod.PERCENTAGE = "%"
const_mod.SIGNAL_STRENGTH_DECIBELS_MILLIWATT = "dBm"


class UnitOfMass:
    GRAMS = "g"


class UnitOfTime:
    DAYS = "d"
    SECONDS = "s"


const_mod.UnitOfMass = UnitOfMass
const_mod.UnitOfTime = UnitOfTime
sys.modules["homeassistant.const"] = const_mod

# Mock core
core_mod = MockModule()


class HomeAssistant:
    pass


class ServiceCall:
    pass


def callback(func):
    return func


core_mod.HomeAssistant = HomeAssistant
core_mod.ServiceCall = ServiceCall
core_mod.callback = callback
sys.modules["homeassistant.core"] = core_mod

# Mock aiohttp_client
aiohttp_client_mod = MockModule()
sys.modules["homeassistant.helpers.aiohttp_client"] = aiohttp_client_mod

# Mock storage
storage_mod = MockModule()


class Store:
    def __init__(self, hass, version, key):
        pass


storage_mod.Store = Store
sys.modules["homeassistant.helpers.storage"] = storage_mod

# Mock update_coordinator
uc_mod = MockModule()


class CoordinatorEntity:
    def __init__(self, coordinator):
        self.coordinator = coordinator

    def _handle_coordinator_update(self) -> None:
        pass


uc_mod.CoordinatorEntity = CoordinatorEntity
sys.modules["homeassistant.helpers.update_coordinator"] = uc_mod

# Mock voluptuous
sys.modules["voluptuous"] = MockModule()

# Mock components.sensor
sensor_mod = MockModule()


class SensorEntity:
    pass


@dataclass(frozen=True)
class SensorEntityDescription:
    key: str
    name: str | None = None
    icon: str | None = None
    device_class: str | None = None
    state_class: str | None = None
    native_unit_of_measurement: str | None = None


class SensorDeviceClass:
    BATTERY = "battery"
    SIGNAL_STRENGTH = "signal_strength"
    TIMESTAMP = "timestamp"


class SensorStateClass:
    MEASUREMENT = "measurement"


sensor_mod.SensorEntity = SensorEntity
sensor_mod.SensorEntityDescription = SensorEntityDescription
sensor_mod.SensorDeviceClass = SensorDeviceClass
sensor_mod.SensorStateClass = SensorStateClass
sys.modules["homeassistant.components.sensor"] = sensor_mod

# Mock components.binary_sensor
bsensor_mod = MockModule()


class BinarySensorEntity:
    pass


@dataclass(frozen=True)
class BinarySensorEntityDescription:
    key: str
    name: str | None = None
    icon: str | None = None
    device_class: str | None = None


class BinarySensorDeviceClass:
    POWER = "power"


bsensor_mod.BinarySensorEntity = BinarySensorEntity
bsensor_mod.BinarySensorEntityDescription = BinarySensorEntityDescription
bsensor_mod.BinarySensorDeviceClass = BinarySensorDeviceClass
sys.modules["homeassistant.components.binary_sensor"] = bsensor_mod

# Get absolute path to the root directory
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Setup custom_components.pawsync namespace using absolute paths
# Define custom_components.pawsync (from __init__.py)
pawsync_init_spec = importlib.util.spec_from_file_location(
    "custom_components.pawsync", os.path.join(ROOT_DIR, "__init__.py")
)
pawsync_init_mod = importlib.util.module_from_spec(pawsync_init_spec)
sys.modules["custom_components.pawsync"] = pawsync_init_mod
sys.modules["__init__"] = pawsync_init_mod

# Define custom_components.pawsync.pawsync
pawsync_spec = importlib.util.spec_from_file_location(
    "custom_components.pawsync.pawsync", os.path.join(ROOT_DIR, "pawsync.py")
)
pawsync_mod = importlib.util.module_from_spec(pawsync_spec)
sys.modules["custom_components.pawsync.pawsync"] = pawsync_mod

# Define custom_components.pawsync.const
const_spec = importlib.util.spec_from_file_location(
    "custom_components.pawsync.const", os.path.join(ROOT_DIR, "const.py")
)
const_mod = importlib.util.module_from_spec(const_spec)
sys.modules["custom_components.pawsync.const"] = const_mod

# Define custom_components.pawsync.config_flow
cf_spec = importlib.util.spec_from_file_location(
    "custom_components.pawsync.config_flow", os.path.join(ROOT_DIR, "config_flow.py")
)
cf_mod = importlib.util.module_from_spec(cf_spec)
sys.modules["custom_components.pawsync.config_flow"] = cf_mod

# Define custom_components.pawsync.sensor
sensor_spec = importlib.util.spec_from_file_location(
    "custom_components.pawsync.sensor", os.path.join(ROOT_DIR, "sensor.py")
)
sensor_mod_impl = importlib.util.module_from_spec(sensor_spec)
sys.modules["custom_components.pawsync.sensor"] = sensor_mod_impl

# Define custom_components.pawsync.binary_sensor
bsensor_spec = importlib.util.spec_from_file_location(
    "custom_components.pawsync.binary_sensor",
    os.path.join(ROOT_DIR, "binary_sensor.py"),
)
bsensor_mod_impl = importlib.util.module_from_spec(bsensor_spec)
sys.modules["custom_components.pawsync.binary_sensor"] = bsensor_mod_impl

# Load / execute them in the correct dependency order
const_spec.loader.exec_module(const_mod)
pawsync_spec.loader.exec_module(pawsync_mod)
pawsync_init_spec.loader.exec_module(pawsync_init_mod)
cf_spec.loader.exec_module(cf_mod)
sensor_spec.loader.exec_module(sensor_mod_impl)
bsensor_spec.loader.exec_module(bsensor_mod_impl)

# Prevent pytest from collecting or importing root integration files
collect_ignore = [
    "../__init__.py",
    "../pawsync.py",
    "../sensor.py",
    "../binary_sensor.py",
    "../config_flow.py",
    "../const.py",
    "../device_registry.py",
]
