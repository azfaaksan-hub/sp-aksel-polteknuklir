#!/usr/bin/env python3
"""
LANGKAH 1 TRY & ERROR CLI: Uji Isolasi Relay Kipas Vakum (GPIO 21) & Buzzer (GPIO 17)
Jalankan di terminal Raspberry Pi 3B+:
  python3 01_test_relay_buzzer.py
"""
import json
import time
import RPi.GPIO as GPIO

with open("config_hardware.json", "r") as f:
    CFG = json.load(f)

PIN_VAC = CFG["pins_bcm"]["relay_vacuum_fan"]
ACTIVE_LOW = CFG["pins_bcm"]["relay_vacuum_active_low"]
PIN_BUZ = CFG["pins_bcm"]["buzzer"]
PIN_ESTOP = CFG["pins_bcm"]["estop_button"]

def set_vacuum_relay(turn_on: bool):
    if ACTIVE_LOW:
        GPIO.output(PIN_VAC, GPIO.LOW if turn_on else GPIO.HIGH)
    else:
        GPIO.output(PIN_VAC, GPIO.HIGH if turn_on else GPIO.LOW)

def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(PIN_VAC, GPIO.OUT)
    GPIO.setup(PIN_BUZ, GPIO.OUT)
    GPIO.setup(PIN_ESTOP, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # Kondisi awal: Kipas Mati, Buzzer Mati
    set_vacuum_relay(False)
    GPIO.output(PIN_BUZ, GPIO.LOW)

    print("=== UJI ISOLASI RELAY KIPAS VAKUM & BUZZER DECY-13 ===")
    print(f"Pin Relay Kipas (BCM): GPIO {PIN_VAC} (Active-Low={ACTIVE_LOW})")
    print(f"Pin Buzzer      (BCM): GPIO {PIN_BUZ}")
    print("Ketik perintah: [1] Buzzer 1s  [2] Kipas ON  [3] Kipas OFF  [q] Keluar")

    try:
        while True:
            cmd = input("CLI > ").strip().lower()
            if cmd == "1":
                print("-> Buzzer ON selama 1 detik...")
                GPIO.output(PIN_BUZ, GPIO.HIGH)
                time.sleep(1.0)
                GPIO.output(PIN_BUZ, GPIO.LOW)
                print("-> Buzzer OFF.")
            elif cmd == "2":
                print("-> Kipas Vakum ON (Simulasi Pemompaan Ruang Hampa)...")
                set_vacuum_relay(True)
            elif cmd == "3":
                print("-> Kipas Vakum OFF.")
                set_vacuum_relay(False)
            elif cmd == "q":
                break
    finally:
        set_vacuum_relay(False)
        GPIO.output(PIN_BUZ, GPIO.LOW)
        GPIO.cleanup()
        print("GPIO dibersihkan.")

if __name__ == "__main__":
    main()
