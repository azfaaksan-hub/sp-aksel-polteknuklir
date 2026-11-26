# Panduan Serah Terima — Ketua DECY-13

## 1. Branch Kandidat

Repository:
https://github.com/azfaaksan-hub/sp-aksel-polteknuklir

Branch:
divisi-3-single-writer-final

Commit implementasi:
d26b767

## 2. File Implementasi

- decy13_mqtt_kit/raspi_cli/03_test_led_pixel_finder.py
- decy13_mqtt_kit/raspi_cli/config_hardware.json
- decy13_mqtt_kit/raspi_cli/modules/mod_led_ws2812b.py

Core Daemon dan modul divisi lainnya tidak dimodifikasi.

## 3. Pengujian Software

Dari root repository kandidat:

    cd decy13_mqtt_kit/raspi_cli

    python3 -m py_compile modules/mod_led_ws2812b.py

    python3 03_test_led_pixel_finder.py --mode test

Target regression: 20/20 PASS.

Pengujian tersebut menggunakan mode virtual.

## 4. Konfigurasi Raspberry Pi

Worktree pengujian:

    /home/sp-aksel/decy13-divisi3-v16

Direktori perangkat pengujian tambahan:

    /home/sp-aksel/decy13-integration-test

Wrapper pengujian:

    run_core_test.py

Wrapper tersebut berada di luar repository dan
tersedia pada Raspberry Pi pengujian, bukan hasil clone.

Wrapper menggunakan broker terisolasi port 18884,
brightness 10/255, serta menonaktifkan modul LCD
dan fungsi interlock hardware untuk pengujian.

## 5. Pengujian MQTT

Topic command:

    decy13/hmi/cmd

Topic telemetry:

    decy13/rpi/state

Pemeriksaan telemetry pada broker pengujian:

    mosquitto_sub -h 127.0.0.1 -p 18884 \
    -t decy13/rpi/state -C 5 -W 10

Broker dan wrapper pengujian harus sudah berjalan.

## 6. Pemeriksaan Sebelum Commissioning

- Pastikan hanya satu Core Daemon berjalan.
- Pastikan GPIO data LED menggunakan BCM12.
- Pastikan mapping sesuai 437 LED.
- Koordinasikan konflik audio PWM dengan tim.
- Peroleh persetujuan kesiapan kelistrikan.
- Gunakan brightness awal yang telah disepakati.
- Jangan menjalankan konfigurasi lama secara otomatis.

Service decy13.service pada Raspberry Pi pengujian
dinonaktifkan sementara untuk mencegah konflik
dengan daemon versi lama.

Pengaktifan kembali service dilakukan oleh tim
setelah konfigurasi final disetujui.

## 7. Kriteria Penerimaan Akhir

- Standby: 16 LED biru.
- Vacuum: visualisasi ungu.
- Ready: cyan dan RF gaps.
- Acceleration: dua paket cyan bergerak.
- Extraction: spiral tetap berjalan.
- Target: indikator hijau.
- Exposure OFF: hanya beamline berhenti.
- Emergency Stop: LED padam.
- Stress test fisik: tidak hang atau mengalami
  gangguan kelistrikan.
- Shutdown: cleanup berhasil.

Pengujian fisik dilakukan setelah divisi kelistrikan
menyatakan perangkat siap.

## 8. Integrasi Git

Lakukan review branch kandidat sebelum merge.
Jangan mengganti konfigurasi hardware seluruh sistem
tanpa koordinasi dengan divisi yang berkaitan.

## 9. Status Serah Terima

Software: siap review.
Integrasi tanpa beban LED: PASS.
Penerimaan hardware fisik setelah patch: PENDING.

Referensi hasil pengujian:
QA_REPORT.md.
