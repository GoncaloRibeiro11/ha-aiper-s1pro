"""Vacuum platform for Aiper Scuba S1 Pro."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.vacuum import (
    STATE_CLEANING,
    STATE_DOCKED,
    STATE_ERROR,
    STATE_IDLE,
    STATE_PAUSED,
    STATE_RETURNING,
    StateVacuumEntity,
    VacuumEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import CLEANING_MODES
from .const import CONF_DEVICE_ID, COORDINATOR, DOMAIN
from .coordinator import AiperDataCoordinator

_LOGGER = logging.getLogger(__name__)

# Map Aiper API states → HA vacuum states
AIPER_STATE_MAP: dict[str, str] = {
    "CLEANING":  STATE_CLEANING,
    "DOCKED":    STATE_DOCKED,
    "CHARGING":  STATE_DOCKED,
    "IDLE":      STATE_IDLE,
    "PAUSED":    STATE_PAUSED,
    "RETURNING": STATE_RETURNING,
    "ERROR":     STATE_ERROR,
}

SUPPORTED_FEATURES = (
    VacuumEntityFeature.START
    | VacuumEntityFeature.STOP
    | VacuumEntityFeature.PAUSE
    | VacuumEntityFeature.RETURN_HOME
    | VacuumEntityFeature.BATTERY
    | VacuumEntityFeature.STATUS
    | VacuumEntityFeature.FAN_SPEED   # re-used for cleaning mode
    | VacuumEntityFeature.LOCATE
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the vacuum entity."""
    data        = hass.data[DOMAIN][entry.entry_id]
    coordinator = data[COORDINATOR]
    device_id   = entry.data[CONF_DEVICE_ID]

    async_add_entities([AiperS1ProVacuum(coordinator, entry, device_id)])


class AiperS1ProVacuum(CoordinatorEntity[AiperDataCoordinator], StateVacuumEntity):
    """Representation of the Aiper Scuba S1 Pro as a HA vacuum entity."""

    _attr_supported_features = SUPPORTED_FEATURES
    _attr_fan_speed_list      = list(CLEANING_MODES.keys())
    _attr_has_entity_name     = True
    _attr_name                = None  # uses device name

    def __init__(
        self,
        coordinator: AiperDataCoordinator,
        entry: ConfigEntry,
        device_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._device_id  = device_id
        self._entry      = entry
        self._attr_unique_id = f"{device_id}_vacuum"

    # ------------------------------------------------------------------
    # Device info
    # ------------------------------------------------------------------

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=self._entry.title,
            manufacturer="Aiper",
            model="Scuba S1 Pro",
        )

    # ------------------------------------------------------------------
    # State properties
    # ------------------------------------------------------------------

    @property
    def state(self) -> str:
        raw = self.coordinator.data.get("state", "IDLE")
        return AIPER_STATE_MAP.get(raw, STATE_IDLE)

    @property
    def battery_level(self) -> int | None:
        return self.coordinator.data.get("batteryLevel")

    @property
    def fan_speed(self) -> str | None:
        """Return current cleaning mode (re-used as fan_speed)."""
        api_mode = self.coordinator.data.get("cleaningMode", "AUTO")
        # Reverse lookup
        return next(
            (k for k, v in CLEANING_MODES.items() if v == api_mode),
            "auto",
        )

    @property
    def error(self) -> str | None:
        if self.state == STATE_ERROR:
            return self.coordinator.data.get("errorMsg", "Unknown error")
        return None

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    async def async_start(self) -> None:
        await self.coordinator.client.async_start_cleaning(
            self._device_id, mode=self.fan_speed or "auto"
        )
        await self.coordinator.async_request_refresh()

    async def async_stop(self, **kwargs: Any) -> None:
        await self.coordinator.client.async_stop_cleaning(self._device_id)
        await self.coordinator.async_request_refresh()

    async def async_pause(self) -> None:
        await self.coordinator.client.async_pause_cleaning(self._device_id)
        await self.coordinator.async_request_refresh()

    async def async_return_to_base(self, **kwargs: Any) -> None:
        await self.coordinator.client.async_return_to_dock(self._device_id)
        await self.coordinator.async_request_refresh()

    async def async_locate(self, **kwargs: Any) -> None:
        await self.coordinator.client.async_locate(self._device_id)

    async def async_set_fan_speed(self, fan_speed: str, **kwargs: Any) -> None:
        """Change cleaning mode (before starting a cycle)."""
        # Store locally; applied on next async_start()
        self._attr_fan_speed = fan_speed
        self.async_write_ha_state()
