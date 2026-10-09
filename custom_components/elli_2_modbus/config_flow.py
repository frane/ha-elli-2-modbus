"""Config flow."""

from __future__ import annotations

import logging
from typing import Any

from elli2modbus import ElliCharger, ModbusConnectionError, ModbusError
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_UNIT_ID,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_UNIT_ID,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)
from .coordinator import ElliConfigEntry

_LOGGER = logging.getLogger(__name__)


def _connection_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=defaults.get(CONF_HOST, vol.UNDEFINED)): str,
            vol.Required(CONF_PORT, default=defaults.get(CONF_PORT, DEFAULT_PORT)): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=65535)
            ),
            vol.Required(
                CONF_UNIT_ID, default=defaults.get(CONF_UNIT_ID, DEFAULT_UNIT_ID)
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=255)),
        }
    )


async def _validate(data: dict[str, Any]) -> str | None:
    """Return an error key, or None if the wallbox answered."""
    charger = ElliCharger(data[CONF_HOST], data[CONF_PORT], data[CONF_UNIT_ID])
    try:
        await charger.read_info()
    except ModbusConnectionError:
        return "cannot_connect"
    except ModbusError:
        return "modbus_error"
    except Exception:  # noqa: BLE001
        _LOGGER.exception("Unexpected error validating wallbox")
        return "unknown"
    finally:
        await charger.close()
    return None


def _unique_id(data: dict[str, Any]) -> str:
    return f"{data[CONF_HOST].strip().lower()}:{data[CONF_PORT]}:{data[CONF_UNIT_ID]}"


class ElliConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            user_input[CONF_HOST] = user_input[CONF_HOST].strip()
            await self.async_set_unique_id(_unique_id(user_input))
            self._abort_if_unique_id_configured()
            if (error := await _validate(user_input)) is None:
                name = user_input.pop(CONF_NAME, DEFAULT_NAME)
                return self.async_create_entry(title=name, data=user_input)
            errors["base"] = error

        schema = vol.Schema(
            {vol.Required(CONF_NAME, default=DEFAULT_NAME): str}
        ).extend(_connection_schema(user_input or {}).schema)
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            user_input[CONF_HOST] = user_input[CONF_HOST].strip()
            if (error := await _validate(user_input)) is None:
                # Keep the unique id stable so entities survive an IP change.
                return self.async_update_reload_and_abort(entry, data_updates=user_input)
            errors["base"] = error
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_connection_schema(user_input or dict(entry.data)),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry: ElliConfigEntry) -> ElliOptionsFlow:
        return ElliOptionsFlow()


class ElliOptionsFlow(OptionsFlow):
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                data={CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL])}
            )
        current = self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        schema = vol.Schema(
            {
                vol.Required(CONF_SCAN_INTERVAL, default=current): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=MIN_SCAN_INTERVAL,
                        max=MAX_SCAN_INTERVAL,
                        step=1,
                        unit_of_measurement="s",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                )
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
