#!/usr/bin/env python3
"""Simulator PENDIDIKAN DECY-13; hanya localhost MQTT, tidak mengakses GPIO."""
import json
import threading
import time
import uuid
import argparse
import paho.mqtt.client as mqtt

TOPIC_STATE = 'decy13/rpi/state'
TOPIC_CMD = 'decy13/hmi/cmd'
lock = threading.Lock()
state = {
    'power': False, 'vacuum': False, 'rf': False, 'magnet': False,
    'interlocks': False, 'beam': False, 'exposureActive': False,
    'emergency': False, 'stage': 0, 'mode': 'OFF',
    'lcd_line1': 'DECY-13 DEMO', 'lcd_line2': 'READY',
    'lcd_line3': 'SIMULATOR', 'lcd_line4': 'NO GPIO',
    'pressure': 1.0, 'beamEnergy': 0.0, 'beamCurrent': 0.0,
    'targetCurrent': 0.0, 'activeLedIdx': -1, 'shootLedIdx': -1,
    'buzzerActive': False, 'logs': ['Simulator dimulai']
}
shoot_position = 48
stage6_started_at = None
STAGE6_HOLD_SECONDS = 1.0

def log(msg):
    state['logs'] = [msg] + state['logs'][:9]
    print('[CMD]', msg, flush=True)

def on_connect(client, userdata, flags, reason_code, properties=None):
    print('MQTT terhubung:', reason_code, flush=True)
    client.subscribe(TOPIC_CMD)

def on_message(client, userdata, msg):
    global shoot_position, stage6_started_at
    try:
        data = json.loads(msg.payload)
        cmd = data.get('cmd')
    except (ValueError, AttributeError, TypeError):
        return
    with lock:
        if state['emergency']:
            log('Ditolak: E-Stop aktif; restart simulator untuk reset')
            return
        if cmd == 'EMERGENCY_STOP':
            state.update(emergency=True, beam=False, exposureActive=False, rf=False,
                         magnet=False, buzzerActive=True, activeLedIdx=-1,
                         shootLedIdx=-1, beamCurrent=0.0, targetCurrent=0.0,
                         mode='EMERGENCY')
            log('EMERGENCY_STOP')
        elif cmd == 'TOGGLE_POWER':
            if state['power']:
                stage6_started_at = None
                state.update(power=False, vacuum=False, rf=False, magnet=False,
                             interlocks=False, beam=False, exposureActive=False,
                             stage=0, mode='OFF', beamEnergy=0.0,
                             beamCurrent=0.0, targetCurrent=0.0,
                             activeLedIdx=-1, shootLedIdx=-1, pressure=1.0, buzzerActive=False)
            else:
                state.update(power=True, stage=1, mode='POWER_ON')
            log(cmd)
        elif not state['power']:
            log(f'Ditolak: {cmd}, power OFF')
        elif cmd == 'TOGGLE_VACUUM':
            state['vacuum'] = not state['vacuum']
            if state['vacuum']:
                state.update(stage=max(2, state['stage']), mode='VACUUM_ON')
            log(cmd)
        elif cmd == 'TOGGLE_INTERLOCK':
            state['interlocks'] = not state['interlocks']
            if state['interlocks']:
                state.update(stage=max(3, state['stage']), mode='INTERLOCK_READY')
            log(cmd)
        elif cmd == 'AUTO_INIT':
            if state['vacuum'] and state['interlocks']:
                state.update(stage=4, mode='INITIALIZED', rf=True, magnet=True)
                log(cmd)
            else:
                log('Ditolak: AUTO_INIT memerlukan vacuum + interlocks')
        elif cmd == 'START_BEAM':
            if state['vacuum'] and state['interlocks'] and state['rf'] and state['magnet']:
                state.update(stage=5, mode='BEAM_ACCELERATING', beam=True)
                log(cmd)
            else:
                log('Ditolak: belum siap START_BEAM')
        elif cmd == 'SHOOT':
            if state['beam'] and state['beamEnergy'] >= 12.35:
                state.update(stage=6, mode='EXPOSURE', exposureActive=True,
                             shootLedIdx=48, targetCurrent=0.08)
                shoot_position = 48
                stage6_started_at = time.monotonic()
                log(cmd)
            else:
                log('Ditolak: SHOOT menunggu energi >= 12.35 MeV')
        else:
            log(f'Perintah tidak dikenali: {cmd}')

def main():
    global shoot_position, stage6_started_at
    ap = argparse.ArgumentParser(description='Simulator DECY-13 untuk pengujian lokal Divisi 6')
    ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=1883)
    args = ap.parse_args()
    if args.host not in ('localhost', '127.0.0.1'):
        ap.error('Demi keamanan, simulator ini hanya diizinkan ke broker localhost.')
    if hasattr(mqtt, 'CallbackAPIVersion'):
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                             client_id='decy13_demo_' + uuid.uuid4().hex[:8])
    else:
        client = mqtt.Client(client_id='decy13_demo_' + uuid.uuid4().hex[:8])
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(args.host, args.port, 30)
    client.loop_start()
    print('Simulator lokal berjalan 5 Hz. Tekan Ctrl+C untuk berhenti.', flush=True)
    last = time.monotonic()
    try:
        while True:
            time.sleep(0.2)
            now = time.monotonic()
            dt = min(now - last, 1)
            last = now
            with lock:
                if state['vacuum']:
                    state['pressure'] = max(1e-6, state['pressure'] * 0.89)
                if state['beam']:
                    state['beamEnergy'] = min(13.0, state['beamEnergy'] + dt * 1.5)
                    state['beamCurrent'] = 0.12
                    state['activeLedIdx'] = (int(now * 12) % 48)
                    if state['beamEnergy'] >= 12.35 and not state['exposureActive']:
                        state['stage'] = 5
                        state['mode'] = 'BEAM_READY'
                if state['exposureActive']:
                    state['shootLedIdx'] = shoot_position
                    shoot_position += 1
                    if shoot_position > 63:
                        shoot_position = 48
                    if (
                        stage6_started_at is not None
                        and now - stage6_started_at >= STAGE6_HOLD_SECONDS
                    ):
                        state['stage'] = 7
                state['lcd_line2'] = f"Stage {state['stage']} {state['mode']}"[:25]
                state['lcd_line3'] = f"Energy {state['beamEnergy']:.1f} MeV"
                state['lcd_line4'] = f"Vacuum {state['pressure']:.2e} mbar"
                payload = json.dumps(state, allow_nan=False)
            client.publish(TOPIC_STATE, payload, qos=0, retain=False)
    except KeyboardInterrupt:
        print('\nSimulator berhenti.', flush=True)
    finally:
        client.disconnect()
        client.loop_stop()

if __name__ == '__main__':
    main()
