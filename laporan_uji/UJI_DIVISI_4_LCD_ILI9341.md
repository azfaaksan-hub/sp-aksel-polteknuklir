# 🧪 Kartu Ceklis Uji Hardware — Divisi 4 (Layar LCD TFT SPI ILI9341)

- **Divisi:** Divisi 4 — Sistem Layar LCD TFT SPI ILI9341 *(Anggota 4)*
- **Branch:** `divisi-4-lcd-ili9341`
- **File Kode Utama:** `decy13_mqtt_kit/raspi_cli/modules/mod_lcd_ili9341.py`, `decy13_mqtt_kit/raspi_cli/02_test_lcd_ili9341.py`
- **Status Push Saat Ini:** `BELUM_MULAI`
- **Terakhir Diuji di Raspi Fisik:** *(Belum pernah)*

---

## A. Ceklis Uji Kode & Simulasi di Laptop (Boleh Dicek Bareng AI)
- [ ] Kode berjalan aman di laptop Windows tanpa library `luma.lcd` (`try/except ImportError` fallback aktif).
- [ ] `LcdDisplayModule(HardwareModule)` merender lewat background thread agar transfer SPI tidak memblokir loop MQTT 200ms.
- [ ] Hanya mengedit file milik Divisi 4 + kartu ceklis ini.
- [ ] `python tools/cek_integrasi_dan_announcer.py --ci` lulus tanpa error.

## B. Ceklis Uji Fisik Hardware Raspberry Pi 3B+ (WAJIB Tes Alat Nyata!)
> **Aturan AI:** JANGAN centang `[x]` bagian B sebelum anggota menguji langsung di RPi 3B+ fisik dan menempelkan outputnya di Bagian C!

- [ ] Interface SPI di RPi aktif (`ls /dev/spi*` menampilkan `/dev/spidev0.0`).
- [ ] `python3 02_test_lcd_ili9341.py` menampilkan gambar tajam 320x240 di layar fisik (orientasi tidak terbalik, warna tidak pudar/inverted, wiring `DC=24`, `RST=25`, `CE0=8` benar).
- [ ] Teks `lcd_line1..4`, kotak Safety Interlock, bar Vakum logaritmik, dan bar Energi MeV terbaca jelas dari jarak 1–2 meter tanpa terpotong.
- [ ] Saat `04_decy13_mqtt_daemon.py` jalan bersamaan dengan LED WS2812B (`GPIO 18`), layar tidak *freeze* dan tidak mengganggu animasi LED.

## C. Catatan Masalah / Bukti Output Terminal Raspi
*(Tempelkan output terminal Raspi atau catatan kendala layar putih/blank/terbalik jika ada sebelum push.)*
- Menunggu push pertama dari branch `divisi-4-lcd-ili9341`.
