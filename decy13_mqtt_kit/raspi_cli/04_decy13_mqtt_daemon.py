#!/usr/bin/env python3
"""
LANGKAH 4 & 5: DAEMON UTAMA MQTT RASPBERRY PI 3B+ (SUMBER KEBENARAN HARDWARE NYATA)
Program ini menjalankan State Machine 7-Tahap Siklotron DECY-13 secara real-time:
  - Subscribe perintah dari Web HMI pada topic: decy13/hmi/cmd
  - Menggerakkan Kipas Vakum, Buzzer, LCD TFT SPI ILI9341, dan LED Strip WS2812B
  - Mem-publish keadaan nyata (Real Hardware Telemetry) ke topic: decy13/rpi/state
    sehingga animasi di Web HMI 100% mengikuti keadaan fisik yang terjadi di Raspberry Pi 3B+!

Jalankan di Raspberry Pi 3B+:
  sudo python3 04_decy13_mqtt_daemon.py
"""
import json
import math
import random
import threading
import time
import paho.mqtt.client as mqtt

# Import opsional agar skrip juga bisa diuji di laptop/PC dalam mode simulasi CLI
try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
except ImportError:
    HAS_GPIO = False

try:
    from rpi_ws281x import PixelStrip, Color
    HAS_WS281X = True
except ImportError:
    HAS_WS281X = False

try:
    from luma.core.interface.serial import spi
    from luma.core.render import canvas
    from luma.lcd.device import ili9341
    from PIL import ImageFont
    HAS_LCD = True
except ImportError:
    HAS_LCD = False

with open("config_hardware.json", "r") as f:
    CFG = json.load(f)

class Decy13HardwareDaemon:
    def __init__(self):
        self.lock = threading.Lock()
        # Keadaan Nyata Perangkat Keras (Source of Truth)
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
            "peakEnergy": 13.0,
            "exposureSeconds": 0.0,
            "activeLedIdx": -1,
            "shootLedIdx": -1,
            "buzzerActive": False,
            "buzzerUntil": 0.0,
            "logs": ["Sistem Daemon RPi 3B+ siap. Menunggu perintah MQTT."]
        }
        self.last_tick = time.time()
        self.init_hardware()

    def add_log(self, msg: str):
        ts = time.strftime("%H:%M:%S")
        self.state["logs"].insert(0, f"{ts} - {msg}")
        self.state["logs"] = self.state["logs"][:12]
        print(f"[{ts}] {msg}")

    def init_hardware(self):
        pins = CFG["pins_bcm"]
        if HAS_GPIO:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(pins["relay_vacuum_fan"], GPIO.OUT)
            GPIO.setup(pins["buzzer"], GPIO.OUT)
            GPIO.setup(pins["estop_button"], GPIO.IN, pull_up_down=GPIO.PUD_UP)
            self._write_vacuum_pin(False)
            GPIO.output(pins["buzzer"], GPIO.LOW)

        self.strip = None
        if HAS_WS281X:
            led_cfg = CFG["led_mapping"]
            self.strip = PixelStrip(
                led_cfg["total_leds"],
                pins["led_ws2812b"],
                800000, 10, False, led_cfg["brightness"], 0
            )
            self.strip.begin()

        self.lcd = None
        if HAS_LCD:
            try:
                serial_spi = spi(
                    port=pins["lcd_spi_port"],
                    device=pins["lcd_spi_device_ce"],
                    gpio_DC=pins["lcd_dc"],
                    gpio_RST=pins["lcd_rst"],
                    bus_speed_hz=16000000
                )
                self.lcd = ili9341(serial_spi, width=320, height=240, rotate=0)
                self.font = ImageFont.load_default()
            except Exception as e:
                print("Peringatan LCD SPI:", e)

    def _write_vacuum_pin(self, on: bool):
        if not HAS_GPIO:
            return
        pin = CFG["pins_bcm"]["relay_vacuum_fan"]
        active_low = CFG["pins_bcm"]["relay_vacuum_active_low"]
        if active_low:
            GPIO.output(pin, GPIO.LOW if on else GPIO.HIGH)
        else:
            GPIO.output(pin, GPIO.HIGH if on else GPIO.LOW)

    def handle_command(self, payload: dict):
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
                if "magnet_a" in payload:
                    s["setpoint_magnet_a"] = float(payload["magnet_a"])
                if "rf_mhz" in payload:
                    s["setpoint_rf_mhz"] = float(payload["rf_mhz"])
                if "rf_kv" in payload:
                    s["setpoint_rf_kv"] = float(payload["rf_kv"])
                if "beam_ua" in payload:
                    s["setpoint_beam_ua"] = float(payload["beam_ua"])
                self.add_log(f"Tahap 2: Input HMI diperbarui (I_mag={s['setpoint_magnet_a']}A, V_dee={s['setpoint_rf_kv']}kV)")

    def step_physics_and_hardware(self):
        now = time.time()
        dt = max(0.01, min(1.0, now - self.last_tick))
        self.last_tick = now

        with self.lock:
            s = self.state

            # Cek tombol fisik E-Stop jika ada di GPIO 22 (Active-LOW)
            if HAS_GPIO and GPIO.input(CFG["pins_bcm"]["estop_button"]) == GPIO.LOW and not s["emergency"]:
                s["emergency"] = True
                s["power"] = s["vacuum"] = s["interlocks"] = s["beam"] = s["exposureActive"] = False
                s["buzzerUntil"] = now + 3.0
                self.add_log("INTERUPSI FISIK: Tombol E-Stop Hardware Ditekan!")

            # 1. Fisika Vakum Eksponensial
            if s["power"] and s["vacuum"]:
                s["basePressure"] = max(1.2e-7, s["basePressure"] * math.exp(-dt * 3.2))
            else:
                s["basePressure"] = min(1013.0, s["basePressure"] * 2.5 + 5.0)
            s["pressure"] = s["basePressure"] * (1.0 + random.uniform(-0.08, 0.08)) if s["basePressure"] < 1e-5 else s["basePressure"]

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

            s["magnetCurrent"] = s["setpoint_magnet_a"] + random.uniform(-1.5, 1.5) if (s["power"] and s["magnet"]) else 0.0
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

            # 4. Update Output Fisik (Relay Kipas, Buzzer, LED Strip WS2812B)
            self._write_vacuum_pin(s["power"] and s["vacuum"])
            s["buzzerActive"] = (now < s["buzzerUntil"]) or (s["exposureActive"] and int(now * 2) % 2 == 0)
            if HAS_GPIO:
                GPIO.output(CFG["pins_bcm"]["buzzer"], GPIO.HIGH if s["buzzerActive"] else GPIO.LOW)

            # Update Indeks LED Spiral & Shoot
            led_cfg = CFG["led_mapping"]
            if s["beam"]:
                step_inc = max(1, int((s["beamEnergy"] / 13.0) * 3) + 1)
                s["activeLedIdx"] = led_cfg["spiral_start_idx"] + (
                    (s["activeLedIdx"] - led_cfg["spiral_start_idx"] + step_inc)
                    % (led_cfg["spiral_end_idx"] - led_cfg["spiral_start_idx"] + 1)
                )
                if s["exposureActive"]:
                    s["shootLedIdx"] = led_cfg["shoot_start_idx"] + (
                        (s["shootLedIdx"] - led_cfg["shoot_start_idx"] + 2)
                        % (led_cfg["shoot_end_idx"] - led_cfg["shoot_start_idx"] + 1)
                    )
                else:
                    s["shootLedIdx"] = -1
            else:
                s["activeLedIdx"] = 0 if s["power"] else -1
                s["shootLedIdx"] = -1

            if self.strip:
                for i in range(self.strip.numPixels()):
                    self.strip.setPixelColor(i, Color(0, 0, 0))
                if s["emergency"]:
                    for i in range(self.strip.numPixels()):
                        self.strip.setPixelColor(i, Color(180, 0, 0))
                elif s["beam"]:
                    idx = s["activeLedIdx"]
                    self.strip.setPixelColor(idx, Color(0, 220, 255))
                    if s["exposureActive"] and s["shootLedIdx"] >= 0:
                        self.strip.setPixelColor(s["shootLedIdx"], Color(255, 100, 0))
                elif s["power"]:
                    self.strip.setPixelColor(0, Color(0, 0, 120))
                self.strip.show()

def main():
    daemon = Decy13HardwareDaemon()
    mqtt_cfg = CFG["mqtt"]

    try:
        # paho-mqtt >= 2.0.0
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id="rpi3b_decy13_hardware_daemon")
    except (AttributeError, TypeError):
        # paho-mqtt < 2.0.0
        client = mqtt.Client(client_id="rpi3b_decy13_hardware_daemon")

    def on_connect(c, userdata, flags, rc):
        print(f"Terhubung ke MQTT Broker ({mqtt_cfg['broker_host']}:{mqtt_cfg['broker_port_tcp']}) rc={rc}")
        c.subscribe(mqtt_cfg["topic_cmd"])

    def on_message(c, userdata, msg):
        try:
            data = json.loads(msg.payload.decode("utf-8"))
            daemon.handle_command(data)
        except Exception as e:
            print("Gagal parsing payload MQTT:", e)

    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(mqtt_cfg["broker_host"], mqtt_cfg["broker_port_tcp"], 60)
        client.loop_start()
    except Exception as e:
        print(f"Mode Offline (Broker MQTT {mqtt_cfg['broker_host']} belum aktif): {e}")

    print("Daemon Hardware DECY-13 berjalan. Tekan Ctrl+C untuk keluar.")
    try:
        while True:
            daemon.step_physics_and_hardware()
            payload_out = json.dumps(daemon.state)
            try:
                client.publish(mqtt_cfg["topic_state"], payload_out, qos=0)
            except Exception:
                pass
            time.sleep(mqtt_cfg["publish_interval_sec"])
    except KeyboardInterrupt:
        print("Menghentikan daemon...")
    finally:
        client.loop_stop()
        if HAS_GPIO:
            GPIO.cleanup()

if __name__ == "__main__":
    main()
