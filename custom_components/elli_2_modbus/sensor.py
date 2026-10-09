"""Sensors."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from elli2modbus import ChargerStatus, ChargingState

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import ElliConfigEntry, ElliCoordinator
from .entity import ElliEntity


@dataclass(frozen=True, kw_only=True)
class ElliSensorDescription(SensorEntityDescription):
    value_fn: Callable[[ChargerStatus], float | int | str | None]


def _current(phase: int) -> ElliSensorDescription:
    return ElliSensorDescription(
        key=f"current_l{phase + 1}",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda d: d.currents[phase],
    )


def _voltage(phase: int) -> ElliSensorDescription:
    return ElliSensorDescription(
        key=f"voltage_l{phase + 1}",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.voltages[phase],
    )


SENSORS: tuple[ElliSensorDescription, ...] = (
    ElliSensorDescription(
        key="charging_state",
        device_class=SensorDeviceClass.ENUM,
        options=[s.name.lower() for s in ChargingState] + ["unknown"],
        value_fn=lambda d: d.state.name.lower() if d.state else "unknown",
    ),
    ElliSensorDescription(
        # Register 14 is apparent power (VA); at charging power factor ~1
        # it is used as active power, as evcc does.
        key="power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.power,
    ),
    ElliSensorDescription(
        key="energy_total",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=2,
        value_fn=lambda d: d.energy_total,
    ),
    ElliSensorDescription(
        key="energy_since_power_on",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=2,
        entity_registry_enabled_default=False,
        value_fn=lambda d: d.energy_since_power_on,
    ),
    ElliSensorDescription(
        key="current_limit",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda d: d.current_limit,
    ),
    _current(0),
    _current(1),
    _current(2),
    _voltage(0),
    _voltage(1),
    _voltage(2),
    ElliSensorDescription(
        key="pcb_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda d: d.pcb_temperature,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ElliConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(ElliSensor(coordinator, desc) for desc in SENSORS)


class ElliSensor(ElliEntity, SensorEntity):
    entity_description: ElliSensorDescription

    def __init__(
        self, coordinator: ElliCoordinator, description: ElliSensorDescription
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> float | int | str | None:
        return self.entity_description.value_fn(self.coordinator.data)
