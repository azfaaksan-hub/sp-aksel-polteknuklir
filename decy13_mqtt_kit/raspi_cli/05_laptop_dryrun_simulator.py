#!/usr/bin/env python3
"""
SKRIP DRY-RUN DECY-13 DI LAPTOP / PC WINDOWS
==============================================
Tujuan: Mensimulasikan MQTT Daemon RPi 3B+ dari laptop Anda SEBELUM
        hardware fisik siap atau sebelum transfer file ke RPi.

Cara pakai di Windows (PowerShell / CMD):
  1. Install: pip install paho-mqtt
  2. Jalankan Mosquitto di laptop (lihat instruksi di bawah)
  3. python 05_laptop_dryrun_simulator.py

Cara pakai di Linux/Mac:
  pip3 install paho-mqtt
  python3 05_laptop_dryrun_simulator.py

PRASYARAT — Mosquitto di Laptop Windows:
  Download: https://mosquitto.org/download/
  Install, lalu buat file C:/mosquitto/mosquitto.conf berisi:
    listener 1883
    allow_anonymous true
    listener 9001
    protocol websockets
    allow_anonymous true
  Jalankan: "C:/Program Files/mosquitto/mosquitto.exe" -c C:/mosquitto/mosquitto.conf -v

CARA UJI WEB HMI TANPA RPi:
  1. Jalankan skrip ini di laptop
  2. Di web_hmi/index.html, ubah URL MQTT menjadi:
     ws://127.0.0.1:9001  (localhost)
  3. Buka index.html di browser, klik Hubungkan
  4. Kontrol tombol di HMI → daemon ini akan merespons
  5. State publish tiap 200ms → animasi HMI bergerak!
"""

import json
import math
import random
import threading
import time
import sys

try:
    import paho.mqtt.client as mqtt
    print("[OK] paho-mqtt tersedia.")
except ImportError:
    print("[ERROR] paho-mqtt belum terinstall!")
    print("        Jalankan: pip install paho-mqtt")
    sys.exit(1)

# ──────────────────────────────────────────────────────────────────
# KONFIGURASI (bisa diubah sesuai kebutuhan)
# ──────────────────────────────────────────────────────────────────
MQTT_HOST   = "127.0.0.1"   # localhost — ubah ke IP RPi jika diuji remote
MQTT_PORT   = 1883
TOPIC_CMD   = "decy13/hmi/cmd"
TOPIC_STATE = "decy13/rpi/state"
INTERVAL    = 0.2            # publish tiap 200ms

# ──────────────────────────────────────────────────────────────────
# STATE MACHINE (identik dengan 04_decy13_mqtt_daemon.py)
# ──────────────────────────────────────────────────────────────────
lock  = threading.Lock()
state = {
    "power": False, "vacuum": False, "rf": False, "magnet": True,
    "interlocks": False, "beam": False, "exposureActive": False,
    "emergency": False, "stage": 0, "mode": "Standby",
    "lcd_line1": "DECY-13 CYCLOTRON",
    "lcd_line2": "MODE: STANDBY",
    "lcd_line3": "VAC : 1.0e+3 mbar",
    "lcd_line4": "Menunggu Power & Vakum",
    "setpoint_magnet_a": 1450.0,
    "setpoint_rf_mhz": 22.5,
    "setpoint_rf_kv": 45.0,
    "setpoint_beam_ua": 8.4,
    "basePressure": 1013.0, "baseRf": 0.0,
    "baseCurrent": 0.0,     "baseEnergy": 0.0,
    "magnetCurrent": 1450.0,"frequency": 0.0,
    "rfPower": 0.0,         "pressure": 1013.0,
    "magnetPower": 85.2,    "targetCurrent": 0.0,
    "beamCurrent": 0.0,     "beamEnergy": 0.0,
    "peakEnergy": 13.0,     "exposureSeconds": 0.0,
    "activeLedIdx": -1,     "shootLedIdx": -1,
    "buzzerActive": False,  "buzzerUntil": 0.0,
    "logs": ["[DRY-RUN] Simulator laptop DECY-13 aktif. Menunggu perintah MQTT."]
}

SPIRAL_START, SPIRAL_END = 0, 47
SHOOT_START,  SHOOT_END  = 48, 63
last_tick = time.time()

def add_log(msg: str):
    ts = time.strftime("%H:%M:%S")
    entry = f"{ts} - {msg}"
    state["logs"].insert(0, entry)
    state["logs"] = state["logs"][:12]
    print(f"\033[96m[{ts}]\033[0m {msg}")

def handle_command(payload: dict):
    with lock:
        cmd = str(payload.get("cmd", "")).upper()
        s   = state

        if cmd == "TOGGLE_POWER":
            s["emergency"] = False
            s["power"] = not s["power"]
            if s["power"]:
                s["buzzerUntil"] = time.time() + 5.0
                add_log(">>> Tahap 1: POWER ON — Buzzer 5 detik (simulasi)")
            else:
                s["vacuum"] = s["interlocks"] = s["beam"] = s["exposureActive"] = False
                add_log("Power OFF: semua subsistem dimatikan.")

        elif cmd == "TOGGLE_VACUUM":
            if not s["power"]:
                add_log("[TOLAK] Nyalakan Power terlebih dahulu!"); return
            s["vacuum"] = not s["vacuum"]
            add_log(">>> Tahap 4: Kipas Vakum " + ("ON — memompa" if s["vacuum"] else "OFF"))

        elif cmd == "TOGGLE_INTERLOCK":
            if s["power"] and s["vacuum"] and s["pressure"] <= 1e-3:
                s["interlocks"] = not s["interlocks"]
                add_log(">>> Tahap 5: Interlock " + ("LOCKED — BEAM READY" if s["interlocks"] else "OPEN"))
            elif s["power"] and s["vacuum"]:
                add_log("[TUNGGU] Tekanan vakum belum < 1e-3 mbar!")
            else:
                add_log("[TOLAK] Power & Vacuum harus ON!")

        elif cmd == "AUTO_INIT":
            s["emergency"] = False
            s["power"] = True
            s["vacuum"] = True
            s["basePressure"] = 5.0e-6
            s["pressure"] = 5.0e-6
            s["interlocks"] = True
            s["mode"] = "Beam Ready"
            add_log(">>> Tahap 5: AUTO-INIT OK — Power, Vakum (< 1e-3 mbar), dan Interlock SIAP!")

        elif cmd == "START_BEAM":
            if not (s["power"] and s["vacuum"] and s["interlocks"]):
                s["emergency"] = False
                s["power"] = True
                s["vacuum"] = True
                s["basePressure"] = 5.0e-6
                s["pressure"] = 5.0e-6
                s["interlocks"] = True
                add_log(">>> [AUTO-PREPARE] Power, Vakum, dan Interlock disiapkan otomatis untuk START BEAM!")
            s["emergency"] = False
            s["beam"] = True
            s["exposureActive"] = False
            s["activeLedIdx"]   = SPIRAL_START
            add_log(">>> Tahap 6: START BEAM! LED Spiral mulai berputar.")

        elif cmd == "SHOOT":
            if s["beam"]:
                s["exposureActive"] = not s["exposureActive"]
                s["shootLedIdx"] = SHOOT_START if s["exposureActive"] else -1
                add_log(">>> Tahap 7: SHOOT " + ("AKTIF — menembak target!" if s["exposureActive"] else "DIHENTIKAN"))
            else:
                add_log("[TOLAK] Beam belum aktif!")

        elif cmd == "EMERGENCY_STOP":
            s["emergency"] = True
            s["power"] = s["vacuum"] = s["interlocks"] = s["beam"] = s["exposureActive"] = False
            s["buzzerUntil"] = time.time() + 3.0
            add_log("!!! EMERGENCY STOP !!! Semua sistem diputus.")

        elif cmd == "SET_PARAMS":
            if "magnet_a" in payload: s["setpoint_magnet_a"] = float(payload["magnet_a"])
            if "rf_mhz"   in payload: s["setpoint_rf_mhz"]   = float(payload["rf_mhz"])
            if "rf_kv"    in payload: s["setpoint_rf_kv"]     = float(payload["rf_kv"])
            if "beam_ua"  in payload: s["setpoint_beam_ua"]   = float(payload["beam_ua"])
            add_log(f"SET_PARAMS: Mag={s['setpoint_magnet_a']}A  Vdee={s['setpoint_rf_kv']}kV")

        else:
            add_log(f"[INFO] Perintah tidak dikenal: {cmd}")

def step_physics():
    global last_tick
    now = time.time()
    dt  = max(0.01, min(1.0, now - last_tick))
    last_tick = now

    with lock:
        s = state

        # Vakum eksponensial
        if s["power"] and s["vacuum"]:
            s["basePressure"] = max(1.2e-7, s["basePressure"] * math.exp(-dt * 3.2))
        else:
            s["basePressure"] = min(1013.0, s["basePressure"] * 2.5 + 5.0)
        s["pressure"] = s["basePressure"] * (1 + random.uniform(-0.08, 0.08)) \
                        if s["basePressure"] < 1e-5 else s["basePressure"]

        # Cascading interlock
        if not s["power"] or not s["vacuum"]:
            s["interlocks"] = False
        if not s["interlocks"] and s["beam"]:
            s["beam"] = s["exposureActive"] = False
            add_log("BEAM DROP: Interlock terbuka!")

        # Fisika energi, RF, arus
        b_ratio  = s["setpoint_magnet_a"] / 1450.0
        rf_ratio = s["setpoint_rf_kv"]    / 45.0
        max_mev  = 13.0 * min(1.15, b_ratio * rf_ratio)

        if s["beam"]:
            s["rf"]         = True
            s["baseRf"]     = min(185.7 * rf_ratio, s["baseRf"] + (185.7 / 4.0) * dt)
            s["baseCurrent"]= min(s["setpoint_beam_ua"], s["baseCurrent"] + (s["setpoint_beam_ua"] / 3.0) * dt)
            s["baseEnergy"] = min(max_mev, s["baseEnergy"] + (max_mev / 6.0) * dt)
            if s["exposureActive"]:
                s["exposureSeconds"] += dt
        else:
            s["rf"]         = False
            s["baseRf"]     = max(0.0, s["baseRf"] - (185.7 / 3.0) * dt)
            s["baseCurrent"]= max(0.0, s["baseCurrent"] - 4.0 * dt)
            s["baseEnergy"] = max(0.0, s["baseEnergy"] - 5.0 * dt)

        s["magnetCurrent"]= s["setpoint_magnet_a"] + random.uniform(-1.5, 1.5) if s["power"] else 0.0
        s["magnetPower"]  = (s["magnetCurrent"] / 1450.0) * 85.2
        s["frequency"]    = s["setpoint_rf_mhz"] + random.uniform(-0.01, 0.01) if s["rf"] else 0.0
        s["rfPower"]      = s["baseRf"]
        s["beamCurrent"]  = s["baseCurrent"]
        s["beamEnergy"]   = s["baseEnergy"]
        s["targetCurrent"]= s["beamCurrent"] * 0.95 if s["exposureActive"] else 0.0

        # Tahap & teks LCD
        if s["emergency"]:
            s["stage"], s["mode"] = 0, "EMERGENCY"
            s["lcd_line1"] = "!!! EMERGENCY STOP !!!"
            s["lcd_line2"] = "Seluruh Daya & RF Terputus"
        elif not s["power"]:
            s["stage"], s["mode"] = 0, "Standby"
            s["lcd_line1"] = "TAHAP 0: SYSTEM STANDBY"
            s["lcd_line2"] = "Nyalakan Saklar [Power]"
        elif not s["vacuum"]:
            s["stage"], s["mode"] = 1, "Power On"
            s["lcd_line1"] = "TAHAP 1-3: INISIASI & HMI"
            s["lcd_line2"] = "Nyalakan [Vacuum] Kipas"
        elif s["pressure"] > 1e-3:
            s["stage"], s["mode"] = 4, "Vacuum Pumping"
            s["lcd_line1"] = "TAHAP 4: POMPA VAKUM AKTIF"
            s["lcd_line2"] = f"P: {s['pressure']:.1e} mbar"
        elif not s["interlocks"]:
            s["stage"], s["mode"] = 5, "Vac OK - Set Interlock"
            s["lcd_line1"] = "TAHAP 5: VAKUM TERCAPAI"
            s["lcd_line2"] = "Aktifkan [Interlocks]"
        elif not s["beam"]:
            s["stage"], s["mode"] = 5, "Beam Ready"
            s["lcd_line1"] = "TAHAP 5: BEAM READY"
            s["lcd_line2"] = "Tekan [START BEAM]"
        elif not s["exposureActive"]:
            s["stage"], s["mode"] = 6, "Beam On"
            s["lcd_line1"] = "TAHAP 6: SPIRAL & RF"
            s["lcd_line2"] = f"Energi: {s['beamEnergy']:.1f} MeV"
        else:
            s["stage"], s["mode"] = 7, "Exposure Active"
            s["lcd_line1"] = "TAHAP 7: SHOOT EXPOSURE!"
            s["lcd_line2"] = f"Target: {s['targetCurrent']:.1f} uA"

        s["lcd_line3"] = f"Mag:{s['magnetCurrent']:.0f}A | RF:{s['frequency']:.1f}MHz"
        s["lcd_line4"] = f"Vac:{s['pressure']:.1e}mbar | E:{s['beamEnergy']:.1f}MeV"

        # Update indeks LED spiral
        if s["beam"]:
            step_inc = max(1, int((s["beamEnergy"] / 13.0) * 3) + 1)
            s["activeLedIdx"] = SPIRAL_START + (
                (s["activeLedIdx"] - SPIRAL_START + step_inc)
                % (SPIRAL_END - SPIRAL_START + 1)
            )
            if s["exposureActive"]:
                s["shootLedIdx"] = SHOOT_START + (
                    (s["shootLedIdx"] - SHOOT_START + 2)
                    % (SHOOT_END - SHOOT_START + 1)
                )
            else:
                s["shootLedIdx"] = -1
        else:
            s["activeLedIdx"] = 0 if s["power"] else -1
            s["shootLedIdx"]  = -1

        s["buzzerActive"] = (now < s["buzzerUntil"]) or \
                            (s["exposureActive"] and int(now * 2) % 2 == 0)

def main():
    print("=" * 60)
    print("  DECY-13 MQTT DRY-RUN SIMULATOR (Mode Laptop)")
    print(f"  Broker: {MQTT_HOST}:{MQTT_PORT}")
    print(f"  CMD  : {TOPIC_CMD}")
    print(f"  STATE: {TOPIC_STATE} (tiap {int(INTERVAL*1000)} ms)")
    print("=" * 60)
    print("  PERINTAH UJI (kirim via mosquitto_pub atau Web HMI):")
    print('  TOGGLE_POWER     : {"cmd":"TOGGLE_POWER"}')
    print('  TOGGLE_VACUUM    : {"cmd":"TOGGLE_VACUUM"}')
    print('  TOGGLE_INTERLOCK : {"cmd":"TOGGLE_INTERLOCK"}')
    print('  START_BEAM       : {"cmd":"START_BEAM"}')
    print('  SHOOT            : {"cmd":"SHOOT"}')
    print('  EMERGENCY_STOP   : {"cmd":"EMERGENCY_STOP"}')
    print("=" * 60)

    try:
        # paho-mqtt >= 2.0.0
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id="decy13_laptop_dryrun")
    except (AttributeError, TypeError):
        # paho-mqtt < 2.0.0
        client = mqtt.Client(client_id="decy13_laptop_dryrun")

    def on_connect(c, userdata, flags, rc):
        if rc == 0:
            c.subscribe(TOPIC_CMD)
            add_log(f"Terhubung ke Mosquitto {MQTT_HOST}:{MQTT_PORT}. Subscribe: {TOPIC_CMD}")
        else:
            print(f"[ERROR] Gagal connect MQTT rc={rc}")
            print(f"        Pastikan Mosquitto berjalan di {MQTT_HOST}:{MQTT_PORT}")

    def on_message(c, userdata, msg):
        try:
            data = json.loads(msg.payload.decode("utf-8"))
            handle_command(data)
        except Exception as e:
            print(f"[ERROR] Parse payload: {e}")

    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_HOST, MQTT_PORT, 60)
        client.loop_start()
    except Exception as e:
        print(f"\n[ERROR] Tidak bisa terhubung ke MQTT Broker: {e}")
        print(f"        Pastikan Mosquitto berjalan di port {MQTT_PORT}")
        print(f"        Windows: jalankan mosquitto.exe -c mosquitto.conf")
        sys.exit(1)

    print("\nSimulator berjalan... Ctrl+C untuk berhenti.\n")
    try:
        while True:
            step_physics()
            with lock:
                payload = json.dumps(state)
            try:
                client.publish(TOPIC_STATE, payload, qos=0)
            except Exception:
                pass
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("\nSimulator dihentikan.")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
