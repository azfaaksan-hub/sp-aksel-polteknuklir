# 🧪 Kartu Ceklis Uji Hardware & Progres Mandiri (Anti-Konflik)

Folder ini dibuat supaya setiap anggota tim (bersama asisten AI masing-masing — baik **AI Web** maupun **AI CLI/IDE**) dapat mencatat dengan jujur **apakah kode yang di-push sudah dites langsung di Raspberry Pi 3B+ / alat fisik**, atau **baru aman di laptop (Draft Push)**.

## 🛡️ Aturan Wajib Anti-Konflik & Anti-Bohong
1. **Satu Divisi = Satu File:** Anggota & AI **HANYA BOLEH mengedit kartu milik divisinya sendiri** (misal Divisi 3 hanya edit `UJI_DIVISI_3_LED_WS2812B.md`). Dilarang mengedit `README.md` utama di root repo agar tidak pernah terjadi *Merge Conflict*.
2. **Standar 4 Status Resmi (`Status Push Saat Ini`):**
   - `BELUM_MULAI` : Belum ada kode atau pengujian yang dikerjakan di branch divisi ini.
   - `DRAFT_PUSH_LAPTOP` : Kode sudah di-push dan lolos uji sintaks/simulasi laptop (`--ci`), tetapi **BELUM dites di Raspberry Pi 3B+ / alat fisik**. *(Aman jika Ketua meminta "push dulu progresnya biar saya cek").*
   - `SEDANG_REVISI_HARDWARE` : Sudah diuji di Raspi atau direview Ketua, namun **masih ada masalah/bug** yang dicatat pada Bagian C untuk diperbaiki.
   - `LULUS_UJI_FISIK` : **Seluruh ceklis Tahap A dan Tahap B sudah lulus** langsung pada perangkat keras nyata.
3. **ATURAN KERAS UNTUK AI (CHATGPT / GEMINI / CLAUDE / CURSOR):**
   - **DILARANG mencentang `[x]` pada Tahap B (Uji Hardware Raspi)** atau menuliskan status `LULUS_UJI_FISIK` **sebelum anggota tim benar-benar menguji di alat fisik dan menempelkan bukti hasil tes / output terminal Raspi pada Bagian C!**
   - Jika anggota baru disuruh *"push dulu aja"* sementara masih ada error di hardware, AI wajib mengubah status ke `SEDANG_REVISI_HARDWARE` (atau `DRAFT_PUSH_LAPTOP`) dan menuliskan dengan jujur bagian mana yang masih bermasalah.

## 📂 Daftar Kartu Resmi per Divisi
| Divisi | File Kartu Eksklusif | Branch |
| :--- | :--- | :--- |
| **Divisi 1 (Ketua / Core)** | [`UJI_DIVISI_1_CORE_RASPI.md`](UJI_DIVISI_1_CORE_RASPI.md) | `main` / `core-raspi-backend` |
| **Divisi 2 (Vakum & Safety)** | [`UJI_DIVISI_2_VAKUM_SAFETY.md`](UJI_DIVISI_2_VAKUM_SAFETY.md) | `divisi-2-vacum-safety` |
| **Divisi 3 (LED WS2812B)** | [`UJI_DIVISI_3_LED_WS2812B.md`](UJI_DIVISI_3_LED_WS2812B.md) | `divisi-3-led-ws2812b` |
| **Divisi 4 (LCD ILI9341)** | [`UJI_DIVISI_4_LCD_ILI9341.md`](UJI_DIVISI_4_LCD_ILI9341.md) | `divisi-4-lcd-ili9341` |
| **Divisi 5 (Web HMI SCADA)** | [`UJI_DIVISI_5_WEB_HMI.md`](UJI_DIVISI_5_WEB_HMI.md) | `divisi-5-web-hmi` |
| **Divisi 6 (MQTT QA & Node-RED)** | [`UJI_DIVISI_6_MQTT_QA.md`](UJI_DIVISI_6_MQTT_QA.md) | `divisi-6-nodered-qa` |
