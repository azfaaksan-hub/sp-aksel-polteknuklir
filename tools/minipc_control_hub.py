#!/usr/bin/env python3
"""
PUSAT KENDALI & AUTO-DISCOVERY MINI PC <-> RASPBERRY PI 3B+ (100% WI-FI, 0 ETHERNET)
====================================================================================
Penanggung Jawab : Divisi 1 (Ketua / Core Raspi Backend & Integrator)
File             : tools/minipc_control_hub.py

Fungsi Utama:
1. Menemukan IP Wi-Fi Raspberry Pi (`sp-aksel`) secara OTOMATIS di jaringan Wi-Fi /
   Hotspot mana pun tanpa perlu kabel Ethernet dan tanpa perlu mencari IP manual:
   - Metode 1 (Instan <1 detik): UDP Auto-Link Discovery (`port 51313`) membaca
     telemetri lengkap dari `tools/raspi_auto_link.py` di Raspi.
   - Metode 2 (Fallback otomatis ~1.5 detik): Paralel TCP scan port 22/1883/9001
     pada subnet Wi-Fi Mini PC (tetap berhasil walau `decy13-autolink` belum dipasang!).
2. Memungkinkan operator mengatur & mengendalikan Raspi langsung dari PowerShell Mini PC:
   - [1] Buka Terminal SSH Raspi otomatis (kompatibel Windows 8/10/11 & Git SSH)
   - [2] Auto-Setup / Restart Daemon Raspi + Matikan Ethernet `eth0` (anti drop daya)
   - [3] Start / Restart Hub 3-TFT USB (`accelerator_hub.py`) di Raspi
   - [4] Tambah / Simpan Wi-Fi baru di Raspi langsung dari Mini PC
   - [5] Jalankan Server Web HMI Offline (anti 404) + Auto-Copy `ws://<IP>:9001` + Buka Browser
   - [6] Jalankan Uji QA (`06_test_mqtt_healthcheck.py`) ke Raspi

Cara pakai di PowerShell Mini PC:
  python tools/minipc_control_hub.py
  python tools/minipc_control_hub.py --scan-only
"""

import argparse
import functools
import http.server
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

DISCOVERY_PORT = 51313
BEACON_PORT = 51314

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
WEB_HMI_DIR = os.path.join(REPO_ROOT, "decy13_mqtt_kit", "web_hmi")
HEALTHCHECK_SCRIPT = os.path.join(
    REPO_ROOT, "decy13_mqtt_kit", "raspi_cli", "06_test_mqtt_healthcheck.py"
)

_HTTP_SERVER_STARTED = False
_HTTP_PORT = 8000


def _find_ssh_binary() -> str:
    ssh_path = shutil.which("ssh")
    if ssh_path:
        return ssh_path
    candidates = [
        r"C:\Program Files\Git\usr\bin\ssh.exe",
        r"C:\Program Files (x86)\Git\usr\bin\ssh.exe",
        r"C:\Windows\System32\OpenSSH\ssh.exe",
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return "ssh"


def _get_local_ipv4_list() -> List[str]:
    ips: List[str] = []
    try:
        hn = socket.gethostname()
        for info in socket.getaddrinfo(hn, None, socket.AF_INET):
            addr = info[4][0]
            if not addr.startswith("127.") and addr not in ips:
                ips.append(addr)
    except Exception:
        pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.3)
        s.connect(("8.8.8.8", 80))
        primary = s.getsockname()[0]
        s.close()
        if primary and not primary.startswith("127.") and primary not in ips:
            ips.insert(0, primary)
    except Exception:
        pass
    return ips


def _copy_to_clipboard(text: str) -> bool:
    if os.name == "nt":
        try:
            p = subprocess.Popen(["clip"], stdin=subprocess.PIPE)
            p.communicate(input=text.encode("utf-8"))
            return p.returncode == 0
        except Exception:
            return False
    return False


def _stop_windows_mosquitto() -> None:
    if os.name == "nt":
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Stop-Service mosquitto -ErrorAction SilentlyContinue"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def discover_via_udp(timeout: float = 2.0) -> Optional[Dict[str, Any]]:
    """Kirim probe UDP ke port 51313 dan tunggu balasan JSON dari raspi_auto_link.py."""
    local_ips = _get_local_ipv4_list()
    targets = {"255.255.255.255"}
    for ip in local_ips:
        parts = ip.split(".")
        if len(parts) == 4:
            targets.add(f"{parts[0]}.{parts[1]}.{parts[2]}.255")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(0.4)

    probe = json.dumps({
        "cmd": "DECY13_DISCOVER",
        "pc_host": socket.gethostname(),
        "pc_ips": local_ips,
        "ts": int(time.time()),
    }).encode("utf-8")

    deadline = time.time() + timeout
    try:
        while time.time() < deadline:
            for tgt in targets:
                try:
                    sock.sendto(probe, (tgt, DISCOVERY_PORT))
                except Exception:
                    pass
            try:
                data, addr = sock.recvfrom(4096)
                obj = json.loads(data.decode("utf-8", errors="ignore"))
                if isinstance(obj, dict) and obj.get("type") == "DECY13_RPI_STATUS":
                    if not obj.get("wifi_ip") or obj.get("wifi_ip") == "127.0.0.1":
                        obj["wifi_ip"] = addr[0]
                        obj["ws_url"] = f"ws://{addr[0]}:9001"
                        obj["mqtt_tcp"] = f"{addr[0]}:1883"
                    obj["discovery_method"] = "UDP Auto-Link (51313)"
                    return obj
            except socket.timeout:
                continue
            except Exception:
                continue
    finally:
        sock.close()
    return None


def _probe_host_ports(ip: str) -> Optional[Tuple[str, bool, bool, bool]]:
    """Cek cepat apakah suatu IP di subnet membuka port 22 (SSH) + 1883/9001 (MQTT)."""
    def _is_open(p: int, to: float = 0.28) -> bool:
        try:
            with socket.create_connection((ip, p), timeout=to):
                return True
        except OSError:
            return False

    p1883 = _is_open(1883, 0.25)
    p9001 = _is_open(9001, 0.25)
    p22 = _is_open(22, 0.28)
    if p22 or p1883 or p9001:
        return (ip, p22, p1883, p9001)
    return None


def discover_via_subnet_scan() -> Optional[Dict[str, Any]]:
    """Fallback: scan cepat port 22/1883/9001 di subnet Wi-Fi aktif bila UDP diblokir hotspot."""
    local_ips = _get_local_ipv4_list()
    candidates: List[str] = []
    for lip in local_ips:
        parts = lip.split(".")
        if len(parts) != 4:
            continue
        prefix = f"{parts[0]}.{parts[1]}.{parts[2]}."
        for host_id in range(1, 255):
            cip = f"{prefix}{host_id}"
            if cip != lip and cip not in candidates:
                candidates.append(cip)

    if not candidates:
        return None

    best: Optional[Tuple[str, bool, bool, bool]] = None
    with ThreadPoolExecutor(max_workers=48) as pool:
        futs = [pool.submit(_probe_host_ports, c) for c in candidates]
        for f in as_completed(futs):
            res = f.result()
            if res is not None:
                ip, p22, p1883, p9001 = res
                # Prioritaskan host yang membuka SSH (22) sekaligus Mosquitto (1883/9001)
                if p22 and (p1883 or p9001):
                    best = res
                    break
                if best is None or (p22 and not best[1]):
                    best = res

    if best is None:
        return None

    ip, p22, p1883, p9001 = best
    return {
        "type": "DECY13_RPI_STATUS",
        "hostname": "sp-aksel (terdeteksi via TCP Scan)",
        "user": "sp-aksel",
        "wifi_ip": ip,
        "all_ips": [ip],
        "wifi_ssid": "Jaringan Wi-Fi / Hotspot Sama",
        "eth0_state": "tidak dipakai (Wi-Fi mode)",
        "mosquitto_1883": p1883,
        "mosquitto_9001": p9001,
        "daemon_active": p1883 and p9001,
        "usb_hub_active": False,
        "throttled_note": "Jalankan menu [2] untuk mengaktifkan agen Auto-Link penuh",
        "cpu_temp_c": 0.0,
        "ws_url": f"ws://{ip}:9001",
        "mqtt_tcp": f"{ip}:1883",
        "discovery_method": "TCP Subnet Scan (Port 22/1883/9001)",
    }


def find_raspberry_pi() -> Optional[Dict[str, Any]]:
    print("\n[..] Mencari Raspberry Pi di jaringan Wi-Fi / Hotspot...")
    st = discover_via_udp(timeout=2.0)
    if st is not None:
        return st
    print("[..] Beacon UDP belum merespons, memindai cepat port SSH/MQTT di subnet Wi-Fi...")
    return discover_via_subnet_scan()


def start_local_web_hmi_server() -> str:
    global _HTTP_SERVER_STARTED, _HTTP_PORT
    if not os.path.isdir(WEB_HMI_DIR):
        raise FileNotFoundError(f"Folder Web HMI tidak ditemukan: {WEB_HMI_DIR}")

    if not _HTTP_SERVER_STARTED:
        handler = functools.partial(
            http.server.SimpleHTTPRequestHandler,
            directory=WEB_HMI_DIR,
        )

        class _QuietServer(http.server.ThreadingHTTPServer):
            allow_reuse_address = True

        for port in (8000, 8080, 8888):
            try:
                httpd = _QuietServer(("127.0.0.1", port), handler)
                _HTTP_PORT = port
                t = threading.Thread(target=httpd.serve_forever, daemon=True)
                t.start()
                _HTTP_SERVER_STARTED = True
                break
            except OSError:
                continue

    return f"http://127.0.0.1:{_HTTP_PORT}"


def _run_ssh_command(ssh_bin: str, user: str, ip: str, remote_cmd: str) -> int:
    print(f"\n[SSH -> {user}@{ip}] Menjalankan:\n  {remote_cmd}\n")
    return subprocess.call([ssh_bin, "-t", f"{user}@{ip}", remote_cmd])


def print_dashboard(st: Optional[Dict[str, Any]], local_ips: List[str]) -> None:
    print("\n" + "=" * 74)
    print("  PUSAT KENDALI MINI PC <-> RASPBERRY PI 3B+ (100% WI-FI • TANPA ETHERNET)")
    print("=" * 74)
    print(f"  IP Wi-Fi Mini PC : {', '.join(local_ips) if local_ips else 'Tidak terdeteksi'}")
    if st is None:
        print("  Status Raspi     : [BELUM TERDETEKSI DI WI-FI INI]")
        print("  Pastikan Mini PC & Raspi terhubung ke Wi-Fi / Hotspot HP yang sama,")
        print("  lalu tekan [R] untuk scan ulang atau [M] untuk input IP Raspi manual.")
    else:
        ip = st.get("wifi_ip", "?")
        user = st.get("user", "sp-aksel")
        ssid = st.get("wifi_ssid", "?")
        m1883 = "AKTIF" if st.get("mosquitto_1883") else "MATI"
        m9001 = "AKTIF" if st.get("mosquitto_9001") else "MATI"
        d_act = "AKTIF" if st.get("daemon_active") else "BELUM JALAN"
        u_act = "AKTIF" if st.get("usb_hub_active") else "BELUM JALAN"
        temp = st.get("cpu_temp_c", 0.0)
        temp_str = f"{temp} C" if temp else "-"
        print(f"  Status Raspi     : [ONLINE] via {st.get('discovery_method', 'Wi-Fi')}")
        print(f"  Identitas & Wi-Fi: {user}@{st.get('hostname', 'sp-aksel')}  |  SSID: {ssid}")
        print(f"  IP Wi-Fi Raspi   : {ip}  (Semua IP: {', '.join(st.get('all_ips', [ip]))})")
        print(f"  URL Web HMI      : {st.get('ws_url', f'ws://{ip}:9001')}   <-- pakai di Developer Menu")
        print(f"  Broker Node-RED  : {st.get('mqtt_tcp', f'{ip}:1883')}")
        print(f"  Layanan Raspi    : Mosquitto 1883={m1883}, 9001={m9001} | Daemon={d_act} | USB-Hub={u_act}")
        print(f"  Daya 5V & Suhu   : {st.get('throttled_note', '-')} | CPU: {temp_str} | eth0: {st.get('eth0_state', '-')}")
    print("-" * 74)
    print("  [1] Buka Terminal SSH Raspi otomatis (tanpa ketik IP)")
    print("  [2] Auto-Setup & Nyalakan Semua di Raspi (Update + Matikan eth0 + Auto-Start Daemon)")
    print("  [3] Nyalakan / Restart Hub 3-TFT Arduino Uno (accelerator_hub.py) di Raspi")
    print("  [4] Tambah / Simpan Wi-Fi Baru di Raspi langsung dari Mini PC")
    print("  [5] Buka Web HMI Offline (http://127.0.0.1:8000) + Auto-Copy ws://<IP_RASPI>:9001")
    print("  [6] Jalankan Uji QA Healthcheck (06_test_mqtt_healthcheck.py) ke Raspi")
    print("  [R] Scan Ulang IP Raspi   |   [M] Input IP Raspi Manual   |   [Q] Keluar")
    print("=" * 74)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pusat Kendali & Auto-Discovery Mini PC <-> Raspberry Pi 3B+ (100% Wi-Fi)"
    )
    parser.add_argument(
        "--scan-only",
        action="store_true",
        help="Cari Raspberry Pi 1x, tampilkan hasil JSON/status, lalu keluar",
    )
    args = parser.parse_args()

    _stop_windows_mosquitto()
    st = find_raspberry_pi()

    if args.scan_only:
        if st:
            print(json.dumps(st, indent=2, ensure_ascii=False))
            sys.exit(0)
        print("[INFO] Raspberry Pi belum ditemukan di subnet aktif saat ini.")
        sys.exit(0)

    ssh_bin = _find_ssh_binary()

    while True:
        local_ips = _get_local_ipv4_list()
        print_dashboard(st, local_ips)
        try:
            choice = input("Pilih menu [1-6 / R / M / Q]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nKeluar.")
            break

        if choice == "q":
            break
        elif choice == "r":
            st = find_raspberry_pi()
            continue
        elif choice == "m":
            ip_in = input("Masukkan IP Wi-Fi Raspi (contoh 10.211.191.158): ").strip()
            if ip_in:
                user_in = input("Username SSH Raspi [default: sp-aksel]: ").strip() or "sp-aksel"
                st = {
                    "type": "DECY13_RPI_STATUS",
                    "hostname": "sp-aksel",
                    "user": user_in,
                    "wifi_ip": ip_in,
                    "all_ips": [ip_in],
                    "wifi_ssid": "Input Manual",
                    "eth0_state": "-",
                    "mosquitto_1883": True,
                    "mosquitto_9001": True,
                    "daemon_active": False,
                    "usb_hub_active": False,
                    "throttled_note": "-",
                    "cpu_temp_c": 0.0,
                    "ws_url": f"ws://{ip_in}:9001",
                    "mqtt_tcp": f"{ip_in}:1883",
                    "discovery_method": "Manual Input",
                }
            continue

        if choice == "5":
            url = start_local_web_hmi_server()
            ws_endpoint = st.get("ws_url", "ws://127.0.0.1:9001") if st else "ws://127.0.0.1:9001"
            copied = _copy_to_clipboard(ws_endpoint)
            print(f"\n[OK] Server Web HMI Offline aktif di: {url}")
            if copied:
                print(f"[OK] Endpoint '{ws_endpoint}' SUDAH DISALIN ke Clipboard!")
                print("     Di browser -> klik 'Developer Menu' -> paste (Ctrl+V) di kotak WebSocket -> klik 'Hubungkan MQTT'!")
            else:
                print(f"[INFO] Isi kotak WebSocket di Developer Menu dengan: {ws_endpoint}")
            webbrowser.open(url)
            input("\nTekan Enter untuk kembali ke menu...")
            continue

        if st is None:
            print("\n[!] Raspi belum terdeteksi. Tekan [R] untuk scan atau [M] untuk isi IP dulu.")
            time.sleep(1.2)
            continue

        ip = str(st.get("wifi_ip", "")).strip()
        user = str(st.get("user", "sp-aksel")).strip() or "sp-aksel"

        if choice == "1":
            print(f"\n[..] Membuka sesi SSH interaktif ke {user}@{ip} (ketik 'exit' untuk kembali ke menu Mini PC)...")
            subprocess.call([ssh_bin, f"{user}@{ip}"])
            st = discover_via_udp(timeout=1.5) or st
        elif choice == "2":
            _stop_windows_mosquitto()
            remote_cmd = (
                "REPO_DIR=$( [ -d ~/decy13/.git ] && echo ~/decy13 || echo ~/sp-aksel-polteknuklir ); "
                "cd \"$REPO_DIR\" && git fetch origin && git checkout main && git reset --hard origin/main && "
                "(pkill -f decy13_simulator_divisi6.py 2>/dev/null || true) && "
                "bash tools/raspi_bootstrap.sh --install-service --install-autolink --install-usb-service --disable-eth && "
                "sudo systemctl restart decy13-autolink.service decy13.service decy13-usb-hub.service && "
                "python3 tools/raspi_auto_link.py --status"
            )
            _run_ssh_command(ssh_bin, user, ip, remote_cmd)
            st = discover_via_udp(timeout=2.0) or st
            input("\nTekan Enter untuk kembali ke menu...")
        elif choice == "3":
            remote_cmd = (
                "if systemctl list-unit-files | grep -q decy13-usb-hub.service; then "
                "sudo systemctl restart decy13-usb-hub.service && sleep 3 && "
                "sudo journalctl -u decy13-usb-hub.service -n 20 --no-pager; "
                "else "
                "REPO_DIR=$( [ -d ~/decy13/AKSEL-DECY13 ] && echo ~/decy13/AKSEL-DECY13 || echo ~/sp-aksel-polteknuklir/AKSEL-DECY13 ); "
                "cd \"$REPO_DIR\" && sudo apt install -y python3-serial python3-paho-mqtt && "
                "python3 raspi/accelerator_hub.py --mqtt-host 127.0.0.1 --mqtt-port 1883 --mqtt-control; "
                "fi"
            )
            _run_ssh_command(ssh_bin, user, ip, remote_cmd)
            st = discover_via_udp(timeout=1.5) or st
            input("\nTekan Enter untuk kembali ke menu...")
        elif choice == "4":
            ssid_new = input("Masukkan Nama Wi-Fi / Hotspot baru untuk Raspi: ").strip()
            if ssid_new:
                pass_new = input(f"Masukkan Password Wi-Fi '{ssid_new}': ").strip()
                safe_ssid = ssid_new.replace('"', '\\"')
                safe_pass = pass_new.replace('"', '\\"')
                remote_cmd = (
                    f'sudo nmcli dev wifi rescan 2>/dev/null || true; sleep 2; '
                    f'sudo nmcli dev wifi connect "{safe_ssid}" password "{safe_pass}" && '
                    f'nmcli -t -f NAME,TYPE,AUTOCONNECT con show'
                )
                _run_ssh_command(ssh_bin, user, ip, remote_cmd)
                st = discover_via_udp(timeout=2.0) or st
                input("\nTekan Enter untuk kembali ke menu...")
        elif choice == "6":
            if os.path.isfile(HEALTHCHECK_SCRIPT):
                subprocess.call([sys.executable, HEALTHCHECK_SCRIPT, "--host", ip, "--duration", "10", "--no-menu"])
            else:
                print(f"[!] File tidak ditemukan: {HEALTHCHECK_SCRIPT}")
            input("\nTekan Enter untuk kembali ke menu...")


if __name__ == "__main__":
    main()
