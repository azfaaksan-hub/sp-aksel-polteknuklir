# Audit data QA asli — 19 November 2026

Sumber: arsip `DECY13_Divisi6_QA.zip` yang diberikan operator. Ketiga CSV di folder `bukti/data_asli/` dipertahankan byte-per-byte, tidak disintesis ulang.

## Hasil audit terukur

| Ukuran | Nilai |
|---|---|
| Pengamatan lima menit | 300 baris |
| Status ONLINE | 300/300 |
| Rata-rata frekuensi | 4.9900 Hz |
| Frekuensi minimum | 4.9221 Hz |
| Frekuensi maksimum | 5.2666 Hz |
| Kenaikan penghitung paket | 1.503 |
| Paket invalid tercatat | 0 pada semua baris |
| Sampel dengan field wajib hilang | 0 |
| Stage QA MQTT | 8/8 PASS; Stage 0–7; 22 field |
| Stage QA HMI | 8/8 PASS; Stage 0–7; 22 field |

## SHA-256 CSV untuk pemeriksaan integritas

```text
0a37c025543b2564a1ea22327b6536f8c9ce0c60894c35b7202ab133f6b3127b  DECY13_QA_5menit.csv
ac46aa7cf494742a8a9db193239e9bfdb04b2857ccf18e62d723cce458f4ed34  DECY13_QA_Stage_0_7.csv
d9c3d1d2bb441dcb267320c8101dff745fd5813f8eb77d66981e2cb8ba976568  DECY13_QA_Stage_0_7_HMI.csv 
```

Perintah pemeriksaan di PowerShell:

```powershell
Get-FileHash .\bukti\data_asli\DECY13_QA_*.csv -Algorithm SHA256
```

**Batas:** hasil ONLINE dan statistik Hz berasal dari polling REST API selama 300 sampel, bukan pencatatan setiap paket jaringan. Stage 0–7 merupakan data simulasi sintetis. Bukti visual HMI terdapat pada screenshot, bukan merupakan pengukuran independen dari nilai CSV HMI.
