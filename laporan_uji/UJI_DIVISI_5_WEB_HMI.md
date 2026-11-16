# 🧪 Kartu Ceklis Uji Hardware — Divisi 5 (Web HMI SCADA & Simulator 2D)

- **Divisi:** Divisi 5 — Sistem Web HMI SCADA & Simulator 2D *(Anggota 5)*
- **Branch:** `divisi-5-web-hmi`
- **File Kode Utama:** `decy13_mqtt_kit/web_hmi/index.html`
- **Status Push Saat Ini:** `BELUM_MULAI`
- **Terakhir Diuji di Alat Nyata (Mini PC <-> RPi):** *(Belum pernah)*

---

## A. Ceklis Uji Kode & Browser Lokal di Laptop (Boleh Dicek Bareng AI)
- [ ] Mode simulasi offline di browser (`index.html`) berjalan tanpa error di *Browser DevTools Console*.
- [ ] Topic `decy13/hmi/cmd`, `decy13/rpi/state`, fungsi `applyRpiState()`, serta 8 perintah JSON wajib tidak berubah.
- [ ] Saat `state.mqttConnected === true`, loop animasi browser tidak menimpa `activeLedIndex` dan `shootLedIndex` dari Raspi.
- [ ] `python tools/cek_integrasi_dan_announcer.py --ci` lulus tanpa error.

## B. Ceklis Uji Koneksi Nyata Mini PC <-> Raspberry Pi 3B+ (WAJIB Tes Alat Nyata!)
> **Aturan AI:** JANGAN centang `[x]` bagian B sebelum diuji langsung tersambung ke broker MQTT Raspberry Pi `9001`!

- [ ] Status koneksi MQTT WebSocket (`ws://192.168.137.1:9001` atau IP RPi lokal) berubah hijau **"MQTT TERHUBUNG"**.
- [ ] Klik tombol di Web HMI (`Power`, `Vacuum`, `Interlock`, `Start Beam`, `Shoot`) langsung menggerakkan kipas, buzzer, LCD, dan LED fisik di Raspi.
- [ ] Indeks animasi LED 2D di kanvas Web HMI bergerak sinkron dengan LED fisik WS2812B di alat peraga.
- [ ] Menekan tombol fisik **E-Stop** di Raspberry Pi langsung memicu tampilan darurat merah di Web HMI Mini PC.

## C. Catatan Masalah / Bukti Pengujian Mini PC <-> Raspi
*(Catat jika WebSocket gagal connect, delay animasi, atau layout monitor Mini PC terpotong saat diuji.)*
- Menunggu push pertama dari branch `divisi-5-web-hmi`.
