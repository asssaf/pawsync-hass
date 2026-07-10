from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from . import pawsync
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class PawsyncConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pawsync."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Validate credentials
                session = async_get_clientsession(self.hass)
                client = pawsync.PawsyncClient(session)
                if not await client.login(
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD],
                ):
                    errors["base"] = "invalid_auth"
                else:
                    # Check if entry already exists
                    existing = await self.async_set_unique_id(user_input[CONF_USERNAME])
                    if existing is None:
                        self._abort_if_unique_id_configured()

                        return self.async_create_entry(
                            title=user_input[CONF_USERNAME],
                            data=user_input,
                        )
            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception: %s", err)
                errors["base"] = "unknown"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def async_step_import(self, import_data):
        """Handle import from configuration.yaml."""
        return await self.async_step_user(import_data)
