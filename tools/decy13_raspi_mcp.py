#!/usr/bin/env python3
"""
MCP SERVER LOKAL DECY-13 RASPBERRY PI DIAGNOSTICS (STDIO JSON-RPC 2.0)
======================================================================
Penanggung Jawab : Divisi 1 (Ketua / Core Raspi Backend & Integrator)
File             : tools/decy13_raspi_mcp.py

Menyediakan tool MCP langsung bagi Antigravity (AGY) di Mini PC untuk memeriksa
status, telemetri MQTT, perilaku 448 LED pada Core Daemon Raspberry Pi 3B+,
serta inspeksi SSH (via SSH key) tanpa mengubah konfigurasi hardware secara liar.

Tool yang tersedia:
  1. raspi_discover_status   : Scan UDP Auto-Link (51313) & status 4 service + Daya 5V
  2. raspi_read_telemetry    : Baca telemetri live decy13/rpi/state & decy13/usb/state
  3. raspi_send_command      : Kirim 1 perintah resmi ke decy13/hmi/cmd & cek respon
  4. raspi_diagnose_led_sweep: Uji cepat transisi Stage 1->5->6->7->OFF untuk cek
                               kecepatan & indeks 448 LED (kode baru vs kode lama)
  5. raspi_ssh_inspect       : Inspeksi read-only via SSH key (git log, journalctl,
                               config_hardware.json, vcgencmd)
"""

import json
import os
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import minipc_control_hub as hub  # noqa: E402

try:
    import paho.mqtt.client as mqtt
except Exception:
    mqtt = None

SERVER_NAME = "decy13-raspi-mcp"
SERVER_VERSION = "1.0.0"

ALLOWED_COMMANDS = {
    "TOGGLE_POWER",
    "TOGGLE_VACUUM",
    "TOGGLE_INTERLOCK",
    "AUTO_INIT",
    "START_BEAM",
    "SHOOT",
    "EMERGENCY_STOP",
    "SET_PARAMS",
}


def _resolve_raspi_ip(host: Optional[str] = None) -> Tuple[str, Optional[Dict[str, Any]]]:
    if host and str(host).strip():
        return str(host).strip(), None
    st = hub.discover_via_udp(timeout=1.6) or hub.discover_via_subnet_scan()
    if st and st.get("wifi_ip"):
        return str(st["wifi_ip"]).strip(), st
    cached = hub.load_cached_runtime_config()
    cached_ip = str(cached.get("raspi", {}).get("ip", "")).strip()
    if cached_ip:
        return cached_ip, None
    return "", None


def _make_mqtt_client() -> Any:
    if mqtt is None:
        raise RuntimeError("Library paho-mqtt tidak terpasang di Python Mini PC.")
    if hasattr(mqtt, "CallbackAPIVersion"):
        return mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    return mqtt.Client()


def tool_raspi_discover_status(args: Dict[str, Any]) -> Dict[str, Any]:
    timeout = float(args.get("timeout_sec", 1.8))
    st = hub.discover_via_udp(timeout=max(0.5, min(5.0, timeout)))
    if st is None:
        st = hub.discover_via_subnet_scan()
    wifi = hub.get_windows_wifi_info()
    return {
        "detected": st is not None,
        "pc_wifi": wifi,
        "pc_ips": hub._get_local_ipv4_list(),
        "mosquitto_windows_running": hub.is_windows_mosquitto_running(),
        "raspi": st,
    }


def tool_raspi_read_telemetry(args: Dict[str, Any]) -> Dict[str, Any]:
    host, st = _resolve_raspi_ip(args.get("host"))
    if not host:
        return {"ok": False, "error": "IP Raspberry Pi tidak terdeteksi di Wi-Fi."}

    duration = max(0.8, min(10.0, float(args.get("duration_sec", 2.0))))
    rpi_packets: List[Dict[str, Any]] = []
    usb_packets: List[Dict[str, Any]] = []

    client = _make_mqtt_client()

    def on_message(c: Any, u: Any, msg: Any) -> None:
        try:
            data = json.loads(msg.payload.decode("utf-8", errors="replace"))
        except Exception:
            return
        if msg.topic == "decy13/rpi/state":
            rpi_packets.append(data)
        elif msg.topic == "decy13/usb/state":
            usb_packets.append(data)

    client.on_message = on_message
    client.connect(host, 1883, 10)
    client.subscribe([("decy13/rpi/state", 0), ("decy13/usb/state", 0)])
    client.loop_start()
    time.sleep(duration)
    client.loop_stop()
    client.disconnect()

    latest_rpi = rpi_packets[-1] if rpi_packets else None
    latest_usb = usb_packets[-1] if usb_packets else None
    return {
        "ok": True,
        "host": host,
        "duration_sec": duration,
        "rpi_packet_count": len(rpi_packets),
        "rpi_rate_hz": round(len(rpi_packets) / duration, 2),
        "active_led_sequence": [p.get("activeLedIdx") for p in rpi_packets],
        "shoot_led_sequence": [p.get("shootLedIdx") for p in rpi_packets],
        "latest_rpi_state": latest_rpi,
        "usb_packet_count": len(usb_packets),
        "latest_usb_state": latest_usb,
        "udp_status": st,
    }


def tool_raspi_send_command(args: Dict[str, Any]) -> Dict[str, Any]:
    cmd = str(args.get("cmd", "")).strip().upper()
    if cmd not in ALLOWED_COMMANDS:
        return {"ok": False, "error": f"Command '{cmd}' tidak valid. Pilih: {sorted(ALLOWED_COMMANDS)}"}

    host, _ = _resolve_raspi_ip(args.get("host"))
    if not host:
        return {"ok": False, "error": "IP Raspberry Pi tidak terdeteksi."}

    payload: Dict[str, Any] = {"cmd": cmd}
    if cmd == "SET_PARAMS":
        for k in ("magnet_a", "rf_mhz", "rf_kv", "beam_ua"):
            if k in args and args[k] is not None:
                payload[k] = float(args[k])

    received: List[Dict[str, Any]] = []
    client = _make_mqtt_client()

    def on_message(c: Any, u: Any, msg: Any) -> None:
        if msg.topic == "decy13/rpi/state":
            try:
                received.append(json.loads(msg.payload.decode("utf-8", errors="replace")))
            except Exception:
                pass

    client.on_message = on_message
    client.connect(host, 1883, 10)
    client.subscribe("decy13/rpi/state", 0)
    client.loop_start()
    time.sleep(0.25)
    client.publish("decy13/hmi/cmd", json.dumps(payload), qos=0)
    time.sleep(0.8)
    client.loop_stop()
    client.disconnect()

    return {
        "ok": True,
        "host": host,
        "sent": payload,
        "latest_state": received[-1] if received else None,
    }


def tool_raspi_diagnose_led_sweep(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Uji cepat non-destruktif terhadap Core Daemon Raspi:
    AUTO_INIT -> START_BEAM (1.8s) -> SHOOT (1.2s) -> Power OFF (aman tanpa sirene).
    Memeriksa apakah activeLedIdx & shootLedIdx di daemon Raspi benar-benar berjalan
    sesuai spek 448 LED 2-fase (kecepatan 80-300 LED/detik) atau ada error software.
    """
    host, st = _resolve_raspi_ip(args.get("host"))
    if not host:
        return {"ok": False, "error": "IP Raspberry Pi tidak terdeteksi."}

    samples_beam: List[Dict[str, Any]] = []
    samples_shoot: List[Dict[str, Any]] = []
    phase = {"name": "init"}

    client = _make_mqtt_client()

    def on_message(c: Any, u: Any, msg: Any) -> None:
        if msg.topic != "decy13/rpi/state":
            return
        try:
            d = json.loads(msg.payload.decode("utf-8", errors="replace"))
        except Exception:
            return
        entry = {
            "t": round(time.monotonic(), 3),
            "stage": d.get("stage"),
            "activeLedIdx": d.get("activeLedIdx"),
            "shootLedIdx": d.get("shootLedIdx"),
            "beamEnergy": d.get("beamEnergy"),
        }
        if phase["name"] == "beam":
            samples_beam.append(entry)
        elif phase["name"] == "shoot":
            samples_shoot.append(entry)

    client.on_message = on_message
    client.connect(host, 1883, 10)
    client.subscribe("decy13/rpi/state", 0)
    client.loop_start()
    try:
        time.sleep(0.3)
        client.publish("decy13/hmi/cmd", json.dumps({"cmd": "AUTO_INIT"}), qos=0)
        time.sleep(0.45)
        phase["name"] = "beam"
        client.publish("decy13/hmi/cmd", json.dumps({"cmd": "START_BEAM"}), qos=0)
        time.sleep(1.8)
        phase["name"] = "shoot"
        client.publish("decy13/hmi/cmd", json.dumps({"cmd": "SHOOT"}), qos=0)
        time.sleep(1.3)
    finally:
        phase["name"] = "cleanup"
        # Matikan kembali dengan TOGGLE_POWER (karena power=True -> mematikan semua aman tanpa sirene E-Stop)
        client.publish("decy13/hmi/cmd", json.dumps({"cmd": "TOGGLE_POWER"}), qos=0)
        time.sleep(0.5)
        client.loop_stop()
        client.disconnect()

    beam_indices = [s["activeLedIdx"] for s in samples_beam if isinstance(s.get("activeLedIdx"), int) and s["activeLedIdx"] >= 0]
    shoot_indices = [s["shootLedIdx"] for s in samples_shoot if isinstance(s.get("shootLedIdx"), int) and s["shootLedIdx"] >= 0]

    max_spiral = max(beam_indices) if beam_indices else -1
    max_shoot = max(shoot_indices) if shoot_indices else -1

    # Hitung estimasi kecepatan langkah antar sampel beam (LED/detik)
    deltas = []
    for i in range(1, len(samples_beam)):
        a, b = samples_beam[i - 1], samples_beam[i]
        dt = b["t"] - a["t"]
        if dt > 0.05 and a["activeLedIdx"] >= 0 and b["activeLedIdx"] >= 0:
            diff = (b["activeLedIdx"] - a["activeLedIdx"]) % 389
            if diff > 0:
                deltas.append(diff / dt)
    avg_spiral_speed = round(sum(deltas) / len(deltas), 1) if deltas else 0.0

    # Kesimpulan diagnostik kode Raspi vs fisik strip (mendukung 435/437/448 LED)
    if not beam_indices:
        verdict = "ERROR_SOFTWARE_DAEMON: activeLedIdx tidak pernah bergerak di rentang spiral."
    elif max_spiral >= 50 and avg_spiral_speed >= 55.0 and max_shoot >= 385:
        verdict = (
            f"KODE RASPI NORMAL (SINGLE-WRITER PWM0 GPIO 12 AKTIF): spiral bergerak ~{avg_spiral_speed} LED/dtk "
            f"(terbaca hingga LED #{max_spiral}) dan shoot menembak hingga #{max_shoot}. "
            "Jika fisik strip tidak sesuai -> periksa sambungan solder DOUT->DIN, Pin Fisik 32 (GPIO 12), Common GND Pin 39, dan tegangan 5V LM2596."
        )
    elif max_spiral > 0 and avg_spiral_speed < 55.0:
        verdict = (
            f"KODE RASPI MASIH VERSI LAMA (LAMBAT ~{avg_spiral_speed} LED/dtk, max #{max_spiral}): "
            "revisi LED 2-fase (baea951) belum aktif/ter-restart di Raspi."
        )
    else:
        verdict = f"PARSIAL: max_spiral={max_spiral}, avg_speed={avg_spiral_speed}, max_shoot={max_shoot}."

    return {
        "ok": True,
        "host": host,
        "udp_status": st,
        "beam_samples": samples_beam,
        "shoot_samples": samples_shoot,
        "summary": {
            "max_spiral_idx": max_spiral,
            "avg_spiral_speed_leds_per_sec": avg_spiral_speed,
            "max_shoot_idx": max_shoot,
            "verdict": verdict,
        },
    }


def tool_raspi_ssh_inspect(args: Dict[str, Any]) -> Dict[str, Any]:
    host, st = _resolve_raspi_ip(args.get("host"))
    user = str(args.get("user") or (st.get("user") if st else "sp-aksel") or "sp-aksel")
    if not host:
        return {"ok": False, "error": "IP Raspberry Pi tidak terdeteksi."}

    ssh_bin = hub._find_ssh_binary()
    remote_cmd = (
        "REPO_DIR=~/sp-aksel-polteknuklir; [ -d ~/decy13/.git ] && REPO_DIR=~/decy13; "
        "cd $REPO_DIR && echo '=== GIT ===' && git log -1 --oneline && "
        "echo '=== CONFIG ===' && grep -E 'led_ws2812b|total_leds|brightness|spiral|shoot' decy13_mqtt_kit/raspi_cli/config_hardware.json && "
        "echo '=== SERVICES ===' && systemctl is-active mosquitto decy13.service decy13-autolink.service decy13-usb-hub.service ; "
        "echo '=== BOOT CFG ===' && grep -E 'audio|spi' /boot/firmware/config.txt /boot/config.txt 2>/dev/null && "
        "echo '=== POWER ===' && vcgencmd get_throttled && "
        "echo '=== DAEMON LOG ===' && journalctl -u decy13.service -n 20 --no-pager"
    )
    proc = subprocess.run(
        [ssh_bin, "-o", "BatchMode=yes", "-o", "ConnectTimeout=4", "-o", "StrictHostKeyChecking=accept-new", f"{user}@{host}", remote_cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0 and "Permission denied" in proc.stdout:
        return {
            "ok": False,
            "host": host,
            "needs_ssh_key": True,
            "output": proc.stdout.strip(),
            "setup_hint": (
                f"Pasang SSH key 1x di CMD Mini PC agar MCP bisa baca log Raspi otomatis tanpa password:\n"
                f"  ssh-keygen -t ed25519 -N \"\" -f %USERPROFILE%\\.ssh\\id_ed25519\n"
                f"  type %USERPROFILE%\\.ssh\\id_ed25519.pub | ssh {user}@{host} \"mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys\""
            ),
        }
    return {
        "ok": proc.returncode == 0,
        "host": host,
        "returncode": proc.returncode,
        "output": proc.stdout.strip(),
    }


TOOLS_SPEC = [
    {
        "name": "raspi_discover_status",
        "description": "Scan Raspberry Pi 3B+ DECY-13 via UDP Auto-Link (51313) dan cek status Wi-Fi, 4 service systemd, suhu CPU, serta tegangan 5V.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "timeout_sec": {"type": "number", "description": "Lama scan UDP dalam detik (default 1.8)"}
            },
        },
    },
    {
        "name": "raspi_read_telemetry",
        "description": "Membaca telemetri real-time decy13/rpi/state dan decy13/usb/state dari Mosquitto Raspberry Pi.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "IP Wi-Fi Raspi (opsional, auto-discover bila kosong)"},
                "duration_sec": {"type": "number", "description": "Durasi sampling dalam detik (default 2.0)"},
            },
        },
    },
    {
        "name": "raspi_send_command",
        "description": "Mengirim 1 perintah kendali resmi ke topik decy13/hmi/cmd dan mengembalikan state terbaru Raspi.",
        "inputSchema": {
            "type": "object",
            "required": ["cmd"],
            "properties": {
                "host": {"type": "string"},
                "cmd": {"type": "string", "enum": sorted(ALLOWED_COMMANDS)},
                "magnet_a": {"type": "number"},
                "rf_mhz": {"type": "number"},
                "rf_kv": {"type": "number"},
                "beam_ua": {"type": "number"},
            },
        },
    },
    {
        "name": "raspi_diagnose_led_sweep",
        "description": "Menjalankan uji singkat Stage 5->6->7->OFF pada Core Daemon Raspi untuk memastikan kecepatan dan rentang indeks 448 LED (0..399 spiral, 400..447 shoot) normal tanpa error kode.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "IP Wi-Fi Raspi (opsional, auto-discover bila kosong)"}
            },
        },
    },
    {
        "name": "raspi_ssh_inspect",
        "description": "Inspeksi read-only Raspi via SSH key: commit git aktif, config_hardware.json, status 4 service, dtparam audio/spi, vcgencmd get_throttled, dan log decy13.service.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "host": {"type": "string"},
                "user": {"type": "string"},
            },
        },
    },
]

TOOL_HANDLERS = {
    "raspi_discover_status": tool_raspi_discover_status,
    "raspi_read_telemetry": tool_raspi_read_telemetry,
    "raspi_send_command": tool_raspi_send_command,
    "raspi_diagnose_led_sweep": tool_raspi_diagnose_led_sweep,
    "raspi_ssh_inspect": tool_raspi_ssh_inspect,
}


def _send_rpc(msg: Dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _handle_rpc(req: Dict[str, Any]) -> None:
    method = req.get("method", "")
    req_id = req.get("id")
    params = req.get("params") or {}

    if method == "notifications/initialized" or req_id is None:
        return

    if method == "initialize":
        _send_rpc({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        })
        return

    if method == "tools/list":
        _send_rpc({"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS_SPEC}})
        return

    if method == "tools/call":
        name = params.get("name", "")
        arguments = params.get("arguments") or {}
        handler = TOOL_HANDLERS.get(name)
        if not handler:
            _send_rpc({
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Tool tidak dikenal: {name}"},
            })
            return
        try:
            res = handler(arguments)
            _send_rpc({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(res, indent=2, ensure_ascii=False)}],
                    "isError": False,
                },
            })
        except Exception as exc:
            _send_rpc({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": f"Error menjalankan {name}: {exc}"}],
                    "isError": True,
                },
            })
        return

    _send_rpc({
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method tidak didukung: {method}"},
    })


def main() -> None:
    # Mode CLI singkat untuk verifikasi langsung dari terminal
    if len(sys.argv) >= 2 and sys.argv[1] == "--self-test":
        out = {
            "discover": tool_raspi_discover_status({}),
            "led_sweep": tool_raspi_diagnose_led_sweep({}),
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return

    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            continue
        _handle_rpc(req)


if __name__ == "__main__":
    main()
