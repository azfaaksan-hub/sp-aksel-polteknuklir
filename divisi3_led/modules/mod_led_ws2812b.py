
"""
DECY-13 DIVISI 3
WS2812B LED ENGINE - 200 PIXELS

LED 0-149   : Spiral Acceleration
LED 150-199 : Extraction / Shoot

Windows  : MemoryStrip
Pi 5     : Pi5NeoStrip (SPI0)

Render bersifat non-blocking.
Stage dan progress dikirim oleh controller.
"""

from __future__ import annotations

import importlib
import math
import time
from typing import Optional, Tuple


# ============================================
# CONFIGURATION
# ============================================

LED_COUNT = 200

SPIRAL_START = 0
SPIRAL_END = 149

TARGET_START = 150
TARGET_END = 199

SPIRAL_COUNT = SPIRAL_END - SPIRAL_START + 1
TARGET_COUNT = TARGET_END - TARGET_START + 1

DEFAULT_BRIGHTNESS = 0.20
DEFAULT_FPS = 25

RGB = Tuple[int, int, int]

BLACK: RGB = (0, 0, 0)
BLUE: RGB = (0, 130, 255)
PURPLE: RGB = (90, 0, 180)
CYAN: RGB = (0, 200, 220)
GREEN: RGB = (0, 180, 80)
ORANGE: RGB = (255, 110, 0)


# ============================================
# WINDOWS VIRTUAL LED DRIVER
# ============================================

class MemoryStrip:
    """Driver virtual untuk simulasi Windows."""

    def __init__(self, count: int = LED_COUNT):
        self.count = count
        self.pixels = [BLACK] * count
        self.frames = 0

    def set(self, index: int, color: RGB) -> None:
        if 0 <= index < self.count:
            self.pixels[index] = tuple(color)

    def show(self) -> None:
        self.frames += 1

    def clear(self) -> None:
        self.pixels[:] = [BLACK] * self.count
        self.show()

    def close(self) -> None:
        self.clear()


# ============================================
# RASPBERRY PI 5 HARDWARE DRIVER
# ============================================

class Pi5NeoStrip:
    """Driver Raspberry Pi 5 menggunakan SPI0."""

    def __init__(self, count: int = LED_COUNT):

        try:
            module = importlib.import_module("pi5neo")
            Pi5Neo = module.Pi5Neo

        except ImportError as exc:
            raise RuntimeError(
                "Library pi5neo belum tersedia. "
                "Gunakan MemoryStrip di Windows."
            ) from exc

        self.count = count

        self.neo = Pi5Neo(
            "/dev/spidev0.0",
            num_leds=count,
            spi_speed_khz=800,
            quiet_mode=True
        )

    def set(self, index: int, color: RGB) -> None:

        if 0 <= index < self.count:
            self.neo.set_led_color(index, *color)

    def show(self) -> None:
        self.neo.update_strip(sleep_duration=None)

    def clear(self) -> None:
        self.neo.clear_strip()
        self.show()

    def close(self) -> None:
        self.clear()
        self.neo.close()


# ============================================
# CYCLOTRON LED ENGINE
# ============================================

class CyclotronLED:
    """
    Stage:
    0 - IDLE
    1 - PREPARATION
    2 - VACUUM
    3 - MAGNETIC FIELD
    4 - INJECTION
    5 - ACCELERATION
    6 - EXTRACTION
    7 - COMPLETE
    """

    STAGES = {
        0: "IDLE",
        1: "PREPARATION",
        2: "VACUUM",
        3: "MAGNETIC FIELD",
        4: "INJECTION",
        5: "ACCELERATION",
        6: "EXTRACTION",
        7: "COMPLETE"
    }

    def __init__(
        self,
        strip=None,
        brightness=DEFAULT_BRIGHTNESS,
        fps=DEFAULT_FPS
    ):

        if (
            not math.isfinite(brightness)
            or not 0 <= brightness <= 1
        ):
            raise ValueError(
                "Brightness harus antara 0 dan 1."
            )

        if not math.isfinite(fps) or fps <= 0:
            raise ValueError("FPS harus positif.")

        self.strip = (
            strip if strip is not None
            else MemoryStrip()
        )

        if getattr(
            self.strip, "count", LED_COUNT
        ) != LED_COUNT:
            raise ValueError(
                "Strip harus memiliki 200 LED."
            )

        self.brightness = brightness
        self.fps = fps
        self.frame_interval = 1.0 / fps

        self.stage = 0
        self.progress = 0.0

        self.running = True
        self.paused = False
        self.enabled = True
        self.estop = False

        self._started = time.monotonic()
        self._last_frame = None
        self._paused_at = None
        self._closed = False

    # ========================================
    # STATE MANAGEMENT
    # ========================================

    def set_state(
        self,
        *,
        stage: Optional[int] = None,
        progress: Optional[float] = None,
        estop: Optional[bool] = None,
        enabled: Optional[bool] = None
    ) -> None:

        if stage is not None:

            if (
                type(stage) is not int
                or stage not in self.STAGES
            ):
                raise ValueError(
                    "Stage harus 0 sampai 7."
                )

            if stage != self.stage:
                self.stage = stage
                self._started = time.monotonic()
                self._last_frame = None

        if progress is not None:

            value = float(progress)

            if not math.isfinite(value):
                raise ValueError(
                    "Progress tidak valid."
                )

            self.progress = max(
                0.0,
                min(100.0, value)
            )

        if estop:
            self.emergency_stop()

        if enabled is not None:
            self.enabled = bool(enabled)

            if not self.enabled:
                self.render(force=True)

    # ========================================
    # CONTROL METHODS
    # ========================================

    def start(self) -> bool:

        if self.estop or self._closed:
            return False

        self.running = True
        return self.resume()

    def pause(self) -> None:

        if (
            self.running
            and not self.paused
            and not self._closed
        ):
            self.paused = True
            self._paused_at = time.monotonic()

    def resume(self) -> bool:

        if self.estop or self._closed:
            return False

        if self.paused:

            if self._paused_at is not None:
                self._started += (
                    time.monotonic() - self._paused_at
                )

            self.paused = False
            self._paused_at = None
            self._last_frame = None

        return True

    def stop(self) -> None:

        self.running = False
        self.paused = False
        self._paused_at = None

        self.render(force=True)

    def reset(self) -> None:

        self.stage = 0
        self.progress = 0.0

        self.running = False
        self.paused = False
        self.estop = False
        self.enabled = True

        self._started = time.monotonic()
        self._last_frame = None
        self._paused_at = None

        self.render(force=True)

    def emergency_stop(self) -> None:

        self.estop = True
        self.running = False
        self.paused = False
        self._paused_at = None

        self.render(force=True)

    def blackout(self) -> None:
        self.emergency_stop()

    # ========================================
    # COMET ANIMATION
    # ========================================

    @staticmethod
    def _comet(
        pixels,
        head,
        start,
        end,
        color,
        tail=8,
        wrap=False
    ):

        width = end - start + 1

        for k in range(tail):

            index = head - k

            if wrap:
                index = (
                    start
                    + (index - start) % width
                )

            elif not start <= index <= end:
                continue

            fade = (tail - k) / tail

            faded = tuple(
                int(value * fade)
                for value in color
            )

            pixels[index] = faded

    # ========================================
    # SPIRAL POSITION
    # ========================================

    def _spiral_position(self) -> int:
        """
        Progress 0-100 menjadi posisi
        LED 0-149.

        Gerak semakin cepat menuju tepi.
        Ini profil animasi, bukan model
        fisika siklotron terkalibrasi.
        """

        p = self.progress / 100.0

        fraction = (
            0.30 * p
            + 0.70 * p * p
        )

        position = int(
            fraction * SPIRAL_COUNT
        )

        return (
            SPIRAL_START
            + min(SPIRAL_COUNT - 1, position)
        )

    # ========================================
    # MAIN RENDER ENGINE
    # ========================================

    def render(
        self,
        now=None,
        force=False
    ) -> bool:

        if self._closed:
            return False

        now = (
            time.monotonic()
            if now is None
            else now
        )

        # STOP / E-STOP
        if (
            self.estop
            or not self.running
            or not self.enabled
        ):

            self._output(
                [BLACK] * LED_COUNT
            )

            self._last_frame = now
            return True

        # PAUSE: pertahankan frame terakhir.
        if self.paused:
            return False

        # FPS limiter.
        if (
            not force
            and self._last_frame is not None
            and now - self._last_frame
            < self.frame_interval
        ):
            return False

        self._last_frame = now

        elapsed = max(
            0.0,
            now - self._started
        )

        pixels = [BLACK] * LED_COUNT

        # ====================================
        # STAGE 0 - IDLE
        # ====================================

        if self.stage == 0:
            pass

        # ====================================
        # STAGE 1 - PREPARATION
        # ====================================

        elif self.stage == 1:

            intensity = int(
                30
                + 80
                * (1 + math.sin(elapsed * 3)) / 2
            )

            for i in range(
                SPIRAL_START,
                SPIRAL_START + 6
            ):
                pixels[i] = (
                    0, 0, intensity
                )

        # ====================================
        # STAGE 2 - VACUUM
        # ====================================

        elif self.stage == 2:

            count = int(
                self.progress
                / 100.0
                * SPIRAL_COUNT
            )

            for i in range(
                SPIRAL_START,
                SPIRAL_START + count
            ):
                pixels[i] = PURPLE

        # ====================================
        # STAGE 3 - MAGNETIC FIELD
        # ====================================

        elif self.stage == 3:

            for i in range(
                SPIRAL_START,
                SPIRAL_END + 1
            ):
                pixels[i] = (
                    0, 50, 40
                )

        # ====================================
        # STAGE 4 - INJECTION
        # ====================================

        elif self.stage == 4:

            head = (
                SPIRAL_START
                + min(5, int(elapsed * 10))
            )

            self._comet(
                pixels,
                head,
                SPIRAL_START,
                SPIRAL_START + 5,
                CYAN,
                tail=4,
                wrap=False
            )

        # ====================================
        # STAGE 5 - ACCELERATION
        # ====================================

        elif self.stage == 5:

            # Dari LED 0 menuju LED 149.
            head = self._spiral_position()

            self._comet(
                pixels,
                head,
                SPIRAL_START,
                SPIRAL_END,
                BLUE,
                tail=12,
                wrap=False
            )

            # Background spiral redup.
            for i in range(
                SPIRAL_START,
                SPIRAL_END + 1
            ):
                if pixels[i] == BLACK:
                    pixels[i] = (0, 0, 4)

        # ====================================
        # STAGE 6 - EXTRACTION
        # ====================================

        elif self.stage == 6:

            # Indikator keluar spiral.
            pixels[SPIRAL_END] = BLUE

            # Progress 0-100 dipetakan
            # ke LED 150-199.
            head = (
                TARGET_START
                + min(
                    TARGET_COUNT - 1,
                    int(
                        self.progress
                        / 100.0
                        * TARGET_COUNT
                    )
                )
            )

            self._comet(
                pixels,
                head,
                TARGET_START,
                TARGET_END,
                ORANGE,
                tail=8,
                wrap=False
            )

        # ====================================
        # STAGE 7 - COMPLETE
        # ====================================

        elif self.stage == 7:

            for i in range(
                TARGET_START,
                TARGET_END + 1
            ):
                pixels[i] = GREEN

        self._output(pixels)
        return True

    # ========================================
    # OUTPUT DRIVER
    # ========================================

    def _output(self, pixels) -> None:

        for index, rgb in enumerate(pixels):

            scaled = tuple(
                max(
                    0,
                    min(
                        255,
                        round(
                            value * self.brightness
                        )
                    )
                )
                for value in rgb
            )

            self.strip.set(index, scaled)

        self.strip.show()

    # ========================================
    # STATUS
    # ========================================

    def get_status(self) -> dict:

        return {
            "stage": self.stage,
            "stage_name": self.STAGES[self.stage],
            "progress": self.progress,
            "running": self.running,
            "paused": self.paused,
            "estop": self.estop,
            "enabled": self.enabled,
            "brightness": self.brightness
        }

    # ========================================
    # SHUTDOWN
    # ========================================

    def close(self) -> None:

        if not self._closed:

            self.emergency_stop()
            self.strip.close()
            self._closed = True
