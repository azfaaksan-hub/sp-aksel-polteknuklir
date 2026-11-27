#!/usr/bin/env python3
"""
MODUL DIVISI 2: SISTEM VAKUM (RELAY KIPAS 12V), BUZZER & SAFETY E-STOP
======================================================================
Penanggung Jawab : Anggota 2 (Divisi Vakum, Buzzer & Safety Interlock)
Branch GitHub    : divisi-2-vacum-safety
File Terkait     : - raspi_cli/modules/mod_vacuum_safety.py (File ini)
                   - raspi_cli/01_test_relay_buzzer.py

Tugas & Tanggung Jawab Modul Ini:
1. Mengendalikan Relay Kipas DC 12V (GPIO 21 / Pin Fisik 40, Active-LOW) sebagai simulasi Pompa Vakum.
2. Mengendalikan Buzzer SFM-27 (GPIO 27 / Pin Fisik 13, membaca `pins_bcm.buzzer` di config_hardware.json):
   - Tahap 1 (Power ON): Bunyi kontinyu selama 5 detik saat power baru menyala.
   - Tahap 7 (Shoot / `exposureActive`): Bunyi indikator 1 detik saat tembakan baru aktif.
   - Darurat (Emergency Stop dari Web HMI maupun tombol fisik): Alarm kontinyu selama 3 detik.
   - Energi Maksimum (`beamEnergy >= max_energy_mev`): Bunyi kontinyu hingga E-Stop atau Power OFF.
3. Membaca tombol fisik Emergency Stop (GPIO 22, Pull-Up) dengan software debounce
   apabila `estop_hardware_enabled` bernilai True pada `config_hardware.json`.
"""

import time
from typing import Dict, Any
from .base_module import HardwareModule

try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
except ImportError:
    HAS_GPIO = False


POWER_ON_BEEP_SEC = 5.0
SHOOT_BEEP_SEC = 1.0
ESTOP_ALARM_SEC = 3.0
DEBOUNCE_COUNT = 2  # 2 x 200 ms = ~400 ms anti-noise


class VacuumSafetyModule(HardwareModule):
    """Driver modular untuk Relay Kipas Vakum, Buzzer Indikator, dan Tombol E-Stop."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        pins = self.cfg.get("pins_bcm", {})
        self.pin_vac = int(pins.get("relay_vacuum_fan", 21))
        self.vac_active_low = bool(pins.get("relay_vacuum_active_low", True))
        self.pin_buzzer = int(pins.get("buzzer", 27))
        self.buzzer_active_low = bool(pins.get("buzzer_active_low", False))
        self.pin_estop = int(pins.get("estop_button", 22))
        self.estop_active_low = bool(pins.get("estop_active_low", True))
        self.estop_enabled = bool(pins.get("estop_hardware_enabled", True))
        self.max_energy = float(
            self.cfg.get("physics_defaults", {}).get("max_energy_mev", 13.0)
        )

        self._estop_count = 0
        self._estop_down = False
        self._prev_power = False
        self._prev_shoot = False
        self._prev_emergency = False
        self._power_until = 0.0
        self._shoot_until = 0.0
        self._alarm_until = 0.0
        self._max_latched = False
        self._last_vac_state = None
        self._last_buz_state = None

    def setup(self) -> bool:
        if not HAS_GPIO:
            self.enabled = False
            return False

        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            vac_off = GPIO.HIGH if self.vac_active_low else GPIO.LOW
            buz_off = GPIO.HIGH if self.buzzer_active_low else GPIO.LOW
            GPIO.setup(self.pin_vac, GPIO.OUT, initial=vac_off)
            GPIO.setup(self.pin_buzzer, GPIO.OUT, initial=buz_off)
            GPIO.setup(self.pin_estop, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            self.enabled = True
            phys_map = {17: "Pin 11", 27: "Pin 13", 22: "Pin 15", 21: "Pin 40"}
            buz_phys = phys_map.get(self.pin_buzzer, "BCM")
            vac_phys = phys_map.get(self.pin_vac, "BCM")
            print(
                f"    [Divisi 2] Relay Vakum=GPIO {self.pin_vac} ({vac_phys}, active_low={self.vac_active_low}) | "
                f"Buzzer=GPIO {self.pin_buzzer} ({buz_phys}, active_low={self.buzzer_active_low}) | "
                f"E-Stop=GPIO {self.pin_estop} (hw_enabled={self.estop_enabled})",
                flush=True,
            )
            return True
        except Exception as e:
            print(f"[VacuumSafetyModule] setup gagal: {e}")
            self.enabled = False
            return False

    def _write_vacuum_pin(self, turn_on: bool) -> None:
        if not self.enabled or turn_on == self._last_vac_state:
            return
        if self.vac_active_low:
            GPIO.output(self.pin_vac, GPIO.LOW if turn_on else GPIO.HIGH)
        else:
            GPIO.output(self.pin_vac, GPIO.HIGH if turn_on else GPIO.LOW)
        self._last_vac_state = turn_on

    def _write_buzzer_pin(self, turn_on: bool) -> None:
        if not self.enabled or turn_on == self._last_buz_state:
            return
        if self.buzzer_active_low:
            GPIO.output(self.pin_buzzer, GPIO.LOW if turn_on else GPIO.HIGH)
        else:
            GPIO.output(self.pin_buzzer, GPIO.HIGH if turn_on else GPIO.LOW)
        self._last_buz_state = turn_on

    def _is_estop_pressed(self) -> bool:
        if not self.enabled or not self.estop_enabled:
            return False
        raw_val = GPIO.input(self.pin_estop)
        if self.estop_active_low:
            return raw_val == GPIO.LOW
        return raw_val == GPIO.HIGH

    def update(self, state: Dict[str, Any], dt: float, now: float) -> None:
        # 1. Cek Tombol Fisik E-Stop dengan Debounce (sekali per tekanan)
        if self._is_estop_pressed():
            self._estop_count = min(self._estop_count + 1, DEBOUNCE_COUNT)
        else:
            self._estop_count = 0
        stable_estop = self._estop_count >= DEBOUNCE_COUNT

        if stable_estop and not self._estop_down:
            self._estop_down = True
            state["emergency"] = True
            state["power"] = False
            state["vacuum"] = False
            state["rf"] = False
            state["interlocks"] = False
            state["beam"] = False
            state["exposureActive"] = False
            state["stage"] = 0
            state["activeLedIdx"] = -1
            state["shootLedIdx"] = -1
            state["ledOffSeq"] = int(state.get("ledOffSeq", 0)) + 1
            state["buzzerUntil"] = now + ESTOP_ALARM_SEC
            self._alarm_until = now + ESTOP_ALARM_SEC
            ts = time.strftime("%H:%M:%S")
            msg = f"{ts} - INTERUPSI FISIK: Tombol E-Stop Hardware (GPIO {self.pin_estop}) Ditekan!"
            state.setdefault("logs", []).insert(0, msg)
            state["logs"] = state["logs"][:12]
            print(f"[{ts}] [VacuumSafetyModule] {msg}")
        elif not stable_estop and self._estop_down:
            self._estop_down = False

        # Baca state terbaru (mendukung tombol Web HMI maupun interupsi fisik)
        power = bool(state.get("power", False))
        vacuum = bool(state.get("vacuum", False))
        emergency = bool(state.get("emergency", False))
        shoot = bool(state.get("exposureActive", False) or state.get("shootTrigger", False))
        try:
            energy = float(state.get("beamEnergy", 0.0) or 0.0)
        except (TypeError, ValueError):
            energy = 0.0

        # 2. E-Stop dari Web HMI (transisi False -> True): alarm kontinyu 3 detik
        if emergency and not self._prev_emergency:
            self._alarm_until = max(self._alarm_until, now + ESTOP_ALARM_SEC)
        self._prev_emergency = emergency

        # 3. Power ON: bunyi 5 detik saat power baru menyala; Power OFF langsung bersihkan timer
        if power and not self._prev_power and not emergency:
            self._power_until = now + POWER_ON_BEEP_SEC
        elif not power:
            self._power_until = 0.0
            self._shoot_until = 0.0
        self._prev_power = power

        # 4. Tembakan (`exposureActive` / SHOOT): bunyi 1 detik saat tembakan baru aktif
        if power and not emergency and shoot and not self._prev_shoot:
            self._shoot_until = now + SHOOT_BEEP_SEC
        self._prev_shoot = shoot

        # 5. Energi maksimum: bunyi terus sampai E-Stop atau Power OFF
        if emergency or not power:
            self._max_latched = False
        elif energy >= self.max_energy:
            self._max_latched = True

        # 6. Kendalikan Relay Kipas Vakum (hanya menyala bila Power ON, Vacuum ON, & tidak E-Stop)
        vac_on = power and vacuum and not emergency
        self._write_vacuum_pin(vac_on)

        # 7. Gabungkan sumber bunyi Buzzer (tetap sinkron dengan `buzzerUntil` dari Core Daemon)
        daemon_until = float(state.get("buzzerUntil", 0.0) or 0.0)
        in_daemon_timer = (now < daemon_until) and (power or emergency)
        buzzer_on = (
            now < self._alarm_until
            or now < self._power_until
            or now < self._shoot_until
            or self._max_latched
            or in_daemon_timer
        )
        state["buzzerActive"] = buzzer_on
        self._write_buzzer_pin(buzzer_on)

    def cleanup(self) -> None:
        if self.enabled:
            self._last_vac_state = None
            self._last_buz_state = None
            self._write_vacuum_pin(False)
            self._write_buzzer_pin(False)
            self.enabled = False
