#!/usr/bin/env python3
"""
MODUL DIVISI 2: SISTEM VAKUM (RELAY KIPAS 12V), BUZZER & SAFETY E-STOP
======================================================================
Penanggung Jawab : Anggota 2 (Divisi Vakum, Buzzer & Safety Interlock)
Branch GitHub    : divisi-2-vakum-safety
File Terkait     : - raspi_cli/modules/mod_vacuum_safety.py (File ini)
                   - raspi_cli/01_test_relay_buzzer.py

Tugas & Tanggung Jawab Modul Ini:
1. Mengendalikan Relay Kipas DC 12V (GPIO 21, Active-LOW) sebagai simulasi Pompa Vakum.
2. Mengendalikan Buzzer SFM-27 (GPIO 17, Active-HIGH) untuk 3 kondisi:
   - Tahap 1 (Power ON): Bunyi kontinyu selama 5 detik (`buzzerUntil`).
   - Tahap 7 (Shoot Exposure): Bunyi beep-beep periodik (indikator radiasi aktif).
   - Darurat (Emergency Stop): Bunyi alarm cepat/kontinyu selama 3 detik.
3. Membaca tombol fisik Emergency Stop (GPIO 22, Pull-Up) dengan software debounce
   agar kebal terhadap noise listrik, serta mendukung konfigurasi `estop_active_low`
   (True = tombol ditekan bernilai LOW, False = tombol NC terputus bernilai HIGH).
"""

import time
from typing import Dict, Any
from .base_module import HardwareModule

try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
except ImportError:
    HAS_GPIO = False


class VacuumSafetyModule(HardwareModule):
    """Driver modular untuk Relay Kipas Vakum, Buzzer Indikator, dan Tombol E-Stop."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        pins = self.cfg.get("pins_bcm", {})
        self.pin_vac = pins.get("relay_vacuum_fan", 21)
        self.vac_active_low = pins.get("relay_vacuum_active_low", True)
        self.pin_buzzer = pins.get("buzzer", 17)
        self.pin_estop = pins.get("estop_button", 22)
        # Default True: GPIO LOW berarti tombol ditekan (NO ke GND).
        # Ubah ke False di config_hardware.json jika menggunakan saklar NC ke GND.
        self.estop_active_low = pins.get("estop_active_low", True)
        self.estop_enabled = pins.get("estop_hardware_enabled", True)

        self._estop_press_count = 0
        self._debounce_threshold = 2  # Butuh 2 siklus berturut-turut (~400ms) agar bebas noise
        self._last_vac_state = None
        self._last_buz_state = None

    def setup(self) -> bool:
        if not HAS_GPIO:
            self.enabled = False
            return False

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.pin_vac, GPIO.OUT)
        GPIO.setup(self.pin_buzzer, GPIO.OUT)
        GPIO.setup(self.pin_estop, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Pastikan kondisi awal aman (Kipas OFF, Buzzer OFF)
        self._write_vacuum_pin(False)
        GPIO.output(self.pin_buzzer, GPIO.LOW)
        self.enabled = True
        return True

    def _write_vacuum_pin(self, turn_on: bool) -> None:
        if not self.enabled:
            return
        if self.vac_active_low:
            GPIO.output(self.pin_vac, GPIO.LOW if turn_on else GPIO.HIGH)
        else:
            GPIO.output(self.pin_vac, GPIO.HIGH if turn_on else GPIO.LOW)

    def _is_estop_pressed(self) -> bool:
        if not self.enabled or not self.estop_enabled:
            return False
        raw_val = GPIO.input(self.pin_estop)
        if self.estop_active_low:
            return raw_val == GPIO.LOW
        return raw_val == GPIO.HIGH

    def update(self, state: Dict[str, Any], dt: float, now: float) -> None:
        # 1. Cek Tombol Fisik E-Stop dengan Debounce
        if self._is_estop_pressed():
            self._estop_press_count += 1
            if self._estop_press_count >= self._debounce_threshold and not state.get("emergency", False):
                state["emergency"] = True
                state["power"] = False
                state["vacuum"] = False
                state["interlocks"] = False
                state["beam"] = False
                state["exposureActive"] = False
                state["buzzerUntil"] = now + 3.0
                ts = time.strftime("%H:%M:%S")
                msg = f"{ts} - INTERUPSI FISIK: Tombol E-Stop Hardware (GPIO {self.pin_estop}) Ditekan!"
                state.setdefault("logs", []).insert(0, msg)
                state["logs"] = state["logs"][:12]
                print(f"[{ts}] [VacuumSafetyModule] {msg}")
        else:
            self._estop_press_count = 0

        # 2. Kendalikan Relay Kipas Vakum
        vac_on = bool(state.get("power", False) and state.get("vacuum", False) and not state.get("emergency", False))
        if vac_on != self._last_vac_state:
            self._write_vacuum_pin(vac_on)
            self._last_vac_state = vac_on

        # 3. Kendalikan Pola Bunyi Buzzer
        # - Kontinyu saat Power ON 5s atau Emergency Stop 3s (`now < buzzerUntil`)
        # - Beep periodik 2 Hz saat Shoot Exposure aktif
        in_timer_beep = now < state.get("buzzerUntil", 0.0)
        in_exposure_beep = bool(state.get("exposureActive", False) and (int(now * 2) % 2 == 0))
        buzzer_on = in_timer_beep or in_exposure_beep
        state["buzzerActive"] = buzzer_on

        if self.enabled and buzzer_on != self._last_buz_state:
            GPIO.output(self.pin_buzzer, GPIO.HIGH if buzzer_on else GPIO.LOW)
            self._last_buz_state = buzzer_on

    def cleanup(self) -> None:
        if self.enabled:
            self._write_vacuum_pin(False)
            GPIO.output(self.pin_buzzer, GPIO.LOW)
            self.enabled = False
