
#!/usr/bin/env python3
"""
DECY-13 | DIVISI 3
MODUL LED WS2812B - RASPBERRY PI 3B+

Integrasi:
    LedStripModule(config)
    setup()
    update(state, dt, now)
    cleanup()

GPIO18 / PWM0 / DMA, bukan SPI0.

Jumlah LED, spiral, RF gap dan shoot
dibaca dari config_hardware.json.

Windows: mode MemoryStrip (virtual).
Raspberry Pi: rpi_ws281x.
"""

import importlib
import math
import threading
import time

from .base_module import HardwareModule


def Color(r, g, b):
    """Warna RGB 24-bit, kompatibel rpi_ws281x."""
    r = max(0, min(255, int(r)))
    g = max(0, min(255, int(g)))
    b = max(0, min(255, int(b)))
    return (r << 16) | (g << 8) | b


class MemoryStrip:
    """Driver virtual tanpa GPIO."""

    def __init__(self, count):
        self.pixels = [0] * count
        self.frames = 0

    def numPixels(self):
        return len(self.pixels)

    def setPixelColor(self, index, color):
        if 0 <= index < len(self.pixels):
            self.pixels[index] = int(color)

    def show(self):
        self.frames += 1


class LedStripModule(HardwareModule):
    """Modul LED resmi Divisi 3."""

    FPS = 40

    def __init__(self, config):
        super().__init__(config)

        led = self.cfg["led_mapping"]
        pins = self.cfg["pins_bcm"]

        # Konfigurasi berasal dari JSON resmi.
        self.total_leds = int(led["total_leds"])
        self.pin_led = int(pins["led_ws2812b"])
        self.brightness = int(
            led.get("brightness", 110)
        )

        self.spiral_start = int(
            led["spiral_start_idx"]
        )
        self.spiral_end = int(
            led["spiral_end_idx"]
        )
        self.shoot_start = int(
            led["shoot_start_idx"]
        )
        self.shoot_end = int(
            led["shoot_end_idx"]
        )

        self.rf_gaps = set(
            map(
                int,
                led.get("rf_gap_indices", [])
            )
        )

        self._validate_mapping()

        self.strip = MemoryStrip(self.total_leds)
        self.enabled = False

        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread = None

        self._state = {
            "power": False,
            "beam": False,
            "exposure": False,
            "emergency": False,
            "stage": 0,
            "energy_ratio": 0.0
        }

        self._spiral_position = float(
            self.spiral_start
        )
        self._shoot_position = float(
            self.shoot_start
        )

        self._last_beam = False
        self._last_exposure = False

    # ========================================
    # CONFIG VALIDATION
    # ========================================

    def _validate_mapping(self):

        if self.total_leds <= 0:
            raise ValueError(
                "total_leds harus positif"
            )

        if not 0 <= self.brightness <= 255:
            raise ValueError(
                "brightness harus 0..255"
            )

        if not (
            0 <= self.spiral_start
            <= self.spiral_end
            < self.total_leds
        ):
            raise ValueError(
                "Rentang spiral tidak valid"
            )

        if not (
            0 <= self.shoot_start
            <= self.shoot_end
            < self.total_leds
        ):
            raise ValueError(
                "Rentang shoot tidak valid"
            )

        if not (
            self.spiral_end < self.shoot_start
            or self.shoot_end < self.spiral_start
        ):
            raise ValueError(
                "Spiral dan shoot bertumpang tindih"
            )

        for index in self.rf_gaps:
            if not (
                self.spiral_start
                <= index
                <= self.spiral_end
            ):
                raise ValueError(
                    "RF gap di luar spiral"
                )

    # ========================================
    # SETUP - CORE CONTRACT
    # ========================================

    def setup(self):
        """
        True: hardware WS2812B aktif.
        False: mode virtual Windows/fallback.
        """

        if (
            self._thread is not None
            and self._thread.is_alive()
        ):
            return self.enabled

        self._stop_event.clear()
        self.enabled = False
        self.strip = MemoryStrip(
            self.total_leds
        )

        # Flag khusus pengujian, hanya digunakan
        # dalam salinan config di memori.
        force_virtual = self.cfg.get(
            "_div3_force_virtual", False
        )

        if not force_virtual:
            try:
                ws = importlib.import_module(
                    "rpi_ws281x"
                )

                strip = ws.PixelStrip(
                    self.total_leds,
                    self.pin_led,
                    800000,
                    10,
                    False,
                    self.brightness,
                    0
                )

                strip.begin()
                self.strip = strip
                self.enabled = True

            except (
                ImportError,
                RuntimeError,
                OSError,
                ValueError
            ) as exc:
                print(
                    "[DIVISI 3] Fallback virtual:",
                    exc
                )

        self._clear()

        self._thread = threading.Thread(
            target=self._animation_loop,
            daemon=True,
            name="DECY13-LED-DIV3"
        )
        self._thread.start()

        return self.enabled

    # ========================================
    # UPDATE - CORE CONTRACT
    # ========================================

    def update(self, state, dt, now):
        """
        Dipanggil oleh Core Daemon.

        Hanya menulis:
        - state["activeLedIdx"]
        - state["shootLedIdx"]

        Tidak mengubah state divisi lain.
        """

        power = bool(
            state.get("power", False)
        )
        emergency = bool(
            state.get("emergency", False)
        )

        beam = (
            power
            and not emergency
            and bool(state.get("beam", False))
        )

        exposure = (
            beam
            and bool(
                state.get(
                    "exposureActive", False
                )
            )
        )

        try:
            stage = int(
                state.get("stage", 0)
            )
        except (ValueError, TypeError):
            stage = 0

        try:
            energy = float(
                state.get("beamEnergy", 0.0)
            )
            peak = float(
                state.get("peakEnergy", 13.0)
            )

            if not math.isfinite(energy):
                energy = 0.0

            if (
                not math.isfinite(peak)
                or peak <= 0
            ):
                peak = 13.0

            ratio = max(
                0.0,
                min(1.0, energy / peak)
            )

        except (ValueError, TypeError):
            ratio = 0.0

        with self._lock:

            if not beam:
                self._spiral_position = float(
                    self.spiral_start
                )

            if not exposure:
                self._shoot_position = float(
                    self.shoot_start
                )

            self._state = {
                "power": power,
                "beam": beam,
                "exposure": exposure,
                "emergency": emergency,
                "stage": stage,
                "energy_ratio": ratio
            }

            # HMI menerima indeks berdasarkan
            # posisi animasi terbaru.
            if emergency or not power:
                active_idx = -1
                shoot_idx = -1

            elif not beam:
                active_idx = self.spiral_start
                shoot_idx = -1

            else:
                active_idx = int(
                    self._spiral_position
                )

                shoot_idx = (
                    int(self._shoot_position)
                    if exposure
                    else -1
                )

            state["activeLedIdx"] = active_idx
            state["shootLedIdx"] = shoot_idx

    # ========================================
    # PIXEL UTILITIES
    # ========================================

    def _clear(self):
        for i in range(
            self.strip.numPixels()
        ):
            self.strip.setPixelColor(i, 0)

        self.strip.show()

    def _set_pixel(self, index, color):
        if 0 <= index < self.total_leds:
            self.strip.setPixelColor(
                index, color
            )

    def _comet(
        self,
        head,
        start,
        end,
        color,
        tail=7
    ):
        """Komet dengan ekor memudar."""

        if not start <= head <= end:
            return

        length = end - start + 1
        tail = min(tail, length)

        r, g, b = color

        for step in range(tail):
            index = start + (
                head - start - step
            ) % length

            fade = (
                (tail - step) / tail
            ) ** 1.5

            self._set_pixel(
                index,
                Color(
                    r * fade,
                    g * fade,
                    b * fade
                )
            )

    # ========================================
    # ANIMATION WORKER
    # ========================================

    def _animation_loop(self):

        last_time = time.monotonic()

        while not self._stop_event.is_set():

            current = time.monotonic()
            dt = min(
                0.1,
                max(0.0, current - last_time)
            )
            last_time = current

            with self._lock:
                s = dict(self._state)

                power = s["power"]
                beam = s["beam"]
                exposure = s["exposure"]
                emergency = s["emergency"]
                ratio = s["energy_ratio"]

                if emergency or not power:
                    self._spiral_position = float(
                        self.spiral_start
                    )
                    self._shoot_position = float(
                        self.shoot_start
                    )

                elif beam:

                    if not self._last_beam:
                        self._spiral_position = float(
                            self.spiral_start
                        )

                    # Visual particle speed
                    # increases with beam energy.
                    speed = (
                        12.0 + 45.0 * ratio
                    )

                    spiral_length = (
                        self.spiral_end
                        - self.spiral_start + 1
                    )

                    self._spiral_position = (
                        self.spiral_start
                        + (
                            self._spiral_position
                            - self.spiral_start
                            + speed * dt
                        ) % spiral_length
                    )

                    if exposure:

                        if not self._last_exposure:
                            self._shoot_position = float(
                                self.shoot_start
                            )

                        shoot_length = (
                            self.shoot_end
                            - self.shoot_start + 1
                        )

                        self._shoot_position = (
                            self.shoot_start
                            + (
                                self._shoot_position
                                - self.shoot_start
                                + 32.0 * dt
                            ) % shoot_length
                        )

                    else:
                        self._shoot_position = float(
                            self.shoot_start
                        )

                self._last_beam = (
                    beam and not emergency
                )
                self._last_exposure = (
                    exposure and not emergency
                )

                spiral_index = int(
                    self._spiral_position
                )
                shoot_index = int(
                    self._shoot_position
                )

            try:
                self._render(
                    s,
                    spiral_index,
                    shoot_index,
                    current
                )

            except Exception as exc:
                print(
                    "[DIVISI 3] Render error:",
                    exc
                )
                self._stop_event.set()

            self._stop_event.wait(
                1.0 / self.FPS
            )

        try:
            self._clear()
        except Exception as exc:
            print(
                "[DIVISI 3] Cleanup error:",
                exc
            )

    # ========================================
    # RENDER BY CORE STAGE
    # ========================================

    def _render(
        self,
        s,
        spiral_index,
        shoot_index,
        now
    ):

        # Clear frame buffer.
        for i in range(self.total_leds):
            self.strip.setPixelColor(i, 0)

        power = s["power"]
        beam = s["beam"]
        exposure = s["exposure"]
        emergency = s["emergency"]
        stage = s["stage"]

        if emergency or not power:
            # Safe OFF, no warning flash.
            pass

        elif beam:
            # Core Stage 6:
            # Beam acceleration inside Dee.

            self._comet(
                spiral_index,
                self.spiral_start,
                self.spiral_end,
                (0, 170, 255),
                tail=7
            )

            # RF acceleration gap flash.
            if spiral_index in self.rf_gaps:
                self._set_pixel(
                    spiral_index,
                    Color(255, 220, 55)
                )

            if exposure:
                # Core Stage 7:
                # Extraction / Shoot.
                self._comet(
                    shoot_index,
                    self.shoot_start,
                    self.shoot_end,
                    (255, 100, 0),
                    tail=5
                )

                if (
                    shoot_index
                    == self.shoot_end
                ):
                    self._set_pixel(
                        self.shoot_end,
                        Color(255, 235, 130)
                    )

        elif stage == 4:
            # Vacuum pumping: purple glow.
            count = max(
                1,
                (
                    self.spiral_end
                    - self.spiral_start + 1
                ) // 4
            )

            for index in range(
                self.spiral_start,
                self.spiral_start + count
            ):
                self._set_pixel(
                    index,
                    Color(35, 0, 55)
                )

        elif stage == 5:
            # Beam ready:
            # Source + RF markers.
            self._set_pixel(
                self.spiral_start,
                Color(0, 75, 145)
            )

            for index in self.rf_gaps:
                self._set_pixel(
                    index,
                    Color(0, 18, 22)
                )

        else:
            # Stage 1-3: standby.
            self._set_pixel(
                self.spiral_start,
                Color(0, 0, 100)
            )

        self.strip.show()

    # ========================================
    # CLEANUP - CORE CONTRACT
    # ========================================

    def cleanup(self):

        self._stop_event.set()

        if (
            self._thread is not None
            and self._thread.is_alive()
        ):
            self._thread.join(
                timeout=1.0
            )

        self._clear()
        self.enabled = False
