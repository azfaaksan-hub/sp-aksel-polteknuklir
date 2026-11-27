#!/usr/bin/env python3
"""
DIVISI 1 (CORE BACKEND): DAEMON UTAMA MQTT & PHYSICS ENGINE RASPBERRY PI 3B+
============================================================================
Penanggung Jawab : Anggota 1 (Lead / Core Raspi Backend & Integrator)
Branch GitHub    : main / core-raspi-backend
File Terkait     : - raspi_cli/04_decy13_mqtt_daemon.py (File ini)
                   - raspi_cli/config_hardware.json
                   - raspi_cli/modules/base_module.py

Arsitektur Anti-Konflik (Modular Plugin Pattern):
File ini HANYA mengatur:
  1. Koneksi MQTT Broker (`decy13/hmi/cmd` & `decy13/rpi/state`)
  2. State Machine 7-Tahap & Perhitungan Fisika Siklotron DECY-13 (13 MeV H-)
  3. Orkestrasi pemanggilan modul hardware dari Divisi 2, 3, dan 4:
     - `VacuumSafetyModule` (Divisi 2: `modules/mod_vacuum_safety.py`)
     - `LedStripModule`     (Divisi 3: `modules/mod_led_ws2812b.py`)
     - `LcdDisplayModule`   (Divisi 4: `modules/mod_lcd_ili9341.py`)

Jalankan di Raspberry Pi 3B+:
  sudo python3 04_decy13_mqtt_daemon.py
"""

import json
import math
import os
import random
import signal
import socket
import threading
import time
import warnings
import paho.mqtt.client as mqtt

warnings.filterwarnings("ignore", category=DeprecationWarning)

from modules import (
    VacuumSafetyModule,
    LedStripModule,
    LcdDisplayModule,
)

try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
except ImportError:
    HAS_GPIO = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config_hardware.json")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CFG = json.load(f)

# Batas aman setpoint dari HMI (bisa dioverride lewat `setpoint_limits` di config).
# Default mengikuti rentang slider Web HMI agar nilai sah tidak ikut tertolak.
_DEFAULT_SETPOINT_LIMITS = {
    "magnet_a": (400.0, 2200.0),
    "rf_mhz": (15.0, 30.0),
    "rf_kv": (0.0, 120.0),
    "beam_ua": (0.0, 100.0),
}
SETPOINT_LIMITS = dict(_DEFAULT_SETPOINT_LIMITS)
for _k, _v in CFG.get("setpoint_limits", {}).items():
    try:
        _lo, _hi = float(_v[0]), float(_v[1])
        if math.isfinite(_lo) and math.isfinite(_hi) and _lo <= _hi:
            SETPOINT_LIMITS[_k] = (_lo, _hi)
    except (TypeError, ValueError, IndexError):
        pass


def _validasi_setpoint(key: str, raw):
    """Kembalikan float valid dalam batas, atau None bila harus ditolak."""
    if isinstance(raw, bool):
        return None
    try:
        nilai = float(raw)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(nilai):
        return None
    lo, hi = SETPOINT_LIMITS.get(key, (-math.inf, math.inf))
    if nilai < lo or nilai > hi:
        return None
    return nilai


class Decy13CoreDaemon:
    """Core Backend Orchestrator & Physics State Machine Siklotron DECY-13."""

    def __init__(self):
        self.lock = threading.Lock()
        # Keadaan Nyata Perangkat Keras (Source of Truth — Kontrak JSON MQTT)
        self.state = {
            "power": False,
            "vacuum": False,
            "rf": False,
            "magnet": True,
            "interlocks": False,
            "beam": False,
            "exposureActive": False,
            "emergency": False,
            "stage": 0,
            "mode": "Standby",
            "lcd_line1": "DECY-13 CYCLOTRON",
            "lcd_line2": "MODE: STANDBY",
            "lcd_line3": "VAC : 1.0e+3 mbar",
            "lcd_line4": "Menunggu Power & Vakum",
            # Parameter Fisika yang Dapat Diinput dari HMI
            "setpoint_magnet_a": CFG["physics_defaults"]["magnet_current_a"],
            "setpoint_rf_mhz": CFG["physics_defaults"]["rf_freq_mhz"],
            "setpoint_rf_kv": CFG["physics_defaults"]["rf_voltage_kv"],
            "setpoint_beam_ua": 8.4,
            # Nilai Aktual Real-Time
            "basePressure": 1013.0,
            "baseRf": 0.0,
            "baseCurrent": 0.0,
            "baseEnergy": 0.0,
            "magnetCurrent": 1450.0,
            "frequency": 22.50,
            "rfPower": 0.0,
            "pressure": 1013.0,
            "magnetPower": 85.2,
            "targetCurrent": 0.0,
            "beamCurrent": 0.0,
            "beamEnergy": 0.0,
            "peakEnergy": CFG["physics_defaults"].get("max_energy_mev", 13.0),
            "exposureSeconds": 0.0,
            "activeLedIdx": -1,
            "shootLedIdx": -1,
            "buzzerActive": False,
            "buzzerUntil": 0.0,
            "logs": ["Sistem Core Daemon RPi 3B+ siap. Menunggu perintah MQTT."]
        }
        self.last_tick = time.time()

        # Daftar plugin modul dari Divisi 2, 3, dan 4.
        # PENTING: LcdDisplayModule (SPI0 ILI9341) dinonaktifkan secara default saat
        # `lcd_spi_enabled=false` (Divisi 4 resmi memakai 3 Arduino Uno TFT USB) karena
        # default `luma.lcd.device.ili9341` mengklaim `gpio_LIGHT=18` menjadi OUTPUT HIGH
        # yang merampas PWM0 GPIO 18 milik LED WS2812B! Bila `lcd_spi_enabled=true`,
        # LcdDisplayModule ditaruh SEBELUM LedStripModule agar GPIO 18 tetap dipegang PWM0.
        self.lcd_spi_enabled = bool(CFG.get("pins_bcm", {}).get("lcd_spi_enabled", False))
        self.modules = [
            VacuumSafetyModule(CFG),
        ]
        if self.lcd_spi_enabled:
            self.modules.append(LcdDisplayModule(CFG))
        self.modules.append(LedStripModule(CFG))
        self.init_modules()

    def add_log(self, msg: str) -> None:
        ts = time.strftime("%H:%M:%S")
        self.state["logs"].insert(0, f"{ts} - {msg}")
        self.state["logs"] = self.state["logs"][:12]
        print(f"[{ts}] {msg}")

    def init_modules(self) -> None:
        print("=" * 64)
        print("  INISIALISASI MODUL HARDWARE SIKLOTRON DECY-13 (ARSITEKTUR 6 DIVISI)")
        print("=" * 64)
        for mod in self.modules:
            try:
                hw_ok = mod.setup()
                mod.update(self.state, 0.0, time.time())
                status_txt = "HARDWARE AKTIF" if hw_ok else "SIMULASI / FALLBACK"
                print(f"  - {mod.name:<22} : [{status_txt}]")
            except Exception as e:
                print(f"  - {mod.name:<22} : [ERROR ISOLATED: {e}]")
        if not self.lcd_spi_enabled:
            print(f"  - {'LcdDisplayModule':<22} : [NONAKTIF - Mode 3-TFT USB / Anti-Konflik PWM0 LED]")
        print("=" * 64, flush=True)

    def handle_command(self, payload: dict) -> None:
        with self.lock:
            cmd = str(payload.get("cmd", "")).upper()
            s = self.state

            if cmd == "TOGGLE_POWER":
                s["emergency"] = False
                s["power"] = not s["power"]
                if s["power"]:
                    s["buzzerUntil"] = time.time() + 5.0
                    self.add_log("Tahap 1: Power ON (Buzzer Indikator 5 detik aktif)")
                else:
                    s["vacuum"] = False
                    s["interlocks"] = False
                    s["beam"] = False
                    s["exposureActive"] = False
                    s["buzzerUntil"] = 0.0
                    self.add_log("Power OFF: Seluruh subsistem dimatikan.")

            elif cmd == "TOGGLE_VACUUM":
                if not s["power"]:
                    self.add_log("Ditolak: Nyalakan Power utama terlebih dahulu!")
                    return
                s["vacuum"] = not s["vacuum"]
                self.add_log("Tahap 4: Kipas Vakum " + ("ON (Memompa ruang hampa)" if s["vacuum"] else "OFF"))

            elif cmd == "TOGGLE_INTERLOCK":
                if s["power"] and s["vacuum"] and s["pressure"] <= 1e-3:
                    s["interlocks"] = not s["interlocks"]
                    self.add_log("Tahap 5: Safety Interlock " + ("LOCKED (Beam Ready)" if s["interlocks"] else "OPEN"))
                elif s["power"] and s["vacuum"]:
                    self.add_log("Interlock menunggu tekanan vakum < 1e-3 mbar!")
                else:
                    self.add_log("Gagal: Power & Vacuum harus ON sebelum mengunci Interlock!")

            elif cmd == "AUTO_INIT":
                s["emergency"] = False
                s["power"] = True
                s["vacuum"] = True
                s["basePressure"] = 5.0e-6
                s["pressure"] = 5.0e-6
                s["interlocks"] = True
                self.add_log("Tahap 5: AUTO-INIT OK — Power, Vakum, dan Interlock SIAP.")

            elif cmd == "START_BEAM":
                if s["power"] and s["vacuum"] and s["interlocks"]:
                    s["emergency"] = False
                    s["beam"] = True
                    s["exposureActive"] = False
                    s["activeLedIdx"] = CFG["led_mapping"]["spiral_start_idx"]
                    self.add_log("Tahap 6: START BEAM! LED Strip Spiral & RF aktif.")
                else:
                    self.add_log("START BEAM ditolak: Pastikan Power, Vacuum, & Interlock aktif!")

            elif cmd == "SHOOT":
                if s["beam"]:
                    s["exposureActive"] = not s["exposureActive"]
                    s["shootLedIdx"] = CFG["led_mapping"]["shoot_start_idx"] if s["exposureActive"] else -1
                    self.add_log("Tahap 7: SHOOT EXPOSURE " + ("AKTIF (Menembak Target)" if s["exposureActive"] else "DIHENTIKAN"))
                else:
                    self.add_log("SHOOT ditolak: Beam belum aktif!")

            elif cmd == "EMERGENCY_STOP":
                s["emergency"] = True
                s["power"] = False
                s["vacuum"] = False
                s["interlocks"] = False
                s["beam"] = False
                s["exposureActive"] = False
                s["buzzerUntil"] = time.time() + 3.0
                self.add_log("DARURAT: EMERGENCY STOP DITEKAN! Semua sistem diputus.")

            elif cmd == "SET_PARAMS":
                # Validasi input HMI: nilai non-angka, NaN/Infinity, atau di luar
                # batas `setpoint_limits` (config_hardware.json) DITOLAK dan setpoint
                # lama dipertahankan, agar fisika & JSON telemetri tetap valid.
                diterima, ditolak = [], []
                for key_in, key_state in (
                    ("magnet_a", "setpoint_magnet_a"),
                    ("rf_mhz", "setpoint_rf_mhz"),
                    ("rf_kv", "setpoint_rf_kv"),
                    ("beam_ua", "setpoint_beam_ua"),
                ):
                    if key_in not in payload:
                        continue
                    nilai = _validasi_setpoint(key_in, payload[key_in])
                    if nilai is None:
                        ditolak.append(f"{key_in}={payload[key_in]!r}")
                    else:
                        s[key_state] = nilai
                        diterima.append(key_in)
                if ditolak:
                    self.add_log(f"SET_PARAMS ditolak (di luar batas/tidak valid): {', '.join(ditolak)}")
                if diterima:
                    self.add_log(f"Tahap 2: Input HMI diperbarui (I_mag={s['setpoint_magnet_a']}A, V_dee={s['setpoint_rf_kv']}kV)")

    def step_physics_and_hardware(self) -> None:
        now = time.time()
        dt = max(0.01, min(1.0, now - self.last_tick))
        self.last_tick = now

        with self.lock:
            s = self.state

            # 1. Fisika Vakum Eksponensial
            if s["power"] and s["vacuum"]:
                s["basePressure"] = max(1.2e-7, s["basePressure"] * math.exp(-dt * 3.2))
            else:
                s["basePressure"] = min(1013.0, s["basePressure"] * 2.5 + 5.0)
            s["pressure"] = (
                s["basePressure"] * (1.0 + random.uniform(-0.08, 0.08))
                if s["basePressure"] < 1e-5
                else s["basePressure"]
            )

            # Cascading Safety Interlock
            if not s["power"] or not s["vacuum"]:
                s["interlocks"] = False
            if not s["interlocks"] and s["beam"]:
                s["beam"] = False
                s["exposureActive"] = False
                self.add_log("BEAM DROP: Interlock terbuka!")

            # 2. Fisika Energi, RF, & Arus Berkas Berdasarkan Input Setpoint HMI
            b_ratio = s["setpoint_magnet_a"] / 1450.0
            rf_ratio = s["setpoint_rf_kv"] / 45.0
            max_mev = 13.0 * min(1.15, b_ratio * rf_ratio)

            if s["beam"]:
                s["rf"] = True
                s["baseRf"] = min(185.7 * rf_ratio, s["baseRf"] + (185.7 / 4.0) * dt)
                s["baseCurrent"] = min(s["setpoint_beam_ua"], s["baseCurrent"] + (s["setpoint_beam_ua"] / 3.0) * dt)
                s["baseEnergy"] = min(max_mev, s["baseEnergy"] + (max_mev / 6.0) * dt)
                if s["exposureActive"]:
                    s["exposureSeconds"] += dt
            else:
                s["rf"] = False
                s["baseRf"] = max(0.0, s["baseRf"] - (185.7 / 3.0) * dt)
                s["baseCurrent"] = max(0.0, s["baseCurrent"] - 4.0 * dt)
                s["baseEnergy"] = max(0.0, s["baseEnergy"] - 5.0 * dt)

            s["magnetCurrent"] = (
                s["setpoint_magnet_a"] + random.uniform(-1.5, 1.5)
                if (s["power"] and s["magnet"])
                else 0.0
            )
            s["magnetPower"] = (s["magnetCurrent"] / 1450.0) * 85.2
            s["frequency"] = s["setpoint_rf_mhz"] + random.uniform(-0.01, 0.01) if s["rf"] else 0.0
            s["rfPower"] = s["baseRf"]
            s["beamCurrent"] = s["baseCurrent"]
            s["beamEnergy"] = s["baseEnergy"]
            s["targetCurrent"] = s["beamCurrent"] * 0.95 if s["exposureActive"] else 0.0

            # 3. Penentuan Tahap (Stage 0..7) & Teks LCD TFT
            if s["emergency"]:
                s["stage"] = 0
                s["mode"] = "EMERGENCY"
                s["lcd_line1"] = "!!! EMERGENCY STOP !!!"
                s["lcd_line2"] = "Seluruh Daya & RF Terputus"
            elif not s["power"]:
                s["stage"] = 0
                s["mode"] = "Standby"
                s["lcd_line1"] = "TAHAP 0: SYSTEM STANDBY"
                s["lcd_line2"] = "Nyalakan Saklar [Power]"
            elif not s["vacuum"]:
                s["stage"] = 1
                s["mode"] = "Power On"
                s["lcd_line1"] = "TAHAP 1-3: INISIASI & HMI"
                s["lcd_line2"] = "Nyalakan [Vacuum] Kipas"
            elif s["pressure"] > 1e-3:
                s["stage"] = 4
                s["mode"] = "Vacuum Pumping"
                s["lcd_line1"] = "TAHAP 4: POMPA VAKUM AKTIF"
                s["lcd_line2"] = f"P: {s['pressure']:.1e} mbar"
            elif not s["interlocks"]:
                s["stage"] = 5
                s["mode"] = "Vac OK - Set Interlock"
                s["lcd_line1"] = "TAHAP 5: VAKUM TERCAPAI"
                s["lcd_line2"] = "Aktifkan [Interlocks]"
            elif not s["beam"]:
                s["stage"] = 5
                s["mode"] = "Beam Ready"
                s["lcd_line1"] = "TAHAP 5: BEAM READY"
                s["lcd_line2"] = "Tekan [START BEAM]"
            elif not s["exposureActive"]:
                s["stage"] = 6
                s["mode"] = "Beam On"
                s["lcd_line1"] = "TAHAP 6: SPIRAL & RF"
                s["lcd_line2"] = f"Energi: {s['beamEnergy']:.1f} MeV"
            else:
                s["stage"] = 7
                s["mode"] = "Exposure Active"
                s["lcd_line1"] = "TAHAP 7: SHOOT EXPOSURE!"
                s["lcd_line2"] = f"Target: {s['targetCurrent']:.1f} uA"

            s["lcd_line3"] = f"Mag:{s['magnetCurrent']:.0f}A | RF:{s['frequency']:.1f}MHz"
            s["lcd_line4"] = f"Vac:{s['pressure']:.1e}mbar | E:{s['beamEnergy']:.1f}MeV"

            # 4. Delegasikan Update ke Modul Divisi 2, 3, dan 4 (Fault-Isolated)
            for mod in self.modules:
                try:
                    mod.update(s, dt, now)
                except Exception as e:
                    print(f"[Peringatan Modul {mod.name}] Error saat update: {e}")

    def cleanup_all(self) -> None:
        for mod in self.modules:
            try:
                mod.cleanup()
            except Exception as e:
                print(f"[Peringatan Modul {mod.name}] Error saat cleanup: {e}")
        if HAS_GPIO:
            try:
                GPIO.cleanup()
            except Exception:
                pass


def main():
    daemon = Decy13CoreDaemon()
    mqtt_cfg = CFG["mqtt"]

    try:
        # paho-mqtt >= 2.0.0
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id="rpi3b_decy13_hardware_daemon")
    except (AttributeError, TypeError):
        # paho-mqtt < 2.0.0
        client = mqtt.Client(client_id="rpi3b_decy13_hardware_daemon")

    configured_host = mqtt_cfg["broker_host"]
    connected_host = configured_host
    port_tcp = mqtt_cfg["broker_port_tcp"]

    # Fast TCP probe (0.4s) agar langsung fallback ke 127.0.0.1 tanpa menunggu timeout 20 detik
    def _is_reachable(h: str, p: int) -> bool:
        try:
            with socket.create_connection((h, p), timeout=0.4):
                return True
        except OSError:
            return False

    if connected_host != "127.0.0.1" and not _is_reachable(connected_host, port_tcp):
        # Di RPi, Mosquitto berjalan lokal: walau belum siap (misal baru boot),
        # tetap arahkan ke localhost dan biarkan auto-reconnect menunggu broker.
        if _is_reachable("127.0.0.1", port_tcp) or HAS_GPIO:
            print(f"[Auto-Fallback] Broker {configured_host}:{port_tcp} tidak aktif -> beralih ke localhost (127.0.0.1:{port_tcp}).")
            connected_host = "127.0.0.1"

    def on_connect(c, userdata, flags, rc, *args):
        rc_val = getattr(rc, "value", rc)
        if rc_val == 0:
            print(f"Terhubung ke MQTT Broker ({connected_host}:{port_tcp}) rc=0")
            c.subscribe(mqtt_cfg["topic_cmd"])
        else:
            print(f"Broker {connected_host}:{port_tcp} menolak koneksi (rc={rc}). Mencoba ulang otomatis...")

    def on_disconnect(c, userdata, rc, *args):
        if getattr(rc, "value", rc) != 0:
            print(f"Koneksi MQTT terputus (rc={rc}). Auto-reconnect aktif, hardware tetap berjalan aman.")

    def on_message(c, userdata, msg):
        try:
            data = json.loads(msg.payload.decode("utf-8"))
            daemon.handle_command(data)
        except Exception as e:
            print("Gagal parsing payload MQTT:", e)

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=10)

    # connect_async + loop_start: koneksi pertama & reconnect ditangani thread paho,
    # sehingga daemon tidak terjebak "Mode Offline" bila Mosquitto baru siap belakangan.
    try:
        print(f"Menghubungkan ke MQTT Broker {connected_host}:{port_tcp} (auto-reconnect aktif)...")
        client.connect_async(connected_host, port_tcp, 60)
        client.loop_start()
    except Exception as e:
        print(f"Mode Offline (Broker MQTT {connected_host}:{port_tcp} belum aktif): {e}")

    # systemd (`systemctl stop decy13`) mengirim SIGTERM: ubah jadi KeyboardInterrupt
    # agar blok `finally` tetap mematikan relay/buzzer/LED dengan aman.
    def _on_sigterm(signum, frame):
        raise KeyboardInterrupt

    try:
        signal.signal(signal.SIGTERM, _on_sigterm)
    except (ValueError, AttributeError, OSError):
        pass

    interval = float(mqtt_cfg["publish_interval_sec"])
    next_tick = time.monotonic()
    print("Core Daemon Hardware DECY-13 berjalan. Tekan Ctrl+C untuk keluar.")
    try:
        while True:
            daemon.step_physics_and_hardware()
            with daemon.lock:
                payload_out = json.dumps(daemon.state)
            try:
                client.publish(mqtt_cfg["topic_state"], payload_out, qos=0)
            except Exception:
                pass
            # Periode tetap (~200 ms) tanpa akumulasi drift, penting untuk debounce E-Stop.
            next_tick += interval
            sisa = next_tick - time.monotonic()
            if sisa > 0:
                time.sleep(sisa)
            else:
                next_tick = time.monotonic()
    except KeyboardInterrupt:
        print("\nMenghentikan Core Daemon DECY-13...")
    finally:
        try:
            client.disconnect()
        except Exception:
            pass
        client.loop_stop()
        daemon.cleanup_all()
        print("Seluruh modul perangkat keras telah dibersihkan dengan aman.")


if __name__ == "__main__":
    main()
