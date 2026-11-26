# 🧪 Kartu Ceklis Uji Hardware — Divisi 5 (Web HMI SCADA & Simulator 2D)

- **Divisi:** Divisi 5 — Sistem Web HMI SCADA & Simulator 2D *(Dikerjakan & disinkronkan di Stasiun Mini PC atas instruksi Ketua)*
- **Branch:** `divisi-5-web-hmi` *(terintegrasi ke `main`)*
- **File Kode Utama:** `decy13_mqtt_kit/web_hmi/index.html`
- **Status Push Saat Ini:** `DRAFT_PUSH_LAPTOP`
- **Terakhir Diuji di Alat Nyata (Mini PC <-> RPi):** `2026-11-26` *(Broker WebSocket `ws://10.160.166.158:9001` aktif; menunggu uji visual 437 LED fisik pasca-update RPi)*

---

## A. Ceklis Uji Kode & Browser Lokal di Laptop (Boleh Dicek Bareng AI)
- [x] Mode simulasi offline di browser (`index.html`) berjalan tanpa error di *Browser DevTools Console*.
- [x] Topic `decy13/hmi/cmd`, `decy13/rpi/state`, fungsi `applyRpiState()`, serta 8 perintah JSON wajib tidak berubah.
- [x] Saat `state.mqttConnected === true`, loop animasi browser tidak menimpa `activeLedIndex` dan `shootLedIndex` dari Raspi.
- [x] `python tools/cek_integrasi_dan_announcer.py --ci` lulus tanpa error.

## B. Ceklis Uji Koneksi Nyata Mini PC <-> Raspberry Pi 3B+ (WAJIB Tes Alat Nyata!)
> **Aturan AI:** JANGAN centang `[x]` bagian B sebelum diuji langsung tersambung ke broker MQTT Raspberry Pi `9001`!

- [x] Status koneksi MQTT WebSocket (`ws://192.168.137.1:9001` atau IP RPi lokal) berubah hijau **"MQTT TERHUBUNG"**.
- [ ] Klik tombol di Web HMI (`Power`, `Vacuum`, `Interlock`, `Start Beam`, `Shoot`) langsung menggerakkan kipas, buzzer, LCD, dan LED fisik di Raspi.
- [ ] Indeks animasi LED 2D di kanvas Web HMI bergerak sinkron dengan LED fisik WS2812B di alat peraga.
- [ ] Menekan tombol fisik **E-Stop** di Raspberry Pi langsung memicu tampilan darurat merah di Web HMI Mini PC.

## C. Catatan Masalah / Bukti Pengujian Mini PC <-> Raspi
*(Catat jika WebSocket gagal connect, delay animasi, atau layout monitor Mini PC terpotong saat diuji.)*
- **`2026-11-24` s.d. `2026-11-26` (Uji Koneksi Nyata Mini PC `10.160.166.112` <-> RPi 3B+ `10.160.166.158` via Wi-Fi Hotspot `eaaa`):**
  - Koneksi MQTT over WebSocket `ws://10.160.166.158:9001` terhubung otomatis melalui jembatan `/api/runtime-config` (`tools/minipc_control_hub.py` & `MULAI_DECY13.bat`), indikator konsol menyala hijau dan menerima telemetri `decy13/rpi/state` (~5 Hz) serta panel 3-TFT USB (`assets/usb-panel.js`).
  - Pengujian kendali 7 perintah operasi dari Web HMI ke Core Daemon (`Power`, `Vacuum` Relay GPIO 21, `Interlock`, `Start Beam`, `Shoot` Buzzer GPIO 17, `Exposure OFF`, dan `Emergency Stop`) telah lulus (`HMI-01: 7/7 PASS` tanpa beban LED fisik).
- **`2026-11-26` (Penyelarasan Penuh Pemetaan 437 LED & Review QA Divisi 3 PR #4):**
  - Kanvas 2D `drawCyclotronSimulator()`, `renderStrip()`, dan `applyRpiState()` di `decy13_mqtt_kit/web_hmi/index.html` telah diperbarui agar 100% setara dengan driver *single-writer* Divisi 3 (`mod_led_ws2812b.py`):
    1. Pemetaan resmi **437 LED**: Spiral `0..388` (**389 LED**), 4 blok **RF Gap `[96, 193, 290, 387]`** (±2 LED, `RF_HOLD = 0.12 dtk`), serta jalur ekstraksi `389..436` (**48 LED**) dengan fallback adaptif bila daemon RPi masih mengirim profil 448/64 LED.
    2. **Dua paket partikel cyan berseberangan** (`head` dan `(head + 194) % 389`) dengan **ekor spiral 24 LED** (`max(7, 389 // 16) = 24`, peluruhan eksponensial `((24 - k) / 24)^1.5`).
    3. **Bar ekstraksi linear 48 segmen 1:1** (`#389..#436`) dengan **ekor oranye 16 LED tanpa wrap** (`max(5, 48 // 3) = 16`, tidak membungkus ke ujung kanan saat awal ekstraksi).
    4. **Indikator dampak target hijau** (`rgb(170, 255, 65)`) pada **8 piksel ujung (`#429..#436`)** dan kotak `TARGET` tepat saat `shootLedIdx == 436` (`TARGET_HOLD = 0.18 dtk`), serta pemadaman khusus jalur ekstraksi saat `SHOOT` dimatikan (`Exposure OFF`) tanpa mereset putaran spiral.
- **Sisa Verifikasi Lapangan untuk Naik ke `LULUS_UJI_FISIK`:**
  - Butir B.2 & B.3 menunggu `~/decy13` di Raspberry Pi di-update ke commit `main` terbaru (pasca-merge PR #4) dan diuji bersama beban fisik 437 LED WS2812B.
  - Catatan Butir B.4: Sesuai konfigurasi keselamatan `config_hardware.json` (`"estop_hardware_enabled": false`), pemicu E-Stop resmi dipusatkan pada tombol `EMERGENCY_STOP` di Web HMI untuk mencegah *false-trigger* induksi elektromagnetik pada pin `GPIO 22`.
