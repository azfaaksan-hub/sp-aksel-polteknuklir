#!/usr/bin/env python3
"""
LANGKAH 2 TRY & ERROR CLI: Uji Isolasi Layar LCD TFT 2.4/2.8 inch SPI (ILI9341)
Pastikan SPI sudah aktif di RPi 3B+ (sudo raspi-config -> Interface Options -> SPI -> Enable).
Jalankan di terminal Raspberry Pi 3B+:
  python3 02_test_lcd_ili9341.py
"""
import json
import time
from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.lcd.device import ili9341
from PIL import ImageFont

with open("config_hardware.json", "r") as f:
    CFG = json.load(f)

def main():
    pins = CFG["pins_bcm"]
    print("=== UJI ISOLASI LCD TFT SPI ILI9341 ===")
    print(f"SPI Port={pins['lcd_spi_port']}, CE={pins['lcd_spi_device_ce']}, DC=GPIO {pins['lcd_dc']}, RST=GPIO {pins['lcd_rst']}")

    serial_spi = spi(
        port=pins["lcd_spi_port"],
        device=pins["lcd_spi_device_ce"],
        gpio_DC=pins["lcd_dc"],
        gpio_RST=pins["lcd_rst"],
        bus_speed_hz=16000000
    )
    device = ili9341(serial_spi, width=320, height=240, rotate=0)
    font = ImageFont.load_default()

    stages = [
        ("TAHAP 1: INISIASI SISTEM", "Power: ON | Buzzer: 5s", "Vacuum: 1013 mbar (Atm)", "cyan"),
        ("TAHAP 4: POMPA VAKUM AKTIF", "Kipas Vakum: ON (Berputar)", "Pressure: 1.2e-7 mbar", "deepskyblue"),
        ("TAHAP 6: AKSELERASI SPIRAL", "Magnet: 1450 A | RF: 22.5 MHz", "Beam Energy: 13.0 MeV", "lime"),
        ("TAHAP 7: SHOOT EXPOSURE!", "Target Current: 8.4 uA", "Iradiasi Target Berjalan", "orange")
    ]

    for title, line1, line2, color in stages:
        print(f"Menampilkan ke LCD: {title}")
        with canvas(device) as draw:
            draw.rectangle(device.bounding_box, outline="teal", fill="black")
            draw.rectangle((0, 0, 320, 34), fill="teal")
            draw.text((10, 10), "DECY-13 CYCLOTRON STATUS", fill="white", font=font)
            draw.text((12, 55), title, fill=color, font=font)
            draw.text((12, 95), line1, fill="white", font=font)
            draw.text((12, 125), line2, fill="lightgray", font=font)
            draw.text((12, 195), "Tekan Ctrl+C di CLI untuk berhenti", fill="yellow", font=font)
        time.sleep(3.0)

if __name__ == "__main__":
    main()
