"""Sensor platform for Aiper Scuba S1 Pro."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfArea, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_DEVICE_ID,
    COORDINATOR,
    DOMAIN,
    SENSOR_BATTERY,
    SENSOR_CLEAN_AREA,
    SENSOR_CLEAN_TIME,
    SENSOR_ERROR_CODE,
)
from .coordinator import AiperDataCoordinator


@dataclass(frozen=True, kw_only=True)
class AiperSensorDescription(SensorEntityDescription):
    """Description for Aiper sensor entities."""
    data_key: str = ""


SENSOR_DESCRIPTIONS: tuple[AiperSensorDescription, ...] = (
    AiperSensorDescription(
        key=SENSOR_BATTERY,
        name="Battery",
        data_key="batteryLevel",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    AiperSensorDescription(
        key=SENSOR_CLEAN_AREA,
        name="Last clean area",
        data_key="cleanArea",
        native_unit_of_measurement=UnitOfArea.SQUARE_METERS,
        icon="mdi:pool",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    AiperSensorDescription(
        key=SENSOR_CLEAN_TIME,
        name="Last clean duration",
        data_key="cleanTime",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        icon="mdi:timer-outline",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    AiperSensorDescription(
        key=SENSOR_ERROR_CODE,
        name="Error code",
        data_key="errorCode",
        icon="mdi:alert-circle-outline",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities."""
    data        = hass.data[DOMAIN][entry.entry_id]
    coordinator = data[COORDINATOR]
    device_id   = entry.data[CONF_DEVICE_ID]

    async_add_entities(
        AiperSensor(coordinator, entry, device_id, desc)
        for desc in SENSOR_DESCRIPTIONS
    )


class AiperSensor(CoordinatorEntity[AiperDataCoordinator], SensorEntity):
    """A sensor entity for the Aiper Scuba S1 Pro."""

    entity_description: AiperSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AiperDataCoordinator,
        entry: ConfigEntry,
        device_id: str,
        description: AiperSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._device_id         = device_id
        self._attr_unique_id    = f"{device_id}_{description.key}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=self._entry.title if hasattr(self, "_entry") else "Aiper Scuba S1 Pro",
            manufacturer="Aiper",
            model="Scuba S1 Pro",
        )

    @property
    def native_value(self) -> Any:
        return self.coordinator.data.get(self.entity_description.data_key)
