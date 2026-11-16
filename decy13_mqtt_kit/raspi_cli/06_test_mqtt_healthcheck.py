#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DIVISI 6 (JARINGAN MQTT, NODE-RED & QA): DIAGNOSTIC, HEALTHCHECK & COMMISSIONING TOOL
=====================================================================================
Penanggung Jawab : Anggota 6 (Divisi Jaringan MQTT, Node-RED & Commissioning QA)
Branch GitHub    : divisi-6-nodered-qa
File Terkait     : - raspi_cli/06_test_mqtt_healthcheck.py (File ini)
                   - nodered/flows_mqtt_decy13.json
                   - instruksi untuk projek sp/CHECKLIST_COMMISSIONING.txt

Fungsi Alat Ini:
1. JARINGAN   : uji port TCP & WebSocket Mosquitto, waktu CONNACK, dan latensi
                round-trip broker (ping ke topic decy13/qa/ping/<id>).
2. KONTRAK    : validasi JSON `decy13/rpi/state` (22 field wajib, tipe data, rentang
                fisika, nilai NaN/Infinity, konsistensi antar-field) untuk Web HMI
                (Divisi 5) dan Node-RED (Divisi 6).
3. TELEMETRI  : frekuensi rata-rata (target ~5.0 Hz / 200 ms), jitter, p95, interval
                maksimum, dan estimasi paket hilang.
4. UJI 7 TAHAP: (--auto) mengirim perintah berurutan, memverifikasi efeknya di state,
                mengukur latensi perintah->state, dan mencatat tahap (stage) yang
                benar-benar teramati.
5. NODE-RED   : cek port 1880 dan validasi statis flows_mqtt_decy13.json terhadap
                topic & kontrak state.
6. LAPORAN    : (--report) hasil disimpan sebagai .txt bergaya checklist (siap ditempel
                ke CHECKLIST_COMMISSIONING.txt) dan .json (data mentah).
7. MENU       : menu interaktif untuk mengirim perintah `decy13/hmi/cmd` manual.

Cara Pakai:
  python 06_test_mqtt_healthcheck.py                          # cek cepat + menu interaktif
  python 06_test_mqtt_healthcheck.py --host 127.0.0.1 --no-menu
  python 06_test_mqtt_healthcheck.py --host 192.168.137.1 --duration 30 --no-menu
  python 06_test_mqtt_healthcheck.py --auto --report          # cek cepat + uji 7 tahap + laporan
  python 06_test_mqtt_healthcheck.py --auto --estop --yes --report

Kode keluar: 0 = tidak ada GAGAL, 1 = ada GAGAL, 2 = broker tidak dapat dihubungi.

PERHATIAN: --auto mengirim perintah sungguhan (relay, buzzer, LED ikut bergerak) dan
mengubah state sistem untuk semua yang terhubung ke broker yang sama. Beri tahu tim
dulu sebelum menjalankannya. --estop meninggalkan sistem dalam kondisi E-Stop.
"""

import argparse
import json
import math
import os
import socket
import statistics
import sys
import threading
import time
import uuid
import warnings
from collections import deque
from datetime import datetime

warnings.filterwarnings("ignore", category=DeprecationWarning)

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("[ERROR] Library paho-mqtt belum terinstall. Jalankan: pip install paho-mqtt")
    sys.exit(1)

# ---------------------------------------------------------------------------
# KONFIGURASI & KONSTANTA
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config_hardware.json")
DEFAULT_FLOWS_PATH = os.path.normpath(
    os.path.join(BASE_DIR, "..", "nodered", "flows_mqtt_decy13.json"))

_MISSING = object()


def _find(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            r = _find(v, key)
            if r is not _MISSING:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = _find(v, key)
            if r is not _MISSING:
                return r
    return _MISSING


def find_key(obj, key, default=None):
    """Cari key di mana pun di dalam config (nested), agar tidak bergantung struktur."""
    r = _find(obj, key)
    return default if r is _MISSING else r


def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {}, "isi config_hardware.json bukan objek JSON"
        return data, None
    except (OSError, ValueError) as e:
        return {}, f"gagal membaca {CONFIG_PATH}: {e}"


CFG, CFG_ERROR = load_config()


def to_int(v, default):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


REQUIRED_STATE_KEYS = [
    "power", "vacuum", "rf", "magnet", "interlocks", "beam",
    "exposureActive", "emergency", "stage", "mode",
    "lcd_line1", "lcd_line2", "lcd_line3", "lcd_line4",
    "pressure", "beamEnergy", "beamCurrent", "targetCurrent",
    "activeLedIdx", "shootLedIdx", "buzzerActive", "logs"
]

# Tipe data yang diharapkan per field. Pelanggaran tipe = PERINGATAN (bukan GAGAL),
# karena tipe asli ditentukan daemon Divisi 1. Sesuaikan di sini jika kontrak berubah.
FLAG = (bool, int)
NUM = (int, float)
CONTRACT_TYPES = {
    "power": FLAG, "vacuum": FLAG, "rf": FLAG, "magnet": FLAG,
    "interlocks": (bool, int, dict, list),
    "beam": FLAG, "exposureActive": FLAG, "emergency": FLAG,
    "stage": (int,), "mode": (str,),
    "lcd_line1": (str,), "lcd_line2": (str,), "lcd_line3": (str,), "lcd_line4": (str,),
    "pressure": NUM, "beamEnergy": NUM, "beamCurrent": NUM, "targetCurrent": NUM,
    "activeLedIdx": (int,), "shootLedIdx": (int,),
    "buzzerActive": FLAG, "logs": (list,),
}

# Field yang ditampilkan perubahannya saat perintah dikirim.
FLAG_FIELDS = ["power", "vacuum", "rf", "magnet", "interlocks", "beam",
               "exposureActive", "emergency", "stage", "mode", "buzzerActive"]

CMD_MENU = {
    "1": "TOGGLE_POWER", "2": "TOGGLE_VACUUM", "3": "TOGGLE_INTERLOCK",
    "4": "AUTO_INIT", "5": "START_BEAM", "6": "SHOOT", "7": "EMERGENCY_STOP",
}

MAX_BEAM_MEV = 13.0      # energi berkas maksimum siklotron DECY-13
BEAM_TOL = 0.05          # toleransi pembulatan (MeV)

# Ambang penilaian
RTT_WARN_MS, RTT_FAIL_MS = 100.0, 500.0     # latensi round-trip broker
CMD_WARN_MS, CMD_FAIL_MS = 500.0, 2000.0    # latensi perintah -> state
HZ_PASS_TOL, HZ_WARN_TOL = 0.10, 0.25       # penyimpangan frekuensi dari target
GAP_FACTOR = 1.5                            # interval > 1.5x nominal dianggap celah paket
MAX_GAP_WARN_MS = 1000.0                    # celah > 1 detik = telemetri tersendat

STATUS_LABEL = {"PASS": "LULUS", "WARN": "PERINGATAN", "FAIL": "GAGAL",
                "SKIP": "LEWATI", "INFO": "INFO"}
STATUS_BOX = {"PASS": "[x]", "WARN": "[!]", "FAIL": "[ ]", "SKIP": "[-]", "INFO": "[i]"}


# ---------------------------------------------------------------------------
# UTILITAS
# ---------------------------------------------------------------------------
def is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def is_on(v):
    """Interpretasi 'aktif' untuk bool/angka/dict/list (mis. interlocks per-pintu)."""
    if isinstance(v, dict):
        return bool(v) and all(is_on(x) for x in v.values())
    if isinstance(v, (list, tuple)):
        return bool(v) and all(is_on(x) for x in v)
    return bool(v)


def fmt_num(v, spec, default="-"):
    try:
        return format(v, spec)
    except (TypeError, ValueError):
        return default


def percentile(values, pct):
    if not values:
        return float("nan")
    v = sorted(values)
    k = max(0, min(len(v) - 1, int(math.ceil(pct / 100.0 * len(v))) - 1))
    return v[k]


def type_ok(value, types):
    if isinstance(value, bool) and bool not in types:
        return False
    return isinstance(value, types)


def _safe(pred, state):
    try:
        return bool(pred(state))
    except Exception:
        return False


def log_tail(state, n=2):
    logs = state.get("logs") if isinstance(state, dict) else None
    if not isinstance(logs, list) or not logs:
        return ""
    lines = [str(x)[:110] for x in logs[:n]]
    return " | log daemon: " + " / ".join(lines)


def tcp_probe(host, port, timeout=1.0):
    """Return (berhasil, ms_atau_pesan_error)."""
    t0 = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, (time.perf_counter() - t0) * 1000.0
    except OSError as e:
        return False, str(e)


def make_client(client_id, transport="tcp"):
    """Kompatibel paho-mqtt 1.x dan 2.x."""
    if hasattr(mqtt, "CallbackAPIVersion"):
        return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                           client_id=client_id, transport=transport)
    return mqtt.Client(client_id=client_id, transport=transport)


def confirm(prompt):
    try:
        return input(prompt).strip().lower() in ("y", "ya", "yes")
    except EOFError:
        return False


# ---------------------------------------------------------------------------
# PENCATAT HASIL UJI
# ---------------------------------------------------------------------------
class Report:
    def __init__(self):
        self.items = []
        self.extra = {}
        self.started = datetime.now()

    def add(self, cid, name, status, detail=""):
        self.items.append({"id": cid, "name": name, "status": status, "detail": detail})
        line = f"[{STATUS_LABEL[status]}] {cid} {name}"
        if detail:
            line += f" -> {detail}"
        print(line)

    def count(self, status):
        return sum(1 for i in self.items if i["status"] == status)

    def has_fail(self):
        return self.count("FAIL") > 0

    def summary_line(self):
        return (f"LULUS={self.count('PASS')}  PERINGATAN={self.count('WARN')}  "
                f"GAGAL={self.count('FAIL')}  LEWATI={self.count('SKIP')}")


# ---------------------------------------------------------------------------
# MONITOR MQTT (thread-safe)
# ---------------------------------------------------------------------------
class Monitor:
    """Klien MQTT yang menyimpan riwayat telemetri + mendukung tunggu-kondisi."""

    def __init__(self, host, port, topic_state, topic_cmd, transport="tcp", tag="qa"):
        self.host, self.port = host, port
        self.topic_state, self.topic_cmd = topic_state, topic_cmd
        suffix = uuid.uuid4().hex[:8]
        # client_id unik: dua klien ber-ID sama saling menendang di Mosquitto.
        self.client_id = f"decy13_{tag}_{suffix}"
        self.topic_ping = f"decy13/qa/ping/{suffix}"
        self.cond = threading.Condition()
        self.latest = None
        self.seq = 0
        self.history = deque(maxlen=6000)      # (seq, t_terima, state)
        self.bad_payloads = 0
        self.connected = threading.Event()
        self.subscribed = threading.Event()
        self.connect_rc = None
        self.connect_ms = None
        self._t_start = None
        self._pongs = {}
        self.client = make_client(self.client_id, transport)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_subscribe = self._on_subscribe
        self.client.on_message = self._on_message

    # --- callback (signature fleksibel untuk paho 1.x & 2.x) ---
    def _on_connect(self, client, userdata, flags, rc, *args):
        self.connect_rc = rc
        failed = rc.is_failure if hasattr(rc, "is_failure") else (rc != 0)
        if failed:
            return
        if self.connect_ms is None and self._t_start is not None:
            self.connect_ms = (time.perf_counter() - self._t_start) * 1000.0
        self.subscribed.clear()
        client.subscribe([(self.topic_state, 0), (self.topic_ping, 0)])
        self.connected.set()

    def _on_disconnect(self, client, userdata, *args):
        self.connected.clear()

    def _on_subscribe(self, client, userdata, mid, *args):
        self.subscribed.set()

    def _on_message(self, client, userdata, msg):
        t = time.perf_counter()
        if msg.topic == self.topic_ping:
            with self.cond:
                self._pongs[bytes(msg.payload)] = t
                self.cond.notify_all()
            return
        if msg.topic != self.topic_state:
            return
        try:
            data = json.loads(msg.payload.decode("utf-8"))
            if not isinstance(data, dict):
                raise ValueError("payload bukan objek JSON")
        except (ValueError, UnicodeDecodeError):
            self.bad_payloads += 1
            return
        with self.cond:
            self.seq += 1
            self.latest = data
            self.history.append((self.seq, t, data))
            self.cond.notify_all()

    # --- koneksi ---
    def connect(self, timeout=5.0):
        self._t_start = time.perf_counter()
        self.client.connect(self.host, self.port, 30)
        self.client.loop_start()
        ok = self.connected.wait(timeout)
        if ok:
            self.subscribed.wait(1.0)
        return ok

    def close(self):
        try:
            self.client.disconnect()
        except Exception:
            pass
        try:
            self.client.loop_stop()
        except Exception:
            pass

    # --- akses data ---
    def current(self):
        with self.cond:
            return self.latest

    def mark(self):
        with self.cond:
            return self.seq

    def since(self, seq):
        with self.cond:
            return [(t, s) for (q, t, s) in self.history if q > seq]

    def send(self, payload):
        """Kirim perintah ke topic_cmd. Return (t_ref, seq_sebelum_kirim)."""
        seq0 = self.mark()
        t_ref = time.perf_counter()
        self.client.publish(self.topic_cmd, json.dumps(payload))
        return t_ref, seq0

    def ping(self, timeout=1.0):
        """Round-trip ke broker (ms) lewat topic QA, atau None bila tidak ada balasan."""
        token = uuid.uuid4().hex.encode()
        t0 = time.perf_counter()
        self.client.publish(self.topic_ping, token)
        deadline = t0 + timeout
        with self.cond:
            while token not in self._pongs:
                rem = deadline - time.perf_counter()
                if rem <= 0:
                    return None
                self.cond.wait(rem)
            return (self._pongs.pop(token) - t0) * 1000.0

    def wait_for(self, pred, timeout, from_seq=None, t_ref=None):
        """
        Tunggu sampai ada paket state yang memenuhi pred(state).
        from_seq=None : cek state terakhir dulu, lalu paket-paket baru.
        from_seq=N    : periksa SEMUA paket dengan seq > N (tidak melewatkan kondisi sesaat).
        Return (berhasil, detik_sejak_t_ref, state).
        """
        t_start = time.perf_counter()
        if t_ref is None:
            t_ref = t_start
        deadline = t_start + timeout
        with self.cond:
            if from_seq is None:
                cursor = self.seq
                if self.latest is not None and _safe(pred, self.latest):
                    return True, 0.0, self.latest
            else:
                cursor = from_seq
            while True:
                fresh = []
                for entry in reversed(self.history):
                    if entry[0] <= cursor:
                        break
                    fresh.append(entry)
                for seq, t, st in reversed(fresh):
                    cursor = seq
                    if _safe(pred, st):
                        return True, max(0.0, t - t_ref), st
                remaining = deadline - time.perf_counter()
                if remaining <= 0:
                    return False, timeout, self.latest
                self.cond.wait(remaining)


# ---------------------------------------------------------------------------
# ANALISIS TELEMETRI & KONTRAK
# ---------------------------------------------------------------------------
def analyze_rate(msgs, target_hz):
    """msgs = [(t, state), ...]. Frekuensi dihitung dari (n-1) interval, bukan n paket."""
    n = len(msgs)
    if n < 2:
        return {"n": n}
    ts = [t for t, _ in msgs]
    intervals = [b - a for a, b in zip(ts, ts[1:])]
    span = ts[-1] - ts[0]
    nominal = 1.0 / target_hz
    gaps = [i for i in intervals if i > GAP_FACTOR * nominal]
    est_lost = sum(max(0, int(round(i / nominal)) - 1) for i in gaps)
    return {
        "n": n,
        "span_s": span,
        "hz": (n - 1) / span if span > 0 else float("nan"),
        "mean_ms": statistics.mean(intervals) * 1000.0,
        "std_ms": statistics.pstdev(intervals) * 1000.0,
        "min_ms": min(intervals) * 1000.0,
        "p95_ms": percentile(intervals, 95) * 1000.0,
        "max_ms": max(intervals) * 1000.0,
        "gaps": len(gaps),
        "est_lost": est_lost,
    }


def led_ranges(cfg):
    sp0 = to_int(find_key(cfg, "spiral_start_idx", 0), 0)
    sp1 = to_int(find_key(cfg, "spiral_end_idx", 47), 47)
    sh0 = to_int(find_key(cfg, "shoot_start_idx", 48), 48)
    sh1 = to_int(find_key(cfg, "shoot_end_idx", 63), 63)
    return {"spiral": (sp0, sp1), "shoot": (sh0, sh1), "led_max": max(sp1, sh1)}


def validate_state(s, rng):
    """Return (daftar_gagal, daftar_peringatan) untuk satu paket state."""
    fails, warns = [], []
    missing = [k for k in REQUIRED_STATE_KEYS if k not in s]
    if missing:
        fails.append("key hilang: " + ", ".join(missing))
    for k, types in CONTRACT_TYPES.items():
        if k in s and not type_ok(s[k], types):
            warns.append(f"{k}: tipe {type(s[k]).__name__}, diharapkan "
                         + "/".join(t.__name__ for t in types))
    # NaN / Infinity lolos di Python tetapi membuat JSON.parse() Web HMI error.
    for k, v in s.items():
        if isinstance(v, float) and not math.isfinite(v):
            fails.append(f"{k}={v} (NaN/Infinity bukan JSON valid di browser)")
    e = s.get("beamEnergy")
    if is_number(e) and not (-BEAM_TOL <= e <= MAX_BEAM_MEV + BEAM_TOL):
        fails.append(f"beamEnergy={e:.2f} di luar 0..{MAX_BEAM_MEV:g} MeV")
    p = s.get("pressure")
    if is_number(p) and p <= 0:
        fails.append("pressure <= 0 mbar (tidak fisis; skala log di LCD/HMI akan error)")
    for k in ("beamCurrent", "targetCurrent"):
        if is_number(s.get(k)) and s[k] < 0:
            fails.append(f"{k} negatif")
    for k in ("activeLedIdx", "shootLedIdx"):
        v = s.get(k)
        if isinstance(v, int) and not isinstance(v, bool):
            if not (v == -1 or 0 <= v <= rng["led_max"]):
                fails.append(f"{k}={v} di luar 0..{rng['led_max']} (atau -1)")
    if is_on(s.get("emergency")) and (is_on(s.get("beam")) or is_on(s.get("exposureActive"))):
        fails.append("E-Stop aktif tetapi beam/exposure masih aktif")
    if is_on(s.get("exposureActive")) and not is_on(s.get("beam")):
        warns.append("exposureActive aktif tanpa beam")
    return fails, warns


# ---------------------------------------------------------------------------
# PEMERIKSAAN JARINGAN & TELEMETRI
# ---------------------------------------------------------------------------
def check_websocket(report, host, ws_port, topic_state, topic_cmd):
    cid, name = "NET-03", f"WebSocket MQTT port {ws_port} (jalur Web HMI)"
    ok, info = tcp_probe(host, ws_port)
    if not ok:
        report.add(cid, name, "FAIL",
                   f"port tidak terbuka ({info}). Cek mosquitto.conf: 'listener {ws_port}' "
                   "+ 'protocol websockets'")
        return
    wm = Monitor(host, ws_port, topic_state, topic_cmd, transport="websockets", tag="ws")
    try:
        if not wm.connect(timeout=4.0):
            report.add(cid, name, "FAIL", "TCP terbuka tetapi handshake WebSocket/MQTT gagal")
            return
        got, dt, _ = wm.wait_for(lambda s: True, 3.0)
        if got:
            report.add(cid, name, "PASS",
                       f"terhubung via WebSocket dalam {wm.connect_ms:.0f} ms, telemetri diterima")
        else:
            report.add(cid, name, "WARN",
                       "terhubung via WebSocket tetapi belum ada telemetri dalam 3 s")
    except OSError as e:
        report.add(cid, name, "FAIL", f"gagal terhubung: {e}")
    finally:
        wm.close()


def check_ping(report, mon, count):
    cid, name = "NET-04", "Latensi round-trip broker"
    vals = []
    for _ in range(count):
        ms = mon.ping(timeout=1.0)
        if ms is not None:
            vals.append(ms)
        time.sleep(0.05)
    if not vals:
        report.add(cid, name, "WARN",
                   "tidak ada balasan ping (ACL broker mungkin memblokir topic decy13/qa/#)")
        return
    p95 = percentile(vals, 95)
    lost = count - len(vals)
    detail = (f"{len(vals)}/{count} balasan; rata-rata {statistics.mean(vals):.1f} ms, "
              f"p95 {p95:.1f} ms, maks {max(vals):.1f} ms")
    report.extra["ping_ms"] = {"mean": round(statistics.mean(vals), 2),
                               "p95": round(p95, 2), "max": round(max(vals), 2),
                               "lost": lost}
    if lost or p95 > RTT_FAIL_MS:
        status = "FAIL" if (lost > count // 4 or p95 > RTT_FAIL_MS) else "WARN"
    elif p95 > RTT_WARN_MS:
        status = "WARN"
    else:
        status = "PASS"
    report.add(cid, name, status, detail)


def check_contract(report, msgs, rng):
    cid, name = "TLM-02", "Kontrak JSON state"
    problems = {}
    seen_keys = set()
    for _, s in msgs:
        seen_keys.update(s.keys())
        fails, warns = validate_state(s, rng)
        for t in fails:
            problems[("FAIL", t)] = problems.get(("FAIL", t), 0) + 1
        for t in warns:
            problems[("WARN", t)] = problems.get(("WARN", t), 0) + 1
    fail_list = [f"{t} (x{c})" for (lv, t), c in problems.items() if lv == "FAIL"]
    warn_list = [f"{t} (x{c})" for (lv, t), c in problems.items() if lv == "WARN"]
    total = len(REQUIRED_STATE_KEYS)
    if fail_list:
        report.add(cid, name, "FAIL", "; ".join(fail_list[:5]))
    elif warn_list:
        report.add(cid, name, "WARN", "; ".join(warn_list[:5]))
    else:
        report.add(cid, name, "PASS",
                   f"{len(msgs)} paket divalidasi: {total}/{total} field wajib lengkap, "
                   "tipe & rentang sesuai")
    extra = sorted(seen_keys - set(REQUIRED_STATE_KEYS))
    if extra:
        report.add("TLM-02b", "Field di luar daftar wajib", "INFO",
                   ", ".join(extra) + " (tambahkan ke REQUIRED_STATE_KEYS bila dipakai HMI/Node-RED)")


def check_rate(report, stats, target_hz, cid_prefix="TLM"):
    """Hasilkan dua butir: frekuensi dan jitter/kehilangan paket."""
    if stats.get("n", 0) < 5:
        report.add(f"{cid_prefix}-03", "Frekuensi telemetri", "FAIL",
                   f"hanya {stats.get('n', 0)} paket dalam jendela ukur; terlalu sedikit untuk dinilai")
        report.add(f"{cid_prefix}-04", "Jitter & kehilangan paket", "SKIP", "data tidak cukup")
        return
    hz = stats["hz"]
    dev = abs(hz - target_hz) / target_hz
    status = "PASS" if dev <= HZ_PASS_TOL else ("WARN" if dev <= HZ_WARN_TOL else "FAIL")
    report.add(f"{cid_prefix}-03", "Frekuensi telemetri", status,
               f"{stats['n']} paket / {stats['span_s']:.1f} s = {hz:.2f} Hz "
               f"(target {target_hz:g} Hz, selisih {dev * 100:.0f}%)")
    nominal_ms = 1000.0 / target_hz
    if stats["gaps"] == 0 and stats["p95_ms"] <= 2 * nominal_ms:
        status = "PASS"
    elif stats["max_ms"] <= MAX_GAP_WARN_MS:
        status = "WARN"
    else:
        status = "FAIL"
    report.add(f"{cid_prefix}-04", "Jitter & kehilangan paket", status,
               f"interval rata-rata {stats['mean_ms']:.0f} ms, std {stats['std_ms']:.0f} ms, "
               f"p95 {stats['p95_ms']:.0f} ms, maks {stats['max_ms']:.0f} ms; "
               f"{stats['gaps']} celah (~{stats['est_lost']} paket hilang, estimasi)")
    report.extra["telemetry"] = {k: (round(v, 3) if isinstance(v, float) else v)
                                 for k, v in stats.items()}


def check_nodered(report, host, port):
    cid, name = "NR-01", f"Node-RED editor/dashboard port {port}"
    ok, info = tcp_probe(host, port)
    if ok:
        report.add(cid, name, "PASS", f"{host}:{port} dapat dijangkau ({info:.0f} ms)")
    else:
        report.add(cid, name, "WARN",
                   f"{host}:{port} tidak dapat dijangkau ({info}); jalankan 'node-red' bila "
                   "dashboard cadangan diperlukan")


def check_flows(report, path, topic_state, topic_cmd, tcp_port):
    cid, name = "NR-02", "Validasi statis flows_mqtt_decy13.json"
    if not os.path.isfile(path):
        report.add(cid, name, "SKIP", f"berkas tidak ditemukan: {path}")
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
        data = json.loads(raw)
    except (OSError, ValueError) as e:
        report.add(cid, name, "FAIL", f"tidak dapat dibaca / JSON rusak: {e}")
        return
    if not isinstance(data, list):
        report.add(cid, name, "FAIL", "format flows harus berupa array node")
        return
    nodes = [n for n in data if isinstance(n, dict)]
    problems = []
    mqtt_in = [n for n in nodes if n.get("type") == "mqtt in"]
    mqtt_out = [n for n in nodes if n.get("type") == "mqtt out"]
    brokers = [n for n in nodes if n.get("type") == "mqtt-broker"]
    ui_nodes = [n for n in nodes if str(n.get("type", "")).startswith("ui_")]
    if not any(n.get("topic") == topic_state for n in mqtt_in):
        problems.append(f"tidak ada node 'mqtt in' ber-topic {topic_state}")
    if not any(n.get("topic") == topic_cmd for n in mqtt_out):
        problems.append(f"tidak ada node 'mqtt out' ber-topic {topic_cmd} "
                        "(abaikan bila topic diset lewat msg.topic)")
    if not brokers:
        problems.append("tidak ada konfigurasi node 'mqtt-broker'")
    for b in brokers:
        bp = str(b.get("port", "")).strip()
        if bp and bp != str(tcp_port):
            problems.append(f"broker {b.get('broker')}:{bp} berbeda dari port TCP {tcp_port}")
    ids = {n.get("id") for n in nodes}
    dangling = 0
    for n in nodes:
        for outs in n.get("wires", []) or []:
            if isinstance(outs, list):
                dangling += sum(1 for w in outs if w not in ids)
    if dangling:
        problems.append(f"{dangling} wire menunjuk ke node yang tidak ada")
    unused = [k for k in REQUIRED_STATE_KEYS if k not in raw]
    detail = (f"{len(nodes)} node ({len(mqtt_in)} mqtt-in, {len(mqtt_out)} mqtt-out, "
              f"{len(ui_nodes)} dashboard); broker: "
              + (", ".join(f"{b.get('broker')}:{b.get('port')}" for b in brokers) or "-"))
    if unused:
        detail += f"; field state yang tidak dirujuk flows: {', '.join(unused)}"
    if problems:
        report.add(cid, name, "WARN", "; ".join(problems) + " | " + detail)
    else:
        report.add(cid, name, "PASS", detail)


# ---------------------------------------------------------------------------
# UJI OTOMATIS ALUR 7 TAHAP
# ---------------------------------------------------------------------------
def run_command_step(mon, report, cid, name, cmd, success, timeout,
                     skip_if=None, on_timeout="FAIL", hint=""):
    """Kirim perintah, tunggu efeknya di state, laporkan latensi perintah->state."""
    s0 = mon.current()
    if skip_if is not None and s0 is not None and _safe(skip_if, s0):
        report.add(cid, name, "SKIP",
                   f"kondisi target sudah tercapai sebelum uji; {cmd} tidak dikirim")
        return {"ok": True, "executed": False, "state": s0, "seq": mon.mark(), "t_ref": None}
    t_ref, seq0 = mon.send({"cmd": cmd})
    ok, dt, st = mon.wait_for(success, timeout, from_seq=seq0, t_ref=t_ref)
    ms = dt * 1000.0
    if not ok:
        report.add(cid, name, on_timeout,
                   f"{cmd}: efek tidak terlihat di state dalam {timeout:g} s. {hint}{log_tail(st)}".strip())
        return {"ok": False, "executed": True, "state": st, "seq": seq0, "t_ref": t_ref}
    status = "PASS" if ms <= CMD_WARN_MS else ("WARN" if ms <= CMD_FAIL_MS else "FAIL")
    report.add(cid, name, status, f"{cmd} -> efek terlihat di state dalam {ms:.0f} ms")
    report.extra.setdefault("cmd_latency_ms", {})[cmd] = round(ms, 1)
    return {"ok": True, "executed": True, "state": st, "seq": seq0, "t_ref": t_ref}


def stage_table(msgs):
    """Daftar (stage, mode, detik_sejak_awal) setiap kali stage berubah."""
    seen, last = [], object()
    if not msgs:
        return seen
    t0 = msgs[0][0]
    for t, s in msgs:
        st = s.get("stage")
        if st != last:
            seen.append((st, s.get("mode"), t - t0))
            last = st
    return seen


def run_sequence(mon, report, rng, args):
    print("\n--- UJI OTOMATIS ALUR 7 TAHAP ---")
    start_seq = mon.mark()
    s = mon.current()
    if s is None:
        report.add("SEQ-00", "Kondisi awal", "FAIL", "tidak ada telemetri; uji dibatalkan")
        return
    if is_on(s.get("emergency")):
        report.add("SEQ-00", "Kondisi awal", "FAIL",
                   "sistem sedang dalam kondisi E-Stop; reset dulu (restart daemon / tombol fisik) "
                   "lalu ulangi uji")
        return
    report.add("SEQ-00", "Kondisi awal", "INFO",
               f"stage={s.get('stage')} ({s.get('mode')}) power={s.get('power')} "
               f"vacuum={s.get('vacuum')} interlocks={s.get('interlocks')} beam={s.get('beam')}")

    ct, st_to = args.cmd_timeout, args.stage_timeout
    chain_ok = True
    estop_t = None

    def skipped(cid, name):
        report.add(cid, name, "SKIP", "dilewati karena tahap sebelumnya gagal")

    # SEQ-01 Power
    r = run_command_step(mon, report, "SEQ-01", "Power ON", "TOGGLE_POWER",
                         lambda x: is_on(x.get("power")), ct,
                         skip_if=lambda x: is_on(x.get("power")))
    chain_ok = r["ok"]

    # SEQ-02 Vakum (+ tren penurunan tekanan)
    if chain_ok:
        before = mon.current() or {}
        r = run_command_step(mon, report, "SEQ-02", "Pompa vakum ON", "TOGGLE_VACUUM",
                             lambda x: is_on(x.get("vacuum")), ct,
                             skip_if=lambda x: is_on(x.get("vacuum")))
        chain_ok = r["ok"]
        p0 = before.get("pressure")
        if chain_ok and r["executed"] and is_number(p0) and p0 > 0:
            ok, dt, st = mon.wait_for(
                lambda x: is_number(x.get("pressure")) and x["pressure"] < p0 * 0.5,
                args.vacuum_wait, from_seq=r["seq"], t_ref=r["t_ref"])
            if ok:
                report.add("SEQ-02b", "Penurunan tekanan setelah vakum ON", "PASS",
                           f"{p0:.2e} -> {st['pressure']:.2e} mbar (turun >50%) dalam {dt:.1f} s")
            else:
                last_p = (st or {}).get("pressure")
                report.add("SEQ-02b", "Penurunan tekanan setelah vakum ON", "WARN",
                           f"tekanan tidak turun 50% dalam {args.vacuum_wait:g} s "
                           f"(awal {p0:.2e}, akhir {fmt_num(last_p, '.2e')} mbar); "
                           "naikkan --vacuum-wait bila simulasi pump-down lambat")
    else:
        skipped("SEQ-02", "Pompa vakum ON")

    # SEQ-03 Interlock
    if chain_ok:
        r = run_command_step(mon, report, "SEQ-03", "Interlock terpenuhi", "TOGGLE_INTERLOCK",
                             lambda x: is_on(x.get("interlocks")), ct,
                             skip_if=lambda x: is_on(x.get("interlocks")),
                             hint="Asumsi: interlocks=true berarti semua interlock terpenuhi. ")
        chain_ok = r["ok"]
    else:
        skipped("SEQ-03", "Interlock terpenuhi")

    # SEQ-04 AUTO_INIT (stage / mode harus bergerak)
    if chain_ok:
        s_now = mon.current() or {}
        stage0, mode0 = s_now.get("stage"), s_now.get("mode")
        r = run_command_step(mon, report, "SEQ-04", "AUTO_INIT (stage/mode berubah)", "AUTO_INIT",
                             lambda x: x.get("stage") != stage0 or x.get("mode") != mode0, st_to,
                             on_timeout="WARN",
                             hint="Mungkin sistem sudah di tahap siap; lihat tabel tahap di bawah. ")
    else:
        skipped("SEQ-04", "AUTO_INIT (stage/mode berubah)")

    # SEQ-05 START_BEAM (+ energi & LED spiral)
    if chain_ok:
        r = run_command_step(mon, report, "SEQ-05", "START_BEAM -> beam aktif", "START_BEAM",
                             lambda x: is_on(x.get("beam")), st_to)
        chain_ok = r["ok"]
        if chain_ok:
            time.sleep(args.observe)
            msgs = mon.since(r["seq"])
            energies = [x.get("beamEnergy") for _, x in msgs if is_number(x.get("beamEnergy"))]
            leds = [x.get("activeLedIdx") for _, x in msgs
                    if isinstance(x.get("activeLedIdx"), int)]
            sp0, sp1 = rng["spiral"]
            bad_led = sorted({v for v in leds if v != -1 and not (sp0 <= v <= sp1)})
            notes, status = [], "PASS"
            if energies:
                notes.append(f"beamEnergy {energies[0]:.2f} -> {energies[-1]:.2f} MeV "
                             f"(maks {max(energies):.2f})")
                if max(energies) > MAX_BEAM_MEV + BEAM_TOL:
                    status = "FAIL"
                    notes.append(f"melebihi batas {MAX_BEAM_MEV:g} MeV")
                elif energies[-1] <= energies[0] + 0.01:
                    status = "WARN"
                    notes.append("energi tidak naik selama jendela observasi")
            else:
                status = "WARN"
                notes.append("tidak ada data beamEnergy")
            uniq = {v for v in leds if v != -1}
            notes.append(f"LED spiral: {len(uniq)} indeks berbeda")
            if len(uniq) < 2 and status == "PASS":
                status = "WARN"
                notes.append("animasi spiral tampak tidak bergerak")
            if bad_led:
                status = "WARN" if status == "PASS" else status
                notes.append(f"indeks di luar spiral {sp0}..{sp1}: {bad_led[:6]}")
            report.add("SEQ-05b", "Energi berkas & animasi LED spiral", status, "; ".join(notes))
            # SHOOT umumnya baru diterima setelah energi berkas mencapai nominal.
            target_e = MAX_BEAM_MEV * 0.95
            ok, dt, st = mon.wait_for(
                lambda x: is_number(x.get("beamEnergy")) and x["beamEnergy"] >= target_e,
                st_to, t_ref=r["t_ref"])
            if ok:
                report.add("SEQ-05c", "Energi berkas mencapai nominal", "PASS",
                           f"{st['beamEnergy']:.2f} MeV (>= {target_e:.2f}) dalam {dt:.1f} s sejak START_BEAM")
            else:
                last_e = (st or {}).get("beamEnergy")
                report.add("SEQ-05c", "Energi berkas mencapai nominal", "WARN",
                           f"hanya {fmt_num(last_e, '.2f')} MeV setelah {st_to:g} s "
                           f"(target >= {target_e:.2f}); SHOOT berikutnya kemungkinan ditolak")
    else:
        skipped("SEQ-05", "START_BEAM -> beam aktif")

    # SEQ-06 SHOOT (+ LED shoot & arus target)
    if chain_ok:
        r = run_command_step(mon, report, "SEQ-06", "SHOOT -> exposure aktif", "SHOOT",
                             lambda x: is_on(x.get("exposureActive")), ct * 2,
                             hint="SHOOT mungkin butuh energi penuh / beam stabil. ")
        if r["ok"]:
            time.sleep(min(args.observe, 4.0))
            msgs = mon.since(r["seq"])
            sh0, sh1 = rng["shoot"]
            idx = [x.get("shootLedIdx") for _, x in msgs if isinstance(x.get("shootLedIdx"), int)]
            idle = (-1, 0)  # nilai idle yang lazim untuk indeks LED shoot
            active = {v for v in idx if v not in idle}
            bad = sorted({v for v in active if not (sh0 <= v <= sh1)})
            tc = [x.get("targetCurrent") for _, x in msgs if is_number(x.get("targetCurrent"))]
            notes, status = [f"LED shoot: {len(active)} indeks aktif"], "PASS"
            if not active:
                status = "WARN"
                notes.append("indeks LED shoot tidak bergerak")
            if bad:
                status = "WARN"
                notes.append(f"indeks di luar {sh0}..{sh1}: {bad[:6]}")
            if tc:
                notes.append(f"targetCurrent maks {max(tc):.3g}")
                if max(tc) <= 0:
                    status = "WARN"
                    notes.append("arus target tidak pernah > 0")
            report.add("SEQ-06b", "Animasi LED shoot & arus target", status, "; ".join(notes))
    else:
        skipped("SEQ-06", "SHOOT -> exposure aktif")

    # SEQ-07 Emergency stop (tetap diuji walau tahap sebelumnya gagal: fungsi keselamatan)
    if args.estop:
        estop_t = time.perf_counter()
        r = run_command_step(mon, report, "SEQ-07", "EMERGENCY_STOP -> emergency aktif",
                             "EMERGENCY_STOP", lambda x: is_on(x.get("emergency")), ct)
        if r["ok"]:
            ok, dt, _ = mon.wait_for(
                lambda x: not is_on(x.get("beam")) and not is_on(x.get("exposureActive")),
                2.0, from_seq=r["seq"], t_ref=r["t_ref"])
            report.add("SEQ-07b", "Beam & exposure padam setelah E-Stop",
                       "PASS" if ok else "FAIL",
                       f"padam dalam {dt * 1000:.0f} ms" if ok else
                       "beam/exposure masih aktif 2 s setelah E-Stop (BAHAYA, periksa daemon)")
            ok, dt, _ = mon.wait_for(lambda x: is_on(x.get("buzzerActive")), 2.0,
                                     from_seq=r["seq"], t_ref=r["t_ref"])
            report.add("SEQ-07c", "Buzzer alarm saat E-Stop", "PASS" if ok else "WARN",
                       f"buzzerActive aktif dalam {dt * 1000:.0f} ms" if ok else
                       "buzzerActive tidak pernah aktif dalam 2 s")
        print("  CATATAN: sistem sekarang terkunci E-Stop; reset sebelum menjalankan uji ulang.")
    else:
        report.add("SEQ-07", "EMERGENCY_STOP", "SKIP", "tidak diuji (tambahkan --estop)")

    # Tahap (stage) yang benar-benar teramati
    msgs = mon.since(start_seq)
    pre = [(t, x) for t, x in msgs if estop_t is None or t < estop_t]
    table = stage_table(msgs)
    if table:
        listing = "; ".join(f"stage {st} ({md}) t+{t:.1f}s" for st, md, t in table)
        report.extra["stages_observed"] = [{"stage": st, "mode": md, "t_plus_s": round(t, 2)}
                                           for st, md, t in table]
        distinct = len({st for st, _, _ in table})
        status = "PASS" if distinct >= args.expected_stages else "WARN"
        report.add("SEQ-ST1", f"Tahap teramati (target {args.expected_stages})", status,
                   f"{distinct} nilai stage berbeda: {listing}")
        nums = [st for st, _, _ in stage_table(pre) if isinstance(st, int) and not isinstance(st, bool)]
        if nums == sorted(nums):
            report.add("SEQ-ST2", "Urutan stage tidak mundur (sebelum E-Stop)", "PASS",
                       "->".join(str(n) for n in nums) or "-")
        else:
            report.add("SEQ-ST2", "Urutan stage tidak mundur (sebelum E-Stop)", "WARN",
                       "stage sempat turun: " + "->".join(str(n) for n in nums))
    stats = analyze_rate(msgs, args.target_hz)
    if stats.get("n", 0) >= 5:
        status = "PASS" if stats["max_ms"] <= MAX_GAP_WARN_MS else "WARN"
        report.add("SEQ-RATE", "Stabilitas telemetri selama uji perintah", status,
                   f"{stats['hz']:.2f} Hz, interval maks {stats['max_ms']:.0f} ms, "
                   f"{stats['gaps']} celah")


# ---------------------------------------------------------------------------
# LAPORAN & MENU
# ---------------------------------------------------------------------------
def write_report(report, args, host):
    d = args.report_dir or os.path.join(os.path.expanduser("~"), "decy13_qa_reports")
    os.makedirs(d, exist_ok=True)
    base = os.path.join(d, "decy13_qa_" + report.started.strftime("%Y%m%d_%H%M%S"))
    lines = [
        "LAPORAN QA & COMMISSIONING OTOMATIS - SIKLOTRON DECY-13 (DIVISI 6)",
        "=" * 70,
        f"Tanggal      : {report.started.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Komputer     : {socket.gethostname()}",
        f"Broker       : {host}:{args.port} (WebSocket {args.ws_port})",
        f"Topic state  : {args.topic_state}",
        f"Topic cmd    : {args.topic_cmd}",
        f"Mode         : cek cepat{' + uji 7 tahap' if args.auto else ''}"
        f"{' + E-Stop' if args.estop else ''}",
        "-" * 70,
    ]
    for i in report.items:
        lines.append(f"{STATUS_BOX[i['status']]} {STATUS_LABEL[i['status']]:<10} {i['id']:<8} "
                     f"{i['name']}")
        if i["detail"]:
            lines.append(f"      {i['detail']}")
    lines += ["-" * 70, "RINGKASAN: " + report.summary_line(), "",
              "Penguji : ____________________    Paraf Ketua : ____________________", ""]
    with open(base + ".txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    meta = {"tanggal": report.started.isoformat(timespec="seconds"),
            "komputer": socket.gethostname(), "broker": f"{host}:{args.port}",
            "ringkasan": {"lulus": report.count("PASS"), "peringatan": report.count("WARN"),
                          "gagal": report.count("FAIL"), "lewati": report.count("SKIP")}}
    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "hasil": report.items, "data": report.extra},
                  f, ensure_ascii=False, indent=2, default=str)
    return base


def print_status(s):
    if not s:
        print("Belum ada data state yang diterima.")
        return
    print(f"  Stage={s.get('stage')} | Mode={s.get('mode')} | Power={s.get('power')} | "
          f"Vac={s.get('vacuum')} | RF={s.get('rf')} | Magnet={s.get('magnet')}")
    print(f"  Pressure={fmt_num(s.get('pressure'), '.2e')} mbar | Interlock={s.get('interlocks')} | "
          f"Beam={s.get('beam')} ({fmt_num(s.get('beamEnergy'), '.1f')} MeV) | "
          f"Exposure={s.get('exposureActive')} | E-Stop={s.get('emergency')}")
    print(f"  LED Spiral=#{s.get('activeLedIdx')} | LED Shoot=#{s.get('shootLedIdx')} | "
          f"Buzzer={s.get('buzzerActive')}")
    print(f"  LCD1: {s.get('lcd_line1')} | LCD2: {s.get('lcd_line2')}")


def interactive_menu(mon, topic_cmd):
    print("\nMenu Uji Cepat Perintah MQTT:")
    print("  [1] TOGGLE_POWER    [2] TOGGLE_VACUUM   [3] TOGGLE_INTERLOCK")
    print("  [4] AUTO_INIT       [5] START_BEAM      [6] SHOOT")
    print("  [7] EMERGENCY_STOP  [s] Cek Status      [l] Ping latensi    [q] Keluar")
    while True:
        try:
            choice = input("QA-CLI > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if choice in ("q", "quit", "exit"):
            break
        elif choice == "s":
            print_status(mon.current())
        elif choice == "l":
            vals = [mon.ping(1.0) for _ in range(5)]
            ok = [v for v in vals if v is not None]
            print("  Ping broker: " + (f"rata-rata {statistics.mean(ok):.1f} ms ({len(ok)}/5 balasan)"
                                       if ok else "tidak ada balasan"))
        elif choice in CMD_MENU:
            before = mon.current() or {}
            snap = {k: before.get(k) for k in FLAG_FIELDS}
            payload = {"cmd": CMD_MENU[choice]}
            t_ref, seq0 = mon.send(payload)
            print(f"  -> Dikirim ke {topic_cmd}: {json.dumps(payload)}")
            changed = lambda x: ({k: x.get(k) for k in FLAG_FIELDS} != snap
                                 or x.get("logs") != before.get("logs"))
            ok, dt, st = mon.wait_for(changed, 1.5, from_seq=seq0, t_ref=t_ref)
            if ok:
                diffs = [f"{k}: {snap[k]} -> {st.get(k)}" for k in FLAG_FIELDS
                         if st.get(k) != snap[k]]
                print(f"  <- State berubah dalam {dt * 1000:.0f} ms: "
                      + (", ".join(diffs) if diffs else "(hanya log)"))
            else:
                print("  <- Tidak ada perubahan state dalam 1.5 s "
                      "(perintah mungkin ditolak interlock/state machine).")
            logs = (st or {}).get("logs")
            if logs:
                print(f"  <- Log Daemon: {logs[0]}")
        elif choice:
            print("  Pilihan tidak dikenal.")


# ---------------------------------------------------------------------------
# PROGRAM UTAMA
# ---------------------------------------------------------------------------
def build_parser():
    mq = CFG.get("mqtt", {}) if isinstance(CFG.get("mqtt"), dict) else {}
    p = argparse.ArgumentParser(
        description="DECY-13 MQTT Healthcheck, Contract & Commissioning QA Tool (Divisi 6)")
    p.add_argument("--host", default=mq.get("broker_host", "127.0.0.1"),
                   help="Host/IP Broker MQTT (default dari config_hardware.json)")
    p.add_argument("--port", type=int, default=to_int(mq.get("broker_port_tcp"), 1883),
                   help="Port TCP MQTT (default 1883)")
    p.add_argument("--ws-port", type=int,
                   default=to_int(mq.get("broker_port_ws", find_key(CFG, "broker_port_ws", 9001)), 9001),
                   help="Port WebSocket MQTT untuk Web HMI (default 9001)")
    p.add_argument("--topic-state", default=mq.get("topic_state", "decy13/rpi/state"))
    p.add_argument("--topic-cmd", default=mq.get("topic_cmd", "decy13/hmi/cmd"))
    p.add_argument("--duration", type=float, default=10.0,
                   help="Lama sampling telemetri dalam detik (default 10)")
    p.add_argument("--target-hz", type=float, default=5.0, help="Frekuensi telemetri target (default 5.0)")
    p.add_argument("--pings", type=int, default=20, help="Jumlah ping uji latensi broker (default 20)")
    p.add_argument("--auto", action="store_true", help="Jalankan uji otomatis alur 7 tahap (mengirim perintah!)")
    p.add_argument("--estop", action="store_true", help="Sertakan uji EMERGENCY_STOP di akhir (butuh --auto)")
    p.add_argument("--yes", action="store_true", help="Lewati konfirmasi sebelum --auto")
    p.add_argument("--cmd-timeout", type=float, default=5.0, help="Batas tunggu efek perintah sederhana (s)")
    p.add_argument("--stage-timeout", type=float, default=30.0, help="Batas tunggu AUTO_INIT/START_BEAM (s)")
    p.add_argument("--vacuum-wait", type=float, default=15.0, help="Batas tunggu tekanan turun 50%% (s)")
    p.add_argument("--observe", type=float, default=6.0, help="Lama observasi energi/LED setelah START_BEAM (s)")
    p.add_argument("--expected-stages", type=int, default=7, help="Jumlah tahap yang diharapkan (default 7)")
    p.add_argument("--flows", default=DEFAULT_FLOWS_PATH, help="Path flows_mqtt_decy13.json")
    p.add_argument("--nodered-host", default=None, help="Host Node-RED (default sama dengan broker)")
    p.add_argument("--nodered-port", type=int, default=1880)
    p.add_argument("--report", action="store_true", help="Simpan laporan .txt dan .json")
    p.add_argument("--report-dir", default=None,
                   help="Folder laporan (default ~/decy13_qa_reports, di luar repo agar tidak ikut git add)")
    p.add_argument("--no-menu", action="store_true", help="Jangan buka menu interaktif di akhir")
    return p


def finish(report, args, host):
    print("\n" + "=" * 65)
    print("  RINGKASAN: " + report.summary_line())
    print("=" * 65)
    if args.report:
        try:
            base = write_report(report, args, host)
            print(f"  Laporan disimpan: {base}.txt dan .json")
        except OSError as e:
            print(f"  [PERINGATAN] Laporan gagal disimpan: {e}")
    return 1 if report.has_fail() else 0


def main():
    args = build_parser().parse_args()
    if args.estop and not args.auto:
        print("[ERROR] --estop hanya dapat dipakai bersama --auto")
        return 2

    report = Report()
    rng = led_ranges(CFG)

    print("=" * 65)
    print("  DECY-13 MQTT QA & HEALTHCHECK (DIVISI 6)")
    print(f"  Target Broker : {args.host}:{args.port}  (WebSocket {args.ws_port})")
    print(f"  Topic State   : {args.topic_state}")
    print(f"  Topic Command : {args.topic_cmd}")
    print("=" * 65)
    if CFG_ERROR:
        print(f"[PERINGATAN] {CFG_ERROR}; memakai nilai bawaan.")

    # --- NET-01: port TCP (+ auto-fallback ke broker lokal) ---
    host = args.host
    ok, info = tcp_probe(host, args.port)
    if not ok and host != "127.0.0.1":
        ok2, info2 = tcp_probe("127.0.0.1", args.port)
        if ok2:
            print(f"[Auto-Fallback] Host {host}:{args.port} tidak aktif -> beralih ke 127.0.0.1:{args.port}")
            report.add("NET-00", "Host broker", "WARN",
                       f"{host} tidak aktif; yang diuji adalah broker LOKAL 127.0.0.1. "
                       "Jalankan ulang dengan --host <IP Raspi> untuk menguji perangkat sebenarnya")
            host, ok, info = "127.0.0.1", ok2, info2
    if not ok:
        report.add("NET-01", f"Port TCP broker {args.port}", "FAIL",
                   f"{host}:{args.port} tidak dapat dijangkau ({info}). Pastikan Mosquitto berjalan "
                   "dan IP/jaringan benar")
        finish(report, args, host)
        return 2
    report.add("NET-01", f"Port TCP broker {args.port}", "PASS", f"{host}:{args.port} terbuka ({info:.0f} ms)")

    # --- NET-02: koneksi MQTT ---
    mon = Monitor(host, args.port, args.topic_state, args.topic_cmd)
    try:
        connected = mon.connect(timeout=5.0)
    except OSError as e:
        report.add("NET-02", "Koneksi MQTT (CONNACK)", "FAIL", f"tidak dapat menghubungi broker: {e}")
        finish(report, args, host)
        return 2
    if not connected:
        report.add("NET-02", "Koneksi MQTT (CONNACK)", "FAIL",
                   f"tidak ada CONNACK sukses dalam 5 s (rc={mon.connect_rc}); cek autentikasi/ACL")
        mon.close()
        finish(report, args, host)
        return 2
    report.add("NET-02", "Koneksi MQTT (CONNACK)", "PASS",
               f"CONNACK dalam {mon.connect_ms:.0f} ms (client_id={mon.client_id})")

    try:
        check_websocket(report, host, args.ws_port, args.topic_state, args.topic_cmd)
        check_ping(report, mon, args.pings)

        # --- Telemetri ---
        print(f"\nMendengarkan paket telemetri selama {args.duration:g} detik...")
        mark = mon.mark()
        time.sleep(args.duration)
        msgs = mon.since(mark)
        if not msgs:
            report.add("TLM-01", "Telemetri tiba di topic state", "FAIL",
                       f"broker aktif, tetapi tidak ada paket di {args.topic_state}. Pastikan "
                       "04_decy13_mqtt_daemon.py atau 05_laptop_dryrun_simulator.py berjalan!")
            for cid, nm in (("TLM-02", "Kontrak JSON state"), ("TLM-03", "Frekuensi telemetri"),
                            ("TLM-04", "Jitter & kehilangan paket")):
                report.add(cid, nm, "SKIP", "tidak ada telemetri")
        else:
            report.add("TLM-01", "Telemetri tiba di topic state", "PASS", f"{len(msgs)} paket diterima")
            check_contract(report, msgs, rng)
            check_rate(report, analyze_rate(msgs, args.target_hz), args.target_hz)
            s = msgs[-1][1]
            print(f"        Status Saat Ini -> Stage {s.get('stage')} ({s.get('mode')}) | "
                  f"P={fmt_num(s.get('pressure'), '.2e')} mbar | "
                  f"E={fmt_num(s.get('beamEnergy'), '.1f')} MeV")
        if mon.bad_payloads:
            report.add("TLM-05", "Payload JSON rusak", "FAIL",
                       f"{mon.bad_payloads} paket tidak dapat di-parse sebagai objek JSON")
        else:
            report.add("TLM-05", "Payload JSON rusak", "PASS", "tidak ada payload rusak")

        # --- Node-RED ---
        check_nodered(report, args.nodered_host or host, args.nodered_port)
        check_flows(report, args.flows, args.topic_state, args.topic_cmd, args.port)

        # --- Uji otomatis 7 tahap ---
        if args.auto:
            if not msgs:
                report.add("SEQ-00", "Uji 7 tahap", "SKIP", "tidak ada telemetri dari daemon")
            else:
                print("\nUji otomatis akan mengirim perintah sungguhan: TOGGLE_POWER, TOGGLE_VACUUM,")
                print("TOGGLE_INTERLOCK, AUTO_INIT, START_BEAM, SHOOT"
                      + (", EMERGENCY_STOP (sistem akan terkunci E-Stop)." if args.estop else "."))
                print("Relay, buzzer, dan LED akan ikut bergerak; anggota lain di broker yang sama terdampak.")
                if args.yes or confirm("Lanjutkan? [y/N] "):
                    run_sequence(mon, report, rng, args)
                else:
                    report.add("SEQ-00", "Uji 7 tahap", "SKIP",
                               "dibatalkan (tidak ada konfirmasi; gunakan --yes untuk non-interaktif)")

        code = finish(report, args, host)

        if not args.auto and not args.no_menu and sys.stdin.isatty():
            interactive_menu(mon, args.topic_cmd)
        return code
    finally:
        mon.close()


if __name__ == "__main__":
    sys.exit(main())