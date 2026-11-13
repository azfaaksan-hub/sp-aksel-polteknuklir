#!/usr/bin/env python3
"""
MODUL DIVISI 3: SISTEM LED STRIP WS2812B (SPIRAL DEE & BEAMLINE SHOOT)
======================================================================
Penanggung Jawab : Anggota 3 (Divisi Visualisasi Fisik LED WS2812B)
Branch GitHub    : divisi-3-led-ws2812b
File Terkait     : - raspi_cli/modules/mod_led_ws2812b.py (File ini)
                   - raspi_cli/03_test_led_pixel_finder.py

Tugas & Tanggung Jawab Modul Ini:
1. Mengendalikan 64 piksel LED Strip WS2812B pada GPIO 18 (DMA PWM0).
2. Menjalankan animasi di background thread terpisah (~40 FPS) agar putaran
   partikel di dalam elektroda Dee terlihat sangat mulus (tidak patah-patah
   mengikuti interval MQTT 200ms).
3. Menampilkan efek visual fisika siklotron:
   - Standby (Power ON, Beam OFF): LED #0 menyala biru lembut (Ion Source siap).
   - Beam ON (Tahap 6): Partikel bergerak spiral dari indeks `spiral_start_idx` (0)
     ke `spiral_end_idx` (47) dengan ekor cahaya (comet trail) dan kecepatan
     yang meningkat seiring naiknya `beamEnergy` (0 -> 13 MeV).
   - RF Gap Flash: Saat partikel melewati `rf_gap_indices` ([11, 23, 35, 47]),
     piksel menyala kuning-putih terang sebagai visualisasi tendangan medan listrik RF!
   - Shoot Exposure (Tahap 7): Segmen lurus `shoot_start_idx` (48) s.d. `shoot_end_idx` (63)
     menembakkan pulsa oranye-merah menuju Target Station.
   - Emergency Stop: Seluruh LED berkedip merah darurat.
"""

import threading
import time
from typing import Dict, Any
from .base_module import HardwareModule

try:
    from rpi_ws281x import PixelStrip, Color
    HAS_WS281X = True
except ImportError:
    HAS_WS281X = False
    def Color(r, g, b):
        return (r << 16) | (g << 8) | b


class LedStripModule(HardwareModule):
    """Driver modular WS2812B dengan thread animasi berkecepatan tinggi (~40 FPS)."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        pins = self.cfg.get("pins_bcm", {})
        led_cfg = self.cfg.get("led_mapping", {})

        self.pin_led = pins.get("led_ws2812b", 18)
        self.total_leds = led_cfg.get("total_leds", 64)
        self.brightness = led_cfg.get("brightness", 110)
        self.spiral_start = led_cfg.get("spiral_start_idx", 0)
        self.spiral_end = led_cfg.get("spiral_end_idx", 47)
        self.rf_gaps = set(led_cfg.get("rf_gap_indices", [11, 23, 35, 47]))
        self.shoot_start = led_cfg.get("shoot_start_idx", 48)
        self.shoot_end = led_cfg.get("shoot_end_idx", 63)

        self.strip = None
        self._running = False
        self._thread = None
        self._lock = threading.Lock()

        # Snapshot state internal untuk thread animasi
        self._state_ref: Dict[str, Any] = {}
        self._last_spiral_step = time.time()
        self._last_shoot_step = time.time()

    def setup(self) -> bool:
        if HAS_WS281X:
            try:
                self.strip = PixelStrip(
                    self.total_leds,
                    self.pin_led,
                    800000,  # 800 kHz
                    10,      # DMA channel 10
                    False,   # Invert
                    self.brightness,
                    0        # PWM channel 0
                )
                self.strip.begin()
                self.enabled = True
            except Exception as e:
                print(f"[LedStripModule] Peringatan: Gagal inisialisasi WS2812B DMA ({e}). Mode simulasi aktif.")
                self.strip = None
                self.enabled = False
        else:
            self.enabled = False

        # Jalankan worker thread baik di RPi maupun di mode simulasi agar
        # indeks `activeLedIdx` dan `shootLedIdx` tetap ter-update mulus untuk Web HMI
        self._running = True
        self._thread = threading.Thread(target=self._animation_loop, daemon=True)
        self._thread.start()
        return self.enabled

    def update(self, state: Dict[str, Any], dt: float, now: float) -> None:
        with self._lock:
            self._state_ref = state

    def _animation_loop(self) -> None:
        while self._running:
            now = time.time()
            with self._lock:
                s = self._state_ref

            if s:
                power = bool(s.get("power", False))
                beam = bool(s.get("beam", False))
                exposure = bool(s.get("exposureActive", False))
                emergency = bool(s.get("emergency", False))
                energy_mev = float(s.get("beamEnergy", 0.0))
                max_mev = max(1.0, float(s.get("peakEnergy", 13.0)))

                if emergency or not power:
                    s["activeLedIdx"] = 0 if (power and not emergency) else -1
                    s["shootLedIdx"] = -1
                elif not beam:
                    s["activeLedIdx"] = self.spiral_start
                    s["shootLedIdx"] = -1
                else:
                    # Kecepatan putar meningkat seiring kenaikan energi (delay 75ms -> 18ms)
                    energy_ratio = min(1.0, max(0.0, energy_mev / max_mev))
                    spiral_delay = max(0.018, 0.075 - (energy_ratio * 0.055))

                    if now - self._last_spiral_step >= spiral_delay:
                        self._last_spiral_step = now
                        cur_idx = s.get("activeLedIdx", self.spiral_start)
                        if cur_idx < self.spiral_start or cur_idx > self.spiral_end:
                            cur_idx = self.spiral_start
                        else:
                            cur_idx = self.spiral_start + ((cur_idx - self.spiral_start + 1) % (self.spiral_end - self.spiral_start + 1))
                        s["activeLedIdx"] = cur_idx

                    if exposure:
                        shoot_delay = 0.030  # Pulsa ekstraksi cepat menuju target
                        if now - self._last_shoot_step >= shoot_delay:
                            self._last_shoot_step = now
                            cur_shoot = s.get("shootLedIdx", self.shoot_start)
                            if cur_shoot < self.shoot_start or cur_shoot > self.shoot_end:
                                cur_shoot = self.shoot_start
                            else:
                                cur_shoot = self.shoot_start + ((cur_shoot - self.shoot_start + 1) % (self.shoot_end - self.shoot_start + 1))
                            s["shootLedIdx"] = cur_shoot
                    else:
                        s["shootLedIdx"] = -1

                if self.strip and self.enabled:
                    self._render_physical_strip(
                        power=power,
                        beam=beam,
                        exposure=exposure,
                        emergency=emergency,
                        active_idx=s.get("activeLedIdx", -1),
                        shoot_idx=s.get("shootLedIdx", -1),
                        now=now
                    )

            time.sleep(0.025)  # 40 FPS

    def _render_physical_strip(
        self,
        power: bool,
        beam: bool,
        exposure: bool,
        emergency: bool,
        active_idx: int,
        shoot_idx: int,
        now: float
    ) -> None:
        num_px = self.strip.numPixels()
        for i in range(num_px):
            self.strip.setPixelColor(i, Color(0, 0, 0))

        if emergency:
            # Kedip merah cepat saat Emergency Stop
            flash_on = (int(now * 6) % 2) == 0
            col = Color(200, 0, 0) if flash_on else Color(40, 0, 0)
            for i in range(num_px):
                self.strip.setPixelColor(i, col)
        elif beam and active_idx >= self.spiral_start:
            # Gambar ekor partikel (Comet Trail 4 piksel di belakang kepala partikel)
            trail_colors = [
                Color(0, 110, 180),
                Color(0, 55, 110),
                Color(0, 25, 60),
                Color(0, 10, 25),
            ]
            spiral_len = self.spiral_end - self.spiral_start + 1
            for offset, t_col in enumerate(trail_colors, start=1):
                t_idx = self.spiral_start + ((active_idx - self.spiral_start - offset) % spiral_len)
                if 0 <= t_idx < num_px:
                    self.strip.setPixelColor(t_idx, t_col)

            # Kepala partikel: kuning-putih terang jika tepat di celah akselerasi RF (RF Gap),
            # cyan terang jika di dalam ruang magnet Dee
            if active_idx in self.rf_gaps:
                self.strip.setPixelColor(active_idx, Color(255, 220, 60))
            else:
                self.strip.setPixelColor(active_idx, Color(0, 240, 255))

            # Segmen lurus Beamline Shoot (Tahap 7)
            if exposure and self.shoot_start <= shoot_idx <= self.shoot_end:
                self.strip.setPixelColor(shoot_idx, Color(255, 90, 0))
                if shoot_idx - 1 >= self.shoot_start:
                    self.strip.setPixelColor(shoot_idx - 1, Color(160, 40, 0))
                # Piksel ujung target berpendar merah-putih saat ditembak
                if self.shoot_end < num_px:
                    self.strip.setPixelColor(self.shoot_end, Color(255, 180, 100))
        elif power:
            # Standby: Ion source di pusat spiral menyala biru tenang
            if 0 <= self.spiral_start < num_px:
                self.strip.setPixelColor(self.spiral_start, Color(0, 0, 140))

        self.strip.show()

    def cleanup(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)
        if self.strip and self.enabled:
            for i in range(self.strip.numPixels()):
                self.strip.setPixelColor(i, Color(0, 0, 0))
            self.strip.show()
            self.enabled = False
