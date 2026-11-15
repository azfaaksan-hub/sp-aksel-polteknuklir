# ⚛️ Proyek Alat Peraga Siklotron DECY-13 (13 MeV H⁻)

**Politeknik Teknologi Nuklir Indonesia (BRIN) — Arsitektur Kolaborasi 6 Divisi (Multi-AI & GitHub)**

Selamat datang di repositori proyek **DECY-13**. Proyek ini menggunakan sistem **MQTT State-Driven** dengan **Raspberry Pi 3 Model B+** sebagai otak perangkat keras (*Core Backend*) dan **Mini PC** sebagai layar kendali *Web HMI*.

---

## 🚀 WAJIB BACA PERTAMA KALI (Untuk Anggota Tim Baru / Awam GitHub)

Sebelum menyentuh kode atau menjalankan AI, **buka 3 file panduan ini secara berurutan** di laptopmu:

1. **📄 Ringkasan Awal:** Buka file [`BACA_INI_DULU.txt`](BACA_INI_DULU.txt)
2. **🐙 Panduan GitHub Pemula & Ambil Prompt AI Divisimu (PENTING!):**
   Buka file [`instruksi untuk projek sp/PANDUAN_GITHUB_DAN_TIM_AI.html`](instruksi%20untuk%20projek%20sp/PANDUAN_GITHUB_DAN_TIM_AI.html) dengan **Google Chrome / Microsoft Edge** (di GitHub web file HTML tampil berupa kode, jadi **download/clone dulu ke laptopmu** lalu klik kanan → *Open with Chrome*).
3. **⚡ Panduan Cara Kerja & Wiring Alat:**
   Buka file [`instruksi untuk projek sp/PANDUAN_VISUAL.html`](instruksi%20untuk%20projek%20sp/PANDUAN_VISUAL.html) dengan **Google Chrome / Microsoft Edge**.

> 🛡️ **ATURAN WAJIB KOLABORASI MANDIRI:**
> 1. AI milikmu (ChatGPT / Claude / Cursor / Gemini) **HANYA** membantu menulis isi file milik divisimu.
> 2. **DILARANG** menyuruh AI menjalankan `git commit` atau `git push` secara otomatis — **setiap anggota wajib melakukan `branch`, `pull`, `commit`, dan `push` sendiri** agar paham alur GitHub.
> 3. **DILARANG** mengedit file milik divisi lain agar tidak bentrok (*Merge Conflict*).

---

## 📢 Papan Pengumuman & Update Terbaru (`main`)

| Info | Keterangan |
| :--- | :--- |
| **Versi / Status `main`** | **`v1.1` — Fondasi Modular 6 Divisi + Sistem Audit & Announcer Aktif** |
| **Pengumuman Ketua** | Fondasi kode modular (`raspi_cli/modules/`), satpam otomatis GitHub (*Read-Only CI*), dan Papan Rapor 6 Divisi sudah aktif. Silakan cek tabel status & prompt konteks terbaru divisimu di bawah sebelum lanjut ngoding. |
| **Cara Tarik Update Terbaru** | **GitHub Desktop:** Pastikan di branch divisimu → klik *Fetch origin* → menu *Branch* → *Update from main*.<br>**Terminal:** `git fetch origin` lalu `git merge origin/main` |

---

## 📊 Tabel Rapor & Status Integrasi 6 Divisi

Setiap anggota yang melakukan `git push` akan diperiksa oleh **Satpam Otomatis (GitHub Actions)** (tanda ✅/❌) dan direview oleh Ketua sebelum di-*merge* ke `main`.

| Divisi | Penanggung Jawab | Branch Wajib | File Eksklusif (Boleh Diedit) | Status Audit Saat Ini |
| :--- | :--- | :--- | :--- | :--- |
| **Divisi 1 (Ketua)** | `azfaaksan-hub` | `main` | `04_decy13_mqtt_daemon.py`, `05_laptop_dryrun_simulator.py`, `config_hardware.json`, `modules/base_module.py`, `tools/*` | ✅ **Core Aktif** |
| **Divisi 2** | `dzakimumtazi` | `divisi-2-vacum-safety` | `decy13_mqtt_kit/raspi_cli/modules/mod_vacuum_safety.py`<br>`decy13_mqtt_kit/raspi_cli/01_test_relay_buzzer.py` | ✅ **Lulus Audit & Siap Merge** *(Initial relay OFF, cleanup aman, menu tes E-Stop oke)* |
| **Divisi 3** | `blufiaa` | `divisi-3-led-ws2812b` *(saat ini masih di `pacarjeno`)* | `decy13_mqtt_kit/raspi_cli/modules/mod_led_ws2812b.py`<br>`decy13_mqtt_kit/raspi_cli/03_test_led_pixel_finder.py` | ⚠️ **Perlu Revisi Sebelum Merge** *(Lihat tabel kesalahan & prompt perbaikan khusus Divisi 3 di bawah)* |
| **Divisi 4** | *(Anggota 4)* | `divisi-4-lcd-ili9341` | `decy13_mqtt_kit/raspi_cli/modules/mod_lcd_ili9341.py`<br>`decy13_mqtt_kit/raspi_cli/02_test_lcd_ili9341.py` | ⏳ **Menunggu Push Pertama** |
| **Divisi 5** | *(Anggota 5)* | `divisi-5-web-hmi` | `decy13_mqtt_kit/web_hmi/index.html` | ⏳ **Menunggu Push Pertama** |
| **Divisi 6** | *(Anggota 6)* | `divisi-6-nodered-qa` | `decy13_mqtt_kit/raspi_cli/06_test_mqtt_healthcheck.py`, `nodered/flows_mqtt_decy13.json`, `instruksi untuk projek sp/CHECKLIST_COMMISSIONING.txt` | ⏳ **Menunggu Push Pertama** |

---

## ⚠️ Tabel Kesalahan Khusus (Bagian yang Perlu Diperbaiki Saat Ini)

*(Bagian ini hanya menampilkan divisi yang kodenya belum cocok dengan sistem utama agar langsung jelas apa yang harus diperbaiki.)*

### 🔧 Audit Divisi 3 (Branch Saat Ini: `pacarjeno` → Seharusnya `divisi-3-led-ws2812b`)

| No | Bagian yang Salah | Masalah Teknis yang Ditemukan | Perbaikan yang Harus Dilakukan |
| :---: | :--- | :--- | :--- |
| **1** | **Titik Cabang & Nama Branch** | Branch `pacarjeno` dibuat dari `initial commit` lama (`b043fe0`) via web upload sebelum arsitektur modular `main` ada. | Buat branch baru **`divisi-3-led-ws2812b`** dari **`main` terbaru** (`git pull origin main` dulu), jangan upload lewat web ke folder terpisah. |
| **2** | **Lokasi File & `__pycache__`** | File ditaruh di folder baru `divisi3_led/` dan ikut meng-upload file biner `__pycache__/*.pyc`. Core Daemon tidak membaca folder tersebut. | Wajib edit file resmi `decy13_mqtt_kit/raspi_cli/modules/mod_led_ws2812b.py` dan `03_test_led_pixel_finder.py`. Jangan upload `.pyc`! |
| **3** | **Konflik Hardware SPI0 & Board** | Memakai `Pi5NeoStrip` (`pi5neo` di `/dev/spidev0.0` SPI0 untuk Raspberry Pi 5). Padahal instrumen memakai **Raspberry Pi 3B+ GPIO 18 (`rpi_ws281x`)**, dan **SPI0 dipakai LCD ILI9341 (Divisi 4)**. | Gunakan driver `rpi_ws281x` pada `GPIO 18` dengan `try/except ImportError` fallback `MemoryStrip` untuk pengujian di laptop Windows. |
| **4** | **Hardcode 200 LED & Stage Beda** | Mengunci `LED_COUNT = 200` dan definisi `stage` sendiri, bukan membaca `config_hardware.json` (`total_leds: 64`, `0–47` spiral, `48–63` shoot). | Baca jumlah LED, indeks spiral, `rf_gap_indices`, dan indeks shoot secara dinamis dari `self.cfg["led_mapping"]` (`config_hardware.json`). |
| **5** | **Kontrak Class Tidak Cocok** | Membuat class `CyclotronLED` terpisah, bukan `LedStripModule(HardwareModule)`. | Bungkus logika animasi komet (`_comet`) ke dalam class `LedStripModule(HardwareModule)` (`setup()`, `update(state, dt, now)`, `cleanup()`) & wajib update `state["activeLedIdx"]` + `state["shootLedIdx"]` untuk Web HMI! |
| **✨** | **Nilai Plus (Pertahankan!)** | Algoritma ekor komet (`_comet`) dan simulator visual GUI (`tkinter`) di laptop sudah bagus. | Pertahankan logika efek komet + boleh menyertakan simulator visual di `03_test_led_pixel_finder.py` atau mode preview selama membaca `config_hardware.json`. |

---

## 🤖 Prompt Konteks Terbaru per Divisi (Siap Copy-Paste untuk Chat AI Baru!)

Gunakan prompt di bawah ini **setiap kali kamu membuka chat AI baru** (atau setelah Ketua mengumumkan update `main` di WhatsApp) agar AI kamu tidak kehilangan konteks proyek!

<details>
<summary><b>🌀 DIVISI 2 — Prompt Lanjutan Konteks Terbaru (Klik untuk buka & salin)</b></summary>

```text
[KONTEKS TERBARU PROYEK SIKLOTRON DECY-13 — UPDATE v1.1]
Saya adalah Anggota Divisi 2 (Sistem Vakum, Buzzer & Safety E-Stop) pada repo `sp-aksel-polteknuklir`.
Status kode saya di branch `divisi-2-vacum-safety` sudah LULUS AUDIT awal (initial pin relay OFF, cleanup aman menjaga relay tetap OFF, dan menu [4] Tes E-Stop di `01_test_relay_buzzer.py`).

[BATAS KERJA & ATURAN GIT MANDIRI]
- Branch aktif saya: `divisi-2-vacum-safety` (sudah tersinkron dengan `main`).
- File yang BOLEH kamu baca sebagai referensi: `decy13_mqtt_kit/raspi_cli/config_hardware.json` dan `decy13_mqtt_kit/raspi_cli/modules/base_module.py`.
- File yang BOLEH kamu edit HANYA:
  1. `decy13_mqtt_kit/raspi_cli/modules/mod_vacuum_safety.py`
  2. `decy13_mqtt_kit/raspi_cli/01_test_relay_buzzer.py`
- DILARANG mengedit file divisi lain (`04_decy13_mqtt_daemon.py`, `config_hardware.json`, `web_hmi/index.html`, dll).
- DILARANG menjalankan perintah `git commit` atau `git push` secara otomatis; saya akan menjalankan commit dan push sendiri.

[KONTRAK YANG WAJIB DIJAGA]
Class `VacuumSafetyModule(HardwareModule)` wajib memiliki `setup() -> bool`, `update(state, dt, now)`, `cleanup()`, fallback `try/except ImportError` untuk `RPi.GPIO` agar aman jalan di laptop Windows, serta memenuhi pengecekan `python tools/cek_integrasi_dan_announcer.py --ci`.

[TUGAS LANJUTAN]
Baca `mod_vacuum_safety.py` dan `01_test_relay_buzzer.py` saat ini terlebih dahulu, lalu tanyakan fitur lanjutan atau penyempurnaan pengujian fisik apa yang ingin saya kerjakan sekarang.
```

</details>

<details open>
<summary><b>💡 DIVISI 3 — Prompt Perbaikan Khusus & Migrasi dari Branch `pacarjeno` (Klik untuk buka & salin)</b></summary>

```text
[KONTEKS TERBARU PROYEK SIKLOTRON DECY-13 — PERBAIKAN KHUSUS DIVISI 3]
Saya adalah Anggota Divisi 3 (Sistem LED Strip WS2812B) pada proyek Alat Peraga Siklotron DECY-13 (13 MeV H-) di Raspberry Pi 3 Model B+.
Saya memulai sesi chat AI baru agar kamu memahami kondisi terbaru branch `main` dan catatan perbaikan dari Ketua Tim:

[MASALAH PADA KODE LAMA SAYA YANG HARUS DIPERBAIKI]
Pada branch lama saya (`pacarjeno` di folder `divisi3_led/`), terdapat ketidaksesuaian dengan Core Daemon:
1. Kode lama memakai `Pi5NeoStrip` (`/dev/spidev0.0` SPI0 untuk Raspberry Pi 5). Itu SALAH karena sistem kita memakai **Raspberry Pi 3B+** dengan **`rpi_ws281x` di GPIO 18 (DMA PWM0)**, sedangkan SPI0 dipakai oleh Layar LCD ILI9341 (Divisi 4).
2. Kode lama meng-hardcode `LED_COUNT = 200` (`0-149` spiral, `150-199` shoot). Seharusnya WAJIB membaca konfigurasi dinamis dari `config_hardware.json` (`self.cfg["led_mapping"]`: `total_leds`, `spiral_start_idx`, `spiral_end_idx`, `rf_gap_indices`, `shoot_start_idx`, `shoot_end_idx`).
3. Kode lama memakai class `CyclotronLED` di folder baru `divisi3_led/` dan ikut meng-upload `__pycache__/*.pyc`. Seharusnya modul resmi berada di `decy13_mqtt_kit/raspi_cli/modules/mod_led_ws2812b.py` menggunakan class `LedStripModule(HardwareModule)`!
4. Core Daemon (`04_decy13_mqtt_daemon.py`) memanggil `setup()`, `update(state, dt, now)`, dan `cleanup()`, serta membaca `state["activeLedIdx"]` dan `state["shootLedIdx"]` untuk dikirim ke Web HMI melalui MQTT.

[HAL BAGUS YANG INGIN SAYA PERTAHANKAN]
Saya ingin mempertahankan logika efek ekor komet halus (`_comet`), pewarnaan per tahap (`stage` 0..7 dari `state["stage"]`), serta dukungan simulasi visual di laptop Windows (jika library `rpi_ws281x` tidak ada, gunakan mode virtual/simulasi tanpa error!).

[BATAS KERJA & ATURAN GIT MANDIRI]
- Branch kerja saya yang benar adalah `divisi-3-led-ws2812b` (dibuat dari `main` terbaru, BUKAN `pacarjeno`).
- File referensi yang BOLEH dibaca: `decy13_mqtt_kit/raspi_cli/config_hardware.json`, `decy13_mqtt_kit/raspi_cli/modules/base_module.py`, `decy13_mqtt_kit/raspi_cli/04_decy13_mqtt_daemon.py`.
- File yang BOLEH kamu edit/tulis HANYA:
  1. `decy13_mqtt_kit/raspi_cli/modules/mod_led_ws2812b.py`
  2. `decy13_mqtt_kit/raspi_cli/03_test_led_pixel_finder.py`
- JANGAN membuat folder `divisi3_led/` baru, JANGAN edit `04_decy13_mqtt_daemon.py` atau `config_hardware.json`, dan JANGAN jalankan `git commit` / `git push` otomatis (saya yang akan commit & push sendiri).

[TUGAS SEKARANG]
1. Baca isi `decy13_mqtt_kit/raspi_cli/modules/mod_led_ws2812b.py` dan `config_hardware.json` yang ada di `main` sekarang.
2. Adaptasikan algoritma animasi komet & pewarnaan tahap saya ke dalam `LedStripModule(HardwareModule)` di `mod_led_ws2812b.py` agar 100% kompatibel dengan GPIO 18 (`rpi_ws281x`), mode fallback laptop Windows, membaca parameter dinamis dari `self.cfg["led_mapping"]`, dan tetap meng-update `state["activeLedIdx"]` & `state["shootLedIdx"]`.
3. Setelah selesai, bantu saya memverifikasi dengan menjalankan `python tools/cek_integrasi_dan_announcer.py --ci` agar pasti lolos satpam GitHub Actions.
```

</details>

<details>
<summary><b>📟 DIVISI 4 — Prompt Konteks Terbaru Layar LCD TFT SPI (Klik untuk buka & salin)</b></summary>

```text
[KONTEKS TERBARU PROYEK SIKLOTRON DECY-13 — UPDATE v1.1]
Saya adalah Anggota Divisi 4 (Layar Status Lokal LCD TFT SPI ILI9341 320x240) pada Raspberry Pi 3 Model B+.
Hardware LCD memakai SPI0 (`CE0=GPIO 8`, `MOSI=GPIO 10`, `SCLK=GPIO 11`, `DC=GPIO 24`, `RST=GPIO 25`) dengan `luma.lcd` & `Pillow`.

[BATAS KERJA & ATURAN GIT MANDIRI]
- Branch kerja saya: `divisi-4-lcd-ili9341` (dibuat dari `main` terbaru).
- File referensi yang BOLEH dibaca: `decy13_mqtt_kit/raspi_cli/config_hardware.json`, `decy13_mqtt_kit/raspi_cli/modules/base_module.py`.
- File yang BOLEH kamu edit HANYA:
  1. `decy13_mqtt_kit/raspi_cli/modules/mod_lcd_ili9341.py`
  2. `decy13_mqtt_kit/raspi_cli/02_test_lcd_ili9341.py`
- DILARANG mengedit file divisi lain (`04_decy13_mqtt_daemon.py`, `config_hardware.json`, dll) dan DILARANG menjalankan `git commit` / `git push` otomatis.

[TUGAS SEKARANG]
Baca `mod_lcd_ili9341.py` dan `02_test_lcd_ili9341.py` yang ada di `main` sekarang, pastikan background SPI render thread tetap non-blocking dan aman di Windows tanpa `luma.lcd`, lalu bantu saya menyempurnakan tampilan dashboard 320x240 LCD (warna tema per stage, indikator interlock, progress bar vakum & MeV). Pastikan lolos `python tools/cek_integrasi_dan_announcer.py --ci`.
```

</details>

<details>
<summary><b>🖥️ DIVISI 5 — Prompt Konteks Terbaru Web HMI SCADA & 2D Canvas (Klik untuk buka & salin)</b></summary>

```text
[KONTEKS TERBARU PROYEK SIKLOTRON DECY-13 — UPDATE v1.1]
Saya adalah Anggota Divisi 5 (Web HMI SCADA & Live 2D Simulator) untuk Mini PC Ruang Kontrol.
Web HMI berkomunikasi dengan RPi 3B+ via Mosquitto MQTT over WebSockets (port 9001):
- Publish perintah ke `decy13/hmi/cmd` (`TOGGLE_POWER`, `TOGGLE_VACUUM`, `TOGGLE_INTERLOCK`, `AUTO_INIT`, `START_BEAM`, `SHOOT`, `EMERGENCY_STOP`, `SET_PARAMS`).
- Subscribe telemetri dari `decy13/rpi/state` dan sinkronisasi melalui `applyRpiState(rpi)`.

[BATAS KERJA & ATURAN GIT MANDIRI]
- Branch kerja saya: `divisi-5-web-hmi` (dibuat dari `main` terbaru).
- File yang BOLEH kamu edit HANYA: `decy13_mqtt_kit/web_hmi/index.html` (dan aset di `decy13_mqtt_kit/web_hmi/assets/`).
- DILARANG mengedit file Python di `raspi_cli/`, `config_hardware.json`, atau `nodered/`, dan DILARANG menjalankan `git commit` / `git push` otomatis.

[TUGAS SEKARANG]
Baca struktur `decy13_mqtt_kit/web_hmi/index.html` saat ini terlebih dahulu, pertahankan mode State-Driven saat `state.mqttConnected === true`, dan bantu saya menyempurnakan UI SCADA, grafik, atau simulasi 2D. Pastikan lolos `python tools/cek_integrasi_dan_announcer.py --ci`.
```

</details>

<details>
<summary><b>📡 DIVISI 6 — Prompt Konteks Terbaru MQTT QA, Node-RED & Commissioning (Klik untuk buka & salin)</b></summary>

```text
[KONTEKS TERBARU PROYEK SIKLOTRON DECY-13 — UPDATE v1.1]
Saya adalah Anggota Divisi 6 (Jaringan MQTT, Node-RED & Commissioning QA) pada proyek DECY-13.
Sistem menggunakan Mosquitto (`1883` TCP & `9001` WebSocket) dengan topic `decy13/hmi/cmd` dan `decy13/rpi/state` (22 field JSON wajib).

[BATAS KERJA & ATURAN GIT MANDIRI]
- Branch kerja saya: `divisi-6-nodered-qa` (dibuat dari `main` terbaru).
- File yang BOLEH kamu edit HANYA:
  1. `decy13_mqtt_kit/raspi_cli/06_test_mqtt_healthcheck.py`
  2. `decy13_mqtt_kit/nodered/flows_mqtt_decy13.json`
  3. `instruksi untuk projek sp/CHECKLIST_COMMISSIONING.txt`
- DILARANG mengedit `04_decy13_mqtt_daemon.py`, `modules/*.py`, atau `web_hmi/index.html`, dan DILARANG menjalankan `git commit` / `git push` otomatis.

[TUGAS SEKARANG]
Baca `06_test_mqtt_healthcheck.py` dan `flows_mqtt_decy13.json` saat ini, lalu bantu saya menambahkan mode automated end-to-end test 7 tahap + pengukuran latensi MQTT. Pastikan lolos `python tools/cek_integrasi_dan_announcer.py --ci`.
```

</details>

---

## 🛠️ Perintah Rutin Ketua (Divisi 1) Setiap Kali Ada Merge

```powershell
# 1. Tarik & cek branch anggota yang masuk
git fetch origin
git diff --stat main..origin/divisi-2-vacum-safety

# 2. Merge branch yang sudah LULUS ke main
git checkout main
git merge origin/divisi-2-vacum-safety

# 3. Jalankan cek integrasi & buat teks pengumuman WhatsApp otomatis
python tools/cek_integrasi_dan_announcer.py --versi "v1.2" --catatan "Divisi 2 sudah di-merge ke main"

# 4. Update tabel status & prompt di README.md jika perlu, lalu commit & push sendiri ke main
```
