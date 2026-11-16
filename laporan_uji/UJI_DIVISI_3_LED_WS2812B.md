# 🧪 Kartu Ceklis Uji Hardware — Divisi 3 (LED Strip WS2812B Spiral & Shoot)

- **Divisi:** Divisi 3 — Sistem LED Strip WS2812B (`blufiaa`)
- **Branch:** `divisi-3-led-ws2812b` *(perlu migrasi dari `pacarjeno` ke branch baru dari `main`)*
- **File Kode Utama:** `decy13_mqtt_kit/raspi_cli/modules/mod_led_ws2812b.py`, `decy13_mqtt_kit/raspi_cli/03_test_led_pixel_finder.py`
- **Status Push Saat Ini:** `SEDANG_REVISI_HARDWARE`
- **Terakhir Diuji di Raspi Fisik:** *(Belum diuji di RPi 3B+ pada arsitektur `main` resmi)*

---

## A. Ceklis Uji Kode & Simulasi di Laptop (Boleh Dicek Bareng AI)
- [ ] Branch `divisi-3-led-ws2812b` dibuat dari `main` terbaru (tidak ada folder `divisi3_led/` dan tidak ada `__pycache__/*.pyc`).
- [ ] Memakai driver `rpi_ws281x` (`PixelStrip`) pada pin `GPIO 18` dengan `try/except ImportError` fallback simulasi untuk laptop Windows (BUKAN `pi5neo` SPI0).
- [ ] Membaca `total_leds`, `spiral_start_idx`, `spiral_end_idx`, `rf_gap_indices`, `shoot_start_idx`, `shoot_end_idx` secara dinamis dari `self.cfg["led_mapping"]` (tidak meng-hardcode `200`).
- [ ] Dibungkus dalam class `LedStripModule(HardwareModule)` dan meng-update `state["activeLedIdx"]` & `state["shootLedIdx"]`.
- [ ] `python tools/cek_integrasi_dan_announcer.py --ci` lulus tanpa error.

## B. Ceklis Uji Fisik Hardware Raspberry Pi 3B+ (WAJIB Tes Alat Nyata!)
> **Aturan AI:** JANGAN centang `[x]` bagian B sebelum anggota menguji langsung di RPi 3B+ fisik dan menempelkan outputnya di Bagian C!

- [ ] Audio analog di RPi sudah dimatikan (`dtparam=audio=off` di `/boot/config.txt`) agar DMA GPIO 18 berjalan normal.
- [ ] `sudo python3 03_test_led_pixel_finder.py` menyalakan piksel #0 s.d. #63 secara akurat tanpa salah urutan/mati sebagian.
- [ ] Urutan warna LED RGB/GRB benar sesuai warna per tahap (bukan merah tertukar hijau).
- [ ] Animasi komet spiral (`0..47`), kilat RF Gap (`[11, 23, 35, 47]`), dan Shoot (`48..63`) berjalan mulus **tanpa flicker** saat LCD ILI9341 (`SPI0`) juga aktif bersamaan di `04_decy13_mqtt_daemon.py`.
- [ ] Saat `Ctrl+C` / `cleanup()`, seluruh LED padam total (`Color(0,0,0)`).

## C. Catatan Masalah / Bukti Output Terminal Raspi
*(Tempelkan output `sudo python3 03_test_led_pixel_finder.py` dari Raspi atau tulis kendala fisik seperti warna tertukar / flicker / kurang daya 5V di sini.)*
- **Update Audit Commit `0137adb` (`2026-11-16`):** Isi kode baru (`mod_led_ws2812b.py` 664 baris & `03_test_led_pixel_finder.py` 720 baris) **SUDAH BENAR** memakai `GPIO 18`, `rpi_ws281x` + `MemoryStrip`, membaca dinamis `config_hardware.json`, serta lolos uji simulasi `LedStripModule` (`activeLedIdx`/`shootLedIdx`).
- **Kendala Git yang tersisa:** Commit `0137adb` masih bercabang dari `2088dc0` (history lama ex-`pacarjeno`), sehingga masih membawa folder sampah `divisi3_led/` + `__pycache__/*.pyc` dan memicu 2 Merge Conflict bila langsung di-merge. Harap buat ulang branch `divisi-3-led-ws2812b` dari `origin/main` terbaru dan bawa hanya 2 file resminya.
