#!/usr/bin/env python3
"""QA Stage 0–7 sintetis, ONLY broker loopback 127.0.0.1:1885.
Tidak menerbitkan perintah kontrol dan tidak menggunakan GPIO.
Contoh: python qa_stage_0_7.py --hold 4 --output DECY13_QA_Stage_0_7_HMI.csv
"""
import argparse
import csv
import json
import time
import uuid
from datetime import datetime
from threading import Event, Lock

import paho.mqtt.client as mqtt

HOST = '127.0.0.1'
PORT = 1885
TOPIC = 'decy13/qa/state'

def make_state(stage):
    return {
        'power': False, 'vacuum': False, 'rf': False, 'magnet': False,
        'interlocks': False, 'beam': False, 'exposureActive': False,
        'emergency': False, 'stage': stage,
        'mode': 'OFF' if stage == 0 else f'QA_STAGE_{stage}',
        'lcd_line1': 'DECY-13 QA', 'lcd_line2': f'STAGE {stage}',
        'lcd_line3': 'MQTT TEST', 'lcd_line4': 'SIMULATION',
        'pressure': 1.0, 'beamEnergy': 0.0,
        'beamCurrent': 0.0, 'targetCurrent': 0.0,
        'activeLedIdx': 0, 'shootLedIdx': 0,
        'buzzerActive': False, 'logs': [f'QA Stage {stage}']
    }

EXPECTED = make_state(0)
KEYS = set(EXPECTED)
assert len(KEYS) == 22

def main():
    ap = argparse.ArgumentParser(description='QA publish–subscribe Stage 0–7 secara terisolasi')
    ap.add_argument('--hold', type=float, default=0.5, help='Jeda tiap stage (detik), 4 untuk HMI')
    ap.add_argument('--output', default='DECY13_QA_Stage_0_7.csv')
    args = ap.parse_args()
    if not 0 <= args.hold <= 60:
        ap.error('--hold harus 0..60 detik')
    subscribed = Event()
    message_event = Event()
    lock = Lock()
    messages = []

    def on_connect(client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            client.subscribe(TOPIC, qos=1)
        else:
            print('CONNECT FAIL:', reason_code)

    def on_subscribe(client, userdata, mid, reason_codes, properties=None):
        subscribed.set()

    def on_message(client, userdata, msg):
        try:
            value = json.loads(msg.payload.decode('utf-8'))
        except (ValueError, UnicodeDecodeError) as e:
            value = {'_parse_error': str(e)}
        with lock:
            messages.append(value)
        message_event.set()

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                         client_id='decy13-qa-' + uuid.uuid4().hex[:8])
    client.on_connect = on_connect
    client.on_subscribe = on_subscribe
    client.on_message = on_message
    results = []
    try:
        client.connect(HOST, PORT, 30)
        client.loop_start()
        if not subscribed.wait(5):
            raise RuntimeError('Tidak dapat subscribe pada broker QA port 1885')
        print('=== QA STAGE 0-7 (BROKER QA TERISOLASI) ===')
        for stage in range(8):
            with lock:
                before = len(messages)
            message_event.clear()
            state = make_state(stage)
            info = client.publish(TOPIC, json.dumps(state, allow_nan=False), qos=1, retain=False)
            info.wait_for_publish(timeout=5)
            got = message_event.wait(5)
            with lock:
                actual = messages[-1] if got and len(messages) > before else None
            valid = (isinstance(actual, dict) and set(actual) == KEYS
                and len(actual) == 22
                and type(actual.get('stage')) is int and actual.get('stage') == stage
                and actual.get('mode') == state['mode']
                and all(type(actual[k]) is type(state[k]) for k in KEYS))
            status = 'PASS' if valid else 'FAIL'
            results.append({'time': datetime.now().isoformat(timespec='seconds'),
                            'stage': stage, 'status': status, 'field_count': len(state),
                            'received': bool(got and actual is not None)})
            print(f'Stage {stage}: {status} | {len(state)} field')
            time.sleep(args.hold)
    finally:
        client.disconnect()
        client.loop_stop()
    with open(args.output, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['time','stage','status','field_count','received'])
        writer.writeheader()
        writer.writerows(results)
    passed = sum(row['status']=='PASS' for row in results)
    print(f'=== HASIL QA: PASS {passed}/8 | FAIL {8-passed} | CSV {args.output} ===')
    return 0 if passed == 8 else 1

if __name__ == '__main__':
    raise SystemExit(main())
