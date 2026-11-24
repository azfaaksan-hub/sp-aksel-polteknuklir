
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
    Color, Animation
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
        test_animation(config)

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


def test_animation(config):
    """Deterministic frame tests; no physical GPIO or sleeping."""
    a = Animation(config)
    state = dict(power=True, beam=True, stage=6, emergency=False,
                 exposureActive=False, beamEnergy=13., peakEnergy=13.)
    def check(name, ok):
        if not ok:
            raise AssertionError(name)
        print("[PASS] " + name)
    a.step(state, 0)
    check("Energy speed scaling", a.speed(dict(state, beamEnergy=0)) < a.speed(state))
    check("NaN energy handled", a.speed(dict(state, beamEnergy=float('nan'))) == a.speed(dict(state, beamEnergy=0)))
    frame, head, shoot = a.step(state, .01)
    opposite = a.a + (head-a.a + a.n//2) % a.n
    check("Two cyan packets", frame[head] != 0 and frame[opposite] != 0)
    seen = set()
    for _ in range(200):
        frame, _, _ = a.step(state, .025)
        seen.update(g for g in a.gaps if frame[g] == Color(255,220,55))
    check("All RF crossings", seen == set(a.gaps))
    before = a.spiral_pos
    state.update(stage=7, exposureActive=True)
    frame, head, shoot = a.step(state, .025)
    check("Spiral persists on SHOOT", a.spiral_pos == before and head >= a.a and any(frame[a.a:a.b+1]))
    check("Beamline starts without tail wrap", shoot == a.c and not any(frame[a.c+1:a.d+1]))
    hit = False
    restarted = False
    early = False
    for _ in range(200):
        frame, head, shoot = a.step(state, .025)
        if shoot < a.d and frame[a.d] != 0:
            early = True
        if shoot == a.d and frame[a.d] == Color(170,255,65):
            hit = True
        if hit and shoot == a.c:
            restarted = True
            break
    check("No premature target", not early)
    check("Target impact", hit)
    check("Continuous exposure repeats", restarted)
    frame, head, shoot = a.step(dict(state, exposureActive=False, stage=6), .025)
    check("Exposure OFF clears beamline only", shoot == -1 and not any(frame[a.c:a.d+1]) and any(frame[a.a:a.b+1]))
    frame, head, shoot = a.step(dict(state, emergency=True), .025)
    check("Emergency overrides active beam", head == shoot == -1 and not any(frame))
    frame, head, shoot = a.step(dict(state, stage=0), .025)
    check("Stage zero overrides stale flags", head == shoot == -1 and not any(frame))


# ============================================
# 4. PIXEL FINDER
# ============================================


def pixel_finder(config, hardware=False, total=448,
                 spiral_count=400, brightness=10,
                 auto=False, buzzer_pin=17,
                 sound=True, power_ok=False):

    if hardware and auto and not power_ok:
        raise RuntimeError("--auto hardware memerlukan --power-ok setelah PSU diverifikasi")
    if hardware:
        ws = importlib.import_module("rpi_ws281x")
        strip = ws.PixelStrip(
            total, config["pins_bcm"]["led_ws2812b"],
            800000, 10, False, brightness, 0
        )
        strip.begin()
    else:
        strip = MemoryStrip(total)

    GPIO = None

    ready = False
    mapping = config["led_mapping"]
    gaps = set(mapping["rf_gap_indices"])

    def show(p=None):
        p = p or {}
        for i in range(total):
            strip.setPixelColor(i, p.get(i, 0))
        strip.show()

    def beep(n=1, duration=0.045):
        if not sound:
            return
        if GPIO is None:
            print(f"[SIMULASI] Buzzer x{n}")
            return
        for _ in range(n):
            GPIO.output(buzzer_pin, GPIO.HIGH)
            time.sleep(duration)
            GPIO.output(buzzer_pin, GPIO.LOW)
            time.sleep(0.045)

    def move(a, b, color, d1, d2, rf=False):
        for i in range(a, b):
            t = (i-a)/max(1, b-a-1)
            c = Color(255,220,50) if rf and i in gaps else color
            p = {i: c}
            if i > a:
                p[i-1] = Color(0,35,55) if rf else Color(60,20,0)
            show(p)
            time.sleep(d1+(d2-d1)*t)
        show()

    def individual():
        for i in range(total):
            show({i: Color(255,255,255)})
            print("LED", i, flush=True)
            time.sleep(0.045)
        show()

    def fill(c, delay):
        if hardware and not power_ok:
            raise RuntimeError(
                "All ON/RGB memerlukan --power-ok setelah PSU diverifikasi"
            )
        show({i: c for i in range(total)})
        time.sleep(delay)
        show()

    def rgb():
        for name,c in [
            ("RED", Color(255,0,0)),
            ("GREEN", Color(0,255,0)),
            ("BLUE", Color(0,0,255)),
            ("WHITE", Color(255,255,255))
        ]:
            print(name, flush=True)
            fill(c, 1)

    def charge():
        nonlocal ready
        ready = False
        for n in range(1, 21):
            show({i: Color(255,135,0)
                  for i in range(spiral_count-20,
                                 spiral_count-20+n)})
            if n % 5 == 0:
                beep(1, 0.025)
            time.sleep(0.13)

        ready = True
        print("ENERGY READY 100% (simulasi visual)")
        beep(2, 0.09)
        time.sleep(0.7)

    def shoot():
        nonlocal ready
        if not ready:
            charge()

        beep(1, 0.28)
        for i in range(spiral_count, total):
            p = {j: Color(70,30,0)
                 for j in range(spiral_count-20,spiral_count)}
            p[i] = Color(255,180,0)
            if i > spiral_count:
                p[i-1] = Color(100,35,0)
            show(p)
            time.sleep(0.03)

        for v in [40,100,200,255,100,0]:
            show({i: Color(0,v,0)
                  for i in range(total-8,total)})
            time.sleep(0.13)

        ready = False
        show()

    tests = [
        ("ALL OFF AWAL", lambda: (show(), time.sleep(.4))),
        ("INDIVIDUAL LED", individual),
        ("ALL LED ON", lambda: fill(Color(255,255,255), 2)),
        ("RGB COLOR TEST", rgb),
        ("SPIRAL ACCELERATION",
         lambda: move(0,spiral_count,Color(0,170,255),
                      .04,.018,True)),
        ("EXTRACTION / SHOOT",
         lambda: move(spiral_count,total,Color(255,100,0),
                      .04,.025)),
        ("ENERGY CHARGING", charge),
        ("FINAL BEAM SHOT", shoot),
        ("ALL OFF FINAL", show)
    ]

    def run_one(n):
        name, fn = tests[n-1]
        print(f"TEST {n}/9 - {name}", flush=True)
        beep(n)
        fn()

    try:
        show()
        if hardware and sound:
            gpio = importlib.import_module("RPi.GPIO")
            gpio.setwarnings(False)
            gpio.setmode(gpio.BCM)
            gpio.setup(buzzer_pin, gpio.OUT, initial=gpio.LOW)
            GPIO = gpio
        print(f"DECY-13 | {spiral_count} SPIRAL + "
              f"{total-spiral_count} BEAM")
        print(f"BUZZER GPIO{buzzer_pin}" if sound else "BUZZER OFF")

        if auto:
            for n in range(1,10):
                run_one(n)
        else:
            print("f=semua | s=spiral | e=beam")
            print("b=charge+shot | q=keluar")
            idx = 0
            while True:
                cmd = input(f"LED #{idx} > ").strip().lower()
                if cmd == "q":
                    break
                elif cmd == "f":
                    for n in range(1,10):
                        run_one(n)
                elif cmd == "s":
                    run_one(5)
                elif cmd == "e":
                    run_one(6)
                elif cmd == "b":
                    run_one(7)
                    run_one(8)
                elif cmd == "" or cmd.isdecimal():
                    candidate = (idx+1)%total if cmd == "" else int(cmd)
                    if 0 <= candidate < total:
                        idx = candidate
                        show({idx: Color(0,180,255)})
                    else:
                        print("Indeks di luar jangkauan")
                else:
                    print("Perintah tidak dikenal")

    except KeyboardInterrupt:
        print("\nPengujian dihentikan")

    finally:
        try:
            show()
        finally:
            if GPIO is not None:
                try:
                    GPIO.output(buzzer_pin, GPIO.LOW)
                finally:
                    GPIO.cleanup(buzzer_pin)
        print("ALL OFF - SELESAI")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["test","finder"],
                        default="test")
    parser.add_argument("--hardware", action="store_true")
    parser.add_argument("--auto", action="store_true")
    parser.add_argument("--total-leds", type=int, default=None)
    parser.add_argument("--spiral-leds", type=int, default=None)
    parser.add_argument("--brightness", type=int, default=10)
    parser.add_argument("--buzzer-pin", type=int, default=17)
    parser.add_argument("--no-buzzer", action="store_true")
    parser.add_argument("--power-ok", action="store_true")
    args = parser.parse_args()

    config = load_config()
    m = validate_mapping(config)
    if args.total_leds is None:
        args.total_leds = m["total"]
    if args.spiral_leds is None:
        args.spiral_leds = m["spiral_end"] - m["spiral_start"] + 1
    if args.mode == "finder" and (m["spiral_start"] != 0 or
            m["shoot_start"] != args.spiral_leds or m["shoot_end"] != args.total_leds-1 or
            args.total_leds != m["total"] or args.spiral_leds != m["spiral_end"]+1):
        parser.error("Finder harus mengikuti mapping resmi kontigu dari config_hardware.json")
    if not 20 <= args.spiral_leds <= args.total_leds-8:
        parser.error("Pemetaan spiral/beam tidak valid")
    if not 1 <= args.brightness <= 255:
        parser.error("Brightness harus 1..255")
    if args.buzzer_pin != 17:
        parser.error("Buzzer bersama harus GPIO17 (pin fisik 11)")
    if (args.hardware or args.auto) and args.mode != "finder":
        parser.error("--hardware/--auto hanya untuk finder")

    if args.mode == "test":
        test_module(config)
    else:
        pixel_finder(
            config, args.hardware, args.total_leds,
            args.spiral_leds, args.brightness, args.auto,
            args.buzzer_pin, not args.no_buzzer, args.power_ok
        )


if __name__ == "__main__":
    main()
