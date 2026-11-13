"""
Paket Modul Perangkat Keras Siklotron DECY-13 (Arsitektur Modular 6 Divisi)
===========================================================================
Setiap subsistem fisik diisolasi ke dalam file terpisah di folder `modules/`
agar tim beranggotakan 6 orang dapat bekerja secara paralel di GitHub
tanpa menimbulkan Merge Conflict pada file daemon utama.

Daftar Modul:
- base_module.py       : Kontrak interface dasar (dipegang oleh Divisi 1 / Core)
- mod_vacuum_safety.py : Relay Kipas Vakum, Buzzer, & E-Stop (Divisi 2)
- mod_led_ws2812b.py   : Animasi LED Strip WS2812B Spiral & Shoot (Divisi 3)
- mod_lcd_ili9341.py   : Layar Status LCD TFT SPI ILI9341 (Divisi 4)
"""

from .base_module import HardwareModule
from .mod_vacuum_safety import VacuumSafetyModule
from .mod_led_ws2812b import LedStripModule
from .mod_lcd_ili9341 import LcdDisplayModule

__all__ = [
    "HardwareModule",
    "VacuumSafetyModule",
    "LedStripModule",
    "LcdDisplayModule",
]
