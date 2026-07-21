"""Config flow for ZipAssist CMMS integration."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .client import ZipAssistClient
from .const import CONF_BASE_URL, DEFAULT_BASE_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_BASE_URL, default=DEFAULT_BASE_URL): str,
    }
)

REAUTH_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_BASE_URL, default=DEFAULT_BASE_URL): str,
    }
)


class ZipAssistConfigFlow(ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    """Handle a config flow for ZipAssist CMMS."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL]

            await self.async_set_unique_id(f"zipassist_{email}")
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            client = ZipAssistClient(
                email=email,
                password=user_input[CONF_PASSWORD],
                base_url=user_input.get(CONF_BASE_URL, DEFAULT_BASE_URL),
                session=session,
            )

            try:
                if await client.authenticate():
                    return self.async_create_entry(
                        title=f"ZipAssist ({email})",
                        data=user_input,
                    )
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Connection test failed")
                errors["base"] = "cannot_connect"
            finally:
                await client.close()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle reauthentication when credentials change."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Dialog that informs the user that reauth is required."""
        errors: dict[str, str] = {}

        reauth_entry = self._get_reauth_entry()
        email = reauth_entry.data[CONF_EMAIL]

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            client = ZipAssistClient(
                email=email,
                password=user_input[CONF_PASSWORD],
                base_url=user_input.get(CONF_BASE_URL, DEFAULT_BASE_URL),
                session=session,
            )

            try:
                if await client.authenticate():
                    return self.async_update_reload_and_abort(
                        reauth_entry,
                        data_updates=user_input,
                    )
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Reauth connection test failed")
                errors["base"] = "cannot_connect"
            finally:
                await client.close()

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=REAUTH_DATA_SCHEMA,
            description_placeholders={"email": email},
            errors=errors,
        )
