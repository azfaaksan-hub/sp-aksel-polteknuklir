#!/usr/bin/env python3
"""
LANGKAH 3 TRY & ERROR CLI: Uji LED Strip 5V Programmable (WS2812B) & Pencari Nomor Piksel
PENTING: Wajib dijalankan dengan sudo karena DMA mengakses memori perangkat keras:
  sudo python3 03_test_led_pixel_finder.py
"""
import json
import time
from rpi_ws281x import PixelStrip, Color

with open("config_hardware.json", "r") as f:
    CFG = json.load(f)

LED_COUNT = CFG["led_mapping"]["total_leds"]
LED_PIN = CFG["pins_bcm"]["led_ws2812b"]  # GPIO 18 (Pin Fisik 12)
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = CFG["led_mapping"]["brightness"]
LED_INVERT = False
LED_CHANNEL = 0

def clear_strip(strip):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

def main():
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()
    clear_strip(strip)

    print("=== PIXEL FINDER & TESTER WS2812B DECY-13 ===")
    print(f"Total LED dikonfigurasi: {LED_COUNT} piksel pada GPIO {LED_PIN}")
    print("Mode: [Enter] Maju 1 LED | [angka] Lompat ke indeks | [s] Tes Spiral Cepat | [q] Keluar")

    idx = 0
    try:
        while True:
            clear_strip(strip)
            strip.setPixelColor(idx, Color(0, 255, 255))
            strip.show()
            user_in = input(f"LED menyala saat ini = Indeks #{idx}. Perintah > ").strip().lower()
            if user_in == "":
                idx = (idx + 1) % LED_COUNT
            elif user_in.isdigit():
                idx = int(user_in) % LED_COUNT
            elif user_in == "s":
                print("Menjalankan simulasi percepatan spiral dari pusat ke luar...")
                for i in range(LED_COUNT):
                    clear_strip(strip)
                    strip.setPixelColor(i, Color(255, 180, 0) if i in CFG["led_mapping"]["rf_gap_indices"] else Color(0, 200, 255))
                    strip.show()
                    # Delay makin pendek saat radius membesar (efek percepatan RF)
                    delay_s = max(0.012, 0.085 - (i / LED_COUNT) * 0.070)
                    time.sleep(delay_s)
            elif user_in == "q":
                break
    finally:
        clear_strip(strip)
        print("Seluruh LED dimatikan.")

if __name__ == "__main__":
    main()
