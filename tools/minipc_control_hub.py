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
2. Menyediakan jembatan konfigurasi otomatis (`/api/runtime-config` & `/api/rescan`)
   agar Web HMI (`index.html`) otomatis menerima IP Raspi (`ws://<IP>:9001`) dan
   langsung auto-connect ke broker MQTT tanpa perlu copy-paste manual.
3. Memungkinkan operator mengatur & mengendalikan Raspi langsung dari CMD/PowerShell:
   - [1] Buka Terminal SSH Raspi otomatis (kompatibel Windows 8/10/11 & Git SSH)
   - [2] Auto-Setup / Restart Daemon Raspi + Matikan Ethernet `eth0` (anti drop daya)
   - [3] Start / Restart Hub 3-TFT USB (`accelerator_hub.py`) di Raspi
   - [4] Tambah / Simpan Wi-Fi baru di Raspi langsung dari Mini PC
   - [5] Jalankan Server Web HMI Offline + Auto-Sync Konfigurasi ke HTML + Buka Browser
   - [6] Jalankan Uji QA (`06_test_mqtt_healthcheck.py`) ke Raspi
   - [W] Buka Program Konfigurasi Awal (Startup Wizard: Auto-Setup / Panduan Wi-Fi)

Cara pakai di CMD / PowerShell Mini PC:
  python tools/minipc_control_hub.py
  python tools/minipc_control_hub.py --scan-only
"""

import argparse
import http.server
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.parse
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
RUNTIME_CACHE_DIR = os.path.join(REPO_ROOT, "laporan_uji", "backup_lokal")
RUNTIME_CACHE_FILE = os.path.join(RUNTIME_CACHE_DIR, "runtime_hmi_config.json")

_HTTP_SERVER_STARTED = False
_HTTP_PORT = 8000
_WATCHER_STARTED = False
_RUNTIME_LOCK = threading.Lock()
_RUNTIME_CONFIG: Dict[str, Any] = {
    "ok": True,
    "updatedAt": int(time.time()),
    "mode": "simulation",
    "autoConnect": False,
    "wsUrl": "ws://127.0.0.1:9001",
    "mqttTcp": "127.0.0.1:1883",
    "topicCmd": "decy13/hmi/cmd",
    "topicState": "decy13/rpi/state",
    "pcWifiSsid": "",
    "pcIps": [],
    "raspi": {
        "detected": False,
        "ip": "",
        "hostname": "",
        "user": "sp-aksel",
        "wifiSsid": "",
        "discoveryMethod": "",
        "mosquitto1883": False,
        "mosquitto9001": False,
        "daemonActive": False,
        "usbHubActive": False,
        "throttledNote": "-",
        "cpuTempC": 0.0,
    },
    "instructor": {
        "enabled": True,
        "loopOnComplete": True,
        "loopDelaySec": 8,
        "idleResetSec": 60,
    },
}


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


def get_windows_wifi_info() -> Dict[str, str]:
    """Baca status adapter Wi-Fi Mini PC Windows (SSID, State, Signal)."""
    info = {"connected": "false", "ssid": "", "state": " tidak terdeteksi", "signal": ""}
    if os.name != "nt":
        return info
    try:
        out = subprocess.check_output(
            ["netsh", "wlan", "show", "interfaces"],
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
        for raw in out.splitlines():
            line = raw.strip()
            if ":" not in line:
                continue
            k, v = [x.strip() for x in line.split(":", 1)]
            kl = k.lower()
            if kl == "state" or "status" in kl:
                info["state"] = v
                if "connected" in v.lower() or "terhubung" in v.lower():
                    info["connected"] = "true"
            elif kl == "ssid" and not kl.startswith("bssid"):
                info["ssid"] = v
            elif "signal" in kl or "sinyal" in kl:
                info["signal"] = v
    except Exception:
        pass
    return info


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


def is_windows_mosquitto_running() -> bool:
    if os.name != "nt":
        return False
    try:
        res = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "$s = Get-Service -Name mosquitto -ErrorAction SilentlyContinue; if ($s -and $s.Status -eq 'Running') { exit 0 } else { exit 1 }",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return res.returncode == 0
    except Exception:
        return False


def _stop_windows_mosquitto(allow_uac: bool = False) -> bool:
    """Hentikan service Mosquitto Windows agar tidak bentrok dengan broker Raspi."""
    if os.name != "nt":
        return True
    if not is_windows_mosquitto_running():
        return True
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", "Stop-Service mosquitto -Force -ErrorAction SilentlyContinue"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if not is_windows_mosquitto_running():
        return True
    if allow_uac:
        print("[..] Meminta izin Administrator untuk menghentikan Mosquitto lokal Windows...")
        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Start-Process powershell -Verb RunAs -Wait -WindowStyle Hidden -ArgumentList '-NoProfile -Command Stop-Service mosquitto -Force'",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    return not is_windows_mosquitto_running()


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
        # Prioritaskan .158 (kebiasaan DHCP Hotspot Android pada unit RPi tim) di urutan depan
        if f"{prefix}158" != lip:
            candidates.append(f"{prefix}158")
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
        "throttled_note": "Jalankan Auto-Setup untuk mengaktifkan agen Auto-Link penuh",
        "cpu_temp_c": 0.0,
        "ws_url": f"ws://{ip}:9001",
        "mqtt_tcp": f"{ip}:1883",
        "discovery_method": "TCP Subnet Scan (Port 22/1883/9001)",
    }


def find_raspberry_pi(quiet: bool = False) -> Optional[Dict[str, Any]]:
    if not quiet:
        print("\n[..] Mencari Raspberry Pi di jaringan Wi-Fi / Hotspot...")
    st = discover_via_udp(timeout=1.8)
    if st is not None:
        update_runtime_config_from_rpi(st)
        return st
    if not quiet:
        print("[..] Beacon UDP belum merespons, memindai cepat port SSH/MQTT di subnet Wi-Fi...")
    st = discover_via_subnet_scan()
    if st is not None:
        update_runtime_config_from_rpi(st)
    return st


def update_runtime_config_from_rpi(
    st: Optional[Dict[str, Any]],
    mode_override: Optional[str] = None,
    auto_connect: Optional[bool] = None,
    instructor_opts: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Perbarui state konfigurasi bersama yang dibaca otomatis oleh Web HMI (`index.html`)."""
    wifi_info = get_windows_wifi_info()
    local_ips = _get_local_ipv4_list()
    with _RUNTIME_LOCK:
        _RUNTIME_CONFIG["updatedAt"] = int(time.time())
        _RUNTIME_CONFIG["pcWifiSsid"] = wifi_info.get("ssid", "")
        _RUNTIME_CONFIG["pcIps"] = local_ips

        if st and st.get("wifi_ip"):
            ip = str(st.get("wifi_ip", "")).strip()
            ws_url = str(st.get("ws_url") or f"ws://{ip}:9001")
            mqtt_tcp = str(st.get("mqtt_tcp") or f"{ip}:1883")
            _RUNTIME_CONFIG["wsUrl"] = ws_url
            _RUNTIME_CONFIG["mqttTcp"] = mqtt_tcp
            _RUNTIME_CONFIG["mode"] = mode_override or "hardware"
            _RUNTIME_CONFIG["autoConnect"] = True if auto_connect is None else bool(auto_connect)
            _RUNTIME_CONFIG["raspi"] = {
                "detected": True,
                "ip": ip,
                "hostname": str(st.get("hostname", "sp-aksel")),
                "user": str(st.get("user", "sp-aksel")),
                "wifiSsid": str(st.get("wifi_ssid", "")),
                "discoveryMethod": str(st.get("discovery_method", "Wi-Fi")),
                "mosquitto1883": bool(st.get("mosquitto_1883", False)),
                "mosquitto9001": bool(st.get("mosquitto_9001", False)),
                "daemonActive": bool(st.get("daemon_active", False)),
                "usbHubActive": bool(st.get("usb_hub_active", False)),
                "throttledNote": str(st.get("throttled_note", "-")),
                "cpuTempC": float(st.get("cpu_temp_c") or 0.0),
            }
        else:
            if mode_override:
                _RUNTIME_CONFIG["mode"] = mode_override
            if auto_connect is not None:
                _RUNTIME_CONFIG["autoConnect"] = bool(auto_connect)
            if mode_override == "simulation":
                _RUNTIME_CONFIG["raspi"]["detected"] = False

        if instructor_opts:
            _RUNTIME_CONFIG["instructor"].update(instructor_opts)

        snapshot = json.loads(json.dumps(_RUNTIME_CONFIG))

    try:
        os.makedirs(RUNTIME_CACHE_DIR, exist_ok=True)
        with open(RUNTIME_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)
    except Exception:
        pass
    return snapshot


def load_cached_runtime_config() -> Dict[str, Any]:
    if os.path.isfile(RUNTIME_CACHE_FILE):
        try:
            with open(RUNTIME_CACHE_FILE, "r", encoding="utf-8") as f:
                cached = json.load(f)
            if isinstance(cached, dict) and cached.get("ok"):
                with _RUNTIME_LOCK:
                    _RUNTIME_CONFIG.update(cached)
        except Exception:
            pass
    with _RUNTIME_LOCK:
        return json.loads(json.dumps(_RUNTIME_CONFIG))


class _DecyWebHmiHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP Handler untuk Web HMI Offline + API sinkronisasi konfigurasi otomatis."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=WEB_HMI_DIR, **kwargs)

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _send_json(self, payload: Dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/runtime-config":
            with _RUNTIME_LOCK:
                data = json.loads(json.dumps(_RUNTIME_CONFIG))
            self._send_json(data)
            return
        super().do_GET()

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/rescan":
            st = discover_via_udp(timeout=1.4) or discover_via_subnet_scan()
            if st is not None:
                cfg = update_runtime_config_from_rpi(st, mode_override="hardware", auto_connect=True)
            else:
                with _RUNTIME_LOCK:
                    _RUNTIME_CONFIG["updatedAt"] = int(time.time())
                    _RUNTIME_CONFIG["raspi"]["detected"] = False
                    cfg = json.loads(json.dumps(_RUNTIME_CONFIG))
            self._send_json(cfg)
            return
        self._send_json({"ok": False, "error": "Endpoint tidak dikenal"}, status=404)


def _background_udp_watcher() -> None:
    """Pantau perubahan IP Wi-Fi Raspi secara ringan lewat UDP Auto-Link setiap 6 detik."""
    while True:
        time.sleep(6.0)
        try:
            st = discover_via_udp(timeout=1.0)
            if st and st.get("wifi_ip"):
                with _RUNTIME_LOCK:
                    cur_mode = _RUNTIME_CONFIG.get("mode", "hardware")
                if cur_mode != "simulation":
                    update_runtime_config_from_rpi(st, mode_override="hardware", auto_connect=True)
        except Exception:
            pass


def _is_port_in_use(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.2):
            return True
    except OSError:
        return False


def start_local_web_hmi_server(start_watcher: bool = True) -> str:
    global _HTTP_SERVER_STARTED, _HTTP_PORT, _WATCHER_STARTED
    if not os.path.isdir(WEB_HMI_DIR):
        raise FileNotFoundError(f"Folder Web HMI tidak ditemukan: {WEB_HMI_DIR}")

    load_cached_runtime_config()

    if not _HTTP_SERVER_STARTED:
        class _ExclusiveServer(http.server.ThreadingHTTPServer):
            # Di Windows, allow_reuse_address=False wajib agar tidak menumpuk di port proses lama
            allow_reuse_address = False

        for port in (8000, 8013, 8080, 8888, 8130):
            if _is_port_in_use(port):
                continue
            try:
                httpd = _ExclusiveServer(("127.0.0.1", port), _DecyWebHmiHandler)
                _HTTP_PORT = port
                t = threading.Thread(target=httpd.serve_forever, daemon=True)
                t.start()
                _HTTP_SERVER_STARTED = True
                break
            except OSError:
                continue

    if start_watcher and not _WATCHER_STARTED:
        wt = threading.Thread(target=_background_udp_watcher, daemon=True)
        wt.start()
        _WATCHER_STARTED = True

    return f"http://127.0.0.1:{_HTTP_PORT}"


def _find_scp_binary() -> str:
    scp_path = shutil.which("scp")
    if scp_path:
        return scp_path
    candidates = [
        r"C:\Program Files\Git\usr\bin\scp.exe",
        r"C:\Program Files (x86)\Git\usr\bin\scp.exe",
        r"C:\Windows\System32\OpenSSH\scp.exe",
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return "scp"


def _run_ssh_command(ssh_bin: str, user: str, ip: str, remote_cmd: str) -> int:
    print(f"\n[SSH -> {user}@{ip}] Menjalankan perintah remote...")
    return subprocess.call([ssh_bin, "-t", f"{user}@{ip}", remote_cmd])


def run_full_raspi_autosetup_ssh(ssh_bin: str, user: str, ip: str) -> int:
    """Update repo Raspi ke origin/main + pasang & restart seluruh 4 service tanpa Ethernet."""
    _stop_windows_mosquitto(allow_uac=True)
    # Gunakan kutip tunggal/aman Windows (hindari \" bersarang yang sering rusak di cmd.exe)
    # Sekaligus cetak commit aktif, log LED daemon, dan status daya 5V secara transparan.
    remote_cmd = (
        "REPO_DIR=~/sp-aksel-polteknuklir; "
        "[ -d ~/decy13/.git ] && REPO_DIR=~/decy13; "
        "cd $REPO_DIR && "
        "(git fetch origin && git checkout main && git reset --hard origin/main || echo '[PERINGATAN] git fetch gagal - lanjut dengan kode yang ada di Raspi') && "
        "git log -1 --oneline && "
        "(pkill -f decy13_simulator_divisi6.py 2>/dev/null || true) && "
        "bash tools/raspi_bootstrap.sh --install-service --install-autolink --install-usb-service --disable-eth && "
        "sudo systemctl restart decy13-autolink.service decy13.service decy13-usb-hub.service && "
        "sleep 2 && "
        "echo '=== LOG HARDWARE DAEMON (LED/RELAY/LCD) ===' && "
        "sudo journalctl -u decy13.service -n 15 --no-pager && "
        "echo '=== STATUS AUTO-LINK & DAYA 5V ===' && "
        "python3 tools/raspi_auto_link.py --status"
    )
    rc = _run_ssh_command(ssh_bin, user, ip, remote_cmd)
    if rc != 0:
        print(f"\n[PERINGATAN] Setup SSH berakhir dengan kode keluar {rc}.")
        print("  Pastikan password SSH 'sp-aksel' benar dan periksa pesan error di atas.")
    return rc


def sync_local_led_files_to_raspi(ssh_bin: str, user: str, ip: str) -> int:
    """Kirim langsung file daemon, LED, & bootstrap dari Mini PC ke Raspi (via scp, tanpa butuh internet di Raspi)."""
    scp_bin = _find_scp_binary()
    daemon_local = os.path.join(REPO_ROOT, "decy13_mqtt_kit", "raspi_cli", "04_decy13_mqtt_daemon.py")
    cfg_local = os.path.join(REPO_ROOT, "decy13_mqtt_kit", "raspi_cli", "config_hardware.json")
    led_local = os.path.join(REPO_ROOT, "decy13_mqtt_kit", "raspi_cli", "modules", "mod_led_ws2812b.py")
    boot_local = os.path.join(REPO_ROOT, "tools", "raspi_bootstrap.sh")
    print(f"\n[SCP -> {user}@{ip}] Mengirim 04_decy13_mqtt_daemon.py, config_hardware.json, mod_led_ws2812b.py, & raspi_bootstrap.sh...")
    rc0 = subprocess.call([scp_bin, daemon_local, f"{user}@{ip}:~/decy13/decy13_mqtt_kit/raspi_cli/04_decy13_mqtt_daemon.py"])
    rc1 = subprocess.call([scp_bin, cfg_local, f"{user}@{ip}:~/decy13/decy13_mqtt_kit/raspi_cli/config_hardware.json"])
    rc2 = subprocess.call([scp_bin, led_local, f"{user}@{ip}:~/decy13/decy13_mqtt_kit/raspi_cli/modules/mod_led_ws2812b.py"])
    rc3 = subprocess.call([scp_bin, boot_local, f"{user}@{ip}:~/decy13/tools/raspi_bootstrap.sh"])
    if rc0 != 0 or rc1 != 0 or rc2 != 0 or rc3 != 0:
        print("[GAGAL] Pengiriman SCP gagal. Periksa koneksi Wi-Fi / password SSH Raspi.")
        return 1
    remote_cmd = (
        "cd ~/decy13 && "
        "sed -i 's/\\r$//' tools/raspi_bootstrap.sh && "
        "bash tools/raspi_bootstrap.sh --install-service --install-autolink --install-usb-service --disable-eth && "
        "sudo systemctl restart decy13-autolink.service decy13.service decy13-usb-hub.service && "
        "sleep 2 && "
        "echo '=== CEK PIN DATA LED GPIO 12 / PIN FISIK 32 (HARUS a0 / PWM0) ===' && "
        "(command -v pinctrl >/dev/null && pinctrl get 12,17,21) || true && "
        "sudo journalctl -u decy13.service -n 18 --no-pager && "
        "vcgencmd get_throttled"
    )
    return _run_ssh_command(ssh_bin, user, ip, remote_cmd)


def print_dashboard(st: Optional[Dict[str, Any]], local_ips: List[str]) -> None:
    wifi_info = get_windows_wifi_info()
    ssid_pc = wifi_info.get("ssid") or "Tidak terdeteksi / Pakai Kabel"
    mosq_win = "MASIH HIDUP (matikan!)" if is_windows_mosquitto_running() else "MATI (Aman)"
    print("\n" + "=" * 76)
    print("  PUSAT KENDALI MINI PC <-> RASPBERRY PI 3B+ (100% WI-FI - TANPA ETHERNET)")
    print("=" * 76)
    print(f"  Wi-Fi Mini PC    : SSID '{ssid_pc}' | IP: {', '.join(local_ips) if local_ips else '-'}")
    print(f"  Mosquitto Lokal  : {mosq_win}")
    if st is None:
        print("  Status Raspi     : [BELUM TERDETEKSI DI WI-FI INI]")
        print("  Pastikan Mini PC & Raspi terhubung ke Wi-Fi / Hotspot HP yang sama,")
        print("  tekan [W] untuk Panduan Wi-Fi Lengkap, [R] scan ulang, atau [M] isi IP.")
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
        print(f"  URL Web HMI      : {st.get('ws_url', f'ws://{ip}:9001')} (Auto-Sync ke HTML aktif)")
        print(f"  Broker Node-RED  : {st.get('mqtt_tcp', f'{ip}:1883')}")
        print(f"  Layanan Raspi    : Mosquitto 1883={m1883}, 9001={m9001} | Daemon={d_act} | USB-Hub={u_act}")
        print(f"  Daya 5V & Suhu   : {st.get('throttled_note', '-')} | CPU: {temp_str} | eth0: {st.get('eth0_state', '-')}")
    print("-" * 76)
    print("  [1] Buka Terminal SSH Raspi otomatis (tanpa ketik IP)")
    print("  [2] Auto-Setup & Nyalakan Semua di Raspi (Update + Matikan eth0 + 4 Service)")
    print("  [3] Nyalakan / Restart Hub 3-TFT Arduino Uno (accelerator_hub.py) di Raspi")
    print("  [4] Tambah / Simpan Wi-Fi Baru di Raspi langsung dari Mini PC")
    print("  [5] Buka Web HMI Offline (Auto-Connect ke Raspi tanpa copy-paste manual!)")
    print("  [6] Jalankan Uji QA Healthcheck (06_test_mqtt_healthcheck.py) ke Raspi")
    print("  [W] Buka Wizard Konfigurasi Awal & Panduan Penuh Wi-Fi")
    print("  [R] Scan Ulang IP Raspi   |   [M] Input IP Raspi Manual   |   [Q] Keluar")
    print("=" * 76)


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

    _stop_windows_mosquitto(allow_uac=False)
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
            choice = input("Pilih menu [1-6 / W / R / M / Q]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nKeluar.")
            break

        if choice == "q":
            break
        elif choice == "r":
            st = find_raspberry_pi()
            continue
        elif choice == "w":
            wizard_script = os.path.join(SCRIPT_DIR, "decy13_startup_wizard.py")
            if os.path.isfile(wizard_script):
                subprocess.call([sys.executable, wizard_script])
                st = discover_via_udp(timeout=1.5) or st
            continue
        elif choice == "m":
            ip_in = input("Masukkan IP Wi-Fi Raspi (contoh 10.128.143.158): ").strip()
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
                    "daemon_active": True,
                    "usb_hub_active": False,
                    "throttled_note": "-",
                    "cpu_temp_c": 0.0,
                    "ws_url": f"ws://{ip_in}:9001",
                    "mqtt_tcp": f"{ip_in}:1883",
                    "discovery_method": "Manual Input",
                }
                update_runtime_config_from_rpi(st, mode_override="hardware", auto_connect=True)
            continue

        if choice == "5":
            if st and st.get("wifi_ip"):
                update_runtime_config_from_rpi(st, mode_override="hardware", auto_connect=True)
            else:
                update_runtime_config_from_rpi(None, mode_override="simulation", auto_connect=False)
            url = start_local_web_hmi_server()
            ws_endpoint = st.get("ws_url", "ws://127.0.0.1:9001") if st else "ws://127.0.0.1:9001"
            _copy_to_clipboard(ws_endpoint)
            print(f"\n[OK] Server Web HMI Offline + Auto-Sync aktif di: {url}")
            if st and st.get("wifi_ip"):
                print(f"[OK] Konfigurasi Raspi ({ws_endpoint}) OTOMATIS dikirim ke Web HMI!")
                print("     Browser akan langsung tersambung ke broker MQTT Raspi tanpa copy-paste manual.")
            else:
                print("[INFO] Raspi belum terdeteksi; Web HMI dibuka dalam Mode Simulasi + Instruktur.")
            webbrowser.open(url)
            input("\nServer tetap berjalan di latar belakang selama jendela ini terbuka.\nTekan Enter untuk kembali ke menu...")
            continue

        if st is None:
            print("\n[!] Raspi belum terdeteksi. Tekan [W] untuk Panduan Wi-Fi, [R] scan, atau [M] isi IP.")
            time.sleep(1.2)
            continue

        ip = str(st.get("wifi_ip", "")).strip()
        user = str(st.get("user", "sp-aksel")).strip() or "sp-aksel"

        if choice == "1":
            print(f"\n[..] Membuka sesi SSH interaktif ke {user}@{ip} (ketik 'exit' untuk kembali ke menu Mini PC)...")
            subprocess.call([ssh_bin, f"{user}@{ip}"])
            st = discover_via_udp(timeout=1.5) or st
            if st:
                update_runtime_config_from_rpi(st, mode_override="hardware", auto_connect=True)
        elif choice == "2":
            run_full_raspi_autosetup_ssh(ssh_bin, user, ip)
            st = discover_via_udp(timeout=2.0) or st
            if st:
                update_runtime_config_from_rpi(st, mode_override="hardware", auto_connect=True)
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
            if st:
                update_runtime_config_from_rpi(st, mode_override="hardware", auto_connect=True)
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
                if st:
                    update_runtime_config_from_rpi(st, mode_override="hardware", auto_connect=True)
                input("\nTekan Enter untuk kembali ke menu...")
        elif choice == "6":
            if os.path.isfile(HEALTHCHECK_SCRIPT):
                subprocess.call([sys.executable, HEALTHCHECK_SCRIPT, "--host", ip, "--duration", "10", "--no-menu"])
            else:
                print(f"[!] File tidak ditemukan: {HEALTHCHECK_SCRIPT}")
            input("\nTekan Enter untuk kembali ke menu...")


if __name__ == "__main__":
    main()
