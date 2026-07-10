from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from custom_components.pawsync.config_flow import PawsyncConfigFlow


@pytest.mark.asyncio
async def test_config_flow_init():
    flow = PawsyncConfigFlow()
    flow.hass = MagicMock()
    flow.async_show_form = MagicMock(return_value="form_result")

    res = await flow.async_step_user()
    assert res == "form_result"
    flow.async_show_form.assert_called_once()


@pytest.mark.asyncio
async def test_config_flow_user_success():
    flow = PawsyncConfigFlow()
    flow.hass = MagicMock()
    flow.async_create_entry = MagicMock(return_value="entry_result")
    flow.async_set_unique_id = AsyncMock(return_value=None)
    flow._abort_if_unique_id_configured = MagicMock()

    user_input = {"username": "test@example.com", "password": "password123"}

    with (
        patch(
            "custom_components.pawsync.config_flow.pawsync.login",
            new_callable=AsyncMock,
        ) as mock_login,
        patch(
            "custom_components.pawsync.config_flow.async_get_clientsession"
        ) as mock_get_session,
    ):
        res = await flow.async_step_user(user_input)

        mock_login.assert_called_once_with(
            mock_get_session.return_value, "test@example.com", "password123"
        )
        flow.async_set_unique_id.assert_called_once_with("test@example.com")
        flow.async_create_entry.assert_called_once_with(
            title="test@example.com", data=user_input
        )
        assert res == "entry_result"
