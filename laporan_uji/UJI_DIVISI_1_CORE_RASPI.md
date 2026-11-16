# 🧪 Kartu Ceklis Uji Hardware — Divisi 1 (Core Backend Raspi & Integrator)

- **Divisi:** Divisi 1 — Core Backend Raspberry Pi 3B+ (`azfaaksan-hub`)
- **Branch:** `main` / `core-raspi-backend`
- **File Kode Utama:** `decy13_mqtt_kit/raspi_cli/04_decy13_mqtt_daemon.py`, `05_laptop_dryrun_simulator.py`, `config_hardware.json`, `modules/base_module.py`
- **Status Push Saat Ini:** `DRAFT_PUSH_LAPTOP`
- **Terakhir Diuji di Raspi Fisik:** `2026-11-16` *(Bare-board RPi 3B+ `sp-aksel@sp-aksel`, IP LAN `192.168.137.66` — aktuator fisik belum di-wiring & belum diuji di Mini PC fisik)*

---

## A. Ceklis Uji Kode & Simulasi di Laptop (Boleh Dicek Bareng AI)
- [x] `python tools/cek_integrasi_dan_announcer.py --ci` lulus tanpa error.
- [x] `Decy13CoreDaemon` dapat dijalankan di laptop Windows (`05_laptop_dryrun_simulator.py`) dalam mode fallback tanpa `RPi.GPIO`.
- [x] Kontrak pemanggilan `setup()`, `update(state, dt, now)`, `cleanup()` serta 22 field JSON MQTT terjaga.

## B. Ceklis Uji Fisik Hardware Raspberry Pi 3B+ (WAJIB Tes Alat Nyata!)
> **Aturan AI:** JANGAN centang `[x]` bagian B sebelum ada bukti eksekusi langsung di Raspberry Pi 3B+ nyata!

- [x] `/boot/config.txt` sudah `dtparam=audio=off` dan `dtparam=spi=on` (diverifikasi lewat `ls /dev/spi*`).
- [x] Mosquitto Broker aktif di Raspberry Pi pada TCP `1883` dan WebSocket `9001`.
- [ ] `sudo python3 04_decy13_mqtt_daemon.py` berjalan stabil (loop ~200ms) sambil menggerakkan modul Divisi 2, 3, dan 4 sekaligus tanpa lag/crash.
- [ ] Seluruh stage 0..7 + `EMERGENCY_STOP` sinkron antara fisik RPi dan Web HMI Mini PC via jaringan lokal.
- [x] Tekan `Ctrl+C` pada daemon membersihkan GPIO/LED/Relay (`cleanup_all()`) dengan aman (kipas & buzzer mati).

## C. Catatan Masalah / Bukti Output Terminal Raspi
*(Tempelkan output terminal dari RPi 3B+ atau catatan hal yang masih diperbaiki di sini sebelum commit & push.)*
- **Bukti Uji Bare-Board Raspberry Pi 3B+ (`2026-11-16`, unit `sp-aksel@sp-aksel`, IP LAN `192.168.137.66`):**
  1. Konfigurasi OS `/boot/firmware/config.txt` sudah `dtparam=audio=off` & `dtparam=spi=on`; `ls /dev/spi*` menampilkan `/dev/spidev0.0` dan `/dev/spidev0.1`.
  2. Mosquitto Broker aktif pada TCP `1883` dan WebSocket `9001`.
  3. `sudo python3 04_decy13_mqtt_daemon.py` menginisialisasi ketiga modul (`VacuumSafetyModule`, `LedStripModule`, `LcdDisplayModule`) dengan status `[HARDWARE AKTIF]` dan terhubung ke `127.0.0.1:1883 (rc=0)`.
  4. Uji `06_test_mqtt_healthcheck.py --host 192.168.137.66 --duration 5 --no-menu` dari laptop via LAN: `LULUS=10, GAGAL=0`, laju telemetri `4.97 Hz` (interval rata-rata `201 ms`, std `0 ms`, `0` paket hilang, `22/22` field JSON valid, round-trip broker rata-rata `1.5 ms`).
  5. Uji kontrol 2 arah dari Web HMI (`ws://192.168.137.66:9001`): sekuens Tahap 1 (Power ON) → Tahap 4 (Vakum ON) → Tahap 5 (Interlock LOCKED) → Tahap 6 (Start Beam) → Tahap 7 (Shoot Exposure) → Emergency Stop berjalan lancar (`18:33:52` s.d. `18:35:09`), dan `Ctrl+C` (`cleanup_all()`) aman.
  6. Bukti preflight di RPi tersimpan sebagai `laporan_uji/bukti/PREFLIGHT_DIVISI_1_sp-aksel_20261116_190341.txt`.
- **Sisa pengujian (`2/5` Tahap B belum dicentang):** aktuator fisik (Relay kipas/Buzzer/E-Stop, LED strip WS2812B, LCD ILI9341) belum di-wiring bersama di RPi dan belum diuji dari Mini PC ruang kontrol fisik.
