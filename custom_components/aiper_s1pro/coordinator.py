"""DataUpdateCoordinator for Aiper Scuba S1 Pro."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AiperApiClient, AiperAuthError, AiperConnectionError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class AiperDataCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that polls Aiper cloud for device status."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: AiperApiClient,
        device_id: str,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client
        self.device_id = device_id

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Aiper API."""
        try:
            return await self.client.async_get_device_status(self.device_id)
        except AiperAuthError as exc:
            # Try to re-authenticate once
            _LOGGER.warning("Token expired, re-authenticating…")
            try:
                await self.client.async_login()
                return await self.client.async_get_device_status(self.device_id)
            except Exception as reauth_exc:
                raise UpdateFailed(f"Re-auth failed: {reauth_exc}") from reauth_exc
        except AiperConnectionError as exc:
            raise UpdateFailed(f"Connection error: {exc}") from exc
