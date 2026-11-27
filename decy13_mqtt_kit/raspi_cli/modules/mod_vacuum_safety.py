#!/usr/bin/env python3
"""
MODUL DIVISI 2: SISTEM VAKUM (RELAY KIPAS 12V), BUZZER & SAFETY E-STOP
Hanya Divisi 2 yang boleh mengedit file ini.

Buzzer (sesuai perintah yang dipakai tim):
- Power ON: bunyi 5 detik.
- Tembakan: bunyi 1 detik.
- E-Stop ditekan: alarm 3 detik, sekali per tekanan.
- Energi maksimum: bunyi terus sampai E-Stop.
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
DEBOUNCE_COUNT = 2          # 2 x 200 ms = sekitar 400 ms
KEY_SHOOT = "shootTrigger"  # BELUM PASTI: cek ke Ketua


class VacuumSafetyModule(HardwareModule):
    """Driver untuk relay kipas vakum, buzzer, dan tombol E-Stop."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        pins = self.cfg.get("pins_bcm", {})
        self.pin_vac = pins.get("relay_vacuum_fan", 21)
        self.vac_active_low = pins.get("relay_vacuum_active_low", True)
        self.pin_buzzer = pins.get("buzzer", 17)
        self.pin_estop = pins.get("estop_button", 22)
        self.estop_active_low = pins.get("estop_active_low", True)
        self.estop_enabled = pins.get("estop_hardware_enabled", True)
        self.max_energy = float(
            self.cfg.get("physics_defaults", {}).get("max_energy_mev", 13.0)
        )

        self._estop_count = 0
        self._estop_down = False
        self._prev_power = None
        self._prev_shoot = None
        self._power_until = 0.0
        self._shoot_until = 0.0
        self._alarm_until = 0.0
        self._max_latched = False
        self._last_vac = None
        self._last_buz = None

    def setup(self) -> bool:
        if not HAS_GPIO:
            self.enabled = False
            return False
        try:
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            vac_off = GPIO.HIGH if self.vac_active_low else GPIO.LOW
            GPIO.setup(self.pin_vac, GPIO.OUT, initial=vac_off)
            GPIO.setup(self.pin_buzzer, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(self.pin_estop, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            self.enabled = True
            return True
        except Exception as e:
            print(f"[VacuumSafetyModule] setup gagal: {e}")
            self.enabled = False
            return False

    def update(self, state: Dict[str, Any], dt: float, now: float) -> None:
        if not self.enabled:
            return

        # 1. E-Stop: debounce, dan hanya diproses sekali per tekanan
        if self._is_estop_pressed():
            self._estop_count = min(self._estop_count + 1, DEBOUNCE_COUNT)
        else:
            self._estop_count = 0
        stable = self._estop_count >= DEBOUNCE_COUNT

        if stable and not self._estop_down:
            self._estop_down = True
            state["emergency"] = True
            state["power"] = False
            state["vacuum"] = False
            state["interlocks"] = False
            state["beam"] = False
            state["exposureActive"] = False
            self._alarm_until = now + ESTOP_ALARM_SEC
            ts = time.strftime("%H:%M:%S")
            msg = f"{ts} - INTERUPSI FISIK: Tombol E-Stop Hardware (GPIO {self.pin_estop}) Ditekan!"
            state.setdefault("logs", []).insert(0, msg)
            state["logs"] = state["logs"][:12]
            print(f"[{ts}] [VacuumSafetyModule] {msg}")
        elif not stable and self._estop_down:
            self._estop_down = False

        # Baca nilai terbaru setelah E-Stop diproses
        power = bool(state.get("power", False))
        vacuum = bool(state.get("vacuum", False))
        emergency = bool(state.get("emergency", False))
        shoot = bool(state.get(KEY_SHOOT, False))
        energy = float(state.get("beamEnergy", 0.0) or 0.0)

        # 2. Power ON: bunyi 5 detik saat power baru menyala
        if power and self._prev_power is False:
            self._power_until = now + POWER_ON_BEEP_SEC
        self._prev_power = power

        # 3. Tembakan: bunyi 1 detik saat tembakan baru terjadi
        if shoot and self._prev_shoot is False:
            self._shoot_until = now + SHOOT_BEEP_SEC
        self._prev_shoot = shoot

        # 4. Energi maksimum: bunyi terus sampai E-Stop
        if emergency:
            self._max_latched = False
        elif energy >= self.max_energy:
            self._max_latched = True

        # 5. Buzzer
        buzzer_on = (
            now < self._alarm_until
            or now < self._power_until
            or now < self._shoot_until
            or self._max_latched
        )
        self._write_buzzer(buzzer_on)
        state["buzzerActive"] = buzzer_on

        # 6. Relay kipas vakum: nyala hanya jika power, vacuum ON, dan tidak ada emergency
        self._write_vacuum_pin(power and vacuum and not emergency)

    def _is_estop_pressed(self) -> bool:
        if not self.estop_enabled:
            return False
        raw = GPIO.input(self.pin_estop)
        if self.estop_active_low:
            return raw == GPIO.LOW
        return raw == GPIO.HIGH

    def _write_vacuum_pin(self, on: bool) -> None:
        if on == self._last_vac:
            return
        if self.vac_active_low:
            GPIO.output(self.pin_vac, GPIO.LOW if on else GPIO.HIGH)
        else:
            GPIO.output(self.pin_vac, GPIO.HIGH if on else GPIO.LOW)
        self._last_vac = on

    def _write_buzzer(self, on: bool) -> None:
        if on == self._last_buz:
            return
        GPIO.output(self.pin_buzzer, GPIO.HIGH if on else GPIO.LOW)
        self._last_buz = on

    def cleanup(self) -> None:
        if not self.enabled:
            return
        # Pastikan relay mati dan buzzer diam sebelum program berhenti
        off_level = GPIO.HIGH if self.vac_active_low else GPIO.LOW
        GPIO.output(self.pin_vac, off_level)
        GPIO.output(self.pin_buzzer, GPIO.LOW)
        self._last_vac = False
        self._last_buz = False
        self.enabled = False