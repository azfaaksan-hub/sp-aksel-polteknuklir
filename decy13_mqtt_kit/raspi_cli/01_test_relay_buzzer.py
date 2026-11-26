"""
Divisi 2 - Sistem Vakum, Buzzer & Safety E-Stop
Hanya Divisi 2 yang boleh mengedit file ini.
"""

try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
except ImportError:
    GPIO = None
    HAS_GPIO = False

# GANTI baris ini dengan baris import HardwareModule yang sama dengan file lamamu
================================================================================
                      


# ---------- Durasi bunyi (sesuai perintah Ketua) ----------
POWER_ON_BEEP_SEC = 5.0   # Power ON: bunyi 5 detik
SHOOT_BEEP_SEC = 1.0      # tembakan: bunyi 1 detik
ESTOP_ALARM_SEC = 3.0     # E-Stop ditekan: alarm 3 detik, sekali per tekan
DEBOUNCE_COUNT = 2        # 2 x 200 ms = sekitar 400 ms

# ---------- Nama key di state (CEK ke Ketua) ----------
KEY_POWER = "power"
KEY_VACUUM = "vacuum"
KEY_EMERGENCY = "emergency"
KEY_BEAM_ENERGY = "beamEnergy"
KEY_SHOOT = "shootTrigger"   # BELUM PASTI. Kalau key ini tidak ada, beep tembakan tidak bunyi (aman)


class VacuumSafetyModule(HardwareModule):
    def __init__(self, config):
        super().__init__(config)
        pins = self.cfg.get("pins_bcm", {})
        self.pin_vac = pins.get("relay_vacuum_fan", 21)
        self.vac_active_low = pins.get("relay_vacuum_active_low", True)
        self.pin_buzzer = pins.get("buzzer", 17)
        self.pin_estop = pins.get("estop_button", 22)
        self.estop_active_low = pins.get("estop_active_low", True)
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

    def update(self, state, dt, now):
        if not self.enabled:
            return

        power = bool(state.get(KEY_POWER, False))
        vacuum = bool(state.get(KEY_VACUUM, False))
        shoot = bool(state.get(KEY_SHOOT, False))
        energy = float(state.get(KEY_BEAM_ENERGY, 0.0) or 0.0)

        # 1. E-Stop: debounce, dan alarm hanya sekali per tekanan
        if self._read_estop_pressed():
            self._estop_count = min(self._estop_count + 1, DEBOUNCE_COUNT)
        else:
            self._estop_count = 0
        stable = self._estop_count >= DEBOUNCE_COUNT

        if stable and not self._estop_down:
            self._estop_down = True
            state[KEY_EMERGENCY] = True
            self._alarm_until = now + ESTOP_ALARM_SEC
            print("[VacuumSafetyModule] E-Stop ditekan")
        elif not stable and self._estop_down:
            self._estop_down = False

        emergency = bool(state.get(KEY_EMERGENCY, False))

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

        # 5. Gabungkan semua sumber bunyi
        buzzer_on = (
            now < self._alarm_until
            or now < self._power_until
            or now < self._shoot_until
            or self._max_latched
        )
        self._write_buzzer(buzzer_on)
        state["buzzerActive"] = buzzer_on

        # 6. Vakum: nyala hanya kalau power dan vacuum ON dan tidak ada emergency
        self._write_vacuum(power and vacuum and not emergency)

    def _read_estop_pressed(self) -> bool:
        level = GPIO.input(self.pin_estop)
        if self.estop_active_low:
            return level == GPIO.LOW
        return level == GPIO.HIGH

    def _write_vacuum(self, on: bool):
        if on == self._last_vac:
            return
        if self.vac_active_low:
            level = GPIO.LOW if on else GPIO.HIGH
        else:
            level = GPIO.HIGH if on else GPIO.LOW
        GPIO.output(self.pin_vac, level)
        self._last_vac = on

    def _write_buzzer(self, on: bool):
        if on == self._last_buz:
            return
        GPIO.output(self.pin_buzzer, GPIO.HIGH if on else GPIO.LOW)
        self._last_buz = on

    def cleanup(self):
        if not self.enabled:
            return
        # Pastikan relay mati dan buzzer diam sebelum program berhenti
        vac_off = GPIO.HIGH if self.vac_active_low else GPIO.LOW
        GPIO.output(self.pin_vac, vac_off)
        GPIO.output(self.pin_buzzer, GPIO.LOW)
        self._last_vac = False
        self._last_buz = False
        self.enabled = False