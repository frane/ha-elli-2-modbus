"""Charging on/off switch."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import ElliConfigEntry, ElliCoordinator
from .entity import ElliEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ElliConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([ChargingSwitch(entry.runtime_data)])


class ChargingSwitch(ElliEntity, SwitchEntity):
    """On: register 261 = target current. Off: register 261 = 0."""

    _attr_icon = "mdi:ev-plug-type2"

    def __init__(self, coordinator: ElliCoordinator) -> None:
        super().__init__(coordinator, "charging_enabled")

    @property
    def is_on(self) -> bool:
        return self.coordinator.charging_enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_charging(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_charging(False)
