#!/usr/bin/env python3
"""
AGEN AUTO-LINK & TELEMETRI JARINGAN RASPBERRY PI 3B+ -> MINI PC (100% WI-FI)
============================================================================
Penanggung Jawab : Divisi 1 (Ketua / Core Raspi Backend & Integrator)
File             : tools/raspi_auto_link.py

Fungsi Utama:
1. Berjalan otomatis di background Raspberry Pi (via systemd `decy13-autolink.service`)
   TANPA memerlukan kabel Ethernet (menghindari brown-out / drop tegangan LAN7515).
2. Menangkap sinyal pencarian dari Mini PC (`tools/minipc_control_hub.py`) di jaringan
   Wi-Fi / Hotspot mana pun (UDP Port 51313) dan aktif mengirim sinyal beacon ke
   Mini PC (UDP Port 51314), sehingga Mini PC otomatis mengetahui IP Wi-Fi Raspi
   saat ini walaupun IP berubah-ubah.
3. Melaporkan status real-time ke terminal Mini PC:
   - IP Wi-Fi aktif, SSID Wi-Fi, Hostname, & Username SSH (`sp-aksel`)
   - Endpoint siap pakai: `ws://<IP_RPI>:9001` & `<IP_RPI>:1883`
   - Status Mosquitto (`1883`/`9001`), Core Daemon (`04_decy13_mqtt_daemon.py`),
     dan Hub 3-TFT USB (`accelerator_hub.py`)
   - Kesehatan catu daya 5V (`vcgencmd get_throttled`) & suhu CPU Raspi.

Cara pakai di Raspberry Pi:
  python3 tools/raspi_auto_link.py --status        # Cek status 1x di terminal
  sudo python3 tools/raspi_auto_link.py --disable-eth  # Matikan eth0 (hemat daya)
  python3 tools/raspi_auto_link.py                 # Mode daemon (dipanggil systemd)
"""

import argparse
import getpass
import json
import os
import socket
import subprocess
import sys
import time
from typing import Any, Dict, List

DISCOVERY_PORT = 51313
BEACON_PORT = 51314
LAST_PC_FILE = "/tmp/decy13_last_minipc.json"


def _run_cmd(cmd: List[str], timeout: float = 2.0) -> str:
    try:
        out = subprocess.check_output(
            cmd,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
            text=True,
        )
        return out.strip()
    except Exception:
        return ""


def _check_tcp_local(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.35):
            return True
    except OSError:
        return False


def _detect_target_user() -> str:
    for env_key in ("SUDO_USER", "USER", "LOGNAME"):
        val = os.environ.get(env_key, "").strip()
        if val and val != "root":
            return val
    if os.path.isdir("/home/sp-aksel"):
        return "sp-aksel"
    try:
        entries = [
            d for d in os.listdir("/home")
            if os.path.isdir(os.path.join("/home", d))
        ]
        if entries:
            return sorted(entries)[0]
    except Exception:
        pass
    try:
        return getpass.getuser()
    except Exception:
        return "sp-aksel"


def _get_ip_facing(target_ip: str = "8.8.8.8") -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.3)
        s.connect((target_ip, 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and not ip.startswith("127."):
            return ip
    except Exception:
        pass
    ips = _get_all_ips()
    return ips[0] if ips else "127.0.0.1"


def _get_all_ips() -> List[str]:
    raw = _run_cmd(["hostname", "-I"])
    ips: List[str] = []
    for token in raw.split():
        if "." in token and not token.startswith("127."):
            ips.append(token)
    if not ips:
        try:
            hn = socket.gethostname()
            for info in socket.getaddrinfo(hn, None, socket.AF_INET):
                addr = info[4][0]
                if not addr.startswith("127.") and addr not in ips:
                    ips.append(addr)
        except Exception:
            pass
    return ips


def _get_wifi_ssid() -> str:
    ssid = _run_cmd(["iwgetid", "-r"])
    if ssid:
        return ssid
    out = _run_cmd(["nmcli", "-t", "-f", "ACTIVE,SSID", "dev", "wifi"])
    for line in out.splitlines():
        if line.startswith("yes:") or line.startswith("ya:"):
            return line.split(":", 1)[1].strip()
    return "Wi-Fi / Hotspot"


def _get_eth0_state() -> str:
    out = _run_cmd(["nmcli", "-t", "-f", "DEVICE,STATE", "dev", "status"])
    for line in out.splitlines():
        if line.startswith("eth0:"):
            return line.split(":", 1)[1].strip()
    oper = "/sys/class/net/eth0/operstate"
    if os.path.isfile(oper):
        try:
            with open(oper, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            pass
    return "unknown"


def _decode_throttled() -> Dict[str, Any]:
    raw = _run_cmd(["vcgencmd", "get_throttled"])
    if not raw or "=" not in raw:
        return {
            "raw": "N/A",
            "ok": True,
            "note": "Sensor vcgencmd tidak tersedia (atau bukan OS RPi)",
        }
    hex_str = raw.split("=", 1)[1].strip()
    try:
        val = int(hex_str, 16)
    except ValueError:
        return {"raw": hex_str, "ok": True, "note": hex_str}

    if val == 0:
        return {
            "raw": hex_str,
            "ok": True,
            "note": "0x0 (Tegangan 5V Stabil / Normal)",
        }

    notes = []
    if val & 0x1:
        notes.append("UNDER-VOLTAGE SAAT INI (<4.63V)")
    if val & 0x10000:
        notes.append("Pernah Under-Voltage sejak boot")
    if val & 0x2:
        notes.append("ARM Freq Capped")
    if val & 0x4:
        notes.append("Throttled")
    return {
        "raw": hex_str,
        "ok": not bool(val & 0x1),
        "note": f"{hex_str} ({', '.join(notes) or 'Periksa PSU 5V RPi'})",
    }


def _get_cpu_temp_c() -> float:
    tpath = "/sys/class/thermal/thermal_zone0/temp"
    if os.path.isfile(tpath):
        try:
            with open(tpath, "r", encoding="utf-8") as f:
                return round(int(f.read().strip()) / 1000.0, 1)
        except Exception:
            pass
    return 0.0


def _is_proc_running(pattern: str) -> bool:
    try:
        res = subprocess.run(
            ["pgrep", "-f", pattern],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=1.5,
        )
        return res.returncode == 0
    except Exception:
        return False


def build_status_payload(target_pc_ip: str = "") -> Dict[str, Any]:
    primary_ip = _get_ip_facing(target_pc_ip if target_pc_ip else "8.8.8.8")
    th = _decode_throttled()
    return {
        "type": "DECY13_RPI_STATUS",
        "ts": int(time.time()),
        "hostname": socket.gethostname(),
        "user": _detect_target_user(),
        "wifi_ip": primary_ip,
        "all_ips": _get_all_ips(),
        "wifi_ssid": _get_wifi_ssid(),
        "eth0_state": _get_eth0_state(),
        "mosquitto_1883": _check_tcp_local(1883),
        "mosquitto_9001": _check_tcp_local(9001),
        "daemon_active": _is_proc_running("04_decy13_mqtt_daemon.py"),
        "usb_hub_active": _is_proc_running("accelerator_hub.py"),
        "simulator_div6_active": _is_proc_running("decy13_simulator_divisi6.py"),
        "throttled_raw": th["raw"],
        "throttled_ok": th["ok"],
        "throttled_note": th["note"],
        "cpu_temp_c": _get_cpu_temp_c(),
        "ws_url": f"ws://{primary_ip}:9001",
        "mqtt_tcp": f"{primary_ip}:1883",
        "last_minipc_ip": target_pc_ip,
    }


def disable_ethernet_power_save() -> None:
    print("[..] Menonaktifkan profil LAN & memutus eth0 agar RPi hemat daya (100% Wi-Fi)...")
    subprocess.run(
        ["sudo", "nmcli", "con", "mod", "lan-minipc", "connection.autoconnect", "no"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        ["sudo", "nmcli", "con", "down", "lan-minipc"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        ["sudo", "nmcli", "dev", "disconnect", "eth0"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print("[OK] Ethernet (eth0) dinonaktifkan. RPi sekarang berjalan 100% via Wi-Fi.")


def _save_last_pc(pc_ip: str, pc_host: str = "") -> None:
    try:
        with open(LAST_PC_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {"pc_ip": pc_ip, "pc_host": pc_host, "ts": int(time.time())},
                f,
            )
    except Exception:
        pass


def _load_last_pc() -> str:
    try:
        if os.path.isfile(LAST_PC_FILE):
            with open(LAST_PC_FILE, "r", encoding="utf-8") as f:
                return str(json.load(f).get("pc_ip", "")).strip()
    except Exception:
        pass
    return ""


def run_agent_loop() -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(("0.0.0.0", DISCOVERY_PORT))
    sock.settimeout(1.5)

    print("==================================================================")
    print("  DECY-13 RASPI AUTO-LINK AGENT AKTIF (100% WI-FI DISCOVERY)")
    print(f"  Mendengarkan Mini PC di UDP :{DISCOVERY_PORT} & Beacon :{BEACON_PORT}")
    print("==================================================================")

    last_beacon = 0.0
    known_pc_ip = _load_last_pc()

    while True:
        try:
            data, addr = sock.recvfrom(4096)
            sender_ip, sender_port = addr[0], addr[1]
            text = data.decode("utf-8", errors="ignore").strip()
            pc_host = ""
            is_probe = False
            if "DECY13_DISCOVER" in text or "DECY13_WHOIS" in text:
                is_probe = True
                try:
                    obj = json.loads(text)
                    pc_host = str(obj.get("pc_host", ""))
                except Exception:
                    pass

            if is_probe:
                known_pc_ip = sender_ip
                _save_last_pc(known_pc_ip, pc_host)
                payload = json.dumps(build_status_payload(known_pc_ip)).encode("utf-8")
                # Balas langsung ke port pengirim Mini PC (otomatis tembus Windows Firewall)
                sock.sendto(payload, (sender_ip, sender_port))
                # Kirim juga ke port beacon Mini PC
                try:
                    sock.sendto(payload, (sender_ip, BEACON_PORT))
                except Exception:
                    pass
        except socket.timeout:
            pass
        except KeyboardInterrupt:
            print("\n[INFO] Agen Auto-Link dihentikan.")
            break
        except Exception:
            time.sleep(0.5)

        now = time.time()
        if now - last_beacon >= 3.0:
            last_beacon = now
            try:
                payload = json.dumps(build_status_payload(known_pc_ip)).encode("utf-8")
                targets = {"255.255.255.255"}
                for ip in _get_all_ips():
                    parts = ip.split(".")
                    if len(parts) == 4:
                        targets.add(f"{parts[0]}.{parts[1]}.{parts[2]}.255")
                if known_pc_ip:
                    targets.add(known_pc_ip)
                for tgt in targets:
                    try:
                        sock.sendto(payload, (tgt, BEACON_PORT))
                    except Exception:
                        pass
            except Exception:
                pass


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Agen Auto-Link & Discovery Raspberry Pi 3B+ -> Mini PC (100% Wi-Fi)"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Tampilkan status jaringan, layanan MQTT, & tegangan RPi 1x lalu keluar",
    )
    parser.add_argument(
        "--disable-eth",
        action="store_true",
        help="Matikan profil Ethernet (eth0) agar RPi hemat daya & hanya memakai Wi-Fi",
    )
    args = parser.parse_args()

    if args.disable_eth:
        disable_ethernet_power_save()
        if not args.status:
            return

    if args.status:
        st = build_status_payload(_load_last_pc())
        print(json.dumps(st, indent=2, ensure_ascii=False))
        return

    run_agent_loop()


if __name__ == "__main__":
    main()
