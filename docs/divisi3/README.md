# DECY-13 — Divisi 3 LED Visualization

## Identitas Pengembangan

- Branch: divisi-3-single-writer-final
- Commit implementasi: d26b767
- Base repository: 16e2c15
- Perangkat: Raspberry Pi 3 Model B+
- LED: WS2812B
- Tanggal evaluasi: 26 November 2026

## Arsitektur Sistem

Web HMI -> MQTT Broker -> Core Daemon
-> LED Worker -> PWM/DMA -> GPIO12 -> WS2812B

Arsitektur single-writer memisahkan rendering LED
dari proses pembaruan state Core Daemon.

Core Daemon mengirim snapshot state dan membaca
indeks animasi tanpa menunggu operasi strip.show().

## Konfigurasi Hardware

| Parameter | Nilai |
|---|---|
| GPIO LED BCM | 12 |
| Pin fisik | 32 |
| GPIO buzzer | 17 |
| Total LED | 437 |
| Spiral | 0-388 |
| RF gaps | 96, 193, 290, 387 |
| Beamline | 389-436 |
| Target | 429-436 |
| FPS driver | 40 |
| Brightness konfigurasi | 45/255 |
| Brightness pengujian hardware | 10/255 |

## Fitur Animasi

- Standby: 16 LED biru.
- Vacuum pumping: visualisasi ungu.
- Beam ready: cyan dan indikator RF gap.
- Acceleration: dua paket cyan bergerak.
- Kecepatan animasi mengikuti energi simulasi.
- Extraction: paket oranye menuju target.
- Target impact: indikator hijau.
- Continuous exposure.
- Exposure OFF tanpa menghentikan spiral.
- Emergency Stop: seluruh indeks dinonaktifkan.

## Antarmuka Modul

- setup()
- update(state, dt, now)
- cleanup()

Modul LED hanya bertanggung jawab terhadap visualisasi
dan pembaruan activeLedIdx serta shootLedIdx.

Core Daemon tidak dimodifikasi dalam branch ini.

## Komunikasi MQTT

- Command: decy13/hmi/cmd
- Telemetry: decy13/rpi/state
- Interval telemetry: 0.2 detik
- Port produksi: TCP 1883, WebSocket 9001
- Port pengujian: TCP 18884, WebSocket 18885

## Status

Software siap diajukan sebagai kandidat integrasi.

Pengujian LED fisik setelah patch masih menunggu
persetujuan kesiapan kelistrikan dari divisi terkait.

Lihat QA_REPORT.md dan HANDOFF_KETUA.md.
