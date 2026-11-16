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
import fnmatch
import importlib
import json
import os
import py_compile
import re
import subprocess
import sys
import time
from typing import Dict, List, Optional, Tuple

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

            # Uji sekuens 7 tahap + proteksi SET_PARAMS di luar batas (mis. magnet_a=0)
            daemon.handle_command({"cmd": "TOGGLE_POWER"})
            daemon.handle_command({"cmd": "SET_PARAMS", "magnet_a": 1450, "rf_kv": 45})
            daemon.handle_command({"cmd": "SET_PARAMS", "magnet_a": 0, "rf_kv": -10})
            if daemon.state.get("setpoint_magnet_a") != 1450.0 or daemon.state.get("setpoint_rf_kv") != 45.0:
                return False, "Proteksi SET_PARAMS gagal menolak nilai di luar batas (magnet_a=0 / rf_kv=-10)."
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

            return True, "Core Daemon + Modul Divisi 2/3/4 lolos uji 7-tahap, proteksi SET_PARAMS, & 22-key JSON."
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


def check_jobdesk_and_preflight(hw_summaries: List[Dict[str, object]]) -> Tuple[bool, str]:
    """Pastikan jobdesk_divisi.json, raspi_bootstrap.sh (LF), raspi_preflight.py, dan JOBDESK_DAN_DOD.md valid."""
    jobdesk_path = os.path.join(ROOT_DIR, "tools", "jobdesk_divisi.json")
    bootstrap_path = os.path.join(ROOT_DIR, "tools", "raspi_bootstrap.sh")
    preflight_path = os.path.join(ROOT_DIR, "tools", "raspi_preflight.py")
    dod_doc_path = os.path.join(LAPORAN_DIR, "JOBDESK_DAN_DOD.md")

    for req_path in (jobdesk_path, bootstrap_path, preflight_path, dod_doc_path):
        if not os.path.isfile(req_path):
            return False, f"File wajib tidak ditemukan: {os.path.relpath(req_path, ROOT_DIR)}"

    try:
        py_compile.compile(preflight_path, doraise=True)
    except py_compile.PyCompileError as e:
        return False, f"Sintaks raspi_preflight.py gagal: {e}"

    with open(bootstrap_path, "rb") as fb:
        if b"\r\n" in fb.read():
            return False, "tools/raspi_bootstrap.sh mengandung CRLF (\\r\\n); wajib LF murni untuk bash Linux!"

    try:
        with open(jobdesk_path, "r", encoding="utf-8") as f:
            jd = json.load(f)
        divs = jd.get("divisions", [])
        if len(divs) != 6:
            return False, f"jobdesk_divisi.json harus berisi 6 divisi (ditemukan {len(divs)})."
        by_file = {str(item["file"]): item for item in hw_summaries}
        for d in divs:
            rf = d.get("report_file", "")
            if rf not in by_file:
                return False, f"Divisi {d.get('id')}: report_file '{rf}' tidak ditemukan di laporan_uji/."
            expected_b = int(by_file[rf]["b_tot"])
            actual_b = len(d.get("tahap_b_commands", []))
            if expected_b != actual_b:
                return False, f"Divisi {d.get('id')}: jumlah tahap_b_commands ({actual_b}) != ceklis Tahap B di {rf} ({expected_b})."
            if not d.get("current_announcement") or not d.get("current_tasks"):
                return False, f"Divisi {d.get('id')}: current_announcement / current_tasks belum diisi di jobdesk_divisi.json."
        return True, "Valid (6 divisi, pengumuman & tugas aktif, 5 milestone, preflight & bootstrap LF siap)."
    except Exception as e:
        return False, f"Gagal memvalidasi jobdesk_divisi.json: {e}"


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


def _git_run(args: List[str]) -> Tuple[int, str]:
    """Jalankan perintah Git read-only di ROOT_DIR dan kembalikan (returncode, stdout)."""
    try:
        proc = subprocess.run(
            ["git", "-C", ROOT_DIR] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return proc.returncode, proc.stdout.strip()
    except Exception as exc:
        return 1, str(exc)


def _load_division_rules() -> List[Dict[str, object]]:
    """Muat aturan branch dan file eksklusif dari tools/jobdesk_divisi.json."""
    jobdesk_path = os.path.join(ROOT_DIR, "tools", "jobdesk_divisi.json")
    try:
        with open(jobdesk_path, "r", encoding="utf-8") as f:
            return json.load(f).get("divisions", [])
    except Exception:
        return []


def _allowed_patterns_for_branch(branch_short: str, divisions: List[Dict[str, object]]) -> Tuple[str, List[str]]:
    """Cocokkan nama branch anggota dengan divisi dan daftar file eksklusifnya."""
    low = branch_short.lower()
    if "hmi" in low and "tft" in low:
        patterns: List[str] = []
        for d in divisions:
            if d.get("id") in (4, 5):
                patterns.extend(d.get("allowed_files", []))
        return "Divisi 4+5 (hmi+tft)", patterns

    for d in divisions:
        div_id = d.get("id")
        if div_id == 1:
            continue
        if f"divisi-{div_id}" in low or f"div{div_id}" in low:
            return f"Divisi {div_id}", list(d.get("allowed_files", []))

    keywords = {
        2: ("vacum", "vacuum", "relay", "buzzer", "estop"),
        3: ("led", "ws2812"),
        4: ("lcd", "tft", "ili9341"),
        5: ("hmi", "web"),
        6: ("qa", "mqtt", "nodered"),
    }
    for div_id, kws in keywords.items():
        if any(k in low for k in kws):
            for d in divisions:
                if d.get("id") == div_id:
                    return f"Divisi {div_id}", list(d.get("allowed_files", []))
    return "Tidak Terpetakan", []


def _check_branch_files(changed_paths: List[str], patterns: List[str]) -> Tuple[List[str], List[str]]:
    """Pisahkan file yang melanggar cache (.pyc) dan file di luar batas divisi."""
    cache_hits = [p for p in changed_paths if "__pycache__" in p or p.endswith((".pyc", ".pyo"))]
    if not patterns:
        return cache_hits, []
    out_of_scope = [
        p for p in changed_paths
        if p not in cache_hits and not any(fnmatch.fnmatch(p, pat) for pat in patterns)
    ]
    return cache_hits, out_of_scope


def audit_remote_branches(do_fetch: bool = False) -> List[Dict[str, object]]:
    """Audit seluruh branch remote terhadap origin/main tanpa mengubah working tree."""
    if do_fetch:
        _git_run(["fetch", "origin", "--prune"])

    rc, refs_out = _git_run(["for-each-ref", "--format=%(refname:short)", "refs/remotes/origin/"])
    if rc != 0:
        return []

    divisions = _load_division_rules()
    results: List[Dict[str, object]] = []
    for ref in sorted(refs_out.splitlines()):
        ref = ref.strip()
        if not ref or ref in ("origin", "origin/HEAD", "origin/main"):
            continue

        short = ref[len("origin/"):] if ref.startswith("origin/") else ref
        div_label, patterns = _allowed_patterns_for_branch(short, divisions)

        rc_cnt, cnt_out = _git_run(["rev-list", "--count", f"origin/main..{ref}"])
        ahead = int(cnt_out) if rc_cnt == 0 and cnt_out.isdigit() else 0
        rc_bh, bh_out = _git_run(["rev-list", "--count", f"{ref}..origin/main"])
        behind = int(bh_out) if rc_bh == 0 and bh_out.isdigit() else 0

        _, last_info = _git_run(["log", "-1", "--format=%h|%an|%s", ref])
        parts = (last_info.split("|", 2) + ["", ""])[:3]
        commit_hash, author, subject = parts[0], parts[1], parts[2]

        if ahead == 0:
            _, tip_sha = _git_run(["rev-parse", ref])
            _, fp_out = _git_run(["rev-list", "--first-parent", "origin/main"])
            is_main_checkpoint = bool(
                tip_sha
                and tip_sha in fp_out.splitlines()
                and subject.startswith(("Update v", "Tambah v", "Refactor ", "Merge ", "initial commit"))
            )
            if is_main_checkpoint and behind > 0:
                status_idle = "BELUM_ADA_COMMIT"
                note_idle = f"Cabang masih di titik main lama tanpa commit baru (tertinggal {behind} commit)."
            else:
                status_idle = "SUDAH_MERGED"
                note_idle = "Sinkron / hasil kerja branch sudah ter-merge ke main."
            results.append({
                "branch": ref,
                "divisi": div_label,
                "ahead": 0,
                "behind": behind,
                "commit": commit_hash,
                "author": author,
                "subject": subject,
                "files": [],
                "cache_hits": [],
                "out_of_scope": [],
                "conflict": False,
                "status": status_idle,
                "note": note_idle,
            })
            continue

        rc_mb, mb = _git_run(["merge-base", "origin/main", ref])
        diff_range = f"{mb}..{ref}" if rc_mb == 0 and mb else f"origin/main..{ref}"
        _, diff_out = _git_run(["diff", "--name-only", diff_range])
        files = [f.strip() for f in diff_out.splitlines() if f.strip()]
        cache_hits, out_of_scope = _check_branch_files(files, patterns)

        rc_mt, _ = _git_run(["merge-tree", "--write-tree", "origin/main", ref])
        has_conflict = rc_mt != 0

        notes: List[str] = []
        if has_conflict:
            notes.append("Ada Merge Conflict vs origin/main")
        if cache_hits:
            notes.append(f"Mengandung cache Python ({len(cache_hits)} file)")
        if out_of_scope:
            notes.append(f"Ubah file luar divisi ({len(out_of_scope)} file)")
        if not notes:
            notes.append("0 konflik, bersih, siap dipertimbangkan untuk merge.")

        status = "PERLU_REVISI" if (has_conflict or cache_hits or out_of_scope) else "SIAP_MERGE"
        results.append({
            "branch": ref,
            "divisi": div_label,
            "ahead": ahead,
            "commit": commit_hash,
            "author": author,
            "subject": subject,
            "files": files,
            "cache_hits": cache_hits,
            "out_of_scope": out_of_scope,
            "conflict": has_conflict,
            "status": status,
            "note": "; ".join(notes),
        })
    return results


def audit_current_branch_diff() -> Tuple[str, List[str], List[str], List[str]]:
    """Cek perubahan branch saat ini vs origin/main untuk lampiran GitHub Actions Summary."""
    _, cur_branch = _git_run(["rev-parse", "--abbrev-ref", "HEAD"])
    ref_name = os.environ.get("GITHUB_REF_NAME") or cur_branch
    divisions = _load_division_rules()
    div_label, patterns = _allowed_patterns_for_branch(ref_name, divisions)

    rc_mb, mb = _git_run(["merge-base", "origin/main", "HEAD"])
    if rc_mb != 0 or not mb:
        return ref_name, [], [], []
    _, diff_out = _git_run(["diff", "--name-only", f"{mb}..HEAD"])
    files = [f.strip() for f in diff_out.splitlines() if f.strip()]
    if ref_name in ("main", "core-raspi-backend"):
        return ref_name, files, [], []
    cache_hits, out_of_scope = _check_branch_files(files, patterns)
    return f"{ref_name} ({div_label})", files, cache_hits, out_of_scope


def format_audit_markdown(
    branch_results: List[Dict[str, object]],
    checks: List[Tuple[str, bool, str]],
    hw_summaries: List[Dict[str, object]],
    ci_diff: Optional[Tuple[str, List[str], List[str], List[str]]] = None,
) -> str:
    """Format hasil audit branch, cek integrasi, dan progres hardware sebagai Markdown."""
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    lines = [f"# Laporan Otomatis Integrasi & Audit Branch DECY-13 ({ts})", ""]

    if ci_diff is not None:
        label, files, caches, oos = ci_diff
        lines.append(f"## Perubahan Branch Aktif (`{label}` vs `origin/main`)")
        if files:
            for fp in files[:30]:
                tag = " *(cache!)*" if fp in caches else (" *(luar batas divisi!)*" if fp in oos else "")
                lines.append(f"- `{fp}`{tag}")
            if len(files) > 30:
                lines.append(f"- *...dan {len(files) - 30} file lainnya*")
        else:
            lines.append("- *(Tidak ada selisih file dibanding `origin/main` atau commit berada di `main`)*")
        lines.append("")

    if branch_results:
        lines.extend([
            "## Status Branch Remote Terhadap `origin/main`",
            "",
            "| Branch | Divisi | Commit Baru | Status | File Diubah | Catatan Audit |",
            "| :--- | :--- | :---: | :--- | :--- | :--- |",
        ])
        icon_map = {
            "SUDAH_MERGED": "✅",
            "BELUM_ADA_COMMIT": "⏳",
            "SIAP_MERGE": "🚀",
            "PERLU_REVISI": "⚠️",
        }
        for b in branch_results:
            ic = icon_map.get(str(b["status"]), "•")
            f_list = ", ".join(f"`{f}`" for f in list(b["files"])[:4])
            if len(list(b["files"])) > 4:
                f_list += f" *(+{len(list(b['files'])) - 4} lain)*"
            if not f_list:
                f_list = "—"
            lines.append(
                f"| `{b['branch']}` (`{b['commit']}`) | {b['divisi']} | {b['ahead']} | "
                f"{ic} **{b['status']}** | {f_list} | {b['note']} |"
            )
        lines.append("")

    lines.extend([
        "## Hasil Pemeriksaan Integrasi",
        "",
        "| Pemeriksaan | Status | Keterangan |",
        "| :--- | :---: | :--- |",
    ])
    for name, passed, detail in checks:
        lines.append(f"| {name} | {'✅ LULUS' if passed else '❌ GAGAL'} | {detail} |")
    lines.append("")

    if hw_summaries:
        lines.extend([
            "## Rapor Uji Hardware (`laporan_uji/`)",
            "",
            "| Divisi | Status | Tahap A (Laptop) | Tahap B (Fisik RPi) |",
            "| :--- | :--- | :---: | :---: |",
        ])
        for item in hw_summaries:
            lines.append(
                f"| {item['divisi']} | `{item['status']}` | "
                f"{item['a_done']}/{item['a_tot']} | {item['b_done']}/{item['b_tot']} |"
            )
        lines.append("")
    return "\n".join(lines)


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
Buka halaman depan GitHub repo kita (`README.md`) dan `laporan_uji/JOBDESK_DAN_DOD.md` untuk melihat:
1. Divisi mana yang sudah *✅ Merged*, masih *🟡 Draft Laptop (Belum Uji Raspi)*, atau *⚠️ Perlu Revisi*.
2. *Prompt AI Konteks Terbaru* per divisi (tinggal copy-paste kalau kalian mulai chat baru dengan AI Web maupun CLI!).
3. Jika kamu menguji memakai Raspberry Pi 3B+ sendiri, jalankan dulu:
   `bash tools/raspi_bootstrap.sh`
   `python3 tools/raspi_preflight.py --divisi <NOMOR_DIVISIMU>`
   agar OS/SPI/Audio/Mosquitto otomatis siap dan muncul daftar perintah uji Tahap B divisimu!
4. Jangan lupa isi & centang jujur kartu `laporan_uji/UJI_DIVISI_X_*.md` milikmu sebelum `git push` (Tahap B HANYA boleh dicentang setelah tes alat fisik Raspi nyata!).

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
    parser.add_argument("--ci-summary", action="store_true", help="Tulis ringkasan perubahan branch & ceklis ke GITHUB_STEP_SUMMARY")
    parser.add_argument("--cek-branch", action="store_true", help="Audit seluruh branch remote yang belum di-merge terhadap origin/main")
    parser.add_argument("--fetch", action="store_true", help="Jalankan git fetch origin --prune sebelum --cek-branch")
    parser.add_argument(
        "--simpan-audit",
        nargs="?",
        const=os.path.join(os.path.expanduser("~"), "decy13_qa_reports", "AUDIT_BRANCH_TERBARU.md"),
        default=None,
        help="Simpan lampiran laporan audit Markdown (default ~/decy13_qa_reports/AUDIT_BRANCH_TERBARU.md)",
    )
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

    ok_jd, msg_jd = check_jobdesk_and_preflight(hw_summaries)
    checks.append(("Jobdesk, Preflight & Bootstrap RPi", ok_jd, msg_jd))

    all_passed = True
    for name, passed, detail in checks:
        icon = "[LULUS]" if passed else "[GAGAL]"
        print(f"  {icon} {name:<38} -> {detail}")
        if not passed:
            all_passed = False

    if hw_summaries:
        tot_a_done = sum(int(i["a_done"]) for i in hw_summaries)
        tot_a_all = max(1, sum(int(i["a_tot"]) for i in hw_summaries))
        tot_b_done = sum(int(i["b_done"]) for i in hw_summaries)
        tot_b_all = max(1, sum(int(i["b_tot"]) for i in hw_summaries))
        print("\n" + "-" * 70)
        print(
            f"  RINGKASAN STATUS UJI HARDWARE RASPI PER DIVISI "
            f"(Total Laptop: {tot_a_done}/{tot_a_all} [{100*tot_a_done//tot_a_all}%] | "
            f"Raspi Fisik: {tot_b_done}/{tot_b_all} [{100*tot_b_done//tot_b_all}%])"
        )
        print("-" * 70)
        for item in hw_summaries:
            print(
                f"  - {item['divisi']:<10} | {str(item['status']):<23} "
                f"| Laptop {item['a_done']}/{item['a_tot']} | Raspi Fisik {item['b_done']}/{item['b_tot']}"
            )
        print("  Panduan uji di RPi anggota: bash tools/raspi_bootstrap.sh && python3 tools/raspi_preflight.py --divisi <1..6>")

    branch_results: List[Dict[str, object]] = []
    if args.cek_branch or args.fetch or args.simpan_audit:
        branch_results = audit_remote_branches(do_fetch=(args.fetch or bool(args.simpan_audit and args.fetch)))
        print("\n" + "-" * 70)
        print("  AUDIT BRANCH REMOTE VS origin/main (READ-ONLY)")
        print("-" * 70)
        for br in branch_results:
            print(
                f"  - {str(br['branch']):<42} | {str(br['status']):<16} "
                f"| ahead={br['ahead']} | {br['note']}"
            )
            if br["files"]:
                print(f"    file: {', '.join(list(br['files'])[:6])}")

    if args.simpan_audit:
        out_path = os.path.abspath(os.path.expanduser(args.simpan_audit))
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        md_text = format_audit_markdown(branch_results, checks, hw_summaries)
        with open(out_path, "w", encoding="utf-8") as mf:
            mf.write(md_text)
        print(f"\n  [LAMPIRAN DISIMPAN] {out_path}")

    if args.ci_summary:
        summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary_file:
            ci_diff = audit_current_branch_diff()
            md_ci = format_audit_markdown([], checks, hw_summaries, ci_diff=ci_diff)
            with open(summary_file, "a", encoding="utf-8") as sf:
                sf.write(md_ci + "\n")

    if not args.ci:
        branches = get_remote_branches()
        print_wa_announcer(args.versi, args.catatan, branches, all_passed, hw_summaries)

    if not all_passed:
        print("\n[PERINGATAN] Ada pemeriksaan yang GAGAL. Periksa detail di atas sebelum merge!")
        sys.exit(1)

    print("\n[OK] Seluruh pemeriksaan integrasi LULUS!")


if __name__ == "__main__":
    main()
