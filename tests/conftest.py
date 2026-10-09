"""Fixtures: a simulated Elli wallbox on localhost."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from elli2modbus.simulator import ElliSim
import pytest

from homeassistant.const import CONF_HOST, CONF_PORT

from custom_components.elli_2_modbus.const import CONF_UNIT_ID, DOMAIN


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
async def sim(socket_enabled) -> AsyncGenerator[tuple[ElliSim, int]]:
    wallbox = ElliSim()
    server = await wallbox.start("127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    yield wallbox, port
    server.close()
    await server.wait_closed()


@pytest.fixture
def entry_data(sim) -> dict:
    _, port = sim
    return {CONF_HOST: "127.0.0.1", CONF_PORT: port, CONF_UNIT_ID: 1}


@pytest.fixture
async def setup_entry(hass, entry_data):
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Elli Wallbox",
        data=entry_data,
        unique_id=f"127.0.0.1:{entry_data[CONF_PORT]}:1",
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    yield entry
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
