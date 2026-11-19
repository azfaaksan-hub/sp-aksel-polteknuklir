#!/usr/bin/env python3
"""
SISTEM SAFE-PULL & ISOLASI FILE ANTI-RUSAK PER DIVISI (DECY-13)
=================================================================
Melindungi pekerjaan lokal anggota saat menarik update `origin/main`:
  1. Snapshot fisik seluruh file milik divisi & perubahan lokal ke
     `laporan_uji/backup_lokal/divisi_<N>_<YYYYMMDD_HHMMSS>/` (di-ignore Git).
  2. Membuat branch cadangan lokal `backup-divisi<N>-<YYYYMMDD_HHMMSS>`.
  3. Mengkarantina file di luar `allowed_files` divisi (khusus Divisi 2..6)
     agar tidak memicu merge conflict terhadap file divisi lain.
  4. Menjalankan `git fetch origin` dan `git merge origin/main --no-edit`,
     menyelesaikan konflik otomatis agar perubahan milik divisi sendiri
     tidak pernah tertimpa, lalu memulihkan perubahan lokal anggota.

Cara pakai:
  python tools/aman_pull_dan_sync.py --divisi 3
  python tools/aman_pull_dan_sync.py --divisi 3 --dry-run
  python tools/aman_pull_dan_sync.py --divisi 3 --restore-latest
"""

import argparse
import datetime
import fnmatch
import json
import os
import shutil
import subprocess
import sys
from typing import Dict, List, Optional, Set, Tuple

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOBDESK_PATH = os.path.join(ROOT_DIR, "tools", "jobdesk_divisi.json")
BACKUP_ROOT = os.path.join(ROOT_DIR, "laporan_uji", "backup_lokal")
BACKUP_REL_PREFIX = "laporan_uji/backup_lokal/"


def _git(args: List[str], check: bool = False) -> Tuple[int, str]:
    """Jalankan perintah Git pada ROOT_DIR dengan path UTF-8 tanpa octal-escape."""
    cmd = ["git", "-C", ROOT_DIR, "-c", "core.quotepath=false"] + args
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and proc.returncode != 0:
        raise RuntimeError(f"Perintah gagal ({' '.join(cmd)}):\n{proc.stdout.strip()}")
    return proc.returncode, proc.stdout.strip()


def _to_posix(rel_path: str) -> str:
    norm = rel_path.replace("\\", "/")
    while norm.startswith("./"):
        norm = norm[2:]
    return norm.lstrip("/")


def _matches_allowed(rel_posix: str, patterns: List[str]) -> bool:
    for pat in patterns:
        norm = _to_posix(pat)
        if fnmatch.fnmatch(rel_posix, norm):
            return True
        if norm.endswith("/*") and rel_posix.startswith(norm[:-1]):
            return True
    return False


def _is_ignored_internal(rel_posix: str) -> bool:
    return (
        rel_posix.startswith(BACKUP_REL_PREFIX)
        or rel_posix.startswith(".git/")
        or "/__pycache__/" in rel_posix
        or rel_posix.startswith("__pycache__/")
        or rel_posix.endswith((".pyc", ".pyo"))
    )


def _load_division(div_id: int) -> Dict[str, object]:
    with open(JOBDESK_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    for div in data.get("divisions", []):
        if int(div.get("id", 0)) == div_id:
            return div
    raise ValueError(f"Divisi {div_id} tidak ditemukan di {JOBDESK_PATH}")


def _parse_porcelain_z() -> Dict[str, str]:
    """Kembalikan peta {rel_posix_path: status_2char} dari working tree."""
    cmd = ["git", "-C", ROOT_DIR, "-c", "core.quotepath=false", "status", "--porcelain", "-z"]
    raw = subprocess.check_output(cmd)
    entries = raw.split(b"\0")
    result: Dict[str, str] = {}
    i = 0
    while i < len(entries):
        item = entries[i]
        if not item:
            i += 1
            continue
        text = item.decode("utf-8", errors="replace")
        code = text[:2]
        path = _to_posix(text[3:])
        result[path] = code
        if code[0] in ("R", "C") or code[1] in ("R", "C"):
            i += 1  # Lewati path sumber tambahan pada rename/copy
        i += 1
    return result


def _collect_local_allowed_files(patterns: List[str]) -> List[str]:
    """Cari seluruh file lokal pada repo yang cocok dengan allowed_files divisi."""
    matched: List[str] = []
    for root, dirs, files in os.walk(ROOT_DIR):
        dirs[:] = [
            d for d in dirs
            if d not in (".git", "__pycache__", ".venv", "venv", "node_modules")
        ]
        for fname in files:
            full = os.path.join(root, fname)
            rel = _to_posix(os.path.relpath(full, ROOT_DIR))
            if _is_ignored_internal(rel):
                continue
            if _matches_allowed(rel, patterns):
                matched.append(rel)
    return sorted(set(matched))


def _commit_touched_paths(base_ref: str) -> List[str]:
    """Daftar file yang diubah oleh commit lokal sejak merge-base dengan base_ref."""
    rc, mb = _git(["merge-base", "HEAD", base_ref])
    if rc != 0 or not mb:
        return []
    rc2, out = _git(["diff", "--name-only", f"{mb}..HEAD"])
    if rc2 != 0 or not out:
        return []
    return [_to_posix(line) for line in out.splitlines() if line.strip()]


def _copy_to_backup(rel_paths: List[str], backup_dir: str, meta: Dict[str, object]) -> int:
    copied = 0
    for rel in rel_paths:
        src = os.path.join(ROOT_DIR, rel.replace("/", os.sep))
        if not os.path.isfile(src):
            continue
        dst = os.path.join(backup_dir, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1

    os.makedirs(backup_dir, exist_ok=True)
    with open(os.path.join(backup_dir, "_manifest.json"), "w", encoding="utf-8") as mf:
        json.dump(meta, mf, indent=2, ensure_ascii=False)
    return copied


def _snapshot_bytes(rel_paths: Set[str]) -> Dict[str, Optional[bytes]]:
    """Simpan isi byte terkini file dari disk (None jika file dihapus lokal)."""
    data: Dict[str, Optional[bytes]] = {}
    for rel in sorted(rel_paths):
        full = os.path.join(ROOT_DIR, rel.replace("/", os.sep))
        if os.path.isfile(full):
            with open(full, "rb") as f:
                data[rel] = f.read()
        else:
            data[rel] = None
    return data


def _write_bytes_map(bytes_map: Dict[str, Optional[bytes]]) -> List[str]:
    restored: List[str] = []
    for rel, content in bytes_map.items():
        full = os.path.join(ROOT_DIR, rel.replace("/", os.sep))
        if content is None:
            if os.path.isfile(full):
                os.remove(full)
                restored.append(f"{rel} (hapus lokal dipertahankan)")
            continue
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as f:
            f.write(content)
        restored.append(rel)
    return restored


def _quarantine_dirty_tree(
    dirty_map: Dict[str, str],
    allowed_patterns: List[str],
    div_id: int,
) -> List[str]:
    """Bersihkan sementara file modified/untracked sebelum merge agar git merge tidak tertolak."""
    cleaned_out_of_scope: List[str] = []
    tracked_existing: List[str] = []
    staged_new: List[str] = []

    for rel, code in dirty_map.items():
        if _is_ignored_internal(rel):
            continue
        is_allowed = div_id == 1 or _matches_allowed(rel, allowed_patterns)
        if not is_allowed:
            cleaned_out_of_scope.append(rel)
        if code == "??":
            full = os.path.join(ROOT_DIR, rel.replace("/", os.sep))
            if not is_allowed and os.path.isfile(full):
                os.remove(full)
        elif code[0] == "A":
            staged_new.append(rel)
        else:
            tracked_existing.append(rel)

    if staged_new:
        _git(["reset", "-q", "HEAD", "--"] + staged_new)
        for rel in staged_new:
            full = os.path.join(ROOT_DIR, rel.replace("/", os.sep))
            if os.path.isfile(full):
                os.remove(full)

    if tracked_existing:
        _git(["reset", "-q", "HEAD", "--"] + tracked_existing)
        _git(["checkout", "--"] + tracked_existing)
    return cleaned_out_of_scope


def _resolve_merge_conflicts(
    saved_allowed: Dict[str, Optional[bytes]],
    allowed_patterns: List[str],
    div_id: int,
) -> List[str]:
    """Selesaikan konflik merge secara deterministik: divisi sendiri menang, file lain ikut origin/main."""
    rc, unmerged = _git(["diff", "--name-only", "--diff-filter=U"])
    if rc != 0 or not unmerged:
        return []
    resolved: List[str] = []
    for line in unmerged.splitlines():
        rel = _to_posix(line.strip())
        if not rel:
            continue
        if (div_id == 1 or _matches_allowed(rel, allowed_patterns)) and rel in saved_allowed:
            _write_bytes_map({rel: saved_allowed[rel]})
            _git(["add", "--", rel])
            resolved.append(f"{rel} (pertahankan versi Divisi {div_id})")
        else:
            rc_t, _ = _git(["checkout", "--theirs", "--", rel])
            if rc_t == 0:
                _git(["add", "--", rel])
                resolved.append(f"{rel} (ambil versi terbaru origin/main)")
            else:
                _git(["rm", "-f", "--", rel])
                resolved.append(f"{rel} (sinkron hapus dengan origin/main)")
    return resolved


def restore_latest_backup(div_id: int, dry_run: bool) -> int:
    """Pulihkan file divisi dari snapshot backup lokal terbaru."""
    if not os.path.isdir(BACKUP_ROOT):
        print(f"[INFO] Belum ada folder backup di {BACKUP_REL_PREFIX}")
        return 1

    prefix = f"divisi_{div_id}_"
    candidates = sorted(
        d for d in os.listdir(BACKUP_ROOT)
        if d.startswith(prefix) and os.path.isdir(os.path.join(BACKUP_ROOT, d))
    )
    if not candidates:
        print(f"[INFO] Belum ditemukan backup untuk Divisi {div_id} di {BACKUP_REL_PREFIX}")
        return 1

    latest_dir = os.path.join(BACKUP_ROOT, candidates[-1])
    files_to_restore: List[str] = []
    for root, _, files in os.walk(latest_dir):
        for fname in files:
            if fname == "_manifest.json":
                continue
            full = os.path.join(root, fname)
            rel = _to_posix(os.path.relpath(full, latest_dir))
            files_to_restore.append(rel)

    print(f"[RESTORE] Sumber backup: {BACKUP_REL_PREFIX}{candidates[-1]}/ ({len(files_to_restore)} file)")
    for rel in files_to_restore:
        print(f"  - {rel}")
    if dry_run:
        print("[DRY-RUN] Tidak menulis file karena --dry-run aktif.")
        return 0

    for rel in files_to_restore:
        src = os.path.join(latest_dir, rel.replace("/", os.sep))
        dst = os.path.join(ROOT_DIR, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
    print(f"[OK] {len(files_to_restore)} file berhasil dipulihkan dari backup terbaru.")
    return 0


def run_safe_sync(div_id: int, dry_run: bool) -> int:
    """Jalankan prosedur backup berlapis -> karantina file luar divisi -> safe merge origin/main."""
    div = _load_division(div_id)
    allowed_patterns = [str(p) for p in div.get("allowed_files", [])]
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    rc_br, current_branch = _git(["rev-parse", "--abbrev-ref", "HEAD"])
    if rc_br != 0 or current_branch == "HEAD":
        print("[ERROR] Posisi Git sedang detached HEAD atau bukan repo Git yang valid.")
        return 1

    merge_head = os.path.join(ROOT_DIR, ".git", "MERGE_HEAD")
    if os.path.exists(merge_head):
        print("[ERROR] Masih ada proses merge yang belum selesai (.git/MERGE_HEAD aktif). Selesaikan/abort dulu.")
        return 1

    dirty_map = {
        k: v for k, v in _parse_porcelain_z().items()
        if not _is_ignored_internal(k)
    }
    local_allowed = _collect_local_allowed_files(allowed_patterns)
    dirty_allowed = {k for k in dirty_map if div_id == 1 or _matches_allowed(k, allowed_patterns)}
    dirty_out = [k for k in dirty_map if div_id != 1 and not _matches_allowed(k, allowed_patterns)]

    if not dry_run:
        print("[1/4] Mengambil info terbaru dari origin (`git fetch origin`)...")
        rc_f, out_f = _git(["fetch", "origin"])
        if rc_f != 0:
            print(f"[ERROR] git fetch origin gagal:\n{out_f}")
            return 1
    else:
        print("[DRY-RUN] Melewati `git fetch`, membuat branch backup, & `git merge` (mode simulasi aman).")

    committed_touched = _commit_touched_paths("origin/main")
    committed_allowed = {
        p for p in committed_touched
        if div_id == 1 or _matches_allowed(p, allowed_patterns)
    }
    committed_out = [
        p for p in committed_touched
        if div_id != 1 and not _matches_allowed(p, allowed_patterns)
    ]

    # File milik divisi yang benar-benar berubah lokal (harus dipertahankan pasca-merge)
    preserve_set = dirty_allowed | committed_allowed
    backup_list = sorted(set(local_allowed) | set(dirty_map.keys()) | preserve_set)
    backup_dir = os.path.join(BACKUP_ROOT, f"divisi_{div_id}_{ts}")
    backup_branch = f"backup-divisi{div_id}-{ts}"

    print("=" * 74)
    print(f"  SAFE-PULL & SINKRONISASI ANTI-RUSAK — DIVISI {div_id}")
    print(f"  Branch Lokal       : {current_branch}")
    print(f"  Target Sinkron     : origin/main")
    print(f"  File Backup Fisik  : {len(backup_list)} file -> {BACKUP_REL_PREFIX}divisi_{div_id}_{ts}/")
    print(f"  Branch Cadangan    : {backup_branch}")
    print(f"  Pekerjaan Di-Protect: {len(preserve_set)} file berubah milik Divisi {div_id}")
    if dirty_out or committed_out:
        print(f"  ⚠️ File Luar Divisi: {len(dirty_out)} uncommitted, {len(committed_out)} di commit cabang")
    else:
        print(f"  File Luar Divisi   : 0 (bersih)")
    print("=" * 74)

    if dry_run:
        if preserve_set:
            print("\nFile milik divisimu yang akan diproteksi pasca-merge:")
            for p in sorted(preserve_set):
                print(f"  - {p}")
        if dirty_out:
            print("\nFile luar divisi yang akan diamankan ke backup & dikarantina sebelum merge:")
            for p in dirty_out:
                print(f"  - {p}")
        print("\n[DRY-RUN SELESAI] Jalankan tanpa `--dry-run` untuk mengeksekusi sinkronisasi aman.")
        return 0

    meta = {
        "timestamp": ts,
        "division": div_id,
        "branch": current_branch,
        "backup_branch": backup_branch,
        "dirty_map": dirty_map,
        "committed_allowed": sorted(committed_allowed),
        "committed_out_of_scope": committed_out,
    }
    copied = _copy_to_backup(backup_list, backup_dir, meta)
    print(f"[1/4 OK] {copied} file dibackup ke {BACKUP_REL_PREFIX}divisi_{div_id}_{ts}/")

    rc_b, out_b = _git(["branch", backup_branch, "HEAD"])
    if rc_b != 0:
        print(f"[ERROR] Gagal membuat branch cadangan {backup_branch}: {out_b}")
        return 1
    print(f"[1/4 OK] Branch cadangan dibuat: {backup_branch}")

    saved_uncommitted_allowed = _snapshot_bytes(dirty_allowed)
    saved_all_protected = _snapshot_bytes(preserve_set)

    print("[2/4] Mengkarantina perubahan luar divisi & membersihkan working tree sementara...")
    quarantined = _quarantine_dirty_tree(dirty_map, allowed_patterns, div_id)
    for q in quarantined:
        print(f"  - Dikarantina (sudah dibackup): {q}")

    print("[3/4] Menjalankan `git merge origin/main --no-edit`...")
    rc_m, out_m = _git(["merge", "origin/main", "--no-edit"])
    if rc_m != 0:
        print("[INFO] Konflik terdeteksi saat merge — menyelesaikan otomatis dengan proteksi file divisi...")
        res = _resolve_merge_conflicts(saved_all_protected, allowed_patterns, div_id)
        for item in res:
            print(f"  * {item}")
        # Pastikan tidak ada konflik tersisa sebelum commit merge
        rc_u, rem = _git(["diff", "--name-only", "--diff-filter=U"])
        if rc_u == 0 and rem:
            print(f"[ERROR] Masih ada konflik belum terselesaikan:\n{rem}")
            print(f"Workspace Anda aman di branch `{backup_branch}` & folder `{backup_dir}`.")
            return 1
        _git(["commit", "--no-edit"], check=True)
    else:
        if out_m:
            print(f"  {out_m}")

    # Pastikan file di luar allowed_files yang berubah pada commit lama tidak bentrok dengan origin/main
    if div_id != 1 and committed_out:
        print("[3B] Memastikan file luar divisi selaras dengan origin/main...")
        for rel in committed_out:
            rc_co, _ = _git(["checkout", "origin/main", "--", rel])
            if rc_co != 0:
                _git(["rm", "-f", "--", rel])

    # Pulihkan pekerjaan uncommitted milik divisi sendiri yang belum di-commit
    if saved_uncommitted_allowed:
        restored = _write_bytes_map(saved_uncommitted_allowed)
        print(f"[4/4] Memulihkan {len(restored)} file pekerjaan lokal Divisi {div_id}:")
        for r in restored:
            print(f"  + {r}")
    else:
        print("[4/4] Seluruh pekerjaan di commit cabang tetap utuh & sinkron dengan origin/main.")

    print("\n" + "-" * 74)
    print("  LANGKAH SELANJUTNYA UNTUK ANGGOTA:")
    print("  1. Cek perubahan lokal  : git status")
    print("  2. Uji integrasi proyek : python tools/cek_integrasi_dan_announcer.py --ci")
    print(f"  3. Jika sudah siap push : git add <file_divisimu> && git commit -m \"sync(divisi-{div_id}): update progress\" && git push origin {current_branch}")
    print(f"  * Catatan: bila ada yang perlu diambil lagi dari versi sebelum pull, cek `{backup_dir}`")
    print(f"    atau jalankan `python tools/aman_pull_dan_sync.py --divisi {div_id} --restore-latest`")
    print("-" * 74)
    return 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Safe-Pull & Isolasi File Anti-Rusak per Divisi DECY-13"
    )
    parser.add_argument(
        "--divisi", type=int, choices=[1, 2, 3, 4, 5, 6], required=True,
        help="Nomor divisi anggota (1..6)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Simulasi cek file yang akan diamankan tanpa menjalankan git merge"
    )
    parser.add_argument(
        "--restore-latest", action="store_true",
        help="Pulihkan file divisi dari folder backup lokal terakhir"
    )
    args = parser.parse_args()

    if args.restore_latest:
        return restore_latest_backup(args.divisi, args.dry_run)
    return run_safe_sync(args.divisi, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
