"""Constants for the Pawsync integration."""

from homeassistant.const import Platform

DOMAIN = "pawsync"
PAWSYNC_COORDINATOR = "pawsync_coordinator"

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]

TOKEN_INVALID_CODE = -11008800  # Pawsync API code when auth token has expired
