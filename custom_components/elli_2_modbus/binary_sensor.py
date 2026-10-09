"""Binary sensors."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from elli2modbus import ChargerStatus

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import ElliConfigEntry, ElliCoordinator
from .entity import ElliEntity


@dataclass(frozen=True, kw_only=True)
class ElliBinaryDescription(BinarySensorEntityDescription):
    value_fn: Callable[[ChargerStatus], bool]


BINARY_SENSORS = (
    ElliBinaryDescription(
        key="vehicle_connected",
        device_class=BinarySensorDeviceClass.PLUG,
        value_fn=lambda d: d.vehicle_connected,
    ),
    ElliBinaryDescription(
        key="charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        value_fn=lambda d: d.charging,
    ),
    ElliBinaryDescription(
        key="problem",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda d: d.problem,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ElliConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(ElliBinarySensor(coordinator, d) for d in BINARY_SENSORS)


class ElliBinarySensor(ElliEntity, BinarySensorEntity):
    entity_description: ElliBinaryDescription

    def __init__(
        self, coordinator: ElliCoordinator, description: ElliBinaryDescription
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool:
        return self.entity_description.value_fn(self.coordinator.data)
