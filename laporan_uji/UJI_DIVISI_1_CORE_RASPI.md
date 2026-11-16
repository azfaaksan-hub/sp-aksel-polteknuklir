# 🧪 Kartu Ceklis Uji Hardware — Divisi 1 (Core Backend Raspi & Integrator)

- **Divisi:** Divisi 1 — Core Backend Raspberry Pi 3B+
- **Branch:** `main` / `core-raspi-backend`
- **File Kode Utama:** `decy13_mqtt_kit/raspi_cli/04_decy13_mqtt_daemon.py`, `config_hardware.json`, `modules/base_module.py`
- **Status Push Saat Ini:** `DRAFT_PUSH_LAPTOP`
- **Terakhir Diuji di Raspi Fisik:** *(Belum diuji langsung di RPi 3B+ fisik)*

---

## A. Ceklis Uji Kode & Simulasi di Laptop (Boleh Dicek Bareng AI)
- [x] `python tools/cek_integrasi_dan_announcer.py --ci` lulus tanpa error.
- [x] `Decy13CoreDaemon` dapat dijalankan di laptop Windows (`05_laptop_dryrun_simulator.py`) dalam mode fallback tanpa `RPi.GPIO`.
- [x] Kontrak pemanggilan `setup()`, `update(state, dt, now)`, `cleanup()` serta 22 field JSON MQTT terjaga.

## B. Ceklis Uji Fisik Hardware Raspberry Pi 3B+ (WAJIB Tes Alat Nyata!)
> **Aturan AI:** JANGAN centang `[x]` bagian B sebelum ada bukti eksekusi langsung di Raspberry Pi 3B+ nyata!

- [ ] `/boot/config.txt` sudah `dtparam=audio=off` dan `dtparam=spi=on` (diverifikasi lewat `ls /dev/spi*`).
- [ ] Mosquitto Broker aktif di Raspberry Pi pada TCP `1883` dan WebSocket `9001`.
- [ ] `sudo python3 04_decy13_mqtt_daemon.py` berjalan stabil (loop ~200ms) sambil menggerakkan modul Divisi 2, 3, dan 4 sekaligus tanpa lag/crash.
- [ ] Seluruh stage 0..7 + `EMERGENCY_STOP` sinkron antara fisik RPi dan Web HMI Mini PC via jaringan lokal.
- [ ] Tekan `Ctrl+C` pada daemon membersihkan GPIO/LED/Relay (`cleanup_all()`) dengan aman (kipas & buzzer mati).

## C. Catatan Masalah / Bukti Output Terminal Raspi
*(Tempelkan output terminal dari RPi 3B+ atau catatan hal yang masih diperbaiki di sini sebelum commit & push.)*
- Catatan saat ini: Core Daemon & arsitektur modular sudah terverifikasi via simulasi laptop (`2026-11-15`), menunggu uji langsung pada unit Raspberry Pi 3B+ fisik.
