#!/usr/bin/env python3
"""
DIVISI 6 (JARINGAN MQTT, NODE-RED & QA): DIAGNOSTIC & HEALTHCHECK TOOL
=======================================================================
Penanggung Jawab : Anggota 6 (Divisi Jaringan MQTT, Node-RED & Commissioning QA)
Branch GitHub    : divisi-6-nodered-qa
File Terkait     : - raspi_cli/06_test_mqtt_healthcheck.py (File ini)
                   - nodered/flows_mqtt_decy13.json
                   - instruksi untuk projek sp/CHECKLIST_COMMISSIONING.txt

Fungsi Alat Ini:
1. Menguji koneksi ke Mosquitto Broker (lokal 127.0.0.1 maupun IP Raspi 192.168.137.1).
2. Memvalidasi apakah kontrak JSON `decy13/rpi/state` memiliki seluruh field wajib
   yang dibutuhkan oleh Web HMI (Divisi 5) dan Node-RED (Divisi 6).
3. Mengukur frekuensi rata-rata pengiriman telemetri (target: ~5.0 Hz / tiap 200ms).
4. Menyediakan menu uji interaktif untuk mengirim perintah `decy13/hmi/cmd` dan
   melihat perubahan state secara langsung dari terminal.

Cara Pakai:
  python 06_test_mqtt_healthcheck.py
  python 06_test_mqtt_healthcheck.py --host 127.0.0.1
"""

import argparse
import json
import os
import socket
import sys
import time
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("[ERROR] Library paho-mqtt belum terinstall. Jalankan: pip install paho-mqtt")
    sys.exit(1)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config_hardware.json")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CFG = json.load(f)

REQUIRED_STATE_KEYS = [
    "power", "vacuum", "rf", "magnet", "interlocks", "beam",
    "exposureActive", "emergency", "stage", "mode",
    "lcd_line1", "lcd_line2", "lcd_line3", "lcd_line4",
    "pressure", "beamEnergy", "beamCurrent", "targetCurrent",
    "activeLedIdx", "shootLedIdx", "buzzerActive", "logs"
]


def main():
    parser = argparse.ArgumentParser(description="DECY-13 MQTT Contract & Healthcheck Tool (Divisi 6)")
    parser.add_argument("--host", default=CFG["mqtt"]["broker_host"], help="Host/IP Broker MQTT (default dari config_hardware.json)")
    parser.add_argument("--port", type=int, default=CFG["mqtt"]["broker_port_tcp"], help="Port TCP MQTT (default 1883)")
    args = parser.parse_args()

    topic_cmd = CFG["mqtt"]["topic_cmd"]
    topic_state = CFG["mqtt"]["topic_state"]

    stats = {
        "msg_count": 0,
        "first_ts": None,
        "last_state": None,
        "missing_keys": [],
    }

    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id="decy13_qa_healthcheck")
    except (AttributeError, TypeError):
        client = mqtt.Client(client_id="decy13_qa_healthcheck")

    def on_connect(c, userdata, flags, rc):
        if rc == 0:
            print(f"[OK] Terhubung ke Broker MQTT {args.host}:{args.port}")
            c.subscribe(topic_state)
        else:
            print(f"[GAGAL] Kode return MQTT rc={rc}")

    def on_message(c, userdata, msg):
        now = time.time()
        try:
            data = json.loads(msg.payload.decode("utf-8"))
            if stats["first_ts"] is None:
                stats["first_ts"] = now
            stats["msg_count"] += 1
            stats["last_state"] = data
            stats["missing_keys"] = [k for k in REQUIRED_STATE_KEYS if k not in data]
        except Exception as e:
            print(f"[ERR] Payload JSON rusak: {e}")

    client.on_connect = on_connect
    client.on_message = on_message

    print("=" * 65)
    print("  DECY-13 MQTT QA & HEALTHCHECK (DIVISI 6)")
    print(f"  Target Broker : {args.host}:{args.port}")
    print(f"  Topic State   : {topic_state}")
    print(f"  Topic Command : {topic_cmd}")
    print("=" * 65)

    def _is_reachable(h: str, p: int) -> bool:
        try:
            with socket.create_connection((h, p), timeout=0.4):
                return True
        except OSError:
            return False

    if not _is_reachable(args.host, args.port) and args.host != "127.0.0.1":
        if _is_reachable("127.0.0.1", args.port):
            print(f"[Auto-Fallback] Host {args.host}:{args.port} tidak aktif -> beralih ke 127.0.0.1:{args.port}")
            args.host = "127.0.0.1"

    try:
        client.connect(args.host, args.port, 30)
        client.loop_start()
    except Exception as e:
        print(f"[ERROR] Tidak dapat menghubungi broker {args.host}:{args.port} -> {e}")
        sys.exit(1)

    print("Mendengarkan paket telemetri selama 2 detik...")
    time.sleep(2.2)

    if stats["msg_count"] == 0:
        print("[PERINGATAN] Broker aktif, tetapi belum ada paket di topic decy13/rpi/state.")
        print("             Pastikan 04_decy13_mqtt_daemon.py atau 05_laptop_dryrun_simulator.py berjalan!")
    else:
        elapsed = max(0.1, time.time() - stats["first_ts"])
        hz = stats["msg_count"] / elapsed
        s = stats["last_state"]
        print(f"[LULUS] Menerima {stats['msg_count']} paket (~{hz:.1f} Hz).")
        if stats["missing_keys"]:
            print(f"[PERINGATAN KONTRAK] Key hilang: {stats['missing_keys']}")
        else:
            print("[LULUS] Kontrak JSON State 100% valid (22/22 field wajib lengkap).")
        print(f"        Status Saat Ini -> Stage {s.get('stage')} ({s.get('mode')}) | P={s.get('pressure'):.2e} mbar | E={s.get('beamEnergy'):.1f} MeV")

    print("\nMenu Uji Cepat Perintah MQTT:")
    print("  [1] TOGGLE_POWER    [2] TOGGLE_VACUUM   [3] TOGGLE_INTERLOCK")
    print("  [4] AUTO_INIT       [5] START_BEAM      [6] SHOOT")
    print("  [7] EMERGENCY_STOP  [s] Cek Status      [q] Keluar")

    cmd_lookup = {
        "1": {"cmd": "TOGGLE_POWER"},
        "2": {"cmd": "TOGGLE_VACUUM"},
        "3": {"cmd": "TOGGLE_INTERLOCK"},
        "4": {"cmd": "AUTO_INIT"},
        "5": {"cmd": "START_BEAM"},
        "6": {"cmd": "SHOOT"},
        "7": {"cmd": "EMERGENCY_STOP"},
    }

    try:
        while True:
            choice = input("QA-CLI > ").strip().lower()
            if choice == "q":
                break
            elif choice == "s":
                s = stats["last_state"]
                if not s:
                    print("Belum ada data state yang diterima.")
                else:
                    print(f"  Stage={s.get('stage')} | Mode={s.get('mode')} | Power={s.get('power')} | Vac={s.get('vacuum')}")
                    print(f"  Pressure={s.get('pressure'):.2e} mbar | Interlock={s.get('interlocks')} | Beam={s.get('beam')} ({s.get('beamEnergy'):.1f} MeV)")
                    print(f"  LED Spiral=#{s.get('activeLedIdx')} | LED Shoot=#{s.get('shootLedIdx')} | Buzzer={s.get('buzzerActive')}")
                    print(f"  LCD1: {s.get('lcd_line1')} | LCD2: {s.get('lcd_line2')}")
            elif choice in cmd_lookup:
                payload = json.dumps(cmd_lookup[choice])
                client.publish(topic_cmd, payload)
                print(f"  -> Dikirim ke {topic_cmd}: {payload}")
                time.sleep(0.35)
                s = stats["last_state"]
                if s and s.get("logs"):
                    print(f"  <- Respons Log Daemon: {s['logs'][0]}")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
