#!/usr/bin/env python3
"""
MODUL DIVISI 4: LAYAR LCD TFT SPI 2.4/2.8 INCH (DRIVER ILI9341 320x240)
=======================================================================
Penanggung Jawab : Anggota 4 (Divisi Display & Informasi Lokal LCD TFT)
Branch GitHub    : divisi-4-lcd-ili9341
File Terkait     : - raspi_cli/modules/mod_lcd_ili9341.py (File ini)
                   - raspi_cli/02_test_lcd_ili9341.py

Tugas & Tanggung Jawab Modul Ini:
1. Mengendalikan layar LCD TFT SPI0 (CE0=GPIO 8, MOSI=GPIO 10, SCLK=GPIO 11,
   DC=GPIO 24, RST=GPIO 25) beresolusi 320x240 piksel.
2. Menyelesaikan BUG pada daemon lama (dimana `self.lcd` diinisialisasi tetapi
   belum pernah di-render di dalam loop).
3. Menjalankan proses gambar SPI di background thread (~4 FPS) agar transfer
   frame SPI tidak memperlambat loop fisika & MQTT utama.
4. Menampilkan UI lokal yang informatif di alat peraga:
   - Header warna dinamis sesuai tahapan operasi (Standby/Vacuum/Ready/Beam/Shoot/E-Stop)
   - 4 baris teks telemetri (`lcd_line1` .. `lcd_line4`)
   - Progress Bar visual untuk tingkat kevakuman & energi berkas (0 - 13 MeV)
"""

import math
import threading
import time
from typing import Dict, Any
from .base_module import HardwareModule

try:
    from luma.core.interface.serial import spi
    from luma.core.render import canvas
    from luma.lcd.device import ili9341
    from PIL import ImageFont
    HAS_LCD = True
except ImportError:
    HAS_LCD = False


class LcdDisplayModule(HardwareModule):
    """Driver modular LCD TFT ILI9341 dengan non-blocking SPI render thread."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        pins = self.cfg.get("pins_bcm", {})
        self.spi_port = pins.get("lcd_spi_port", 0)
        self.spi_ce = pins.get("lcd_spi_device_ce", 0)
        self.pin_dc = pins.get("lcd_dc", 24)
        self.pin_rst = pins.get("lcd_rst", 25)

        self.device = None
        self.font = None
        self._running = False
        self._thread = None
        self._lock = threading.Lock()
        self._snapshot: Dict[str, Any] = {}
        self._last_signature = None

    def setup(self) -> bool:
        if not HAS_LCD:
            self.enabled = False
            return False

        try:
            serial_spi = spi(
                port=self.spi_port,
                device=self.spi_ce,
                gpio_DC=self.pin_dc,
                gpio_RST=self.pin_rst,
                bus_speed_hz=16000000
            )
            self.device = ili9341(serial_spi, width=320, height=240, rotate=0)
            self.font = ImageFont.load_default()
            self.enabled = True
        except Exception as e:
            print(f"[LcdDisplayModule] Peringatan: LCD SPI tidak terdeteksi ({e}). Mode tanpa LCD aktif.")
            self.device = None
            self.enabled = False
            return False

        self._running = True
        self._thread = threading.Thread(target=self._render_loop, daemon=True)
        self._thread.start()
        return True

    def update(self, state: Dict[str, Any], dt: float, now: float) -> None:
        if not self.enabled:
            return
        with self._lock:
            self._snapshot = {
                "stage": state.get("stage", 0),
                "mode": state.get("mode", "Standby"),
                "emergency": state.get("emergency", False),
                "exposureActive": state.get("exposureActive", False),
                "beam": state.get("beam", False),
                "interlocks": state.get("interlocks", False),
                "vacuum": state.get("vacuum", False),
                "power": state.get("power", False),
                "pressure": float(state.get("pressure", 1013.0)),
                "beamEnergy": float(state.get("beamEnergy", 0.0)),
                "peakEnergy": float(state.get("peakEnergy", 13.0)),
                "lcd_line1": state.get("lcd_line1", "DECY-13 CYCLOTRON"),
                "lcd_line2": state.get("lcd_line2", "MODE: STANDBY"),
                "lcd_line3": state.get("lcd_line3", ""),
                "lcd_line4": state.get("lcd_line4", ""),
            }

    def _render_loop(self) -> None:
        while self._running:
            with self._lock:
                snap = dict(self._snapshot) if self._snapshot else None

            if snap and self.device:
                # Render ulang hanya jika tampilan berubah agar bus SPI hemat
                sig = (
                    snap["stage"],
                    snap["lcd_line1"],
                    snap["lcd_line2"],
                    snap["lcd_line3"],
                    snap["lcd_line4"],
                )
                if sig != self._last_signature:
                    self._last_signature = sig
                    try:
                        self._draw_screen(snap)
                    except Exception as e:
                        print(f"[LcdDisplayModule] Gagal menggambar frame SPI: {e}")

            time.sleep(0.25)  #Maksimal 4 FPS untuk layar status

    def _draw_screen(self, snap: Dict[str, Any]) -> None:
        # Pilih warna tema berdasarkan kondisi operasi
        if snap["emergency"]:
            header_bg, accent = "red", "salmon"
        elif snap["exposureActive"]:
            header_bg, accent = "darkorange", "orange"
        elif snap["beam"]:
            header_bg, accent = "darkgreen", "lime"
        elif snap["interlocks"]:
            header_bg, accent = "teal", "cyan"
        elif snap["vacuum"]:
            header_bg, accent = "navy", "deepskyblue"
        elif snap["power"]:
            header_bg, accent = "darkslateblue", "skyblue"
        else:
            header_bg, accent = "darkslategray", "lightgray"

        # Hitung rasio progress bar Vakum (logaritmik 1013 mbar -> 1e-7 mbar)
        p = max(1e-7, min(1013.0, snap["pressure"]))
        vac_frac = max(0.0, min(1.0, (3.0 - math.log10(p)) / 10.0))

        # Hitung rasio progress bar Energi (0 -> 13 MeV)
        e_frac = max(0.0, min(1.0, snap["beamEnergy"] / max(1.0, snap["peakEnergy"])))

        with canvas(self.device) as draw:
            # Bingkai luar & Header
            draw.rectangle(self.device.bounding_box, outline=accent, fill="black")
            draw.rectangle((0, 0, 320, 32), fill=header_bg)
            draw.text((10, 10), f"DECY-13 CYCLOTRON | STAGE {snap['stage']}/7", fill="white", font=self.font)

            # 4 Baris Utama Telemetri
            draw.text((12, 46), str(snap["lcd_line1"]), fill=accent, font=self.font)
            draw.text((12, 72), str(snap["lcd_line2"]), fill="white", font=self.font)
            draw.text((12, 102), str(snap["lcd_line3"]), fill="lightgray", font=self.font)
            draw.text((12, 126), str(snap["lcd_line4"]), fill="lightgray", font=self.font)

            # Bar 1: Progress Vakum
            draw.text((12, 160), "VACUUM LEVEL:", fill="deepskyblue", font=self.font)
            draw.rectangle((110, 160, 304, 172), outline="deepskyblue", fill="black")
            vac_w = int(192 * vac_frac)
            if vac_w > 0:
                draw.rectangle((111, 161, 111 + vac_w, 171), fill="deepskyblue")

            # Bar 2: Progress Energi MeV
            draw.text((12, 184), "BEAM ENERGY :", fill="lime", font=self.font)
            draw.rectangle((110, 184, 304, 196), outline="lime", fill="black")
            ene_w = int(192 * e_frac)
            if ene_w > 0:
                draw.rectangle((111, 185, 111 + ene_w, 195), fill="lime")

            # Footer Status
            draw.rectangle((1, 214, 318, 238), fill="#111827")
            draw.text((10, 221), f"MODE: {str(snap['mode']).upper()} | MQTT STATE-DRIVEN", fill="yellow", font=self.font)

    def cleanup(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)
        self.enabled = False
