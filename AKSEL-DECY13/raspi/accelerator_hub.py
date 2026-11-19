#!/usr/bin/env python3
"""Hub USB DECY-13. One I/O worker per Uno; all routing happens on the main thread."""
import argparse
import csv
import json
import logging
import queue
import signal
import sys
import threading
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

import serial

ROLES = ("hmi", "sensor", "actuator")
MAX_LINE = 182
CLOCK = time.monotonic
LOG = logging.getLogger("accelerator")
COLUMNS = ("utc", "node", "page", "vac_pa", "hv_v", "temp_dc", "din", "offset_dc",
           "rpm", "target", "mode", "rate", "auto", "left", "bits", "guard", "link")
FIELDS = {
    "hmi": {"page": (0, 2)},
    "sensor": {"vac_pa": (0, 101325), "hv_v": (0, 1000), "temp_dc": (-200, 1200),
               "din": (0, 1), "offset_dc": (-200, 200)},
    "actuator": {"rpm": (0, 9000), "target": (2000, 9000), "mode": (0, 2),
                 "rate": (0, 2), "auto": (0, 1), "left": (0, 10), "bits": (0, 63),
                 "guard": (0, 1), "link": (0, 1)},
}
ACTION_RANGES = {"START": (1, 1), "STOP": (1, 1), "RESET": (1, 1), "AUTO": (0, 1),
                 "RATE": (0, 2), "TARGET": (2000, 9000), "LED": (0, 3), "FAN": (0, 1),
                 "BUZZER": (0, 1), "RELAY_1": (0, 1), "VALVE": (0, 1)}


def integer(value, lo, hi):
    return type(value) is int and lo <= value <= hi


def encode(packet):
    raw = json.dumps(packet, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    if len(raw) > MAX_LINE:
        raise ValueError("Frame terlalu panjang")
    return raw + b"\n"


class Lines:
    def __init__(self):
        self.buffer = bytearray()
        self.discard = False

    def feed(self, data):
        for c in data:
            if c == 10:
                if self.buffer and not self.discard:
                    try:
                        packet = json.loads(self.buffer)
                        if isinstance(packet, dict):
                            yield packet
                    except (ValueError, UnicodeError, RecursionError):
                        pass
                self.buffer.clear()
                self.discard = False
            elif len(self.buffer) >= MAX_LINE + 1:
                self.discard = True
            elif not self.discard:
                self.buffer.append(c)


class Port(threading.Thread):
    def __init__(self, role, path, events, stop):
        super().__init__(name=role, daemon=True)
        self.role, self.path, self.events, self.stop = role, path, events, stop
        self.lock = threading.Lock()
        self.session = 0
        self.ready = False
        self.urgent = deque()
        self.latest = {}

    def generation(self):
        with self.lock:
            return self.session if self.ready else 0

    def post(self, packet, session):
        with self.lock:
            if not self.ready or self.session != session:
                return False
            if packet["type"] == "telemetry":
                self.latest[packet["node"]] = (CLOCK() + 0.8, packet)
            elif len(self.urgent) < 12:
                if packet["type"] == "ack":
                    self.latest.pop(packet["node"], None)
                self.urgent.append((CLOCK() + 0.7, packet))
            else:
                return False
            return True

    def next_packet(self, now):
        with self.lock:
            while self.urgent:
                deadline, packet = self.urgent.popleft()
                if now <= deadline:
                    return packet
            for key in list(self.latest):
                deadline, packet = self.latest.pop(key)
                if now <= deadline:
                    return packet
        return None

    def event(self, session, packet):
        try:
            self.events.put_nowait((self.role, session, CLOCK(), packet))
        except queue.Full:
            # Never delay heartbeat/watchdog I/O for slow disk or console.
            pass

    def exchange(self, device):
        parser = Lines()
        last_rx = CLOCK()
        next_beat = next_tx = 0
        with self.lock:
            self.session += 1
            session = self.session
        while not self.stop.is_set():
            now = CLOCK()
            for packet in parser.feed(device.read(min(device.in_waiting, 512))):
                if packet.get("node") != self.role:
                    raise ValueError("Identitas USB tidak cocok dengan symlink " + self.role)
                kind = packet.get("type")
                if kind == "telemetry":
                    if not all(integer(packet.get(k), *bounds) for k, bounds in FIELDS[self.role].items()):
                        continue
                    packet = {"node": self.role, "type": kind, **{k: packet[k] for k in FIELDS[self.role]}}
                    if not self.ready:
                        with self.lock:
                            self.ready = True
                        LOG.info("%s terhubung melalui %s", self.role, self.path)
                    last_rx = now
                elif kind not in ("ack", "cmd") or not self.ready:
                    continue
                self.event(session, packet)
            if now - last_rx > (3 if self.ready else 8):
                raise ValueError("Telemetri berhenti")
            if self.ready and now >= next_tx:
                if now >= next_beat:
                    packet = {"node": self.role, "type": "heartbeat", "src": "pi"}
                    next_beat = now + 1
                else:
                    packet = self.next_packet(now)
                if packet is not None:
                    raw = encode(packet)
                    if device.write(raw) != len(raw):
                        raise serial.SerialTimeoutException("Penulisan USB parsial")
                    next_tx = now + 0.035
            self.stop.wait(0.003)

    def run(self):
        last_error = ""
        while not self.stop.is_set():
            try:
                with serial.Serial(self.path, 115200, timeout=0, write_timeout=0.15,
                                   exclusive=True) as device:
                    self.exchange(device)
            except (OSError, ValueError, serial.SerialException) as exc:
                reason = str(exc)
                if self.ready or reason != last_error:
                    LOG.warning("%s: %s", self.role, reason)
                last_error = reason
            finally:
                with self.lock:
                    self.ready = False
                    self.urgent.clear()
                    self.latest.clear()
            self.stop.wait(1)


class Hub:
    def __init__(self, ports, writer):
        self.ports, self.writer = ports, writer
        self.sequence = 0
        self.pending = {}
        self.readings = {}

    def reply(self, source, session, dest, request, ok, code, extra=None):
        packet = dict(node=dest, type="ack", id=request, ok=ok, code=code)
        if extra:
            packet.update(extra)
        LOG.info("ACK %s id=%d ok=%d code=%d", dest, request, ok, code)
        if source == "hmi":
            self.ports["hmi"].post(packet, session)

    def command(self, source, session, packet):
        action, val = packet.get("action"), packet.get("val")
        request = packet.get("id")
        if not integer(request, 1, 32767):
            return
        dest = "sensor" if source == "console" else "actuator"
        ranges = {"CAL_TEMP": (-200, 200), "RESET": (1, 1)} if dest == "sensor" else ACTION_RANGES
        if (packet.get("target") != dest or not isinstance(action, str) or action not in ranges
                or not integer(val, *ranges[action]) or (action == "TARGET" and val % 500)):
            self.reply(source, session, dest, request, 0, 1)
            return
        link = self.ports[dest]
        dest_session = link.generation()
        self.sequence = self.sequence % 32767 + 1
        wire_id = self.sequence
        out = dict(node=dest, src="pi", type="cmd", id=wire_id, action=action, val=val)
        if not dest_session or not link.post(out, dest_session):
            self.reply(source, session, dest, request, 0, 5)
            return
        self.pending[(dest, dest_session, wire_id)] = (CLOCK() + 1.2, source, session, request)
        LOG.info("%s -> %s %s=%d id=%d", source, dest, action, val, wire_id)

    def handle(self, role, session, arrived, packet):
        if role == "console":
            if CLOCK()-arrived < 0.7:
                self.command(role, session, packet)
            return
        if self.ports[role].generation() != session:
            return
        kind = packet["type"]
        if kind == "telemetry":
            row = {k: packet[k] for k in FIELDS[role]}
            row.update(utc=datetime.now(timezone.utc).isoformat(timespec="milliseconds"), node=role)
            self.writer.writerow(row)
            self.readings[role] = (session, arrived, packet)
            if role != "hmi" and CLOCK()-arrived < 0.7:
                hmi = self.ports["hmi"]
                hmi.post(packet, hmi.generation())
        elif kind == "cmd" and role == "hmi":
            if CLOCK()-arrived < 0.7:
                self.command(role, session, packet)
        elif kind == "ack" and role in ("sensor", "actuator"):
            if not integer(packet.get("id"), 1, 32767) or not integer(packet.get("ok"), 0, 1):
                return
            entry = self.pending.pop((role, session, packet["id"]), None)
            if entry:
                deadline, source, origin_session, request = entry
                if CLOCK() > deadline:
                    self.reply(source, origin_session, role, request, 0, 6)
                    return
                code = packet.get("code", 0 if packet["ok"] else 1)
                if not integer(code, 0, 4):
                    code = 1
                extra = {k: packet[k] for k, bounds in (("bits", (0,63)), ("offset_dc", (-200,200)))
                         if integer(packet.get(k), *bounds)}
                self.reply(source, origin_session, role, request, packet["ok"], code, extra)

    def expire(self):
        now = CLOCK()
        for key, (deadline, source, session, request) in list(self.pending.items()):
            dest, dest_session, _ = key
            if now > deadline or self.ports[dest].generation() != dest_session:
                del self.pending[key]
                self.reply(source, session, dest, request, 0, 6)


def console(events):
    LOG.info("Konsol sensor: CAL_TEMP -15 atau RESET")
    number = 0
    for line in sys.stdin:
        fields = line.split()
        try:
            if fields == ["RESET"]:
                action, val = "RESET", 1
            elif len(fields) == 2 and fields[0] == "CAL_TEMP":
                action, val = fields[0], int(fields[1])
            else:
                raise ValueError()
            number = number % 32767 + 1
            events.put_nowait(("console", 0, CLOCK(), dict(id=number, target="sensor", action=action, val=val)))
        except (ValueError, queue.Full):
            LOG.warning("Perintah konsol tidak valid atau antrean penuh")


def main():
    args = argparse.ArgumentParser(description=__doc__)
    for role in ROLES:
        args.add_argument("--" + role, default="/dev/arduino_" + role)
    args.add_argument("--csv", type=Path, default=Path("accelerator_telemetry.csv"))
    args.add_argument("--console", action="store_true", help="Aktifkan kalibrasi sensor dari stdin")
    opt = args.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    paths = [str(Path(getattr(opt, role)).resolve()) for role in ROLES]
    if len(set(paths)) != 3:
        args.error("Tiga node harus menggunakan tiga port berbeda")
    stop, events = threading.Event(), queue.Queue(maxsize=256)
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    ports = {role: Port(role, getattr(opt, role), events, stop) for role in ROLES}
    with opt.csv.open("a", encoding="utf-8", newline="", buffering=1) as stream:
        writer = csv.DictWriter(stream, fieldnames=COLUMNS)
        if not stream.tell():
            writer.writeheader()
        hub = Hub(ports, writer)
        for worker in ports.values():
            worker.start()
        if opt.console:
            threading.Thread(target=console, args=(events,), daemon=True).start()
        summary = CLOCK()
        while not stop.is_set():
            try:
                hub.handle(*events.get(timeout=0.1))
            except queue.Empty:
                pass
            hub.expire()
            if CLOCK() - summary >= 10:
                LOG.info("USB %s | CSV %s", " ".join(r+"="+("OK" if p.generation() else "--")
                         for r,p in ports.items()), opt.csv)
                sample = hub.readings.get("sensor")
                if sample and sample[0] == ports["sensor"].generation() and CLOCK()-sample[1] < 1:
                    data = sample[2]
                    LOG.info("Sensor: %d Pa | %d V simulasi | %.1f C | IN=%d",
                             data["vac_pa"], data["hv_v"], data["temp_dc"]/10, data["din"])
                summary = CLOCK()
        stop.set()
        for worker in ports.values():
            worker.join(2)


if __name__ == "__main__":
    main()
