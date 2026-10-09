"""Constants for the Elli Charger 2 (Modbus) integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "elli_2_modbus"

DEFAULT_NAME: Final = "Elli Wallbox"
DEFAULT_PORT: Final = 502
DEFAULT_UNIT_ID: Final = 1
DEFAULT_SCAN_INTERVAL: Final = 5  # s, well below the 15 s default watchdog
MIN_SCAN_INTERVAL: Final = 2
MAX_SCAN_INTERVAL: Final = 60

CONF_UNIT_ID: Final = "unit_id"

MANUFACTURER: Final = "Elli"
MODEL: Final = "Charger 2"
WATCHDOG_MAX_SECONDS: Final = 65
