#!/usr/bin/env python3
r"""
PROGRAM KONFIGURASI AWAL SAAT MINI PC BARU HIDUP (STARTUP WIZARD DECY-13)
=========================================================================
Penanggung Jawab : Divisi 1 (Ketua / Core Raspi Backend & Integrator)
File             : tools/decy13_startup_wizard.py

Dirancang khusus untuk dijalankan saat Mini PC Ruang Kontrol baru menyala:
1. Memberikan pilihan utama di awal:
   - [1] AUTO-SETUP PENUH (Otomatis matikan Mosquitto lokal, cari Wi-Fi Raspi,
         pastikan 4 layanan Raspi aktif, sinkronkan IP ke HTML, & buka Web HMI)
   - [2] KONFIGURASI MANUAL & PANDUAN PENUH WI-FI (Arahan langkah demi langkah
         bila Wi-Fi / Raspi belum terdeteksi, tambah Wi-Fi baru, setup 3-TFT USB)
   - [3] MODE SIMULASI / PAMERAN MANDIRI (Tanpa Raspi, langsung buka Web HMI + Instruktur)
   - [4] PENGATURAN AUTO-MUNCUL SAAT WINDOWS HIDUP (Pasang/Cabut Startup Windows)
2. Menjaga sinkronisasi otomatis (`/api/runtime-config`) antara IP Raspi dan Web HMI
   sehingga tampilan HTML langsung berjalan normal tanpa copy-paste URL manual.

Cara pakai:
  Klik 2x `MULAI_DECY13.bat` atau jalankan:
  python tools\decy13_startup_wizard.py
"""

import argparse
import os
import subprocess
import sys
import time
import webbrowser
from typing import Any, Dict, List, Optional, Tuple

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import minipc_control_hub as hub  # noqa: E402


def _startup_shortcut_path() -> str:
    appdata = os.environ.get("APPDATA", "")
    if not appdata:
        return ""
    return os.path.join(
        appdata,
        "Microsoft",
        "Windows",
        "Start Menu",
        "Programs",
        "Startup",
        "DECY13_AutoStartup_Wizard.cmd",
    )


def is_windows_autostart_enabled() -> bool:
    sp = _startup_shortcut_path()
    return bool(sp and os.path.isfile(sp))


def set_windows_autostart(enable: bool) -> Tuple[bool, str]:
    sp = _startup_shortcut_path()
    if not sp:
        return False, "Folder APPDATA Startup Windows tidak ditemukan."
    try:
        if enable:
            os.makedirs(os.path.dirname(sp), exist_ok=True)
            launcher_bat = os.path.join(REPO_ROOT, "MULAI_DECY13.bat")
            content = (
                "@echo off\r\n"
                "REM Auto-Start Konfigurasi Awal Siklotron DECY-13 saat Mini PC Hidup\r\n"
                f'start "DECY-13 Startup Configuration" cmd /k "cd /d \"{REPO_ROOT}\" && call \"{launcher_bat}\""\r\n'
            )
            with open(sp, "w", encoding="utf-8") as f:
                f.write(content)
            return True, f"Auto-Start berhasil dipasang di:\n  {sp}"
        else:
            if os.path.isfile(sp):
                os.remove(sp)
            return True, "Auto-Start Windows berhasil dinonaktifkan."
    except Exception as exc:
        return False, f"Gagal mengubah Auto-Start: {exc}"


def print_wifi_full_guide(wifi_info: Dict[str, str], local_ips: List[str]) -> None:
    """Tampilkan panduan lengkap & praktis bila Wi-Fi / Raspi belum terdeteksi."""
    ssid = wifi_info.get("ssid") or "(BELUM TERSAMBUNG KE WI-FI)"
    prefix_hint = "10.x.x.158"
    if local_ips:
        parts = local_ips[0].split(".")
        if len(parts) == 4:
            prefix_hint = f"{parts[0]}.{parts[1]}.{parts[2]}.158"

    print("\n" + "=" * 78)
    print("  PANDUAN LENGKAP AGAR RASPBERRY PI OTOMATIS TERKONEKSI KE WI-FI (0 ETHERNET)")
    print("=" * 78)
    print(f"  Status Wi-Fi Mini PC saat ini : SSID = {ssid}")
    print(f"  IPv4 Mini PC saat ini         : {', '.join(local_ips) if local_ips else 'Belum ada IP Wi-Fi'}")
    print("-" * 78)
    print("  PENTING: JANGAN colok kabel LAN/Ethernet ke Raspberry Pi 3B+ unit ini")
    print("           karena memicu drop tegangan 5V (brown-out / mati mendadak).")
    print("-" * 78)
    print("  PILIH KONDISI DI LAPANGAN SAAT INI:")
    print("")
    print("  [KONDISI A] Memakai Hotspot HP yang SUDAH PERNAH dipakai Raspi:")
    print("    1. Nyalakan Hotspot HP pada pita 2.4 GHz (WPA2-Personal, bukan 5 GHz saja).")
    print("    2. Sambungkan Wi-Fi Mini PC Windows ini ke Hotspot HP yang SAMA persis.")
    print("    3. Colok adaptor 5V Raspi -> tunggu 35-45 detik sampai lampu hijau tenang.")
    print("    4. Di menu bawah, pilih [1] Pantau Otomatis sampai Raspi muncul!")
    print(f"       (Tips: bila Hotspot memblokir scan, buka menu Hotspot di HP -> lihat")
    print(f"        perangkat terhubung 'sp-aksel', biasanya berakhiran .158 misal {prefix_hint},")
    print("        lalu pilih [2] Input IP Manual.)")
    print("")
    print("  [KONDISI B] Ingin Pindah ke Wi-Fi Ruangan/Hotspot BARU (Tanpa Monitor Raspi):")
    print("    1. Nyalakan dulu Hotspot HP LAMA yang sudah dikenali Raspi.")
    print("    2. Sambungkan Mini PC ke Hotspot HP lama tersebut -> tunggu Raspi terdeteksi.")
    print("    3. Pilih [3] Simpan Wi-Fi Baru ke Raspi via SSH -> ketik Nama & Password")
    print("       Wi-Fi baru. Raspi otomatis menyimpan profil tersebut ke NetworkManager.")
    print("    4. Pindahkan juga Wi-Fi Mini PC ke Wi-Fi baru tersebut.")
    print("")
    print("  [KONDISI C] Hotspot Lama Tidak Ada (Setup Langsung di Raspi 1 Menit):")
    print("    1. Colok monitor HDMI + keyboard USB ke Raspi (TANPA kabel Ethernet).")
    print("    2. Login di layar hitam Debian 13: user `sp-aksel` -> masukkan password.")
    print("    3. Ketik:  sudo nmtui   -> pilih 'Activate a connection' -> pilih Wi-Fi")
    print("       yang sama dengan Mini PC -> masukkan password -> Quit.")
    print("    4. Cek IP Wi-Fi dengan:  hostname -I   (huruf I besar), cabut monitor/keyboard")
    print("       bila sudah selesai agar hemat daya 5V, lalu kembali ke layar Mini PC ini.")
    print("=" * 78)


def watch_until_raspi_online(max_seconds: int = 60) -> Optional[Dict[str, Any]]:
    """Pantau terus jaringan Wi-Fi selama max_seconds hingga Raspi menyala & merespons."""
    print(f"\n[..] Memantau jaringan Wi-Fi selama maks {max_seconds} detik (tekan Ctrl+C untuk batal)...")
    start_t = time.time()
    attempt = 0
    try:
        while time.time() - start_t < max_seconds:
            attempt += 1
            rem = max(0, int(max_seconds - (time.time() - start_t)))
            print(f"  -> Percobaan #{attempt} (sisa ~{rem} dtk): cek Beacon UDP 51313 & TCP subnet...")
            st = hub.discover_via_udp(timeout=2.0)
            if st is None:
                st = hub.discover_via_subnet_scan()
            if st is not None:
                hub.update_runtime_config_from_rpi(st, mode_override="hardware", auto_connect=True)
                print(f"\n[BERHASIL] Raspberry Pi ditemukan di IP: {st.get('wifi_ip')}!")
                return st
            time.sleep(2.0)
    except KeyboardInterrupt:
        print("\n[INFO] Pemantauan dibatalkan oleh pengguna.")
    return None


def launch_hmi_and_keep_alive(st: Optional[Dict[str, Any]], mode: str) -> None:
    """Aktifkan jembatan runtime_config, buka browser Web HMI, dan jaga server tetap jalan."""
    if mode == "hardware" and st and st.get("wifi_ip"):
        cfg = hub.update_runtime_config_from_rpi(st, mode_override="hardware", auto_connect=True)
        ws_url = cfg["wsUrl"]
        hub._copy_to_clipboard(ws_url)
    else:
        cfg = hub.update_runtime_config_from_rpi(None, mode_override="simulation", auto_connect=False)
        ws_url = cfg["wsUrl"]

    base_url = hub.start_local_web_hmi_server(start_watcher=True)
    open_url = f"{base_url}/?autoconfig=1"

    print("\n" + "=" * 78)
    print("  SERVER WEB HMI & JEMBATAN KONFIGURASI OTOMATIS AKTIF")
    print("=" * 78)
    print(f"  Alamat Web HMI       : {base_url}")
    print(f"  Mode Aktif           : {'HARDWARE RASPBERRY PI (AUTO-CONNECT)' if cfg['autoConnect'] else 'SIMULASI LOKAL + INSTRUKTUR'}")
    if cfg["autoConnect"]:
        print(f"  Broker MQTT Raspi    : {ws_url}  (otomatis dibaca oleh HTML)")
        print(f"  Node-RED TCP Broker  : {cfg['mqttTcp']}")
    print("  Mode Instruktur UI   : AKTIF (Berulang otomatis & auto-reset bila ditinggal)")
    print("-" * 78)
    print("  PENTING: Biarkan jendela terminal ini tetap terbuka selama mengoperasikan alat")
    print("           agar Web HMI terus tersinkronisasi otomatis dengan Raspberry Pi.")
    print("=" * 78)

    webbrowser.open(open_url)
    try:
        input("\nTekan [Enter] kapan saja untuk kembali ke Menu Konfigurasi (server tetap aktif)...")
    except (EOFError, KeyboardInterrupt):
        pass


def run_auto_setup_flow(ssh_bin: str, current_st: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Alur [1] AUTO-SETUP PENUH dari awal hingga Web HMI terbuka dan terkoneksi."""
    print("\n" + "=" * 78)
    print("  MENJALANKAN AUTO-SETUP PENUH (MINI PC <-> RASPBERRY PI <-> WEB HMI)")
    print("=" * 78)

    # Langkah 1: Pastikan Mosquitto lokal Windows mati
    print("[Langkah 1/4] Memeriksa & mematikan service Mosquitto lokal Windows...")
    stopped = hub._stop_windows_mosquitto(allow_uac=True)
    if stopped:
        print("  -> OK: Mosquitto lokal Windows tidak aktif (bebas bentrok port 1883/9001).")
    else:
        print("  -> PERHATIAN: Mosquitto Windows masih berjalan. Jalankan CMD sebagai Admin bila bentrok.")

    # Langkah 2: Cek Wi-Fi & Cari Raspi
    wifi_info = hub.get_windows_wifi_info()
    local_ips = hub._get_local_ipv4_list()
    print(f"[Langkah 2/4] Memeriksa Wi-Fi Mini PC (SSID: '{wifi_info.get('ssid') or 'Tidak terdeteksi'}')...")

    st = current_st or hub.find_raspberry_pi(quiet=False)
    while st is None:
        print("\n[!] Raspberry Pi belum terdeteksi di jaringan Wi-Fi Mini PC saat ini.")
        print_wifi_full_guide(wifi_info, local_ips)
        print("  Pilihan tindakan cepat:")
        print("    [1] Pantau otomatis 60 detik (sambil menyalakan Hotspot / Raspi)")
        print("    [2] Masukkan IP Wi-Fi Raspi secara manual (misal lihat dari daftar Hotspot HP)")
        print("    [3] Lanjut buka Web HMI dalam Mode Simulasi dulu (tanpa Raspi)")
        print("    [B] Kembali ke Menu Utama")
        sub = input("  Pilih [1/2/3/B]: ").strip().lower()
        if sub == "1":
            st = watch_until_raspi_online(max_seconds=60)
            wifi_info = hub.get_windows_wifi_info()
            local_ips = hub._get_local_ipv4_list()
        elif sub == "2":
            ip_in = input("  Masukkan IP Wi-Fi Raspi (contoh 10.128.143.158): ").strip()
            if ip_in:
                user_in = input("  Username SSH Raspi [default: sp-aksel]: ").strip() or "sp-aksel"
                st = {
                    "type": "DECY13_RPI_STATUS",
                    "hostname": "sp-aksel",
                    "user": user_in,
                    "wifi_ip": ip_in,
                    "all_ips": [ip_in],
                    "wifi_ssid": wifi_info.get("ssid", "Input Manual"),
                    "eth0_state": "-",
                    "mosquitto_1883": False,
                    "mosquitto_9001": False,
                    "daemon_active": False,
                    "usb_hub_active": False,
                    "throttled_note": "-",
                    "cpu_temp_c": 0.0,
                    "ws_url": f"ws://{ip_in}:9001",
                    "mqtt_tcp": f"{ip_in}:1883",
                    "discovery_method": "Manual Input",
                }
        elif sub == "3":
            launch_hmi_and_keep_alive(None, mode="simulation")
            return None
        else:
            return None

    ip = str(st.get("wifi_ip", "")).strip()
    user = str(st.get("user", "sp-aksel")).strip() or "sp-aksel"
    print(f"  -> OK: Raspberry Pi terdeteksi di {ip} ({st.get('discovery_method', 'Wi-Fi')}).")

    # Langkah 3: Verifikasi 4 Layanan Raspi; bila ada yang mati, jalankan SSH Auto-Setup
    all_services_ready = bool(
        st.get("mosquitto_1883")
        and st.get("mosquitto_9001")
        and st.get("daemon_active")
        and st.get("usb_hub_active")
    )
    print("[Langkah 3/4] Memeriksa kesiapan layanan daemon & broker di Raspberry Pi...")
    if all_services_ready:
        print("  -> OK: Keempat layanan Raspi (Mosquitto 1883/9001, Core Daemon, Auto-Link, USB Hub 3-TFT) SUDAH AKTIF!")
        ans = input("  Ingin tarik update GitHub terbaru & restart layanan Raspi juga? [t/Y, Enter=Lewati]: ").strip().lower()
        if ans == "y":
            hub.run_full_raspi_autosetup_ssh(ssh_bin, user, ip)
            st = hub.discover_via_udp(timeout=2.5) or st
    else:
        print("  -> Beberapa layanan Raspi belum aktif (atau perlu tarik update terbaru dari GitHub).")
        print(f"  -> Menjalankan konfigurasi otomatis ke {user}@{ip} (masukkan password SSH Raspi bila diminta)...")
        rc = hub.run_full_raspi_autosetup_ssh(ssh_bin, user, ip)
        if rc != 0:
            print("\n[!] Auto-Setup via GitHub belum tuntas (misal Raspi offline / internet lambat).")
            ans_scp = input("  Coba kirim file LED & bootstrap langsung dari Mini PC via SCP (tanpa internet)? [Y/t]: ").strip().lower()
            if ans_scp != "t":
                hub.sync_local_led_files_to_raspi(ssh_bin, user, ip)
        refreshed = hub.discover_via_udp(timeout=2.5) or hub.discover_via_subnet_scan()
        if refreshed:
            st = refreshed
        input("\nPeriksa log hardware di atas (pastikan LedStripModule [HARDWARE AKTIF]). Tekan Enter untuk buka Web HMI...")

    # Langkah 4: Sinkronkan runtime_config & langsung buka Web HMI
    print("[Langkah 4/4] Menyinkronkan konfigurasi Raspi ke Web HMI & membuka layar kendali...")
    launch_hmi_and_keep_alive(st, mode="hardware")
    return st


def run_manual_menu(ssh_bin: str, st: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Alur [2] KONFIGURASI MANUAL & PANDUAN PENUH WI-FI."""
    while True:
        wifi_info = hub.get_windows_wifi_info()
        local_ips = hub._get_local_ipv4_list()
        ip_rpi = st.get("wifi_ip") if st else None

        print("\n" + "=" * 78)
        print("  MODE KONFIGURASI MANUAL & PENGATURAN WI-FI RASPBERRY PI")
        print("=" * 78)
        print(f"  Wi-Fi Mini PC : SSID '{wifi_info.get('ssid') or '-'}' | IP: {', '.join(local_ips) if local_ips else '-'}")
        print(f"  Status Raspi  : {('[ONLINE] ' + str(ip_rpi)) if ip_rpi else '[BELUM TERDETEKSI]'}")
        print("-" * 78)
        print("  [1] Baca Panduan Lengkap Koneksi Wi-Fi Raspi (Semua Skenario Lapangan)")
        print("  [2] Scan / Pantau Otomatis Jaringan Wi-Fi (60 detik) sampai Raspi Muncul")
        print("  [3] Input IP Wi-Fi Raspi secara Manual")
        print("  [4] Tambah / Simpan Wi-Fi Baru ke Raspi via SSH (nmcli)")
        print("  [5] Jalankan Install / Update 4 Layanan Auto-Start di Raspi (tanpa Ethernet)")
        print("  [6] Atur / Cek 3 Port USB Arduino Uno TFT (setup_udev.sh & Log USB Hub)")
        print("  [7] Buka Terminal SSH Raspi Interaktif")
        print("  [8] Buka Web HMI & Sinkronkan dengan Konfigurasi Saat Ini")
        print("  [S] Kirim File LED 2-Fase & Bootstrap Langsung ke Raspi (via SCP, tanpa internet)")
        print("  [B] Kembali ke Menu Awal")
        print("=" * 78)

        choice = input("Pilih langkah manual [1-8 / S / B]: ").strip().lower()
        if choice in ("b", "q"):
            return st
        elif choice == "1":
            print_wifi_full_guide(wifi_info, local_ips)
            input("\nTekan Enter untuk kembali...")
        elif choice == "2":
            found = watch_until_raspi_online(max_seconds=60)
            if found:
                st = found
            input("\nTekan Enter untuk kembali...")
        elif choice == "3":
            ip_in = input("Masukkan IP Wi-Fi Raspi (contoh 10.128.143.158): ").strip()
            if ip_in:
                user_in = input("Username SSH Raspi [default: sp-aksel]: ").strip() or "sp-aksel"
                st = {
                    "type": "DECY13_RPI_STATUS",
                    "hostname": "sp-aksel",
                    "user": user_in,
                    "wifi_ip": ip_in,
                    "all_ips": [ip_in],
                    "wifi_ssid": wifi_info.get("ssid", "Manual"),
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
                hub.update_runtime_config_from_rpi(st, mode_override="hardware", auto_connect=True)
                print(f"[OK] IP Raspi diset ke {ip_in} dan disinkronkan ke Web HMI.")
        elif choice == "8":
            launch_hmi_and_keep_alive(st, mode="hardware" if ip_rpi else "simulation")
        else:
            if not ip_rpi:
                print("\n[!] IP Raspi belum diketahui. Gunakan menu [1], [2], atau [3] terlebih dahulu.")
                time.sleep(1.3)
                continue
            user = str(st.get("user", "sp-aksel")) if st else "sp-aksel"
            if choice == "4":
                ssid_new = input("Masukkan Nama Wi-Fi / Hotspot BARU untuk disimpan di Raspi: ").strip()
                if ssid_new:
                    pass_new = input(f"Masukkan Password Wi-Fi '{ssid_new}': ").strip()
                    safe_ssid = ssid_new.replace('"', '\\"')
                    safe_pass = pass_new.replace('"', '\\"')
                    remote_cmd = (
                        f'sudo nmcli dev wifi rescan 2>/dev/null || true; sleep 2; '
                        f'sudo nmcli dev wifi connect "{safe_ssid}" password "{safe_pass}" && '
                        f'nmcli -t -f NAME,TYPE,AUTOCONNECT con show'
                    )
                    hub._run_ssh_command(ssh_bin, user, ip_rpi, remote_cmd)
                    st = hub.discover_via_udp(timeout=2.0) or st
                    input("\nTekan Enter untuk kembali...")
            elif choice == "5":
                hub.run_full_raspi_autosetup_ssh(ssh_bin, user, ip_rpi)
                st = hub.discover_via_udp(timeout=2.5) or st
                if st:
                    hub.update_runtime_config_from_rpi(st, mode_override="hardware", auto_connect=True)
                input("\nTekan Enter untuk kembali...")
            elif choice == "6":
                print("\n  [A] Cek status & 20 baris log terakhir decy13-usb-hub.service")
                print("  [B] Jalankan ulang setup_udev.sh (pemetaan 3 port fisik USB Hub Uno)")
                sub_u = input("  Pilih [A/B]: ").strip().lower()
                if sub_u == "b":
                    rcmd = (
                        "REPO_DIR=$( [ -d ~/decy13/AKSEL-DECY13 ] && echo ~/decy13/AKSEL-DECY13 || echo ~/sp-aksel-polteknuklir/AKSEL-DECY13 ); "
                        "cd \"$REPO_DIR\" && sudo bash raspi/setup_udev.sh && ls -l /dev/arduino_* && "
                        "sudo systemctl restart decy13-usb-hub.service"
                    )
                else:
                    rcmd = (
                        "ls -l /dev/arduino_* 2>/dev/null || echo 'Symlink /dev/arduino_* belum ada'; "
                        "sudo systemctl restart decy13-usb-hub.service && sleep 2 && "
                        "sudo journalctl -u decy13-usb-hub.service -n 20 --no-pager"
                    )
                hub._run_ssh_command(ssh_bin, user, ip_rpi, rcmd)
                input("\nTekan Enter untuk kembali...")
            elif choice == "7":
                subprocess.call([ssh_bin, f"{user}@{ip_rpi}"])
                st = hub.discover_via_udp(timeout=1.5) or st
            elif choice == "s":
                hub.sync_local_led_files_to_raspi(ssh_bin, user, ip_rpi)
                st = hub.discover_via_udp(timeout=2.5) or st
                if st:
                    hub.update_runtime_config_from_rpi(st, mode_override="hardware", auto_connect=True)
                input("\nTekan Enter untuk kembali...")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Program Konfigurasi Awal Saat Baru Hidup — Siklotron DECY-13"
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Langsung jalankan alur Auto-Setup Penuh tanpa menunggu menu awal",
    )
    parser.add_argument(
        "--check-config-api",
        action="store_true",
        help="Uji cepat inisialisasi server & cetak JSON runtime_config lalu keluar",
    )
    args = parser.parse_args()

    ssh_bin = hub._find_ssh_binary()

    if args.check_config_api:
        url = hub.start_local_web_hmi_server(start_watcher=False)
        cfg = hub.load_cached_runtime_config()
        print(json.dumps({"serverUrl": url, "runtimeConfig": cfg}, indent=2, ensure_ascii=False))
        return

    # Scan cepat di awal (1.2 detik) agar tampilan pembuka langsung informatif
    hub._stop_windows_mosquitto(allow_uac=False)
    st = hub.discover_via_udp(timeout=1.2)
    if st:
        hub.update_runtime_config_from_rpi(st, mode_override="hardware", auto_connect=True)

    if args.auto:
        run_auto_setup_flow(ssh_bin, st)
        return

    while True:
        wifi_info = hub.get_windows_wifi_info()
        local_ips = hub._get_local_ipv4_list()
        autostart_on = is_windows_autostart_enabled()

        print("\n" + "=" * 78)
        print("  KONFIGURASI AWAL STASIUN KENDALI SIKLOTRON DECY-13 (13 MeV H-)")
        print("  Politeknik Teknologi Nuklir Indonesia - Mode 100% Wi-Fi Tanpa Ethernet")
        print("=" * 78)
        print(f"  Wi-Fi Mini PC       : {wifi_info.get('ssid') or 'BELUM TERSAMBUNG KE WI-FI'} ({', '.join(local_ips) if local_ips else 'tanpa IP'})")
        if st and st.get("wifi_ip"):
            svc_ok = (
                st.get("mosquitto_9001") and st.get("daemon_active")
            )
            print(f"  Deteksi Cepat Raspi : TERDETEKSI di {st.get('wifi_ip')} ({'Siap Pakai' if svc_ok else 'Perlu Auto-Setup Layanan'})")
        else:
            print("  Deteksi Cepat Raspi : BELUM TERDETEKSI (pilih [1] atau [2] untuk panduan Wi-Fi)")
        print(f"  Auto-Muncul Windows : {'AKTIF (Muncul otomatis saat Mini PC hidup)' if autostart_on else 'NONAKTIF (Buka lewat MULAI_DECY13.bat)'}")
        print("-" * 78)
        print("  SILAKAN PILIH MODE PENGOPERASIAN SAAT BARU HIDUP:")
        print("")
        print("  [1] AUTO-SETUP PENUH (Rekomendasi)")
        print("      Otomatis cek Wi-Fi, temukan & siapkan Raspberry Pi, sambungkan konfigurasi")
        print("      langsung ke Web HMI, lalu buka layar kontrol + Instruktur.")
        print("")
        print("  [2] KONFIGURASI MANUAL & PANDUAN PENUH WI-FI")
        print("      Atur bertahap secara manual: panduan lengkap bila Wi-Fi/Raspi belum")
        print("      terdeteksi, simpan Wi-Fi baru ke Raspi, atau cek 3 layar TFT USB.")
        print("")
        print("  [3] MODE SIMULASI MANDIRI (Tanpa Raspberry Pi)")
        print("      Langsung jalankan Web HMI Offline + Mode Instruktur Berulang untuk demo.")
        print("")
        print(f"  [4] {'MATIKAN' if autostart_on else 'AKTIFKAN'} AUTO-HIDUP SAAT WINDOWS MENYALA (Startup Mini PC)")
        print("  [5] Buka Menu Pusat Kendali Teknis (minipc_control_hub.py)")
        print("  [Q] Keluar")
        print("=" * 78)

        try:
            ans = input("Pilih mode [1 / 2 / 3 / 4 / 5 / Q] (Enter = 1 Auto-Setup): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nKeluar.")
            break

        if ans == "" or ans == "1":
            st = run_auto_setup_flow(ssh_bin, st)
        elif ans == "2":
            st = run_manual_menu(ssh_bin, st)
        elif ans == "3":
            launch_hmi_and_keep_alive(None, mode="simulation")
        elif ans == "4":
            ok, msg = set_windows_autostart(not autostart_on)
            print(f"\n[{'OK' if ok else 'GAGAL'}] {msg}")
            input("Tekan Enter untuk lanjut...")
        elif ans == "5":
            subprocess.call([sys.executable, os.path.join(SCRIPT_DIR, "minipc_control_hub.py")])
            st = hub.discover_via_udp(timeout=1.2) or st
        elif ans == "q":
            break


if __name__ == "__main__":
    import json  # noqa: F401
    main()
