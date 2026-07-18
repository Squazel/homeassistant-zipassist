"""Config flow for ZipAssist CMMS integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD

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


class ZipAssistConfigFlow(ConfigFlow, domain=DOMAIN):
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

            client = ZipAssistClient(
                email=email,
                password=user_input[CONF_PASSWORD],
                base_url=user_input.get(CONF_BASE_URL, DEFAULT_BASE_URL),
            )

            try:
                if await client.authenticate():
                    await client.close()
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
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reauthentication when credentials change."""
        errors: dict[str, str] = {}

        reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        email = reauth_entry.data[CONF_EMAIL] if reauth_entry else ""

        if user_input is not None:
            client = ZipAssistClient(
                email=email,
                password=user_input[CONF_PASSWORD],
                base_url=user_input.get(CONF_BASE_URL, DEFAULT_BASE_URL),
            )

            try:
                if await client.authenticate():
                    await client.close()
                    # Update the existing entry with new credentials
                    new_data = {**reauth_entry.data, **user_input}
                    self.hass.config_entries.async_update_entry(
                        reauth_entry, data=new_data
                    )
                    await self.hass.config_entries.async_reload(
                        reauth_entry.entry_id
                    )
                    return self.async_abort(reason="reauth_successful")
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Reauth connection test failed")
                errors["base"] = "cannot_connect"
            finally:
                await client.close()

        return self.async_show_form(
            step_id="reauth",
            data_schema=REAUTH_DATA_SCHEMA,
            description_placeholders={"email": email},
            errors=errors,
        )