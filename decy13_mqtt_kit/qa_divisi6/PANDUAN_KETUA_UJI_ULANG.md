# Panduan Ketua Tim — Uji Ulang Divisi 6 DECY-13

**Tujuan:** memungkinkan ketua mengaudit hasil MQTT, Node-RED, dan HMI tanpa perlu mengetahui password anggota atau mengendalikan perangkat keras. Bacalah seluruh *Peringatan* sebelum menjalankan.

## Peringatan sebelum pengujian

1. **Cakupan hanya simulasi dan monitoring.** Cabut/hindari koneksi ke aktuator fisik jika melakukan uji simulator. Jangan menjalankan `04_decy13_mqtt_daemon.py`, `06_test_mqtt_healthcheck.py --auto`, `--estop`, atau mengklik tombol POWER/AUTO INIT/START BEAM/SHOOT pada broker bersama.
2. Di Node-RED, `POST /api/control` pada flow `Cyclotron Dashboard` harus **Disabled**. Tombol HMI mungkin tetap tampak; **jangan digunakan**. Dokumentasikan screenshot node sebelum uji.
3. Jangan menyalin password MQTT ke GitHub/README/CSV/screenshots. Masukkan melalui prompt terminal; jangan kirimkan ke chat.
4. Jangan menjalankan dua simulator yang memublikasikan `decy13/rpi/state` pada broker yang sama. Pertahankan **satu publisher**.
5. `127.0.0.1` pada browser berarti **komputer yang sedang digunakan**, bukan Raspberry Pi/PC kedua lain. Buka dashboard dari PC yang menjalankan Node-RED atau atur akses sesuai kebijakan jaringan.

## Prasyarat

- PC Windows: Node-RED, Mosquitto 1883 (dengan autentikasi), PowerShell 5.1, Python jika diperlukan.
- Raspberry Pi: SSH aktif, Python 3 dan virtual environment berisi `paho-mqtt`, `mosquitto_pub/sub` terpasang.
- Jalur Wi-Fi PC ↔ Pi yang sama. Pada uji 19 November: PC `10.211.191.47`, Pi `10.211.191.158`. **Periksa ulang `ipconfig` (Windows) dan `hostname -I` (Pi); IP tidak tetap.**
- File flow operasional pada branch Divisi 6: `decy13_mqtt_kit/nodered/flows_mqtt_decy13.json`. Flow QA read-only: `qa_divisi6/nodered/DECY13_Cyclotron_QA_Stage_Monitor.json`.
- CSV asli hasil pengujian di [`bukti/data_asli/`](bukti/data_asli/) dan screenshot dokumentasi di [`bukti/`](bukti/). Gunakan untuk membandingkan dengan uji ulang; jangan mengganti data lama dengan data baru.

## Uji A — Audit monitoring yang sudah berjalan (tanpa mengirim perintah)

**A1. Pada PowerShell PC kedua:**

```powershell
Get-Service mosquitto
Get-NetTCPConnection -LocalPort 1883 -State Listen -ErrorAction SilentlyContinue |
  Select-Object LocalAddress,LocalPort,State
Get-NetTCPConnection -LocalPort 1880 -State Listen -ErrorAction SilentlyContinue
```

Target: service `Running`, listener MQTT pada IP PC aktual, port 1880 untuk Node-RED. Bila `Get-NetTCPConnection` kosong, periksa service/log; jangan ubah konfigurasi tanpa izin ketua.

**A2. Periksa akses Pi dari PC:**

```powershell
$piIp = '10.211.191.158' # contoh lama, ganti IP aktual
Test-NetConnection $piIp -Port 22
ssh "sp-aksel@$piIp"
```

Nilai `$piIp` di atas hanya contoh lama; ganti sesuai `hostname -I` Raspberry Pi pada hari pengujian. Masuk SSH tidak perlu jika hanya mengaudit API yang sudah ONLINE.

**A3. Dari browser pada PC yang menjalankan Node-RED:**

- `http://127.0.0.1:1880/cyclotron` — HMI utama; `Telemetry ONLINE`, Stage 0, Mode OFF ketika simulator kondisi awal.
- `http://127.0.0.1:1880/api/status` — periksa `link.online`, `link.hz`, `link.packets`, `link.bad`, `link.missing`. Sebagian metrik adalah kumulatif Node-RED.
- Pada Node-RED, pastikan MQTT In `decy13/rpi/state` berstatus connected, dan node HTTP `POST /api/control` tetap Disabled.

**A4. QA 30 atau 300 sampel (hanya HTTP GET):**

Pada PowerShell PC, di folder repository hasil clone:

```powershell
cd .\decy13_mqtt_kit\qa_divisi6\scripts
.\qa_readonly_api.ps1 -Samples 30
.\qa_readonly_api.ps1 -Samples 300
```

Jika kebijakan PowerShell menolak skrip, buka isinya untuk inspeksi dan minta izin administrator sesuai kebijakan institusi. **Jangan menonaktifkan kebijakan keamanan secara global.** Output CSV berada pada direktori kerja. Target: semua sampel valid/ONLINE, rata-rata mendekati 5 Hz, delta `bad` 0. Skrip ini tidak mengirim MQTT atau perintah operasional.

## Uji B — Menyalakan simulator pendidikan pada lingkungan yang telah diisolasi

Bagian ini hanya diperlukan jika ketua ingin **mengulang dari awal**. Pastikan tidak ada daemon GPIO terhubung ke broker target. Sebelum menyalakan simulator, cek pada Pi:

```bash
pgrep -af 'decy13_simulator_divisi6.py|04_decy13_mqtt_daemon.py'
```

Jangan mulai instance baru jika ada proses lain atau pengguna hardware pada topik bersama. Gunakan broker staging tersendiri jika memungkinkan. Pengujian terdahulu memakai PC Windows dengan Mosquitto berautentikasi, listener TCP 1883, serta **reverse SSH tunnel** agar simulator tetap terhubung ke localhost.

Di **PowerShell PC kedua** (terminal khusus tunnel, biarkan terbuka):

```powershell
# GANTI sesuai hasil ipconfig dan hostname -I
$pcIp = '10.211.191.47'
$piIp = '10.211.191.158'
ssh -N -o ExitOnForwardFailure=yes -R "127.0.0.1:1884:${pcIp}:1883" "sp-aksel@$piIp"
```

Pada **terminal SSH Pi lain**:

```bash
python3 -c "import socket; socket.create_connection(('127.0.0.1',1884),timeout=5).close(); print('TUNNEL OK')"
cd ~/decy13-test
source .venv/bin/activate
export DECY13_MQTT_USER='decy13test'
read -r -s -p 'Password MQTT: ' DECY13_MQTT_PASSWORD; echo
export DECY13_MQTT_PASSWORD
python decy13_simulator_divisi6.py --host 127.0.0.1 --port 1884
```

**PENTING — perbedaan versi skrip:** pada saat dokumentasi ditulis, `raspi_cli/tests/decy13_simulator_divisi6.py` di branch GitHub Divisi 6 **belum menerapkan username/password dari environment**. Versi kerja di Pi operator sudah ditambahkan konfigurasi autentikasi lokal. Untuk menyamakan versi repo, gunakan patch kecil berikut di simulator setelah `import argparse`:

```python
import os
```

Dan tepat **sebelum** `client.connect(args.host, args.port, 30)`:

```python
mqtt_user = os.environ.get('DECY13_MQTT_USER')
mqtt_password = os.environ.get('DECY13_MQTT_PASSWORD')
if mqtt_user and mqtt_password:
    client.username_pw_set(mqtt_user, mqtt_password)
```

Pertahankan validasi `localhost` pada simulator dan periksa `python -m py_compile` terlebih dahulu. Jaga password tetap rahasia. Patch ini untuk reproduksi; **jangan jalankan otomatis pada hardware yang terhubung**.

## Uji C — Stage 0–7 terisolasi, tanpa daemon atau perintah kontrol

**C1. Di Raspberry Pi**, siapkan listener hanya loopback pada port 1885 (jangan membuka port ini ke LAN):

```bash
cat > ~/decy13-test/mosquitto_qa.conf <<'EOF'
listener 1885 127.0.0.1
allow_anonymous true
persistence false
log_dest stdout
EOF
mosquitto -c ~/decy13-test/mosquitto_qa.conf -v
```

Biarkan terminal aktif. `allow_anonymous true` hanya ditoleransi karena listener dibatasi `127.0.0.1`; jangan gunakan untuk broker operasional.

**C2. Di PC kedua**, buka terminal tunnel tambahan:

```powershell
$piIp = '10.211.191.158' # ganti bila IP berubah
ssh -N -o ExitOnForwardFailure=yes -L '127.0.0.1:1886:127.0.0.1:1885' "sp-aksel@$piIp"
```

Di terminal PowerShell lain periksa:

```powershell
Test-NetConnection 127.0.0.1 -Port 1886
```

Target: `TcpTestSucceeded : True`.

**C3. Di Node-RED PC kedua:** import `DECY13_Cyclotron_QA_Stage_Monitor.json` sebagai **new flow**. Periksa agar `MQTT In` menggunakan `127.0.0.1:1886` dan `decy13/qa/state`; tidak ada MQTT Out atau HTTP POST. Deploy. Buka `http://127.0.0.1:1880/cyclotron-qa`. Jangan mengganti broker utama.

**C4. Transfer generator dan jalankan.** Pada **PowerShell PC** dalam root checkout GitHub, kirim kode ke Pi:

```powershell
$piIp = '10.211.191.158' # ganti IP aktual
scp '.\decy13_mqtt_kit\qa_divisi6\scripts\qa_stage_0_7.py' "sp-aksel@${piIp}:/home/sp-aksel/decy13-test/qa_stage_0_7.py"
```

Pada **Raspberry Pi**, dari folder `~/decy13-test`, jalankan:

```bash
cd ~/decy13-test
source .venv/bin/activate
python qa_stage_0_7.py --hold 4 --output DECY13_QA_Stage_0_7_HMI.csv
```

Generator hanya mengirim `decy13/qa/state` ke `127.0.0.1:1885`, tanpa GPIO dan tanpa `/hmi/cmd`.

Target: Stage 0 → 7 terlihat dalam riwayat HMI, Python `8/8 PASS`, CSV berhasil dibuat. **Label HMI QA akan OFFLINE setelah generator selesai**; ini bukan kegagalan karena tidak ada data baru. Jangan menyamakan pengujian stage sintetis dengan transisi FSM fisika simulator.

**C5. Pulihkan dan verifikasi monitoring utama:** buka `http://127.0.0.1:1880/cyclotron` dan GET `/api/status`; pastikan `link.online=true`, paket naik dan Stage 0/OFF jika simulator utama tetap dalam kondisi awal. Tidak perlu mengirim perintah kontrol.

## Uji D — Disconnect dan recovery (opsional, hanya pada simulator pendidikan)

Hentikan **hanya** proses simulator Pi dengan `Ctrl+C`; jangan hentikan Node-RED atau Mosquitto. Setelah lebih dari 2 detik, refresh GET `/api/status`: target `link.online=false`. Jalankan kembali simulator di terminal yang sama (variabel lingkungan masih ada), lalu refresh: target `link.online=true` dan frekuensi mendekati 5 Hz. Ini menguji timeout monitoring, **bukan E-Stop fisik**.

## Bagaimana mengevaluasi hasil

| Pemeriksaan | Kriteria keberhasilan |
|---|---|
| GET monitoring utama | Status ONLINE, paket bertambah, Hz sekitar 5 |
| JSON | 22 field; validator Node-RED PASS |
| QA sampling 30/300 | Seluruh sampel valid dan ONLINE; delta invalid 0; Hz mendekati 5 |
| Stage QA | 8/8 PASS pada topik khusus QA; riwayat browser lengkap |
| Isolasi | HMI utama tetap ONLINE, Stage 0/OFF ketika QA selesai |
| Keselamatan | Tidak ada perintah operasional otomatis; `POST /api/control` Disabled |

Bandingkan dengan hasil acuan dalam laporan. Catat tanggal pengujian ulang, identitas perangkat, IP aktual, konfigurasi Node-RED, hasil PASS/FAIL, dan alasan setiap pengecualian.

## Penutupan

- Export *All Flows* Node-RED dan simpan di lokasi internal; **audit konfigurasi agar tidak berisi kredensial**.
- Simpan tiga CSV asli, screenshot, dan log terminal sebagai bukti pengujian.
- Hentikan publisher QA (berakhir otomatis), broker QA `1885` dengan `Ctrl+C`, tunnel QA `1886`, lalu simulator dan reverse tunnel `1884` bila pengujian selesai. Node-RED dapat dihentikan setelah backup; Mosquitto Windows Service tidak perlu dihapus.
- Jangan merge ke `main` sampai ketua memeriksa laporan, panduan, dan aturan integrasi lintas divisi.


## Audit CSV asli bagi ketua (tanpa menjalankan alat)

Pada PowerShell di root repository setelah PR di-checkout:

```powershell
$folder = ".\decy13_mqtt_kit\qa_divisi6\bukti\data_asli"
$stable = @(Import-Csv "$folder\DECY13_QA_5menit.csv")
$stage = @(Import-Csv "$folder\DECY13_QA_Stage_0_7.csv")
$hmi = @(Import-Csv "$folder\DECY13_QA_Stage_0_7_HMI.csv")
[PSCustomObject]@{ Sampel5Menit=$stable.Count; Online=@($stable | Where-Object Online -eq "True").Count; StagePASS=@($stage | Where-Object status -eq "PASS").Count; HMIPASS=@($hmi | Where-Object status -eq "PASS").Count }
```

Target bukti **arsip pengujian tanggal 19 November 2026**: `300`, `300`, `8`, `8`. Ini hanya audit file hasil terdahulu, bukan uji ulang sistem langsung. Untuk pengujian langsung gunakan perintah QA di bagian Uji A dan C serta simpan log baru bertanggal berbeda.

**Catatan backup:** file `DECY13_Divisi6_Final_Flows_20261119.json` tersedia di folder `ARSIP_LOKAL_JANGAN_UPLOAD` pada paket distribusi, bukan pada folder yang dikirim ke repository publik. Ekspor Node-RED mungkin tidak mencakup password broker karena penyimpanan kredensial dilakukan terpisah; konfigurasi MQTT harus disesuaikan secara lokal.
