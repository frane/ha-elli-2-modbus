# Elli Charger 2 (Modbus) for Home Assistant

**English** | [Deutsch](README.de.md)

> **EEBUS and more:** the successor [ha-elli](https://github.com/frane/ha-elli) supports Modbus TCP and EEBUS. This integration stays Modbus only.

Local Home Assistant integration for **Elli Charger 2** wallboxes over **Modbus TCP**. No cloud, no EEBUS, and the Elli app keeps working.

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
[![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=frane&repository=ha-elli-2-modbus&category=integration)

The Modbus code lives in the library [elli-2-modbus](https://github.com/frane/elli-2-modbus). Home Assistant installs it automatically.

## Supported wallboxes

Second-generation Elli wallboxes with firmware **R03.004.045.121-elli or newer**:

- Elli Charger Connect 2, Pro 2, Pro 2 Eichrecht
- Volkswagen ID. Charger Connect 2 / Pro 2
- Škoda Charger Connect 2 / Pro 2
- CUPRA Charger 2 / Pro 2

First-generation chargers have no Modbus server.

**Why Modbus?** Since firmware R03, the EEBUS connection to several energy managers (for example Solar Manager and evcc) has been broken. Elli's own HEMS whitelist lists Solar Manager only "up to software R04.004.041.009". Modbus TCP is the documented alternative. It runs locally and alongside the Elli backend.

## Setup

### Step 1: Enable Modbus on the wallbox

You need the **card with the access data** that came with the wallbox. The wallbox web interface is available in English and German; the German labels are given in brackets.

1. **Open the charger configuration** in a browser:
   - on your home network: `https://<IP or hostname of the wallbox>` (the hostname is on the card, the IP is in your router), or
   - through the wallbox hotspot: connect to the wallbox Wi-Fi (SSID and password from the card) and open `https://10.0.2.1`.

   The browser warns about the certificate. Click **Advanced** (*Erweitert*) and continue.
2. **Log in as Service User** with the service user password from the card.
3. **Check the firmware** under **Software update** (*Software-Update*). It must be **R03.004.045.121 or newer**; update first if it is older.
4. **Turn on the Modbus server:** **Connections → Modbus server** (*Verbindungen → Modbus-Server*) → **on**. Port 502, unit ID 1.
5. **Give the wallbox a fixed IP address:** a DHCP reservation in your router, or a static IP under **Connections → Ethernet**. Home Assistant must be on the same local network (not via LTE).
6. **Turn off the wallbox's own PV surplus charging**, so it does not regulate against Home Assistant: **Charging management → Charging settings → PV surplus charging → off** (*Ladeverwaltung → Ladeeinstellungen → PV-Laden aus*).
7. For fully automatic charging, enable instant charging (charging without authentication) in the Elli app. Otherwise a session may still need RFID or app authorization.

Optional check from any computer: `pip install elli-2-modbus && elli-2-modbus status <ip>`. More details: [enable-modbus.md](https://github.com/frane/elli-2-modbus/blob/main/docs/enable-modbus.md).

### Step 2: Install the integration with HACS

1. In Home Assistant, open **HACS** and click **⋮ (top right) → Custom repositories**. You can also use the "Open in HACS" button above.
2. Repository: `https://github.com/frane/ha-elli-2-modbus`, Type: **Integration** → **Add**.
3. Search for **Elli Charger 2 (Modbus)** in HACS → **Download**.
4. **Restart Home Assistant** (*Settings → System → Restart*).

<details><summary>Without HACS</summary>

Copy `custom_components/elli_2_modbus` into the `custom_components` folder of your Home Assistant configuration and restart.
</details>

### Step 3: Add the wallbox

1. *Settings → Devices & services → Add integration →* **Elli Charger 2 (Modbus)**.
2. Enter a name, the **IP address** of the wallbox, port `502` and Modbus ID `1`.
3. Done. The wallbox shows up as a device with the entities below.

Later changes: *Configure* sets the polling interval (default 5 s). *Reconfigure* changes the IP address without losing the entities.

### Step 4: Set the failsafe behaviour

Open the device and set **Failsafe current**. This is what the wallbox does when Home Assistant stops talking to it for longer than the **Watchdog timeout** (default 15 s):

- `0` = stop charging (safe for PV-only charging)
- `6`–`16` A = keep charging at that current

Keep the polling interval well below the watchdog timeout.

## Entities

| Entity | Type |
|---|---|
| Charging enabled | switch (off = wallbox blocks charging) |
| Charging current | number, 6–16 A in 0.1 A steps, applied while charging is enabled |
| Charging state | sensor (A1 … F) |
| Vehicle connected, Charging, Problem | binary sensors |
| Charging power, Total energy (Energy dashboard), Energy since power on | sensors |
| Active current limit | sensor (can be below the target because of internal limits) |
| Current and voltage L1–L3, PCB temperature | sensors |
| Failsafe current, Watchdog timeout | configuration |

For PV surplus charging, write an automation that sets *Charging current* and *Charging enabled* from your grid power. Any grid power sensor works: a smart meter, your inverter or your energy manager's integration.

## Firmware limits

- Maximum 16 A over Modbus, also on 22 kW variants (32 A announced by Elli)
- No phase switching over Modbus

## Troubleshooting

| Problem | Fix |
|---|---|
| "Cannot connect" during setup | Is the Modbus server on? Is the IP correct? Are Home Assistant and the wallbox on the same network? |
| "Wallbox answers, but not with the expected registers" | Firmware older than R03.004.045.121, or wrong Modbus ID |
| Charging stops by itself after a while | Watchdog: Home Assistant was unreachable longer than the watchdog timeout, so the failsafe current applies |
| Current is lower than set | The wallbox's internal limits (temperature, load management, §14a) have priority; see *Active current limit* |

## Development

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements_test.txt   # or: pip install -e ../elli-2-modbus
pytest
```

The tests run a real Home Assistant test instance against the wallbox simulator from `elli-2-modbus`.

*Not affiliated with Elli or Volkswagen Group Charging GmbH.*
