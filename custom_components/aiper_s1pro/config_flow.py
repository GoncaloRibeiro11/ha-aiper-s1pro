"""Config flow for Aiper Scuba S1 Pro."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AiperApiClient, AiperAuthError, AiperConnectionError
from .const import CONF_DEVICE_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL):    str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class AiperConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Aiper Scuba S1 Pro."""

    VERSION = 1

    def __init__(self) -> None:
        self._email: str = ""
        self._password: str = ""
        self._devices: list[dict] = []

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """First step: ask for email and password."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._email    = user_input[CONF_EMAIL]
            self._password = user_input[CONF_PASSWORD]

            session = async_get_clientsession(self.hass)
            client  = AiperApiClient(self._email, self._password, session)

            try:
                await client.async_login()
                self._devices = await client.async_get_devices()
            except AiperAuthError as exc:
                _LOGGER.warning("Aiper authentication failed: %s", exc)
                errors["base"] = "invalid_auth"
            except AiperConnectionError as exc:
                _LOGGER.warning("Aiper cloud connection failed: %s", exc)
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during login")
                errors["base"] = "unknown"
            else:
                if not self._devices:
                    errors["base"] = "no_devices"
                elif len(self._devices) == 1:
                    # Only one device, so skip device selection.
                    device = self._devices[0]
                    return self._create_entry(device)
                else:
                    return await self.async_step_select_device()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_select_device(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Second step: choose which device to add (multi-device accounts)."""
        errors: dict[str, str] = {}

        device_map = {
            d["deviceId"]: f"{d.get('deviceName', 'Aiper')} ({d['deviceId'][-6:]})"
            for d in self._devices
        }

        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID]
            device    = next(d for d in self._devices if d["deviceId"] == device_id)
            return self._create_entry(device)

        schema = vol.Schema(
            {vol.Required(CONF_DEVICE_ID): vol.In(device_map)}
        )
        return self.async_show_form(
            step_id="select_device",
            data_schema=schema,
            errors=errors,
        )

    def _create_entry(self, device: dict) -> ConfigFlowResult:
        device_id   = device["deviceId"]
        device_name = device.get("deviceName", "Aiper Scuba S1 Pro")

        # Prevent duplicate entries for the same device
        self._async_abort_entries_match({CONF_DEVICE_ID: device_id})

        return self.async_create_entry(
            title=device_name,
            data={
                CONF_EMAIL:     self._email,
                CONF_PASSWORD:  self._password,
                CONF_DEVICE_ID: device_id,
            },
        )
