# 🧪 Kartu Ceklis Uji Hardware — Divisi 3 (LED Strip WS2812B Spiral & Shoot)

- **Divisi:** Divisi 3 — Sistem LED Strip WS2812B (`blufiaa`)
- **Branch:** `divisi-3-led-ws2812b-v13` *(sudah di-merge ke `main` pada `ac21a27`)*
- **File Kode Utama:** `decy13_mqtt_kit/raspi_cli/modules/mod_led_ws2812b.py`, `decy13_mqtt_kit/raspi_cli/03_test_led_pixel_finder.py`
- **Status Push Saat Ini:** `DRAFT_PUSH_LAPTOP`
- **Terakhir Diuji di Raspi Fisik:** *(Belum diuji di LED WS2812B fisik RPi 3B+ — baru lolos uji virtual & integrasi di `main`)*

---

## A. Ceklis Uji Kode & Simulasi di Laptop (Boleh Dicek Bareng AI)
- [x] Branch `divisi-3-led-ws2812b-v13` dibuat bersih dari `main` terbaru (tidak ada folder `divisi3_led/` dan tidak ada `__pycache__/*.pyc`).
- [x] Memakai driver `rpi_ws281x` (`PixelStrip`) pada pin `GPIO 18` dengan `try/except ImportError` fallback `MemoryStrip` untuk laptop Windows (BUKAN `pi5neo` SPI0).
- [x] Membaca `total_leds`, `spiral_start_idx`, `spiral_end_idx`, `rf_gap_indices`, `shoot_start_idx`, `shoot_end_idx` secara dinamis dari `self.cfg["led_mapping"]` (tidak meng-hardcode `200`).
- [x] Dibungkus dalam class `LedStripModule(HardwareModule)` dan meng-update `state["activeLedIdx"]` & `state["shootLedIdx"]`.
- [x] `python tools/cek_integrasi_dan_announcer.py --ci` & `python 03_test_led_pixel_finder.py --mode test` lulus tanpa error (`ALL DIVISI 3 VIRTUAL TESTS PASSED`).

## B. Ceklis Uji Fisik Hardware Raspberry Pi 3B+ (WAJIB Tes Alat Nyata!)
> **Aturan AI:** JANGAN centang `[x]` bagian B sebelum anggota menguji langsung di RPi 3B+ fisik dan menempelkan outputnya di Bagian C!

- [ ] Audio analog di RPi sudah dimatikan (`dtparam=audio=off` di `/boot/config.txt`) agar DMA GPIO 18 berjalan normal.
- [ ] `sudo python3 03_test_led_pixel_finder.py` menyalakan piksel #0 s.d. #63 secara akurat tanpa salah urutan/mati sebagian.
- [ ] Urutan warna LED RGB/GRB benar sesuai warna per tahap (bukan merah tertukar hijau).
- [ ] Animasi komet spiral (`0..47`), kilat RF Gap (`[11, 23, 35, 47]`), dan Shoot (`48..63`) berjalan mulus **tanpa flicker** saat LCD ILI9341 (`SPI0`) juga aktif bersamaan di `04_decy13_mqtt_daemon.py`.
- [ ] Saat `Ctrl+C` / `cleanup()`, seluruh LED padam total (`Color(0,0,0)`).

## C. Catatan Masalah / Bukti Output Terminal Raspi
*(Tempelkan output `sudo python3 03_test_led_pixel_finder.py --mode finder --hardware` dari Raspi atau tulis kendala fisik seperti warna tertukar / flicker / kurang daya 5V di sini.)*
- **Update Merge (`2026-11-16`, `ac21a27`):** Migrasi bersih lewat `divisi-3-led-ws2812b-v13` sudah masuk ke `main`! Seluruh tes simulasi Tahap A (`--mode test` dan `cek_integrasi_dan_announcer.py --ci`) lulus tanpa error.
- Menunggu hasil pengujian fisik pada LED strip WS2812B + Raspberry Pi 3B+ nyata untuk melengkapi Tahap B.
