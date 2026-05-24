"""Aiper Scuba S1 Pro integration for Home Assistant."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AiperApiClient, AiperAuthError, AiperConnectionError
from .const import CONF_DEVICE_ID, COORDINATOR, DOMAIN, PLATFORMS
from .coordinator import AiperDataCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Aiper Scuba S1 Pro from a config entry."""
    session = async_get_clientsession(hass)
    client  = AiperApiClient(
        email=entry.data[CONF_EMAIL],
        password=entry.data[CONF_PASSWORD],
        session=session,
    )

    try:
        await client.async_login()
    except AiperAuthError as exc:
        _LOGGER.error("Authentication failed: %s", exc)
        return False
    except AiperConnectionError as exc:
        _LOGGER.error("Cannot reach Aiper cloud: %s", exc)
        return False

    coordinator = AiperDataCoordinator(
        hass=hass,
        client=client,
        device_id=entry.data[CONF_DEVICE_ID],
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        COORDINATOR: coordinator,
        "client":    client,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded
