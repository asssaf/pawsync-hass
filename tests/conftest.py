import sys
from unittest.mock import MagicMock

# Mock voluptuous and homeassistant modules to prevent import errors during pytest collection
sys.modules["voluptuous"] = MagicMock()
sys.modules["homeassistant"] = MagicMock()
sys.modules["homeassistant.config_entries"] = MagicMock()
sys.modules["homeassistant.core"] = MagicMock()
sys.modules["homeassistant.helpers"] = MagicMock()
sys.modules["homeassistant.helpers.storage"] = MagicMock()
sys.modules["homeassistant.helpers.typing"] = MagicMock()
sys.modules["homeassistant.const"] = MagicMock()
sys.modules["homeassistant.helpers.config_validation"] = MagicMock()
sys.modules["homeassistant.helpers.aiohttp_client"] = MagicMock()
sys.modules["homeassistant.helpers.update_coordinator"] = MagicMock()

# Mock '__init__' module to prevent Python 3.12 relative import resolution errors in hyphenated package paths
sys.modules["__init__"] = MagicMock()
