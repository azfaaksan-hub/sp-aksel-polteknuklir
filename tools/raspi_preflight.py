#!/usr/bin/env python3
"""
ALAT PREFLIGHT CHECK & PENGINGAT UJI HARDWARE PER DIVISI (DECY-13)
==================================================================
Tujuan:
1. Mengecek kesiapan otomatis Raspberry Pi 3B+ (atau laptop mode simulasi)
   sebelum anggota Divisi 1..6 melakukan pengujian alat.
2. Menampilkan panduan pengingat spesifik sesuai divisi yang diuji:
   - Batas file eksklusif (agar tidak melanggar wilayah divisi lain)
   - Peringatan keamanan rangkaian/wiring lintas-divisi
   - Daftar ceklis Tahap B (Uji Fisik RPi) beserta PERINTAH UJI per butir
3. Menyimpan berkas bukti preflight ke `laporan_uji/bukti/` untuk dilampirkan
   ke Bagian C kartu `laporan_uji/UJI_DIVISI_N_*.md` (TANPA pernah mencentang
   otomatis kotak `[x]` pada kartu uji).

Cara pakai:
  python3 tools/raspi_preflight.py --divisi 2
  python3 tools/raspi_preflight.py --divisi 3 --no-save
  python3 tools/raspi_preflight.py --all
"""

import argparse
import datetime
import importlib
import json
import os
import platform
import socket
import subprocess
import sys
from typing import Any, Dict, List, Tuple

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(ROOT_DIR, "tools")
JOBDESK_PATH = os.path.join(TOOLS_DIR, "jobdesk_divisi.json")
RASPI_DIR = os.path.join(ROOT_DIR, "decy13_mqtt_kit", "raspi_cli")
CONFIG_PATH = os.path.join(RASPI_DIR, "config_hardware.json")
LAPORAN_DIR = os.path.join(ROOT_DIR, "laporan_uji")
BUKTI_DIR = os.path.join(LAPORAN_DIR, "bukti")


def _tcp_open(host: str, port: int, timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _detect_lan_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def _check_boot_config() -> Tuple[str, str]:
    for candidate in ("/boot/firmware/config.txt", "/boot/config.txt"):
        if os.path.isfile(candidate):
            try:
                with open(candidate, "r", encoding="utf-8", errors="ignore") as f:
                    txt = f.read()
                audio_off = "dtparam=audio=off" in txt
                spi_on = "dtparam=spi=on" in txt
                status = "LULUS" if (audio_off and spi_on) else "PERINGATAN"
                return (
                    status,
                    f"{candidate} (audio_off={audio_off}, spi_on={spi_on})",
                )
            except OSError as e:
                return "PERINGATAN", f"Gagal baca {candidate}: {e}"
    return "INFO", "Bukan OS Raspberry Pi (/boot/config.txt tidak ada — mode Laptop/Simulasi)"


def run_environment_checks() -> List[Tuple[str, str, str]]:
    """Kembalikan daftar (label, status, detail) untuk lingkungan saat ini."""
    results: List[Tuple[str, str, str]] = []
    is_linux = platform.system().lower() == "linux"
    hostname = socket.gethostname()
    lan_ip = _detect_lan_ip()
    results.append((
        "Identitas Mesin & Jaringan",
        "INFO",
        f"host={hostname}, os={platform.system()} {platform.release()}, ip={lan_ip}",
    ))

    # 1. Boot config (audio=off, spi=on)
    st_boot, det_boot = _check_boot_config()
    results.append(("Konfigurasi Boot RPi (Audio OFF & SPI ON)", st_boot, det_boot))

    # 2. Device SPI0 (/dev/spidev0.0)
    if is_linux:
        has_spi = os.path.exists("/dev/spidev0.0")
        results.append((
            "Bus Kernel SPI0 (/dev/spidev0.0)",
            "LULUS" if has_spi else "PERINGATAN",
            "/dev/spidev0.0 tersedia" if has_spi else "Belum ada /dev/spidev0.0 (jalankan bash tools/raspi_bootstrap.sh & sudo reboot)",
        ))
    else:
        results.append(("Bus Kernel SPI0 (/dev/spidev0.0)", "INFO", "Lewati di Windows/macOS (mode fallback aktif)"))

    # 3. Port Mosquitto (1883 & 9001)
    p1883 = _tcp_open("127.0.0.1", 1883)
    p9001 = _tcp_open("127.0.0.1", 9001)
    if p1883 and p9001:
        st_mq = "LULUS"
        det_mq = f"Port 1883 (MQTT TCP) & 9001 (WebSocket) terbuka (ws://{lan_ip}:9001)"
    elif p1883 or p9001:
        st_mq = "PERINGATAN"
        det_mq = f"1883={'BUKA' if p1883 else 'TUTUP'}, 9001={'BUKA' if p9001 else 'TUTUP'} (cek /etc/mosquitto/conf.d/decy13.conf)"
    else:
        st_mq = "PERINGATAN"
        det_mq = "Port 1883 & 9001 lokal belum terbuka (nyalakan Mosquitto / jalankan tools/raspi_bootstrap.sh)"
    results.append(("Broker Mosquitto Lokal (1883 & 9001)", st_mq, det_mq))

    # 4. Library Python
    libs = [
        ("paho-mqtt", "paho.mqtt.client"),
        ("RPi.GPIO", "RPi.GPIO"),
        ("rpi-ws281x", "rpi_ws281x"),
        ("luma.lcd", "luma.lcd"),
        ("Pillow", "PIL"),
        ("spidev", "spidev"),
    ]
    ok_libs, miss_libs = [], []
    for label, mod_name in libs:
        try:
            importlib.import_module(mod_name)
            ok_libs.append(label)
        except Exception:
            miss_libs.append(label)
    if not miss_libs:
        results.append(("Library Python Hardware (6 paket)", "LULUS", ", ".join(ok_libs)))
    else:
        st_lib = "PERINGATAN" if is_linux else "INFO"
        results.append((
            "Library Python Hardware (6 paket)",
            st_lib,
            f"Terpasang: {ok_libs or '-'}; Belum ada (fallback jika di laptop): {miss_libs}",
        ))

    # 5. Validasi config_hardware.json
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        pins = cfg["pins_bcm"]
        leds = cfg["led_mapping"]
        results.append((
            "Kontrak config_hardware.json",
            "LULUS",
            f"LED=GPIO{pins['led_ws2812b']} ({leds['total_leds']}px), Relay=GPIO{pins['relay_vacuum_fan']}, "
            f"Buzzer=GPIO{pins['buzzer']}, EStop=GPIO{pins['estop_button']}, LCD_DC=GPIO{pins['lcd_dc']}/RST=GPIO{pins['lcd_rst']}",
        ))
    except Exception as e:
        results.append(("Kontrak config_hardware.json", "GAGAL", str(e)))

    return results


def format_division_guide(div: Dict[str, Any], env_checks: List[Tuple[str, str, str]]) -> str:
    lines: List[str] = []
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines.append("=" * 74)
    lines.append(f"  PREFLIGHT & PENGINGAT UJI RASPI — DIVISI {div['id']}: {div['name'].upper()}")
    lines.append(f"  Waktu Cek   : {now_str}")
    lines.append(f"  PJ / Branch : {div['pic']}  |  Branch: {div['branch']}")
    lines.append(f"  Kartu Uji   : laporan_uji/{div['report_file']}")
    lines.append("=" * 74)

    lines.append("\n[1] HASIL DETEKSI OTOMATIS LINGKUNGAN SAAT INI:")
    for name, status, detail in env_checks:
        lines.append(f"  [{status:<10}] {name:<42} : {detail}")

    lines.append("\n[2] BATAS FILE EKSKLUSIF DIVISI INI (DILARANG EDIT FILE DIVISI LAIN!):")
    for fpath in div.get("allowed_files", []):
        lines.append(f"  - {fpath}")

    lines.append("\n[3] CAKUPAN HARDWARE & PIN BCM YANG WAJIB DICEK:")
    for hw in div.get("hardware_scope", []):
        lines.append(f"  - {hw}")

    lines.append("\n[4] PERINGATAN PENTING SEBELUM NYALAKAN ALAT / WIRING:")
    for w in div.get("cross_division_warnings", []):
        lines.append(f"  ! {w}")

    lines.append(f"\n[5] DAFTAR CEKLIS TAHAP B (laporan_uji/{div['report_file']}) & PERINTAH UJINYA:")
    for idx, item in enumerate(div.get("tahap_b_commands", []), start=1):
        lines.append(f"  {idx}. [ ] {item['item']}")
        lines.append(f"         Perintah Uji : {item['cmd']}")

    lines.append("\n[6] DEFINITION OF DONE (SYARAT DIVISI INI DINYATAKAN SELESAI):")
    lines.append(f"  -> {div.get('definition_of_done', '-')}")
    lines.append("\n[7] ATURAN PELAPORAN KE GITHUB:")
    lines.append(f"  1. Jalankan setiap perintah uji di atas pada Raspberry Pi 3B+ nyata.")
    lines.append(f"  2. Tempelkan output terminal / foto / temuan ke Bagian C pada laporan_uji/{div['report_file']}.")
    lines.append(f"  3. Centang [x] Tahap B HANYA untuk butir yang benar-benar sudah dites di alat fisik.")
    lines.append(f"  4. Jalankan: python3 tools/cek_integrasi_dan_announcer.py --ci sebelum git commit & git push.")
    lines.append("=" * 74)
    return "\n".join(lines)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Preflight Check & Pengingat Uji Raspi per Divisi DECY-13")
    parser.add_argument("--divisi", type=int, choices=[1, 2, 3, 4, 5, 6], help="Nomor divisi (1..6)")
    parser.add_argument("--all", action="store_true", help="Tampilkan panduan untuk seluruh 6 divisi")
    parser.add_argument("--no-save", action="store_true", help="Jangan simpan file bukti ke laporan_uji/bukti/")
    args = parser.parse_args()

    if not args.divisi and not args.all:
        parser.error("Pilih --divisi <1..6> atau --all")

    with open(JOBDESK_PATH, "r", encoding="utf-8") as f:
        jobdesk = json.load(f)

    env_checks = run_environment_checks()
    selected = [
        d for d in jobdesk["divisions"]
        if args.all or d["id"] == args.divisi
    ]

    outputs: List[str] = []
    for div in selected:
        guide_txt = format_division_guide(div, env_checks)
        print(guide_txt)
        outputs.append(guide_txt)

    if not args.no_save and selected:
        os.makedirs(BUKTI_DIR, exist_ok=True)
        host = socket.gethostname()
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        tag = f"DIVISI_{args.divisi}" if args.divisi else "ALL_DIVISI"
        out_path = os.path.join(BUKTI_DIR, f"PREFLIGHT_{tag}_{host}_{ts}.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(outputs) + "\n")
        rel_out = os.path.relpath(out_path, ROOT_DIR)
        print(f"\n[BUKTI TERSIMPAN] Salin isi '{rel_out}' ke Bagian C kartu laporan_uji divisimu setelah uji fisik.")


if __name__ == "__main__":
    main()
