#!/usr/bin/env python3
"""
ALAT VERIFIKASI INTEGRASI & GENERATOR ANNOUNCER WHATSAPP (DIVISI 1 — KETUA)
==========================================================================
Fungsi:
1. Memeriksa kebersihan repo (tidak ada __pycache__/*.pyc yang ter-track Git).
2. Memeriksa sintaks seluruh skrip Python di `decy13_mqtt_kit/raspi_cli/`.
3. Menguji kontrak `Decy13CoreDaemon` + modul Divisi 2, 3, 4 melalui simulasi
   7-tahap operasional dan memvalidasi 22 field wajib JSON MQTT.
4. Memeriksa keberadaan topik & kontrak perintah MQTT pada `web_hmi/index.html`.
5. (Mode Lokal) Mencetak teks **Announcer WhatsApp** siap copy-paste untuk grup tim.

Cara pakai:
  python tools/cek_integrasi_dan_announcer.py
  python tools/cek_integrasi_dan_announcer.py --versi "v1.1" --catatan "Divisi 2 sudah di-merge"
  python tools/cek_integrasi_dan_announcer.py --ci   (dipakai otomatis oleh GitHub Actions)
"""

import argparse
import importlib
import json
import os
import py_compile
import re
import subprocess
import sys
import time
from typing import Dict, List, Tuple

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RASPI_DIR = os.path.join(ROOT_DIR, "decy13_mqtt_kit", "raspi_cli")
WEB_HMI_PATH = os.path.join(ROOT_DIR, "decy13_mqtt_kit", "web_hmi", "index.html")
CONFIG_PATH = os.path.join(RASPI_DIR, "config_hardware.json")
LAPORAN_DIR = os.path.join(ROOT_DIR, "laporan_uji")
VALID_HW_STATUS = {
    "BELUM_MULAI",
    "DRAFT_PUSH_LAPTOP",
    "SEDANG_REVISI_HARDWARE",
    "LULUS_UJI_FISIK",
}

REQUIRED_MQTT_STATE_KEYS = [
    "power", "vacuum", "rf", "magnet", "interlocks", "beam",
    "exposureActive", "emergency", "stage", "mode",
    "lcd_line1", "lcd_line2", "lcd_line3", "lcd_line4",
    "pressure", "beamEnergy", "beamCurrent", "targetCurrent",
    "activeLedIdx", "shootLedIdx", "buzzerActive", "logs"
]

REQUIRED_HMI_COMMANDS = [
    "TOGGLE_POWER", "TOGGLE_VACUUM", "TOGGLE_INTERLOCK",
    "AUTO_INIT", "START_BEAM", "SHOOT", "EMERGENCY_STOP", "SET_PARAMS"
]


def check_tracked_pycache() -> Tuple[bool, str]:
    """Pastikan tidak ada file .pyc atau __pycache__ yang ikut ter-commit ke Git."""
    try:
        out = subprocess.check_output(
            ["git", "-C", ROOT_DIR, "ls-files"],
            stderr=subprocess.DEVNULL,
            text=True
        )
    except Exception:
        return True, "Lewati cek git ls-files (git tidak tersedia)."

    bad_files = [
        line.strip()
        for line in out.splitlines()
        if "__pycache__" in line or line.strip().endswith((".pyc", ".pyo"))
    ]
    if bad_files:
        return False, f"Ditemukan file cache Python ter-commit ke Git: {', '.join(bad_files[:5])}"
    return True, "Bersih (tidak ada __pycache__/.pyc di Git)."


def check_python_syntax() -> Tuple[bool, List[str]]:
    """Kompilasi seluruh file .py di raspi_cli untuk memastikan bebas SyntaxError."""
    errors = []
    checked = 0
    for dirpath, dirnames, filenames in os.walk(RASPI_DIR):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for fname in sorted(filenames):
            if fname.endswith(".py"):
                fpath = os.path.join(dirpath, fname)
                checked += 1
                try:
                    py_compile.compile(fpath, doraise=True)
                except py_compile.PyCompileError as e:
                    errors.append(f"{os.path.relpath(fpath, ROOT_DIR)}: {e}")
    if errors:
        return False, errors
    return True, [f"{checked} file Python lolos cek sintaks."]


def check_config_json() -> Tuple[bool, str]:
    """Validasi config_hardware.json dan konsistensi pin RPi 3B+."""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        pins = cfg["pins_bcm"]
        leds = cfg["led_mapping"]
        mqtt = cfg["mqtt"]
        if pins.get("led_ws2812b") != 18:
            return False, f"Pin LED harus GPIO 18 (ditemukan {pins.get('led_ws2812b')})."
        if leds.get("total_leds", 0) <= 0:
            return False, "total_leds pada config_hardware.json harus > 0."
        if mqtt.get("topic_cmd") != "decy13/hmi/cmd" or mqtt.get("topic_state") != "decy13/rpi/state":
            return False, "Topic MQTT di config_hardware.json berubah dari kontrak!"
        return True, f"Valid (GPIO 18 WS2812B, {leds['total_leds']} LED, SPI0 LCD)."
    except Exception as e:
        return False, f"Gagal membaca config_hardware.json: {e}"


def check_core_daemon_contract() -> Tuple[bool, str]:
    """Uji inisialisasi Decy13CoreDaemon + modul Divisi 2, 3, 4 serta transisi 7 tahap."""
    if RASPI_DIR not in sys.path:
        sys.path.insert(0, RASPI_DIR)

    try:
        daemon_mod = importlib.import_module("04_decy13_mqtt_daemon")
        daemon = daemon_mod.Decy13CoreDaemon()
        try:
            # Uji kontrak 22 key MQTT
            missing = [k for k in REQUIRED_MQTT_STATE_KEYS if k not in daemon.state]
            if missing:
                return False, f"State Daemon kehilangan field wajib: {missing}"

            # Uji sekuens 7 tahap
            daemon.handle_command({"cmd": "TOGGLE_POWER"})
            daemon.handle_command({"cmd": "SET_PARAMS", "magnet_a": 1450, "rf_kv": 45})
            daemon.handle_command({"cmd": "AUTO_INIT"})
            daemon.handle_command({"cmd": "START_BEAM"})
            daemon.handle_command({"cmd": "SHOOT"})
            time.sleep(0.15)
            daemon.step_physics_and_hardware()

            if daemon.state.get("stage") != 7 or not daemon.state.get("exposureActive"):
                return False, f"Sekuens tahap 7 gagal (stage={daemon.state.get('stage')})."

            daemon.handle_command({"cmd": "EMERGENCY_STOP"})
            daemon.step_physics_and_hardware()
            if not daemon.state.get("emergency") or daemon.state.get("beam"):
                return False, "Mekanisme EMERGENCY_STOP gagal memutus beam."

            return True, "Core Daemon + Modul Divisi 2/3/4 lolos uji 7-tahap & 22-key JSON."
        finally:
            daemon.cleanup_all()
    except Exception as e:
        return False, f"Error menjalankan Decy13CoreDaemon: {e}"


def check_web_hmi_contract() -> Tuple[bool, str]:
    """Pastikan Web HMI Divisi 5 masih memiliki topic dan command kontrak."""
    if not os.path.exists(WEB_HMI_PATH):
        return False, "File web_hmi/index.html tidak ditemukan."

    with open(WEB_HMI_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    missing_items = []
    for token in ["decy13/hmi/cmd", "decy13/rpi/state", "applyRpiState"] + REQUIRED_HMI_COMMANDS:
        if token not in html:
            missing_items.append(token)

    if missing_items:
        return False, f"Web HMI kehilangan kontrak wajib: {', '.join(missing_items)}"
    return True, "Web HMI (Divisi 5) memiliki seluruh topik & command MQTT wajib."


def _count_section_checks(text: str, heading_prefix: str) -> Tuple[int, int]:
    """Hitung jumlah [x] dan total item ceklis pada sub-bagian Markdown tertentu."""
    in_section = False
    done = 0
    total = 0
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            in_section = stripped.startswith(heading_prefix)
            continue
        if in_section:
            low = stripped.lower()
            if low.startswith("- [x] "):
                done += 1
                total += 1
            elif low.startswith("- [ ] "):
                total += 1
    return done, total


def check_hardware_reports() -> Tuple[bool, str, List[Dict[str, object]]]:
    """Baca & validasi kartu ceklis uji hardware di folder laporan_uji/."""
    if not os.path.isdir(LAPORAN_DIR):
        return False, "Folder laporan_uji/ tidak ditemukan.", []

    files = sorted(
        f for f in os.listdir(LAPORAN_DIR)
        if f.startswith("UJI_DIVISI_") and f.endswith(".md")
    )
    if not files:
        return False, "Tidak ada file kartu ceklis UJI_DIVISI_*.md di laporan_uji/.", []

    summaries: List[Dict[str, object]] = []
    errors: List[str] = []
    for fname in files:
        fpath = os.path.join(LAPORAN_DIR, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()

        m_div = re.match(r"UJI_DIVISI_(\d+)_", fname)
        div_label = f"Divisi {m_div.group(1)}" if m_div else fname
        m_stat = re.search(r"Status Push Saat Ini:\*\*\s*`([A-Z_]+)`", content)
        status = m_stat.group(1) if m_stat else "TIDAK_VALID"

        a_done, a_tot = _count_section_checks(content, "## A.")
        b_done, b_tot = _count_section_checks(content, "## B.")

        if status not in VALID_HW_STATUS:
            errors.append(f"{fname}: status '{status}' tidak dikenal")
        elif status == "LULUS_UJI_FISIK" and (b_tot == 0 or b_done < b_tot or a_done < a_tot):
            errors.append(
                f"{fname}: berstatus LULUS_UJI_FISIK padahal ceklis Tahap A ({a_done}/{a_tot}) / B ({b_done}/{b_tot}) belum 100%"
            )

        summaries.append({
            "divisi": div_label,
            "file": fname,
            "status": status,
            "a_done": a_done,
            "a_tot": a_tot,
            "b_done": b_done,
            "b_tot": b_tot,
        })

    if errors:
        return False, "; ".join(errors), summaries
    return True, f"{len(summaries)} kartu ceklis uji hardware tervalidasi.", summaries


def get_remote_branches() -> List[str]:
    try:
        out = subprocess.check_output(
            ["git", "-C", ROOT_DIR, "branch", "-r"],
            stderr=subprocess.DEVNULL,
            text=True
        )
        return [b.strip() for b in out.splitlines() if "->" not in b]
    except Exception:
        return []


def print_wa_announcer(
    versi: str,
    catatan: str,
    branches: List[str],
    all_ok: bool,
    hw_summaries: List[Dict[str, object]],
) -> None:
    status_emoji = "✅ LULUS & STABIL" if all_ok else "⚠️ ADA PERINGATAN CEK"
    branch_list = "\n".join(f"• `{b}`" for b in branches) if branches else "• `origin/main`"
    status_icon = {
        "BELUM_MULAI": "⏳",
        "DRAFT_PUSH_LAPTOP": "🟡",
        "SEDANG_REVISI_HARDWARE": "🔧",
        "LULUS_UJI_FISIK": "🟢",
    }
    hw_lines = "\n".join(
        f"• {item['divisi']}: {status_icon.get(str(item['status']), '❓')} `{item['status']}` "
        f"(Laptop {item['a_done']}/{item['a_tot']}, Raspi {item['b_done']}/{item['b_tot']})"
        for item in hw_summaries
    ) or "• *(Kartu laporan_uji belum terbaca)*"

    wa_text = f"""📢 *[UPDATE GITHUB SIKLOTRON DECY-13 — {versi}]*

Halo tim! Branch utama (`main`) di GitHub baru saja saya perbarui & cek integrasinya.
Status integrasi Core saat ini: *{status_emoji}*
Catatan update: {catatan}

🧪 *RAPOR KARTU CEKLIS UJI HARDWARE (`laporan_uji/`):*
{hw_lines}

🔍 *WAJIB CEK RAPOR, KARTU UJI, & PROMPT TERBARU:*
Buka halaman depan GitHub repo kita (`README.md`) untuk melihat:
1. Divisi mana yang sudah *✅ Merged*, masih *🟡 Draft Laptop (Belum Uji Raspi)*, atau *⚠️ Perlu Revisi*.
2. *Prompt AI Konteks Terbaru* per divisi (tinggal copy-paste kalau kalian mulai chat baru dengan AI Web maupun CLI!).
3. Jangan lupa isi & centang jujur kartu `laporan_uji/UJI_DIVISI_X_*.md` milikmu sebelum `git push` (Tahap B HANYA boleh dicentang setelah tes alat fisik Raspi nyata!).

🔄 *YANG HARUS KALIAN LAKUKAN SEKARANG (MANDIRI):*
Jangan lupa tarik update terbaru dari `main` ke branch divisi masing-masing sebelum lanjut ngoding:
• *Pakai GitHub Desktop:* Pastikan sedang di branch divisimu -> klik *Fetch origin* -> menu *Branch* -> *Update from main*.
• *Pakai Terminal:*
  `git fetch origin`
  `git merge origin/main`

📌 *Daftar Branch Terdeteksi di Server Saat Ini:*
{branch_list}

⚠️ *Pengingat:* Tetap lakukan `git commit` dan `git push` sendiri ke branch divisimu masing-masing (jangan suruh AI commit/push langsung, dan jangan edit file divisi lain). Semangat! 🚀"""

    print("\n" + "=" * 70)
    print("  TEMPLATE PESAN ANNOUNCER WHATSAPP (SIAP COPY-PASTE KE GRUP)")
    print("=" * 70)
    print(wa_text)
    print("=" * 70)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Cek Integrasi Tim 6 Divisi & Generator Announcer WA")
    parser.add_argument("--ci", action="store_true", help="Mode CI GitHub Actions (exit 1 jika ada yang gagal)")
    parser.add_argument("--versi", default="Update Terbaru", help="Label versi untuk teks announcer WA")
    parser.add_argument("--catatan", default="Sinkronisasi modul & papan status di README.md", help="Catatan singkat update untuk WA")
    args = parser.parse_args()

    print("=" * 70)
    print("  VERIFIKASI INTEGRASI PROYEK SIKLOTRON DECY-13 (6 DIVISI)")
    print("=" * 70)

    checks = []

    ok_git, msg_git = check_tracked_pycache()
    checks.append(("Kebersihan Git (__pycache__/.pyc)", ok_git, msg_git))

    ok_py, msg_py = check_python_syntax()
    checks.append(("Sintaks Python raspi_cli/", ok_py, "; ".join(msg_py)))

    ok_cfg, msg_cfg = check_config_json()
    checks.append(("Konfigurasi Hardware (JSON)", ok_cfg, msg_cfg))

    ok_core, msg_core = check_core_daemon_contract()
    checks.append(("Kontrak Core Daemon & Modul 2/3/4", ok_core, msg_core))

    ok_hmi, msg_hmi = check_web_hmi_contract()
    checks.append(("Kontrak Web HMI (Divisi 5)", ok_hmi, msg_hmi))

    ok_hw, msg_hw, hw_summaries = check_hardware_reports()
    checks.append(("Kartu Ceklis Hardware (laporan_uji/)", ok_hw, msg_hw))

    all_passed = True
    for name, passed, detail in checks:
        icon = "[LULUS]" if passed else "[GAGAL]"
        print(f"  {icon} {name:<38} -> {detail}")
        if not passed:
            all_passed = False

    if hw_summaries:
        print("\n" + "-" * 70)
        print("  RINGKASAN STATUS UJI HARDWARE RASPI PER DIVISI (laporan_uji/)")
        print("-" * 70)
        for item in hw_summaries:
            print(
                f"  - {item['divisi']:<10} | {str(item['status']):<23} "
                f"| Laptop {item['a_done']}/{item['a_tot']} | Raspi Fisik {item['b_done']}/{item['b_tot']}"
            )

    if not args.ci:
        branches = get_remote_branches()
        print_wa_announcer(args.versi, args.catatan, branches, all_passed, hw_summaries)

    if not all_passed:
        print("\n[PERINGATAN] Ada pemeriksaan yang GAGAL. Periksa detail di atas sebelum merge!")
        sys.exit(1)

    print("\n[OK] Seluruh pemeriksaan integrasi LULUS!")


if __name__ == "__main__":
    main()
