
#!/usr/bin/env python3
"""
DECY-13 - DIVISI 3
WS2812B LED TEST & PIXEL FINDER

Target hardware:
- Raspberry Pi 3 Model B+
- WS2812B 5V Addressable
- GPIO18 / PWM0 / DMA
- Konfigurasi dinamis dari config_hardware.json

Windows:
    python 03_test_led_pixel_finder.py --mode test
    python 03_test_led_pixel_finder.py --mode finder

Raspberry Pi:
    sudo python3 03_test_led_pixel_finder.py --mode finder --hardware

File ini hanya melakukan pengujian Divisi 3.
Tidak mengubah Core Daemon atau konfigurasi resmi.
"""

import argparse
import importlib
import json
import os
import time

from modules.mod_led_ws2812b import (
    LedStripModule,
    MemoryStrip,
    Color
)


BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


# ============================================
# 1. CONFIGURATION
# ============================================

def load_config():

    path = os.path.join(
        BASE_DIR,
        "config_hardware.json"
    )

    if not os.path.isfile(path):
        raise FileNotFoundError(
            "config_hardware.json tidak ditemukan"
        )

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:
        config = json.load(file)

    return config


def validate_mapping(config):

    mapping = config["led_mapping"]

    total = int(mapping["total_leds"])

    spiral_start = int(
        mapping["spiral_start_idx"]
    )

    spiral_end = int(
        mapping["spiral_end_idx"]
    )

    shoot_start = int(
        mapping["shoot_start_idx"]
    )

    shoot_end = int(
        mapping["shoot_end_idx"]
    )

    rf_gaps = set(
        map(
            int,
            mapping.get("rf_gap_indices", [])
        )
    )

    assert total > 0

    assert (
        0 <= spiral_start
        <= spiral_end
        < total
    )

    assert (
        0 <= shoot_start
        <= shoot_end
        < total
    )

    assert (
        spiral_end < shoot_start
        or shoot_end < spiral_start
    )

    assert all(
        spiral_start <= gap <= spiral_end
        for gap in rf_gaps
    )

    return {
        "total": total,
        "spiral_start": spiral_start,
        "spiral_end": spiral_end,
        "shoot_start": shoot_start,
        "shoot_end": shoot_end,
        "rf_gaps": rf_gaps
    }


# ============================================
# 2. LED UTILITIES
# ============================================

def clear_strip(strip):

    for index in range(
        strip.numPixels()
    ):
        strip.setPixelColor(index, 0)

    strip.show()


def show_pixel(strip, index, color):

    clear_strip(strip)

    strip.setPixelColor(
        index,
        color
    )

    strip.show()


def check_all_off(strip):

    if isinstance(strip, MemoryStrip):
        return all(
            pixel == 0
            for pixel in strip.pixels
        )

    # Tidak membaca keadaan listrik hardware.
    return False


# ============================================
# 3. VIRTUAL INTEGRATION TEST
# ============================================

def test_module(config):

    print()
    print("=" * 48)
    print("DECY-13 DIVISI 3 - VIRTUAL TEST")
    print("=" * 48)

    mapping = validate_mapping(config)

    # Hanya salinan dictionary.
    # JSON asli tidak diubah.
    test_config = dict(config)

    test_config["_div3_force_virtual"] = True

    led = LedStripModule(
        test_config
    )

    state = {
        "power": False,
        "beam": False,
        "exposureActive": False,
        "emergency": False,
        "stage": 0,
        "beamEnergy": 0.0,
        "peakEnergy": 13.0,
        "activeLedIdx": -1,
        "shootLedIdx": -1
    }

    try:

        # ====================================
        # TEST 1 - INITIALIZATION
        # ====================================

        hardware_active = led.setup()

        assert hardware_active is False
        assert isinstance(
            led.strip,
            MemoryStrip
        )

        assert (
            led.strip.numPixels()
            == mapping["total"]
        )

        print("[PASS] Virtual initialization")
        print(
            "[INFO] Total LED:",
            mapping["total"]
        )

        # ====================================
        # TEST 2 - POWER OFF
        # ====================================

        led.update(
            state,
            0.2,
            time.monotonic()
        )

        time.sleep(0.10)

        assert (
            state["activeLedIdx"] == -1
        )

        assert (
            state["shootLedIdx"] == -1
        )

        assert check_all_off(led.strip)

        print("[PASS] Stage 0 - Power OFF")

        # ====================================
        # TEST 3 - STANDBY
        # ====================================

        state.update({
            "power": True,
            "stage": 1
        })

        led.update(
            state,
            0.2,
            time.monotonic()
        )

        time.sleep(0.10)

        assert (
            state["activeLedIdx"]
            == mapping["spiral_start"]
        )

        assert (
            led.strip.pixels[
                mapping["spiral_start"]
            ] != 0
        )

        print("[PASS] Stage 1 - Standby")

        # ====================================
        # TEST 4 - VACUUM
        # ====================================

        state["stage"] = 4

        led.update(
            state,
            0.2,
            time.monotonic()
        )

        time.sleep(0.10)

        assert any(
            color != 0
            for color in led.strip.pixels[
                mapping["spiral_start"]:
                mapping["spiral_end"] + 1
            ]
        )

        print("[PASS] Stage 4 - Vacuum")

        # ====================================
        # TEST 5 - BEAM READY
        # ====================================

        state["stage"] = 5

        led.update(
            state,
            0.2,
            time.monotonic()
        )

        time.sleep(0.10)

        assert (
            led.strip.pixels[
                mapping["spiral_start"]
            ] != 0
        )

        print("[PASS] Stage 5 - Beam Ready")

        # ====================================
        # TEST 6 - ACCELERATION
        # ====================================

        state.update({
            "stage": 6,
            "beam": True,
            "beamEnergy": 6.5
        })

        for _ in range(5):

            led.update(
                state,
                0.2,
                time.monotonic()
            )

            time.sleep(0.05)

        active = state["activeLedIdx"]

        assert (
            mapping["spiral_start"]
            <= active
            <= mapping["spiral_end"]
        )

        assert any(
            color != 0
            for color in led.strip.pixels[
                mapping["spiral_start"]:
                mapping["spiral_end"] + 1
            ]
        )

        print(
            "[PASS] Stage 6 - Acceleration",
            f"(LED {active})"
        )

        # ====================================
        # TEST 7 - EXTRACTION / SHOOT
        # ====================================

        state.update({
            "stage": 7,
            "exposureActive": True
        })

        for _ in range(5):

            led.update(
                state,
                0.2,
                time.monotonic()
            )

            time.sleep(0.05)

        shoot = state["shootLedIdx"]

        assert (
            mapping["shoot_start"]
            <= shoot
            <= mapping["shoot_end"]
        )

        assert any(
            color != 0
            for color in led.strip.pixels[
                mapping["shoot_start"]:
                mapping["shoot_end"] + 1
            ]
        )

        print(
            "[PASS] Stage 7 - Extraction",
            f"(LED {shoot})"
        )

        # ====================================
        # TEST 8 - EMERGENCY STOP
        # ====================================

        state.update({
            "emergency": True,
            "power": False,
            "beam": False,
            "exposureActive": False
        })

        led.update(
            state,
            0.2,
            time.monotonic()
        )

        time.sleep(0.10)

        assert (
            state["activeLedIdx"] == -1
        )

        assert (
            state["shootLedIdx"] == -1
        )

        assert check_all_off(led.strip)

        print("[PASS] Emergency Stop")

        # ====================================
        # RESULT
        # ====================================

        print()
        print("=" * 48)
        print(
            "ALL DIVISI 3 VIRTUAL TESTS PASSED"
        )
        print("=" * 48)

    finally:

        led.cleanup()

        if isinstance(led.strip, MemoryStrip):
            assert check_all_off(led.strip)


# ============================================
# 4. PIXEL FINDER
# ============================================

def pixel_finder(config, hardware=False,
                 total=448, spiral_count=400, brightness=20):

    if hardware:
        ws = importlib.import_module("rpi_ws281x")
        strip = ws.PixelStrip(total, 18, 800000, 10,
                              False, brightness, 0)
        strip.begin()
    else:
        strip = MemoryStrip(total)

    gaps = {spiral_count*k//4-1 for k in range(1, 5)}

    def show(p={}):
        for i in range(total):
            strip.setPixelColor(i, p.get(i, 0))
        strip.show()

    def all_on(c):
        show({i: c for i in range(total)})

    def move(a, b, c, d1, d2, rf=False):
        for i in range(a, b):
            x = (i-a)/max(1, b-a-1)
            head = Color(255,220,55) if rf and i in gaps else c
            p = {i: head}
            if i > a:
                p[i-1] = Color(0,50,90) if rf else Color(90,25,0)
            show(p)
            time.sleep(d1+(d2-d1)*x)
        show()

    def spiral():
        move(0, spiral_count, Color(0,170,255),
             0.04, 0.015, True)

    def beam():
        move(spiral_count, total, Color(255,100,0),
             0.04, 0.025)

    def individual():
        for i in range(total):
            show({i: Color(255,255,255)})
            print("LED", i, flush=True)
            time.sleep(0.05)

    def rgb():
        for c in [Color(255,0,0), Color(0,255,0),
                  Color(0,0,255), Color(255,255,255)]:
            all_on(c)
            time.sleep(1.5)

    def repeat():
        for _ in range(3):
            spiral()
            beam()

    def final_shot():
        spiral()
        beam()
        for v in [30,100,200,255,200,100,30,0]:
            show({i: Color(0,v,0)
                  for i in range(total-8,total)})
            time.sleep(0.15)

    def all_test():
        individual()                       # 1
        all_on(Color(255,255,255))         # 2
        time.sleep(3)
        rgb()                              # 3
        spiral()                           # 4
        beam()                             # 5
        repeat()                           # 6
        final_shot()                       # 7
        show()                             # 8

    commands = {
        "t": individual,
        "a": lambda: (all_on(Color(255,255,255)), time.sleep(3), show()),
        "r": rgb,
        "s": spiral,
        "e": beam,
        "p": repeat,
        "b": final_shot,
        "f": all_test
    }

    try:
        show()
        i = 0
        print("DECY-13 | 400 SPIRAL + 48 BEAM")
        print("t/a/r/s/e/p/b/f = test | q = off")
        while True:
            cmd = input(f"LED #{i} > ").strip().lower()
            if cmd in ("q", "o"):
                break
            elif cmd in commands:
                commands[cmd]()
            elif cmd == "":
                show({i: Color(0,180,255)})
                i = (i+1) % total
            elif cmd.isdecimal() and int(cmd) < total:
                i = int(cmd)
                show({i: Color(0,180,255)})
            else:
                print("Perintah tidak dikenal")
    finally:
        show()
        time.sleep(0.2)
        show()
        print("ALL OFF - SELESAI")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["test","finder"],
                        default="test")
    parser.add_argument("--hardware", action="store_true")
    parser.add_argument("--total-leds", type=int, default=448)
    parser.add_argument("--spiral-leds", type=int, default=400)
    parser.add_argument("--brightness", type=int, default=20)
    args = parser.parse_args()

    if not 1 <= args.spiral_leds < args.total_leds:
        parser.error("Pemetaan LED tidak valid")
    if not 1 <= args.brightness <= 255:
        parser.error("Brightness tidak valid")

    config = load_config()
    if args.mode == "test":
        test_module(config)
    else:
        pixel_finder(config, args.hardware, args.total_leds,
                     args.spiral_leds, args.brightness)


if __name__ == "__main__":
    main()
