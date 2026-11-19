# LAPORAN QUALITY ASSURANCE (QA) DAN COMMISSIONING DECY-13

**Subdivisi:** Implementasi Jaringan MQTT, Node-RED, dan QA Testing  
**Proyek:** Pengembangan dan Integrasi Sistem Kontrol, Instrumentasi, serta Visualisasi pada Alat Peraga Akselerator Siklotron Skala Edukatif  
**Institusi:** Politeknik Teknologi Nuklir Indonesia  
**Tanggal pengujian akhir:** 19 November 2026

> **Ruang lingkup:** semua pengukuran yang disajikan berasal dari sistem komunikasi, data telemetri **simulasi**, dan observasi Node-RED/REST API. Tidak ada verifikasi sensor atau aktuator siklotron fisik.

## 1. Tujuan

Memverifikasi konektivitas jaringan, pertukaran MQTT dua arah, autentikasi, validasi 22 field JSON, frekuensi telemetri target 5 Hz, ketahanan selama sampling, deteksi timeout dan pemulihan, serta penerimaan dan visualisasi data Stage 0–7 secara aman. Hasil menjadi dasar serah terima subsistem komunikasi dan monitoring Divisi 6 kepada ketua tim.

## 2. Konfigurasi dan arsitektur uji

| Komponen | Konfigurasi yang dipakai saat uji |
|---|---|
| Raspberry Pi | Raspberry Pi 3, Debian GNU/Linux 13 (trixie), Python 3.13.5 |
| MQTT client | Paho MQTT 2.2.0 |
| PC pengendali | Windows 10 Pro, Node-RED 5.0.10 |
| Mosquitto PC | Windows Service, Mosquitto 2.1.2, TCP 1883, autentikasi |
| Mosquitto QA Pi | Mosquitto 2.0.21, `127.0.0.1:1885` |
| Jaringan saat uji | PC `10.211.191.47`, Pi `10.211.191.158`, jaringan Wi-Fi yang sama |
| Telemetri utama | `decy13/rpi/state`; simulator Pi → reverse SSH `127.0.0.1:1884` → broker PC:1883 |
| Dashboard utama | Node-RED `/cyclotron`, REST API `/api/status` |
| QA terisolasi | Generator JSON → Mosquitto Pi:1885 → SSH tunnel PC:1886 → Node-RED `/cyclotron-qa` |
| QA topic | `decy13/qa/state` (bukan topik perintah perangkat keras) |

IP merupakan nilai yang diamati pada tanggal pengujian; pada instalasi baru harus diperiksa kembali. MQTT V3.1.1 digunakan pada flow utama. Autentikasi broker PC telah dikonfigurasi. Password tidak dimasukkan ke laporan/repository.

## 3. Hasil pengujian

### 3.1 Konektivitas, autentikasi, dan komunikasi dua arah

| No. | Uji | Bukti | Status |
|---:|---|---|---|
| 1 | IP PC/Pi pada jaringan yang sama | Akses SSH; IP tercatat | PASS |
| 2 | SSH Raspberry Pi | TCP 22 terbuka; login berhasil | PASS |
| 3 | Windows Service Mosquitto | `Running`; listener `10.211.191.47:1883` | PASS |
| 4 | Autentikasi MQTT | `CONNACK (0)` diterima dengan kredensial pengujian | PASS |
| 5 | Publish Pi → Node-RED | Pesan uji Pi terlihat pada Debug | PASS |
| 6 | Publish Node-RED → Pi | `PING_FROM_NODE_RED` diterima subscriber Pi | PASS |
| 7 | Reverse SSH tunnel | Pi `127.0.0.1:1884` terhubung ke broker PC | PASS |
| 8 | Node-RED subscribe state | `decy13/rpi/state` terhubung; payload JSON tampil | PASS |

Masalah awal yang telah diperbaiki meliputi listener broker PC yang hanya tersedia pada loopback dan izin baca akun Windows Service ke berkas password. Selama pengujian tidak digunakan broker anonim terbuka pada jaringan operasional.

### 3.2 Kontrak telemetri 22 field

Pemeriksaan melalui Function Node-RED menunjukkan format payload objek JSON, **22 field wajib tersedia**, kesesuaian tipe data dan beberapa pemeriksaan rentang dasar: **PASS**. Kelompok field terdiri dari status sistem, `stage`, `mode`, empat baris LCD, tekanan, energi/arus berkas, indeks LED simulasi, buzzer, dan logs. Hasil pada sampel tidak menunjukkan `missing`, `wrongType`, atau `invalidRange`. Pemeriksaan ini **bukan validasi semua kondisi operasi/batas fisik**.

### 3.3 Stabilitas 30 sampel

| Parameter | Hasil |
|---|---:|
| Sampel valid | 30/30 |
| ONLINE / OFFLINE | 30 / 0 |
| Rata-rata / minimum / maksimum | 4,99 / 4,93 / 5,07 Hz |
| Pertambahan paket | 146 |
| Delta paket invalid | 0 |
| Usia telemetri maksimum | 236 ms |
| Sampel dengan field hilang | 0 |
| Stage akhir / mode | 0 / OFF |
| Penilaian dalam cakupan sampling | **PASS** |

### 3.4 Stabilitas 300 sampel (sekitar 5 menit)

| Parameter | Hasil |
|---|---:|
| Sampel valid | **300/300** |
| Sampel ONLINE | **300** |
| OFFLINE/API error | **0** |
| Frekuensi rata-rata | **4,99 Hz** |
| Frekuensi minimum / maksimum | 4,92 / 5,27 Hz |
| Pertambahan paket | **1.503** |
| Delta paket invalid | **0** |
| Penilaian dalam cakupan sampling | **PASS** |

Frekuensi rata-rata meleset sekitar 0,01 Hz atau **0,2%** dari target 5 Hz. Selisih 1.503 paket selama jendela pengamatan sesuai orde publikasi lima kali per detik. **Catatan metodologi:** skrip membaca respons REST API setiap sekitar satu detik, bukan menghitung kehilangan setiap paket MQTT; karenanya tidak dapat disimpulkan *packet loss* jaringan secara mutlak 0%.

### 3.5 Timeout dan recovery

| Fase | Observasi | Status |
|---|---|---|
| Awal | `link.online=true`, frekuensi sekitar 5 Hz | PASS |
| Simulator dihentikan | Pengiriman telemetri berhenti | PASS |
| Timeout | `link.online=false`, `ageMs` meningkat (sekitar 22,2 detik pada tangkapan layar) | PASS |
| Simulator dijalankan kembali | `MQTT terhubung: Success` | PASS |
| Recovery | API kembali `link.online=true`, HMI utama ONLINE | PASS |

Fungsi ini hanya menandai *kehilangan pembaruan telemetri*. Pengujian fail-safe relay, E-Stop, atau aktuator tidak dilakukan.

### 3.6 QA Stage 0–7 dan HMI terisolasi

Pengujian menggunakan Python generator payload JSON **sintetis** pada broker Pi loopback:1885 dan topik `decy13/qa/state`, bukan perintah kontrol operasional. Payload mengandung 22 field, mode `OFF` pada Stage 0 dan `QA_STAGE_N` untuk Stage 1–7. Semua delapan pesan diterima kembali dan lolos pemeriksaan struktur.

| Stage | Field | Hasil publish–subscribe | Hasil validasi |
|---:|---:|---|---|
| 0 | 22 | Diterima | PASS |
| 1 | 22 | Diterima | PASS |
| 2 | 22 | Diterima | PASS |
| 3 | 22 | Diterima | PASS |
| 4 | 22 | Diterima | PASS |
| 5 | 22 | Diterima | PASS |
| 6 | 22 | Diterima | PASS |
| 7 | 22 | Diterima | PASS |

**Total: 8 PASS, 0 FAIL.** Uji HMI dilakukan dengan jeda sekitar empat detik per stage. Browser `/cyclotron-qa` merekam urutan Stage 0 → 7 dan menampilkan Stage 7 sebagai keadaan terakhir. Ketika publisher berhenti, label QA menjadi **OFFLINE** sebagaimana mestinya. Hasil ini **tidak memvalidasi transisi otomatis logika simulator Raspberry Pi atau keluaran fisik siklotron**.

### 3.7 Integrasi monitoring utama pasca-QA

| Waktu | `online` | Frekuensi | Paket kumulatif | Stage / Mode |
|---|---|---:|---:|---|
| 15:36:10 | True | 4,98 Hz | 26.220 | 0 / OFF |
| 15:36:12 | True | 4,98 Hz | 26.230 | 0 / OFF |
| 15:36:14 | True | 4,98 Hz | 26.240 | 0 / OFF |

Pertambahan **20 paket dalam empat detik** konsisten dengan telemetri sekitar 5 Hz. Monitoring utama tetap ONLINE setelah QA terisolasi.

## 4. Pembahasan

Arsitektur publish–subscribe MQTT memisahkan sumber data Raspberry Pi dan pemantauan PC. Node-RED mengolah telemetri menjadi indikator HMI dan status REST API. Penggunaan reverse SSH tunnel mempertahankan pembatasan localhost pada simulator pengujian; broker terpisah untuk QA mengurangi risiko tercampurnya pesan pengujian dengan topik kontrol utama. Pemeriksaan 30 dan 300 sampel menunjukkan frekuensi dan status link yang konsisten dalam rentang pengamatan. Pengujian timeout/reconnect membuktikan pembaruan status komunikasi dapat terdeteksi. Perlu pengujian tambahan untuk jitter/latensi rinci, kehilangan paket per-pesan, serta fungsi keselamatan pada perangkat keras.

## 5. Kesimpulan dan keputusan QA

Subsistem **komunikasi MQTT, Node-RED, REST API, dan HMI DECY-13 dinyatakan PASS untuk cakupan uji simulasi yang tercatat pada 19 November 2026**. Keputusan ini tidak mencakup operasi siklotron sebenarnya, verifikasi GPIO/sensor/relay/LED fisik, interlock fisik, ataupun E-Stop perangkat keras. Integrasi perangkat keras memerlukan protokol commissioning tersendiri dan otorisasi tim.

## 6. Data mentah dan lampiran

- `DECY13_QA_5menit.csv` — 300 baris sampling API; tersimpan pada PC kedua operator.
- `DECY13_QA_Stage_0_7.csv` — hasil validasi Python 8 stage; tersimpan pada PC kedua operator.
- `DECY13_QA_Stage_0_7_HMI.csv` — hasil QA visualisasi 8 stage; tersimpan pada PC kedua operator.
- Backup *All Flows* Node-RED dari komputer yang diuji: berkas internal, audit kredensial sebelum dibagikan.
- Screenshot pada folder [`bukti/`](bukti/).
- Dokumen Word bergambar tersedia sebagai [`Laporan_QA_Commissioning_DECY13_Divisi6.docx`](Laporan_QA_Commissioning_DECY13_Divisi6.docx).

**Provenans:** angka-angka di laporan ini disalin dari output terminal PowerShell, Python, Node-RED, dan screenshot yang diperlihatkan operator. Berkas CSV mentah belum disertakan dalam paket GitHub ini karena salinan PC kedua tidak diberikan sebagai file dalam percakapan; jangan mengganti bukti mentah dengan data rekaan.


## 6. Audit data mentah asli (lampiran 19 November 2026)

Tiga file CSV asli hasil commissioning diperoleh langsung dari arsip operator dan disimpan **tanpa perubahan isi** di `bukti/data_asli/`. Pemeriksaan ulang berikut berasal dari CSV tersebut, bukan angka contoh:

| Bukti mentah | Baris data | Temuan audit |
|---|---:|---|
| `DECY13_QA_5menit.csv` | 300 | Semua `Online=True`, `Bad=0`, `Missing=0`; rata-rata Hz 4,9900; min 4,9221; max 5,2666; delta paket 1.503 |
| `DECY13_QA_Stage_0_7.csv` | 8 | Stage 0–7 lengkap dan urut, semua PASS, `field_count=22`, `received=True` |
| `DECY13_QA_Stage_0_7_HMI.csv` | 8 | Stage 0–7 lengkap dan urut, semua PASS, `field_count=22`, `received=True` |

**Keterbatasan:** CSV HMI mencatat penerimaan MQTT dan validasi payload oleh skrip. Bukti bahwa browser memperlihatkan urutan stage berasal dari screenshot, bukan diukur independen oleh file CSV. CSV stabilitas merekam polling REST API, bukan seluruh paket MQTT individu. Audit ini tidak memperluas klaim hingga perangkat keras nyata.
