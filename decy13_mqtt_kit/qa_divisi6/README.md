# DECY-13 — Divisi 6: MQTT, Node-RED, QA & Commissioning

**Lingkup:** komunikasi/monitoring berbasis **simulasi**, bukan commissioning perangkat keras siklotron.  
**Pengujian terakhir:** 19 November 2026.  
**Kondisi:** pengujian yang tercantum pada laporan **PASS untuk cakupan simulasi**; review ketua dan serah terima tetap diperlukan.

## Untuk ketua tim: mulai dari sini

1. Baca [PANDUAN_KETUA_UJI_ULANG.md](PANDUAN_KETUA_UJI_ULANG.md). Mulai dari **Uji A — baca monitoring tanpa mengirim perintah**.
2. Baca [LAPORAN_QA_COMMISSIONING_2026-11-19.md](LAPORAN_QA_COMMISSIONING_2026-11-19.md) untuk angka pengujian dan batasannya.
3. Laporan Word bergambar: [Laporan_QA_Commissioning_DECY13_Divisi6.docx](Laporan_QA_Commissioning_DECY13_Divisi6.docx).
4. Jalankan [scripts/qa_readonly_api.ps1](scripts/qa_readonly_api.ps1) pada **PC yang menjalankan Node-RED** untuk uji 30 atau 300 sampel.
5. Untuk memeriksa Stage 0–7 **tanpa operasi perangkat keras**, gunakan [scripts/qa_stage_0_7.py](scripts/qa_stage_0_7.py) pada broker loopback terisolasi dan flow [nodered/DECY13_Cyclotron_QA_Stage_Monitor.json](nodered/DECY13_Cyclotron_QA_Stage_Monitor.json).
6. Gunakan [CHECKLIST_SERAH_TERIMA.md](CHECKLIST_SERAH_TERIMA.md) untuk persetujuan akhir.

## Ringkasan hasil yang telah diamati

| Aspek | Hasil |
|---|---|
| Koneksi MQTT Raspberry Pi ↔ PC kedua | PASS dua arah; broker berautentikasi |
| JSON state | 22 field wajib, validasi Node-RED PASS pada sampel |
| Telemetri 30 sampel | 30/30 ONLINE; rata-rata 4,99 Hz; invalid tambahan 0 |
| Telemetri 300 sampel | 300/300 ONLINE; 4,99 Hz; tambahan 1.503 paket; invalid tambahan 0 |
| Loss-of-telemetry / recovery | `link.online: false` saat simulator berhenti; `true` setelah reconnect |
| MQTT QA Stage 0–7 | 8 PASS / 0 FAIL, 22 field, nilai stage sintetis |
| Visualisasi QA | Stage 0–7 terekam berurutan pada `/cyclotron-qa` |
| Monitoring utama pasca-QA | ONLINE 4,98 Hz, paket 26.220 → 26.240 dalam 4 detik |

## Pembatasan, keamanan, dan bukti

- **DILARANG menggunakan `--auto` dan `--estop` pada broker yang juga digunakan daemon perangkat keras.**
- Endpoint `POST /api/control` pada flow monitoring utama dibiarkan **Disabled** untuk pengujian baca saja. Tombol tampak pada HMI **bukan izin untuk menekannya**.
- Broker QA terpisah hanya di `127.0.0.1:1885` pada Pi; tunnel akses dari PC `127.0.0.1:1886`.
- Paket QA Divisi 6 ini tidak menyimpan kredensial MQTT. Gunakan environment variable, terminal prompt, dan penyimpanan kredensial sesuai kebijakan tim.
- **Tidak mengklaim:** pengujian GPIO, relay, LED fisik, sensor nyata, E-Stop perangkat keras, keselamatan akselerator, atau packet-loss per pesan MQTT.
- **Tiga CSV mentah asli** hasil uji kini disertakan tanpa modifikasi di folder [`bukti/data_asli/`](bukti/data_asli/): [`DECY13_QA_5menit.csv`](bukti/data_asli/DECY13_QA_5menit.csv), [`DECY13_QA_Stage_0_7.csv`](bukti/data_asli/DECY13_QA_Stage_0_7.csv), [`DECY13_QA_Stage_0_7_HMI.csv`](bukti/data_asli/DECY13_QA_Stage_0_7_HMI.csv). Baca [`AUDIT_DATA_ASLI.md`](AUDIT_DATA_ASLI.md) untuk rekonsiliasi dan SHA-256. Data mentah tidak dibuat ulang.
- Dokumentasi screenshot pilihan ada pada folder [`bukti/`](bukti/). Waktu/IP pada gambar adalah rekaman pengujian, bukan alamat yang dijamin tetap.

Folder ini menambahkan dokumentasi Divisi 6 tanpa mengubah modul divisi lain. Review perubahan sebelum merge ke `main`.

## Ekspor flow Node-RED asli

Ekspor penuh Node-RED hasil PC operator disimpan dalam folder **`ARSIP_LOKAL_JANGAN_UPLOAD` di luar path repository**. File tersebut merupakan cadangan lokal, bukan berkas yang otomatis aman untuk repo publik. Ketua dapat mengimpor `nodered/DECY13_Cyclotron_QA_Stage_Monitor.json` untuk pengujian QA dan flow utama dari `../nodered/flows_mqtt_decy13.json`; isi kredensial MQTT secara lokal.
