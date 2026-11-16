
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

def pixel_finder(config, hardware=False):

    mapping = validate_mapping(config)

    total = mapping["total"]

    if hardware:

        # Hanya diimpor dalam mode hardware.
        ws = importlib.import_module(
            "rpi_ws281x"
        )

        strip = ws.PixelStrip(
            total,
            int(
                config["pins_bcm"][
                    "led_ws2812b"
                ]
            ),
            800000,
            10,
            False,
            int(
                config["led_mapping"].get(
                    "brightness", 110
                )
            ),
            0
        )

        strip.begin()

        print(
            "[HARDWARE] WS2812B initialized"
        )

    else:

        strip = MemoryStrip(total)

        print(
            "[VIRTUAL] No GPIO output"
        )

    index = 0

    print()
    print("=" * 48)
    print("DECY-13 LED PIXEL FINDER")
    print("=" * 48)

    print("Total LED:", total)

    print(
        "Spiral:",
        mapping["spiral_start"],
        "-",
        mapping["spiral_end"]
    )

    print(
        "Extraction:",
        mapping["shoot_start"],
        "-",
        mapping["shoot_end"]
    )

    print()
    print("ENTER = Next LED")
    print("Angka = Jump to LED")
    print("s = Test spiral")
    print("e = Test extraction")
    print("q = Quit")

    try:

        while True:

            show_pixel(
                strip,
                index,
                Color(0, 180, 255)
            )

            command = input(
                f"LED #{index} > "
            ).strip().lower()

            if command == "q":
                break

            elif command == "":

                index = (
                    index + 1
                ) % total

            elif command == "s":

                start = mapping[
                    "spiral_start"
                ]

                end = mapping[
                    "spiral_end"
                ]

                gaps = mapping[
                    "rf_gaps"
                ]

                print(
                    "[TEST] Spiral acceleration"
                )

                for i in range(
                    start,
                    end + 1
                ):

                    color = (
                        Color(255, 220, 55)
                        if i in gaps
                        else Color(0, 170, 255)
                    )

                    show_pixel(
                        strip,
                        i,
                        color
                    )

                    fraction = (
                        (i - start)
                        / max(1, end - start)
                    )

                    delay = max(
                        0.015,
                        0.09 - fraction * 0.075
                    )

                    time.sleep(delay)

                index = start

            elif command == "e":

                start = mapping[
                    "shoot_start"
                ]

                end = mapping[
                    "shoot_end"
                ]

                print(
                    "[TEST] Extraction beamline"
                )

                for i in range(
                    start,
                    end + 1
                ):

                    show_pixel(
                        strip,
                        i,
                        Color(255, 100, 0)
                    )

                    time.sleep(0.04)

                index = start

            elif command.isdecimal():

                target = int(command)

                if 0 <= target < total:
                    index = target

                else:
                    print(
                        "[WARNING] Index out of range"
                    )

            else:

                print(
                    "[WARNING] Unknown command"
                )

    except KeyboardInterrupt:
        print("\nTest dihentikan pengguna.")

    finally:

        clear_strip(strip)

        print(
            "[SAFE] Pixel finder cleared"
        )


# ============================================
# 5. APPLICATION ENTRY
# ============================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "DECY-13 Division 3 "
            "WS2812B test utility"
        )
    )

    parser.add_argument(
        "--mode",
        choices=("test", "finder"),
        default="test"
    )

    parser.add_argument(
        "--hardware",
        action="store_true",
        help="Enable physical LED output"
    )

    args = parser.parse_args()

    if (
        args.hardware
        and args.mode != "finder"
    ):
        parser.error(
            "--hardware hanya untuk --mode finder"
        )

    config = load_config()

    if args.mode == "test":

        test_module(config)

    else:

        pixel_finder(
            config,
            hardware=args.hardware
        )


if __name__ == "__main__":
    main()
