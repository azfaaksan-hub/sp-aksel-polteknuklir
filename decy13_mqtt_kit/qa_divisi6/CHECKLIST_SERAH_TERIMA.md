# Checklist review dan serah terima — Divisi 6 DECY-13

Gunakan sebagai lembar verifikasi ketua setelah melakukan uji ulang. Isi nama, tanggal, PASS/FAIL, dan catatan pemeriksaan.

| Item pemeriksaan | Hasil acuan 19-11-2026 | Uji ulang ketua | Catatan |
|---|---|---|---|
| Jaringan PC–Pi dan SSH | PASS | ☐ | |
| Mosquitto TCP 1883 + autentikasi | PASS | ☐ | |
| MQTT dua arah pada topik uji | PASS | ☐ | |
| 22 field JSON | PASS | ☐ | |
| Node-RED `/api/status` | ONLINE ±5 Hz | ☐ | |
| QA 30 sampel | 30/30, rata-rata 4,99 Hz | ☐ | |
| QA 300 sampel | 300/300, rata-rata 4,99 Hz | ☐ | |
| Deteksi OFFLINE | PASS | ☐ | |
| Recovery ONLINE | PASS | ☐ | |
| Stage 0–7 sintetis | 8/8 PASS | ☐ | |
| `/cyclotron-qa` menampilkan 0–7 | PASS | ☐ | |
| HMI utama tidak terganggu | 4,98 Hz, paket terus naik | ☐ | |
| Node `POST /api/control` Disabled | Sudah dicek | ☐ | |
| Backup Node-RED tersimpan aman | Perlu dicek | ☐ | |
| 3 CSV mentah asli tersedia | Disertakan di `bukti/data_asli/` | ☐ | |
| Laporan Word dan Markdown | Tersedia | ☐ | |

**Batas keputusan:** commissioning komunikasi dan monitoring **berbasis simulasi**. Tidak mencakup uji perangkat keras siklotron. Review keselamatan perangkat keras memerlukan checklist tersendiri.

**Pemeriksa:** ____________________  **Tanggal:** ____________________  **Keputusan:** LULUS / PERLU PERBAIKAN
