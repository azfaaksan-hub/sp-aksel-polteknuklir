#!/usr/bin/env python3
"""DECY-13 Divisi 3: visualisasi WS2812B, GPIO12 (Pin Fisik 32) PWM0/DMA10.

Core: LedStripModule(config), setup(), update(state, dt, now), cleanup().
Animasi edukatif, bukan model lintasan partikel atau interlock keselamatan.
"""
import importlib
import math
import threading
import time
from .base_module import HardwareModule


def Color(r, g, b):
    r, g, b = (max(0, min(255, int(v))) for v in (r, g, b))
    return (r << 16) | (g << 8) | b


class MemoryStrip:
    """Buffer virtual dengan API yang sama seperti PixelStrip."""
    def __init__(self, count):
        self.pixels = [0] * count
        self._buffer = self.pixels.copy()
        self.frames = 0

    def numPixels(self):
        return len(self.pixels)

    def setPixelColor(self, index, color):
        if not 0 <= index < len(self.pixels):
            raise IndexError(index)
        self._buffer[index] = int(color)

    def show(self):
        # Readers see a complete virtual frame, not a partially drawn frame.
        self.pixels = self._buffer.copy()
        self.frames += 1


def validate_mapping(config):
    m = config['led_mapping']
    total = int(m['total_leds'])
    a, b, c, d = (int(m[k]) for k in ('spiral_start_idx', 'spiral_end_idx',
                                      'shoot_start_idx', 'shoot_end_idx'))
    gaps = frozenset(int(i) for i in m.get('rf_gap_indices', []))
    brightness = int(m.get('brightness', 10))
    pin = int(config['pins_bcm']['led_ws2812b'])
    if not (0 <= a <= b < c <= d < total):
        raise ValueError('Mapping tidak valid: spiral harus mendahului shoot dan tidak overlap')
    if not all(a <= i <= b for i in gaps):
        raise ValueError('RF gap harus berada di zona spiral')
    if not 1 <= brightness <= 255:
        raise ValueError('Brightness harus 1..255')
    if pin not in (12, 18):
        raise ValueError('Divisi 3 menggunakan GPIO12 atau GPIO18 PWM0')
    return total, a, b, c, d, gaps, brightness, pin


def open_strip(count, pin, brightness):
    """Tidak menyembunyikan kegagalan hardware dari Pixel Finder."""
    ws = importlib.import_module('rpi_ws281x')
    # Alokasikan minimal 450 piksel pada hardware fisik agar sisa mata LED di ujung strip ikut padam.
    strip = ws.PixelStrip(max(int(count), 450), pin, 800000, 10, False, brightness, 0)
    strip.begin()
    return strip


def write_frame(strip, frame):
    n = strip.numPixels()
    for i, color in enumerate(frame):
        if i < n:
            strip.setPixelColor(i, color)
    for i in range(len(frame), n):
        strip.setPixelColor(i, 0)
    strip.show()


def _number(value, default):
    try:
        v = float(value)
        return v if math.isfinite(v) else default
    except (TypeError, ValueError, OverflowError):
        return default


class Animation:
    """Mesin frame murni: dapat diuji tanpa thread, GPIO atau waktu nyata."""
    RF_HOLD = 0.12
    TARGET_HOLD = 0.18

    def __init__(self, config):
        (self.total, self.a, self.b, self.c, self.d, self.gaps,
         self.brightness, self.pin) = validate_mapping(config)
        self.n = self.b - self.a + 1
        self.m = self.d - self.c + 1
        self.peak = _number(config.get('physics_defaults', {}).get('max_energy_mev'), 13.)
        if self.peak <= 0:
            self.peak = 13.
        self.reset()

    def reset(self):
        self.spiral_pos = 0.
        self.shoot_pos = 0.
        self.rf_timers = {}
        self.target_time = 0.
        self.last_mode = 'off'

    def mode(self, state):
        if state.get('emergency') or not state.get('power') or state.get('stage') == 0:
            return 'off'
        if state.get('beam'):
            return 'shoot' if state.get('exposureActive') else 'spiral'
        stage = int(_number(state.get('stage'), 0))
        return {4: 'vacuum', 5: 'ready'}.get(stage, 'standby')

    @staticmethod
    def comet(frame, head, start, color, tail, end=None):
        # Spiral boleh wrap; ekstraksi linear tanpa wrap.
        count = min(tail, end-start+1) if end is not None else min(tail, head-start+1)
        for k in range(count):
            f = ((tail - k) / tail) ** 1.5
            idx = start + (head-start-k) % (end-start+1) if end is not None else head-k
            frame[idx] = Color(*(v * f for v in color))

    def speed(self, state):
        peak = _number(state.get('peakEnergy'), self.peak)
        if peak <= 0:
            peak = self.peak
        ratio = max(0., min(1., _number(state.get('beamEnergy'), 0.) / peak))
        return self.n * (0.20 + 0.55 * ratio)

    def step(self, state, dt):
        dt = max(0., min(0.20, _number(dt, 0.)))
        frame = [0] * self.total
        active = shoot = -1
        mode = self.mode(state)
        prior = self.last_mode
        entering = mode != prior
        if entering:
            if mode in ('spiral', 'shoot') and prior in ('spiral', 'shoot'):
                # Exposure changes must not reset the circulating spiral.
                self.shoot_pos = self.target_time = 0.
            else:
                self.reset()
            self.last_mode = mode
            dt = 0.
        if mode == 'off':
            return frame, active, shoot
        if mode in ('standby', 'vacuum', 'ready'):
            active = self.a
            count = max(1, self.n // 4) if mode == 'vacuum' else min(16, self.n)
            color = {'standby': (0, 95, 225), 'vacuum': (120, 20, 220),
                     'ready': (0, 200, 255)}[mode]
            for i in range(self.a, self.a + count):
                frame[i] = Color(*color)
            if mode == 'ready':
                for gap in self.gaps:
                    for i in range(max(self.a, gap-2), min(self.b, gap+2)+1):
                        frame[i] = Color(220, 180, 30)
            return frame, active, shoot

        # Both phases retain two circulating cyan particle packets.
        old = self.spiral_pos
        delta = self.speed(state) * dt
        self.spiral_pos = (old + delta) % self.n
        offsets = [0]
        tail = max(7, self.n // 16)
        if self.n >= tail * 2:
            offsets.append(self.n // 2)
        self.rf_timers = {g: t-dt for g, t in self.rf_timers.items() if t > dt}
        for offset in offsets:
            start = (old + offset) % self.n
            head = self.a + int((self.spiral_pos + offset) % self.n)
            self.comet(frame, head, self.a, (0, 190, 255), tail, self.b)
            # Crossings include wrap and a head which starts on the gap.
            for gap in self.gaps:
                distance = (gap - self.a - start) % self.n
                if distance <= delta:
                    self.rf_timers[gap] = self.RF_HOLD
        active = self.a + int(self.spiral_pos)
        for gap in self.rf_timers:
            for i in range(max(self.a, gap-2), min(self.b, gap+2)+1):
                frame[i] = Color(255, 220, 55)

        # Continuous exposure: repeat beam packets until Core disables SHOOT.
        if mode == 'shoot':
            end = self.m - 1
            if self.shoot_pos >= end and self.target_time >= self.TARGET_HOLD:
                self.shoot_pos = self.target_time = 0.
                dt = 0.
            if self.shoot_pos < end:
                self.shoot_pos = min(float(end), self.shoot_pos + max(32., self.m * 1.4) * dt)
            else:
                self.target_time += dt
            shoot = self.c + int(self.shoot_pos)
            if self.shoot_pos >= end:
                for i in range(max(self.c, self.d - 7), self.d + 1):
                    frame[i] = Color(170, 255, 65)
            else:
                self.comet(frame, shoot, self.c, (255, 110, 0), max(5, self.m // 3))
        return frame, active, shoot


class LedStripModule(HardwareModule):
    FPS = 40

    def __init__(self, config):
        super().__init__(config)
        self.anim = Animation(config)
        self.total_leds = self.anim.total
        self.spiral_start, self.spiral_end = self.anim.a, self.anim.b
        self.shoot_start, self.shoot_end = self.anim.c, self.anim.d
        self.rf_gaps = self.anim.gaps
        self.pin_led, self.brightness = self.anim.pin, self.anim.brightness
        self.strip = MemoryStrip(self.total_leds)
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self._state = None
        self._snapshot = {}
        self._indices = (-1, -1)
        self.error = None

    def _publish_indices(self, indices):
        self._indices = indices

    def _clear(self):
        self._publish_indices((-1, -1))
        write_frame(self.strip, [0] * self.total_leds)

    def setup(self):
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return self.enabled
            self._stop.clear()
            self.anim.reset()
            self._snapshot = {}
            self._state = None
            self.error = None
            self.enabled = False
            self.strip = MemoryStrip(self.total_leds)
            if not self.cfg.get('_div3_force_virtual', False):
                try:
                    self.strip = open_strip(self.total_leds, self.pin_led, self.brightness)
                    self.enabled = True
                except (ImportError, RuntimeError, OSError, ValueError) as exc:
                    print('[DIVISI 3] Hardware tidak aktif; fallback virtual:', exc, flush=True)
            try:
                self._clear()
            except Exception:
                self.enabled = False
                raise
            self._thread = threading.Thread(target=self._worker, name='DECY13-LED-DIV3', daemon=True)
            self._thread.start()
            return self.enabled

    def update(self, state, dt, now):
        # Core hanya mengirim snapshot dan membaca indeks.
        # Tidak ada operasi GPIO, PWM, DMA atau strip.show().
        with self._lock:
            self._snapshot = {
                k: state.get(k)
                for k in (
                    "power", "beam", "exposureActive",
                    "emergency", "stage", "beamEnergy",
                    "peakEnergy"
                )
            }

            active, shoot = self._indices

            if (
                self._stop.is_set()
                or self.error is not None
                or self._thread is None
                or not state.get("power")
                or state.get("emergency")
            ):
                active, shoot = -1, -1

            if not state.get("exposureActive"):
                shoot = -1

            state.update(
                activeLedIdx=active,
                shootLedIdx=shoot
            )

    def _draw(self, snapshot, dt):
        frame, active, shoot = self.anim.step(snapshot, dt)
        write_frame(self.strip, frame)
        return active, shoot

    def _worker(self):
        last = time.monotonic()
        off_flushes = 0

        try:
            while not self._stop.is_set():
                start = time.monotonic()

                # Lock hanya untuk menyalin snapshot.
                with self._lock:
                    snapshot = dict(self._snapshot)

                # Seluruh operasi hardware berada di luar lock.
                mode = self.anim.mode(snapshot)

                if mode == "off":
                    self.anim.reset()
                    if off_flushes < 2:
                        indices = self._draw(snapshot, 0.0)
                        off_flushes += 1
                    else:
                        # Berhenti menembak strip.show() 40 FPS saat OFF agar jalur PWM0
                        # diam tenang di 0V (mencegah glitch pulsa 3.3V->5V menyalakan LED).
                        indices = (-1, -1)
                else:
                    off_flushes = 0
                    dt = (
                        0.0 if mode != self.anim.last_mode
                        else start - last
                    )
                    indices = self._draw(snapshot, dt)

                # Publikasi hasil tanpa mengakses state Core.
                with self._lock:
                    keys = (
                        "power", "beam", "exposureActive",
                        "emergency", "stage"
                    )

                    if all(
                        snapshot.get(k) == self._snapshot.get(k)
                        for k in keys
                    ):
                        self._publish_indices(indices)

                last = start

                self._stop.wait(
                    max(
                        0.0,
                        1 / self.FPS -
                        (time.monotonic() - start)
                    )
                )

        except Exception as exc:
            with self._lock:
                self.error = str(exc)
                self.enabled = False
                self._publish_indices((-1, -1))

            self._stop.set()
            print("[DIVISI 3] Render gagal:", exc, flush=True)

        finally:
            # Hanya worker yang memadamkan LED saat shutdown.
            try:
                write_frame(
                    self.strip,
                    [0] * self.total_leds
                )
            except Exception as exc:
                with self._lock:
                    self.error = str(exc)

                print(
                    "[DIVISI 3] Gagal blank LED:",
                    exc,
                    flush=True
                )

            finally:
                with self._lock:
                    self._publish_indices((-1, -1))
                    self.enabled = False

    def cleanup(self):
        self._stop.set()

        thread = self._thread

        if thread is not None:
            thread.join(timeout=2.0)

            if thread.is_alive():
                raise RuntimeError(
                    "LED worker belum berhenti. "
                    "Matikan PSU LED secara manual."
                )

        with self._lock:
            error = self.error
            self.enabled = False
            self._thread = None
            self._state = None
            self._snapshot = {}
            self._indices = (-1, -1)

        if error is not None:
            raise RuntimeError(
                "LED worker melaporkan error: " + error
            )
