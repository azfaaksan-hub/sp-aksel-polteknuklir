# Dokumentasi screenshot QA

Folder ini berisi tangkapan layar pengujian yang sudah ditinjau; bagian bilah browser dipotong agar tab pribadi tidak ikut dipublikasikan dalam pengujian Divisi 6. File screenshot merupakan **bukti visual terbatas**, bukan sumber tunggal angka statistik; untuk angka 300 sampel dan stage gunakan CSV asli dari PC operator.

| Berkas | Keterangan |
|---|---|
| `01_validasi_json_nodered.jpeg` | Flow Node-RED dengan validator jumlah field dan tipe |
| `02_cyclotron_main_online.jpeg` | HMI utama menerima telemetri pada Stage 0 / OFF |
| `03_api_offline_timeout.jpeg` | `/api/status` menunjukkan `link.online=false` |
| `04_qa_stage_hmi_8pass.jpeg` | HMI QA dan terminal Stage 0–7 PASS |
| `05_hmi_main_setelah_qa.jpeg` | HMI utama tetap ONLINE setelah QA terisolasi |

Alamat IP, username mesin, dan timestamp pada gambar adalah rekaman pengujian lokal, bukan konfigurasi yang harus dipakai ketua.
