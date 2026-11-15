
import time

from modules.mod_led_ws2812b import CyclotronLED, MemoryStrip

def main():
    strip = MemoryStrip()
    led = CyclotronLED(strip=strip)

    try:
        for stage in range(8):
            led.set_state(stage=stage, progress=75)
            print(f"Stage {stage}")

            for _ in range(50):
                led.render()
                time.sleep(0.04)

        led.blackout()
        print("E-stop/blackout OK")

    finally:
        led.close()

if __name__ == "__main__":
    main()
