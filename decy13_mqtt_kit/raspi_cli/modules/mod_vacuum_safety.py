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
2. Mengendalikan Buzzer SFM-27 (GPIO 26 / Pin Fisik 37, membaca `pins_bcm.buzzer` di config_hardware.json):
   - Tahap 1 (Power ON): Bunyi kontinyu selama 5 detik saat daya utama baru dihidupkan.
   - Tahap 4 (Pompa Vakum ON): Bunyi kontinyu selama 1 detik saat pompa vakum baru dihidupkan.
   - Tahap 6 (Start Beam ON): Bunyi kontinyu selama 3 detik saat berkas spiral baru dihidupkan.
   - Darurat (Emergency Stop dari Web HMI maupun tombol fisik): Alarm kontinyu selama 3 detik.
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
VACUUM_ON_BEEP_SEC = 1.0
BEAM_ON_BEEP_SEC = 3.0
ESTOP_ALARM_SEC = 3.0
DEBOUNCE_COUNT = 2  # 2 x 200 ms = ~400 ms anti-noise


class VacuumSafetyModule(HardwareModule):
    """Driver modular untuk Relay Kipas Vakum, Buzzer Indikator, dan Tombol E-Stop."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        pins = self.cfg.get("pins_bcm", {})
        self.pin_vac = int(pins.get("relay_vacuum_fan", 21))
        self.vac_active_low = bool(pins.get("relay_vacuum_active_low", True))
        self.pin_buzzer = int(pins.get("buzzer", 26))
        self.buzzer_active_low = bool(pins.get("buzzer_active_low", False))
        self.buzzer_passive_pwm = bool(pins.get("buzzer_passive_pwm", False))
        try:
            self.buzzer_pwm_freq = max(100.0, min(10000.0, float(pins.get("buzzer_pwm_freq_hz", 2500.0))))
        except (TypeError, ValueError):
            self.buzzer_pwm_freq = 2500.0
        self.pin_estop = int(pins.get("estop_button", 22))
        self.estop_active_low = bool(pins.get("estop_active_low", True))
        self.estop_enabled = bool(pins.get("estop_hardware_enabled", True))
        self.max_energy = float(
            self.cfg.get("physics_defaults", {}).get("max_energy_mev", 13.0)
        )

        self._estop_count = 0
        self._estop_down = False
        self._prev_power = False
        self._prev_vacuum = False
        self._prev_beam = False
        self._prev_emergency = False
        self._prev_off_seq = None
        self._last_now = None
        self._power_rem = 0.0
        self._vacuum_rem = 0.0
        self._beam_rem = 0.0
        self._alarm_rem = 0.0
        self._last_vac_state = None
        self._last_buz_state = None
        self._buz_pwm = None

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
            if self.buzzer_passive_pwm:
                self._buz_pwm = GPIO.PWM(self.pin_buzzer, self.buzzer_pwm_freq)
            self.enabled = True
            phys_map = {16: "Pin 36", 17: "Pin 11", 20: "Pin 38", 21: "Pin 40", 22: "Pin 15", 23: "Pin 16", 26: "Pin 37", 27: "Pin 13"}
            self._buz_phys = phys_map.get(self.pin_buzzer, "BCM")
            vac_phys = phys_map.get(self.pin_vac, "BCM")
            buz_mode = f"PWM {int(self.buzzer_pwm_freq)}Hz" if self.buzzer_passive_pwm else f"DC active_low={self.buzzer_active_low}"
            print(
                f"    [Divisi 2] Relay Vakum=GPIO {self.pin_vac} ({vac_phys}, active_low={self.vac_active_low}) | "
                f"Buzzer=GPIO {self.pin_buzzer} ({self._buz_phys}, {buz_mode}) | "
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

    def _write_buzzer_pin(self, turn_on: bool, reason: str = "") -> None:
        if not self.enabled or turn_on == self._last_buz_state:
            return
        if self.buzzer_passive_pwm and self._buz_pwm is not None:
            if turn_on:
                self._buz_pwm.start(50.0)
            else:
                self._buz_pwm.stop()
                GPIO.output(self.pin_buzzer, GPIO.HIGH if self.buzzer_active_low else GPIO.LOW)
        else:
            if self.buzzer_active_low:
                GPIO.output(self.pin_buzzer, GPIO.LOW if turn_on else GPIO.HIGH)
            else:
                GPIO.output(self.pin_buzzer, GPIO.HIGH if turn_on else GPIO.LOW)
        prev = self._last_buz_state
        self._last_buz_state = turn_on
        if prev is not None or turn_on:
            ts = time.strftime("%H:%M:%S")
            buz_phys = getattr(self, "_buz_phys", "BCM")
            tag = f" ({reason})" if reason else ""
            print(
                f"[{ts}] [Divisi 2 Buzzer] GPIO {self.pin_buzzer} ({buz_phys}) -> "
                f"{'ON' if turn_on else 'OFF'}{tag}",
                flush=True,
            )

    def _is_estop_pressed(self) -> bool:
        if not self.enabled or not self.estop_enabled:
            return False
        raw_val = GPIO.input(self.pin_estop)
        if self.estop_active_low:
            return raw_val == GPIO.LOW
        return raw_val == GPIO.HIGH

    def update(self, state: Dict[str, Any], dt: float, now: float) -> None:
        # Hitung selang waktu kebal loncatan jam NTP (RPi 3B+ tidak memiliki RTC baterai):
        # gunakan selisih `now` bila wajar (<=10 dtk), dan fallback ke `dt` bila jam meloncat ekstrem.
        try:
            safe_dt = max(0.0, min(1.0, float(dt)))
        except (TypeError, ValueError):
            safe_dt = 0.0
        if self._last_now is None:
            step_dt = safe_dt
        else:
            raw_delta = now - self._last_now
            step_dt = raw_delta if (0.0 <= raw_delta <= 10.0) else safe_dt
        self._last_now = now

        # Kurangi timer sisa secara monotonik
        self._alarm_rem = max(0.0, self._alarm_rem - step_dt)
        self._power_rem = max(0.0, self._power_rem - step_dt)
        self._vacuum_rem = max(0.0, self._vacuum_rem - step_dt)
        self._beam_rem = max(0.0, self._beam_rem - step_dt)

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
            self._alarm_rem = max(self._alarm_rem, ESTOP_ALARM_SEC)
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
        beam = bool(state.get("beam", False))
        emergency = bool(state.get("emergency", False))
        off_seq = state.get("ledOffSeq")

        # 2. Hentikan Darurat / E-Stop (transisi False -> True atau ditekan ulang): bunyi kontinyu 3 detik
        retriggered_estop = (
            emergency
            and off_seq is not None
            and self._prev_off_seq is not None
            and off_seq != self._prev_off_seq
        )
        if (emergency and not self._prev_emergency) or retriggered_estop:
            self._alarm_rem = max(self._alarm_rem, ESTOP_ALARM_SEC)
        self._prev_emergency = emergency
        self._prev_off_seq = off_seq

        # 3. Daya Utama ON: bunyi kontinyu 5 detik saat power baru menyala; Power OFF langsung bersihkan semua timer
        if power and not self._prev_power and not emergency:
            self._power_rem = POWER_ON_BEEP_SEC
            self._alarm_rem = 0.0
        elif not power:
            self._power_rem = 0.0
            self._vacuum_rem = 0.0
            self._beam_rem = 0.0
            if not emergency:
                self._alarm_rem = 0.0
        self._prev_power = power

        # 4. Pompa Vakum ON: bunyi kontinyu 1 detik saat pompa vakum baru dihidupkan
        if power and not emergency and vacuum and not self._prev_vacuum:
            self._vacuum_rem = VACUUM_ON_BEEP_SEC
        self._prev_vacuum = vacuum

        # 5. Start Beam ON: bunyi kontinyu 3 detik saat berkas spiral baru dihidupkan
        if power and not emergency and beam and not self._prev_beam:
            self._beam_rem = BEAM_ON_BEEP_SEC
        self._prev_beam = beam

        # 6. Kendalikan Relay Kipas Vakum (hanya menyala bila Power ON, Vacuum ON, & tidak E-Stop)
        vac_on = power and vacuum and not emergency
        self._write_vacuum_pin(vac_on)

        # 7. Gabungkan sumber bunyi Buzzer kontinyu (kebal loncatan NTP & sinkron `buzzerUntil` daemon)
        daemon_until = float(state.get("buzzerUntil", 0.0) or 0.0)
        daemon_rem = daemon_until - now
        in_daemon_timer = (0.0 < daemon_rem <= 10.0) and (power or emergency)
        reasons = []
        if self._alarm_rem > 0.0:
            reasons.append("estop")
        if self._power_rem > 0.0:
            reasons.append("power_on")
        if self._vacuum_rem > 0.0:
            reasons.append("vacuum_on")
        if self._beam_rem > 0.0:
            reasons.append("beam_on")
        if in_daemon_timer and not reasons:
            reasons.append("daemon_timer")
        buzzer_on = bool(reasons)
        state["buzzerActive"] = buzzer_on
        self._write_buzzer_pin(buzzer_on, "+".join(reasons))

    def cleanup(self) -> None:
        if self.enabled:
            if self._buz_pwm is not None:
                try:
                    self._buz_pwm.stop()
                except Exception:
                    pass
                self._buz_pwm = None
            self._last_vac_state = None
            self._last_buz_state = None
            self._write_vacuum_pin(False)
            self._write_buzzer_pin(False, "cleanup")
            self.enabled = False
