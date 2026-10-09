"""Tests against the simulated wallbox from elli-2-modbus."""

from __future__ import annotations

import socket

import pytest

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import ServiceValidationError

from custom_components.elli_2_modbus.const import CONF_UNIT_ID, DOMAIN


# --- Config flow -----------------------------------------------------------


async def test_config_flow_success(hass, entry_data):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_NAME: "Garage", **entry_data}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Garage"
    assert result["data"] == entry_data
    await hass.async_block_till_done()

    # second time: already configured
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_NAME: "Garage", **entry_data}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    for entry in hass.config_entries.async_entries(DOMAIN):
        await hass.config_entries.async_unload(entry.entry_id)


async def test_config_flow_cannot_connect(hass, socket_enabled):
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_NAME: "x", CONF_HOST: "127.0.0.1", CONF_PORT: port, CONF_UNIT_ID: 1},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_options_flow(hass, setup_entry):
    result = await hass.config_entries.options.async_init(setup_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_SCAN_INTERVAL: 10}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert setup_entry.options == {CONF_SCAN_INTERVAL: 10}
    assert setup_entry.runtime_data.update_interval.total_seconds() == 10


# --- Entities --------------------------------------------------------------


def _state(hass, entity_id):
    st = hass.states.get(entity_id)
    assert st is not None, f"{entity_id} missing; have {hass.states.async_entity_ids()}"
    return st.state


async def test_entities_idle(hass, setup_entry):
    assert _state(hass, "sensor.elli_wallbox_charging_state") == "b1"
    assert _state(hass, "binary_sensor.elli_wallbox_vehicle_connected") == "on"
    assert _state(hass, "binary_sensor.elli_wallbox_charging") == "off"
    assert _state(hass, "binary_sensor.elli_wallbox_problem") == "off"
    assert _state(hass, "switch.elli_wallbox_charging_enabled") == "off"
    assert float(_state(hass, "sensor.elli_wallbox_total_energy")) == pytest.approx(1234.567)
    assert float(_state(hass, "sensor.elli_wallbox_voltage_l2")) == 229
    assert float(_state(hass, "sensor.elli_wallbox_pcb_temperature")) == 32.5
    assert float(_state(hass, "number.elli_wallbox_charging_current")) == 16  # hw max
    assert float(_state(hass, "number.elli_wallbox_watchdog_timeout")) == 15
    num = hass.states.get("number.elli_wallbox_charging_current")
    assert num.attributes["min"] == 6 and num.attributes["max"] == 16


async def test_charging_control(hass, setup_entry, sim):
    wallbox, _ = sim

    # set target while blocked: nothing is written
    await hass.services.async_call(
        "number", "set_value",
        {"entity_id": "number.elli_wallbox_charging_current", "value": 10},
        blocking=True,
    )
    assert wallbox.writes == []
    assert float(_state(hass, "number.elli_wallbox_charging_current")) == 10

    # enable charging -> 261 = 100 (10 A)
    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": "switch.elli_wallbox_charging_enabled"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert wallbox.writes == [(261, 100)]
    assert _state(hass, "switch.elli_wallbox_charging_enabled") == "on"
    assert _state(hass, "sensor.elli_wallbox_charging_state") == "c2"
    assert _state(hass, "binary_sensor.elli_wallbox_charging") == "on"
    assert float(_state(hass, "sensor.elli_wallbox_charging_power")) == 6900
    assert float(_state(hass, "sensor.elli_wallbox_current_l1")) == 10
    assert float(_state(hass, "sensor.elli_wallbox_active_current_limit")) == 10

    # change current while charging -> written immediately (0.1 A resolution)
    await hass.services.async_call(
        "number", "set_value",
        {"entity_id": "number.elli_wallbox_charging_current", "value": 7.3},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert wallbox.writes[-1] == (261, 73)

    # disable -> 0
    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": "switch.elli_wallbox_charging_enabled"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert wallbox.writes[-1] == (261, 0)
    assert _state(hass, "sensor.elli_wallbox_charging_state") == "b1"

    # re-enable resumes last target
    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": "switch.elli_wallbox_charging_enabled"},
        blocking=True,
    )
    assert wallbox.writes[-1] == (261, 73)


async def test_failsafe_and_watchdog(hass, setup_entry, sim):
    wallbox, _ = sim
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            "number", "set_value",
            {"entity_id": "number.elli_wallbox_failsafe_current", "value": 3},
            blocking=True,
        )
    await hass.services.async_call(
        "number", "set_value",
        {"entity_id": "number.elli_wallbox_failsafe_current", "value": 6},
        blocking=True,
    )
    await hass.services.async_call(
        "number", "set_value",
        {"entity_id": "number.elli_wallbox_watchdog_timeout", "value": 30},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert (262, 60) in wallbox.writes and (257, 30000) in wallbox.writes
    assert float(_state(hass, "number.elli_wallbox_failsafe_current")) == 6
    assert float(_state(hass, "number.elli_wallbox_watchdog_timeout")) == 30


async def test_unavailable_when_wallbox_gone(hass, setup_entry, sim):
    coordinator = setup_entry.runtime_data
    await coordinator.charger.close()
    coordinator.charger.client.port = 1  # nothing listens there
    coordinator.charger.client.timeout = 0.5
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert not coordinator.last_update_success
    assert _state(hass, "sensor.elli_wallbox_charging_power") == "unavailable"
