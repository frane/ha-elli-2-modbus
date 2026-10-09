# Elli Charger 2 (Modbus) für Home Assistant

[English](README.md) | **Deutsch**

> **EEBUS und mehr:** Der Nachfolger [ha-elli](https://github.com/frane/ha-elli) kann Modbus TCP und EEBUS, mit EEBUS auch die Elli-Wallboxen der ersten Generation. Diese Integration bleibt reine Modbus-Integration.

Lokale Home-Assistant-Integration für **Elli Charger 2** Wallboxen über **Modbus TCP**. Ohne Cloud, ohne EEBUS, und die Elli-App funktioniert weiter.

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
[![In HACS öffnen](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=frane&repository=ha-elli-2-modbus&category=integration)

Der Modbus-Code steckt in der Bibliothek [elli-2-modbus](https://github.com/frane/elli-2-modbus). Home Assistant installiert sie automatisch.

## Unterstützte Wallboxen

Elli-Wallboxen der zweiten Generation mit Firmware **R03.004.045.121-elli oder neuer**:

- Elli Charger Connect 2, Pro 2, Pro 2 Eichrecht
- Volkswagen ID. Charger Connect 2 / Pro 2
- Škoda Charger Connect 2 / Pro 2
- CUPRA Charger 2 / Pro 2

Wallboxen der ersten Generation haben keinen Modbus-Server.

**Warum Modbus?** Seit Firmware R03 ist die EEBUS-Anbindung an mehrere Energiemanager (z. B. Solar Manager und evcc) defekt. Ellis eigene HEMS-Whitelist führt Solar Manager nur „bis Software R04.004.041.009“. Modbus TCP ist die dokumentierte Alternative. Es läuft lokal und parallel zum Elli-Backend.

## Einrichtung

### Schritt 1: Modbus an der Wallbox aktivieren

Du brauchst die **Zugangsdatenkarte**, die bei der Wallbox lag. Die Weboberfläche der Wallbox gibt es auf Deutsch und Englisch; die englischen Bezeichnungen stehen in Klammern.

1. **Wallbox-Konfiguration öffnen** im Browser:
   - im Heimnetz: `https://<IP oder Hostname der Wallbox>` (Hostname steht auf der Karte, die IP im Router), oder
   - über den Hotspot der Wallbox: mit dem WLAN der Wallbox verbinden (SSID und Passwort von der Karte) und `https://10.0.2.1` öffnen.

   Der Browser warnt wegen des Zertifikats. Auf **Erweitert** (*Advanced*) klicken und fortfahren.
2. **Als Service User anmelden**, mit dem Service-User-Passwort von der Karte.
3. **Firmware prüfen** unter **Software-Update** (*Software update*). Sie muss **R03.004.045.121 oder neuer** sein; sonst zuerst aktualisieren.
4. **Modbus-Server einschalten:** **Verbindungen → Modbus-Server** (*Connections → Modbus server*) → **an**. Port 502, Modbus-ID 1.
5. **Feste IP-Adresse vergeben:** DHCP-Reservierung im Router oder statische IP unter **Verbindungen → Ethernet**. Home Assistant muss im selben lokalen Netz sein (nicht über LTE).
6. **Eigenes PV-Überschussladen der Wallbox ausschalten**, damit sie nicht gegen Home Assistant regelt: **Ladeverwaltung → Ladeeinstellungen → PV-Überschuss-Laden → PV-Laden aus** (*Charging management → Charging settings → PV surplus charging → off*).
7. Für vollautomatisches Laden in der Elli-App *Sofortladen* (Laden ohne Authentifizierung) aktivieren. Sonst kann ein Ladevorgang weiterhin eine Freigabe per RFID oder App brauchen.

Optionaler Test von einem beliebigen Rechner: `pip install elli-2-modbus && elli-2-modbus status <ip>`. Ausführlich: [enable-modbus.de.md](https://github.com/frane/elli-2-modbus/blob/main/docs/enable-modbus.de.md).

### Schritt 2: Integration über HACS installieren

1. In Home Assistant **HACS** öffnen → **⋮ (oben rechts) → Benutzerdefinierte Repositories**. Alternativ den Button „In HACS öffnen“ oben nutzen.
2. Repository: `https://github.com/frane/ha-elli-2-modbus`, Typ: **Integration** → **Hinzufügen**.
3. In HACS nach **Elli Charger 2 (Modbus)** suchen → **Herunterladen**.
4. **Home Assistant neu starten** (*Einstellungen → System → Neu starten*).

<details><summary>Ohne HACS</summary>

Den Ordner `custom_components/elli_2_modbus` in den Ordner `custom_components` deiner Home-Assistant-Konfiguration kopieren und neu starten.
</details>

### Schritt 3: Wallbox hinzufügen

1. *Einstellungen → Geräte & Dienste → Integration hinzufügen →* **Elli Charger 2 (Modbus)**.
2. Name, **IP-Adresse** der Wallbox, Port `502` und Modbus-ID `1` eintragen.
3. Fertig. Die Wallbox erscheint als Gerät mit den Entitäten unten.

Spätere Änderungen: Über *Konfigurieren* stellst du das Abfrageintervall ein (Standard 5 s). Über *Neu konfigurieren* änderst du die IP, ohne die Entitäten zu verlieren.

### Schritt 4: Failsafe festlegen

Im Gerät den **Failsafe-Strom** setzen. Diesen Strom nutzt die Wallbox, wenn Home Assistant länger als der **Watchdog-Timeout** (Standard 15 s) nicht mit ihr spricht:

- `0` = Laden stoppen (sicher für reines PV-Laden)
- `6`–`16` A = mit diesem Strom weiterladen

Das Abfrageintervall deutlich kürzer als den Watchdog-Timeout halten.

## Entitäten

| Entität | Typ |
|---|---|
| Laden freigegeben | Schalter (aus = Wallbox sperrt das Laden) |
| Ladestrom | Zahl, 6–16 A in 0,1-A-Schritten, wirkt solange das Laden freigegeben ist |
| Ladestatus | Sensor (A1 … F) |
| Fahrzeug verbunden, Lädt, Störung | Binärsensoren |
| Ladeleistung, Energie gesamt (Energie-Dashboard), Energie seit Neustart | Sensoren |
| Aktive Stromgrenze | Sensor (kann wegen interner Grenzen unter dem Sollwert liegen) |
| Strom und Spannung L1–L3, Platinentemperatur | Sensoren |
| Failsafe-Strom, Watchdog-Timeout | Konfiguration |

Für PV-Überschussladen eine Automation schreiben, die *Ladestrom* und *Laden freigegeben* anhand der Netzleistung setzt. Dafür eignet sich jeder Netzleistungs-Sensor: Smart Meter, Wechselrichter oder die Integration deines Energiemanagers.

## Grenzen der Firmware

- Maximal 16 A per Modbus, auch bei 22-kW-Varianten (Elli hat 32 A angekündigt)
- Keine Phasenumschaltung per Modbus

## Fehlersuche

| Problem | Lösung |
|---|---|
| „Keine Verbindung“ bei der Einrichtung | Ist der Modbus-Server an? Stimmt die IP? Sind Home Assistant und Wallbox im selben Netz? |
| „Die Wallbox antwortet, aber nicht mit den erwarteten Registern“ | Firmware älter als R03.004.045.121 oder falsche Modbus-ID |
| Laden stoppt nach einer Weile von selbst | Watchdog: Home Assistant war länger als der Watchdog-Timeout nicht erreichbar, deshalb greift der Failsafe-Strom |
| Strom niedriger als eingestellt | Die internen Grenzen der Wallbox (Temperatur, Lastmanagement, §14a) haben Vorrang; siehe *Aktive Stromgrenze* |

## Entwicklung

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements_test.txt   # oder: pip install -e ../elli-2-modbus
pytest
```

Die Tests starten eine echte Home-Assistant-Testinstanz gegen den Wallbox-Simulator aus `elli-2-modbus`.

*Kein offizielles Projekt von Elli oder der Volkswagen Group Charging GmbH.*
