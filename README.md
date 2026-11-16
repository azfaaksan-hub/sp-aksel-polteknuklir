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
| **Versi / Status `main`** | **`v1.5` — Core Hardening (`setpoint_limits` + Reconnect MQTT), Bootstrap & Preflight RPi, dan Uji Bare-Board RPi `3/5`!** |
| **Pengumuman Ketua** | 1. **Perubahan `config_hardware.json` (`setpoint_limits`):** Core Daemon sekarang memvalidasi perintah `SET_PARAMS` terhadap batas `magnet_a` `[400..2200]`, `rf_mhz` `[15..30]`, `rf_kv` `[0..120]`, dan `beam_ua` `[0..100]` (nilai `0` atau di luar rentang ditolak otomatis). **Penting untuk Divisi 5 & Divisi 6!**<br>2. **Alat Baru untuk Tes di RPi Anggota:** Jalankan `bash tools/raspi_bootstrap.sh` & `python3 tools/raspi_preflight.py --divisi <1..6>` sebelum tes hardware! Lihat peta RACI & *Definition of Done* di [`laporan_uji/JOBDESK_DAN_DOD.md`](laporan_uji/JOBDESK_DAN_DOD.md).<br>3. Core RPi lolos uji *bare-board* (`4.97 Hz`, 0 paket hilang) — lanjut uji wiring aktuator bersama! |
| **Cara Tarik Update Terbaru** | **GitHub Desktop:** Pastikan di branch divisimu → klik *Fetch origin* → menu *Branch* → *Update from main*.<br>**Terminal:** `git fetch origin` lalu `git merge origin/main` |

---

## 📊 Tabel Rapor & Status Integrasi 6 Divisi

Setiap anggota yang melakukan `git push` akan diperiksa oleh **Satpam Otomatis (GitHub Actions)** (tanda ✅/❌) dan direview oleh Ketua sebelum di-*merge* ke `main`.

| Divisi | Penanggung Jawab | Branch Wajib | File Eksklusif (Boleh Diedit) | Status Audit Kode / CI | Status Uji Hardware RPi |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Divisi 1 (Ketua)** | `azfaaksan-hub` | `main` / `core-raspi-backend` | `04_decy13_mqtt_daemon.py`, `05_laptop_dryrun_simulator.py`, `config_hardware.json`, `modules/base_module.py`, `tools/*`, `laporan_uji/UJI_DIVISI_1_CORE_RASPI.md` | ✅ **Core Aktif** *(`setpoint_limits`, `connect_async`, `SIGTERM`, bootstrap & preflight siap)* | 🟡 [`DRAFT_PUSH_LAPTOP`](laporan_uji/UJI_DIVISI_1_CORE_RASPI.md) *(3/3 Laptop, **3/5 RPi bare-board** `192.168.137.66`)* |
| **Divisi 2** | `dzakimumtazi` | `divisi-2-vacum-safety` | `decy13_mqtt_kit/raspi_cli/modules/mod_vacuum_safety.py`, `01_test_relay_buzzer.py`, `laporan_uji/UJI_DIVISI_2_VAKUM_SAFETY.md` | ✅ **Sudah Di-Merge ke `main`** *(Initial relay OFF, cleanup aman, menu tes E-Stop oke)* | 🟡 [`DRAFT_PUSH_LAPTOP`](laporan_uji/UJI_DIVISI_2_VAKUM_SAFETY.md) *(3/3 Laptop, 0/5 RPi — menunggu uji alat nyata)* |
| **Divisi 3** | `blufiaa` | `divisi-3-led-ws2812b-v13` | `decy13_mqtt_kit/raspi_cli/modules/mod_led_ws2812b.py`, `03_test_led_pixel_finder.py`, `laporan_uji/UJI_DIVISI_3_LED_WS2812B.md` | ✅ **Sudah Di-Merge ke `main`** *(`ac21a27` — GPIO 18 `rpi_ws281x`, virtual test PASS)* | 🟡 [`DRAFT_PUSH_LAPTOP`](laporan_uji/UJI_DIVISI_3_LED_WS2812B.md) *(5/5 Laptop, 0/5 RPi — lanjut uji fisik RPi)* |
| **Divisi 4** | *(Anggota 4 / `HDMrishiki`?)* | `divisi-4-lcd-ili9341` *(atau `hmi+tft`)* | `decy13_mqtt_kit/raspi_cli/modules/mod_lcd_ili9341.py`, `02_test_lcd_ili9341.py`, `laporan_uji/UJI_DIVISI_4_LCD_ILI9341.md` | ⏳ **Branch `hmi+tft` masih di `045c321` — Harap Merge `main` & Push Kode** | ⏳ [`BELUM_MULAI`](laporan_uji/UJI_DIVISI_4_LCD_ILI9341.md) *(0/4 Laptop, 0/4 RPi)* |
| **Divisi 5** | *(Anggota 5 / `HDMrishiki`?)* | `divisi-5-web-hmi` *(atau `hmi+tft`)* | `decy13_mqtt_kit/web_hmi/index.html`, `laporan_uji/UJI_DIVISI_5_WEB_HMI.md` | ⏳ **Branch `hmi+tft` masih di `045c321` — Harap Merge `main` & Push Kode** | ⏳ [`BELUM_MULAI`](laporan_uji/UJI_DIVISI_5_WEB_HMI.md) *(0/4 Laptop, 0/4 Alat)* |
| **Divisi 6** | `rekypurnomo` | `divisi-6-mqtt-nodered-qa-testing` | `06_test_mqtt_healthcheck.py`, `flows_mqtt_decy13.json`, `CHECKLIST_COMMISSIONING.txt`, `laporan_uji/UJI_DIVISI_6_MQTT_QA.md` | ✅ **Sudah Di-Merge ke `main`** *(`4ed588d` + `b2b42f6`: QA & Node-RED `18 node` tanpa konflik GPIO)* | 🟡 [`DRAFT_PUSH_LAPTOP`](laporan_uji/UJI_DIVISI_6_MQTT_QA.md) *(3/3 Laptop, 0/4 Alat Nyata)* |

### 🧪 Aturan "Push Dulu" vs "Lulus Uji Raspi" (`laporan_uji/`)
Supaya tidak pernah terjadi *Merge Conflict* dan kita bisa tahu dengan jujur apakah kode teman yang baru di-push sudah dites di alat nyata atau masih ada bug:
1. **Jangan edit `README.md` ini dari branch divisi!** Anggota + AI-nya cukup mengisi **1 file kartu ceklis milik divisinya sendiri** di folder [`laporan_uji/`](laporan_uji/README.md).
2. **Kalau Ketua bilang "Push dulu progresmu" saat alat/kode belum 100% beres:**
   - Isi `Status Push Saat Ini` dengan **`DRAFT_PUSH_LAPTOP`** *(baru lolos simulasi laptop)* atau **`SEDANG_REVISI_HARDWARE`** *(masih ada bug/kendala saat diuji)*.
   - Centang **`[x]` pada Tahap A (Laptop)** saja jika sudah lolos, dan tulis detail masalah yang masih terjadi di **Bagian C** agar terbaca oleh Ketua dan sesi AI berikutnya.
3. **Aturan Keras AI:** AI **DILARANG** mencentang **`[x]` pada Tahap B (Uji Fisik RPi)** atau menulis **`LULUS_UJI_FISIK`** sebelum anggota menempelkan bukti hasil tes nyata dari Raspberry Pi 3B+ / Mini PC! (*Alat `cek_integrasi_dan_announcer.py --ci` otomatis menolak status `LULUS_UJI_FISIK` jika kotak Tahap A/B masih ada yang kosong.*)

---

## 📝 Catatan Penyelarasan & Rencana Uji Berikutnya

*(Tidak ada divisi yang memicu konflik/error blocking saat ini — Divisi 3 sudah lolos & ter-merge bersih ke `main`! Berikut catatan penyelarasan ringan sebelum uji alat fisik:)*

### 🛠️ Alat Auto-Setup & Preflight RPi untuk Anggota yang Pakai Raspi Sendiri
Jika kamu mengetes modul memakai Raspberry Pi 3B+ sendiri (username/hostname bebas, bukan harus `pi@raspberrypi`), baca [`laporan_uji/JOBDESK_DAN_DOD.md`](laporan_uji/JOBDESK_DAN_DOD.md) dan jalankan 2 perintah ini di RPi setelah menarik kode terbaru:
```bash
bash tools/raspi_bootstrap.sh                    # auto-set SPI0, Audio OFF, Mosquitto 1883/9001, 6 paket Python
python3 tools/raspi_preflight.py --divisi <1..6> # cek kesiapan OS + tampilkan batas file & perintah uji Tahap B divisimu
```
*(Skrip preflight otomatis menyimpan log ke `laporan_uji/bukti/` sebagai lampiran Bagian C tanpa pernah mencentang `[x]` otomatis.)*

### 📡 Catatan Penyelarasan & Perubahan `config_hardware.json` (Pasca `v1.5`)

| No | Bagian | Temuan / Perubahan Terbaru di `main` | Penyesuaian yang Disarankan (Divisi Terkait) |
| :---: | :--- | :--- | :--- |
| **1** | **Baru: `setpoint_limits` di `config_hardware.json`** | `04_decy13_mqtt_daemon.py` & `05_*` sekarang menolak perintah `SET_PARAMS` non-angka, `NaN/Infinity`, atau di luar `magnet_a` `[400..2200]`, `rf_mhz` `[15..30]`, `rf_kv` `[0..120]`, `beam_ua` `[0..100]`. | **Divisi 5 (Web HMI):** pastikan slider/tombol tidak mengirim nilai `0` untuk `magnet_a` atau di luar rentang di atas (atau tampilkan validasi input). **Divisi 6 (QA):** gunakan rentang `setpoint_limits` ini bila menguji perintah `SET_PARAMS`. |
| **2** | **`--auto` `SEQ-03` (`TOGGLE_INTERLOCK`)** | Setelah `TOGGLE_VACUUM`, skrip baru menunggu tekanan turun >50% lalu langsung kirim `TOGGLE_INTERLOCK`. Daemon asli (`04_decy13_mqtt_daemon.py`) menolak sampai `pressure <= 1e-3 mbar` (~6–7 detik). | **Divisi 6:** tunggu `pressure <= 1e-3` sebelum kirim `TOGGLE_INTERLOCK` (atau jalankan dengan `--cmd-timeout 10`). |
| **3** | **`--expected-stages` Default `7`** | Integer `state["stage"]` di `04_decy13_mqtt_daemon.py` melewati 6 nilai `{0, 1, 4, 5, 6, 7}` (tahap 2 & 3 berupa log teks), sehingga `SEQ-ST1` mencetak `WARN`. | **Divisi 6:** boleh sesuaikan default atau catatan pengecekan ke 6 integer `stage` aktif. |
| **4** | **IP Broker di `flows_mqtt_decy13.json`** | Node `"Local Mosquitto Broker"` memakai `localhost:1883` (cocok bila Node-RED jalan di Raspberry Pi yang sama). | **Divisi 6:** jika Node-RED dijalankan dari Mini PC terpisah, ubah host broker ke IP RPi (mis. `192.168.137.1` atau IP LAN RPi saat tes). |

### 💡 Info Kebersihan Branch Lama Divisi 3
- Branch `divisi-3-led-ws2812b-v13` (`ac21a27`) sudah menggantikan dan masuk ke `main`. Branch lama `divisi-3-led-ws2812b` (`0137adb`) maupun **PR #2** boleh ditutup/dihapus di GitHub agar tidak membingungkan.

### 📟🖥️ Info untuk Divisi 4 & Divisi 5 (`hmi+tft` / `HDMrishiki`)
- Branch `origin/hmi+tft` masih berada di commit `v1.2` (`045c321`). Sebelum mengedit kode & kartu ceklis (`UJI_DIVISI_4_LCD_ILI9341.md` / `UJI_DIVISI_5_WEB_HMI.md`), wajib jalankan `git fetch origin` lalu `git merge origin/main` agar sinkron dengan `v1.5`!

---

## 🤖 Prompt Konteks Terbaru per Divisi (Siap Copy-Paste untuk Chat AI Baru!)

Gunakan prompt di bawah ini **setiap kali kamu membuka chat AI baru** (atau setelah Ketua mengumumkan update `main` di WhatsApp) agar AI kamu tidak kehilangan konteks proyek!

> 💡 **Pakai AI Web (ChatGPT / Gemini / Claude di Browser) vs AI IDE/CLI (Cursor / Antigravity / Copilot)? Keduanya BISA & AMAN!**
> - **Kalau pakai AI Web (di browser):** AI di browser **tidak bisa membuka folder laptopmu atau menjalankan terminal** secara otomatis. Jadi saat membuka chat baru: **(1)** *paste* prompt divisimu, **(2)** sekaligus **upload atau *copy-paste* isi file referensi + file divisimu** (misal `config_hardware.json`, `modules/base_module.py`, dan file modulmu) agar AI tidak mengarang, lalu **(3)** salin kode lengkap dari AI ke file resminya di VS Code dan jalankan perintah tes di terminal laptopmu sendiri (`python tools/cek_integrasi_dan_announcer.py --ci`).
> - **Kalau pakai AI IDE/CLI (di VS Code / terminal):** AI bisa langsung membaca file & menjalankan tes, tetapi **tetap DILARANG** melakukan `git commit` / `git push` otomatis. Kamu wajib commit & push sendiri!

<details>
<summary><b>🌀 DIVISI 2 — Prompt Lanjutan Konteks Terbaru (Klik untuk buka & salin)</b></summary>

```text
[KONTEKS TERBARU PROYEK SIKLOTRON DECY-13 — UPDATE v1.5]
Saya adalah Anggota Divisi 2 (Sistem Vakum, Buzzer & Safety E-Stop) pada repo `sp-aksel-polteknuklir`.
Status kode saya di branch `divisi-2-vacum-safety` sudah **RESMI DI-MERGE ke `main`** (initial pin relay OFF, cleanup aman menjaga relay tetap OFF, dan menu [4] Tes E-Stop di `01_test_relay_buzzer.py`), tetapi **Tahap B (Uji Fisik RPi 3B+)** masih menunggu bukti uji alat nyata di `laporan_uji/UJI_DIVISI_2_VAKUM_SAFETY.md`.
Core Raspi (`v1.5`) juga sudah lolos uji bare-board RPi 3B+ dan menyediakan alat bantu baru (`tools/raspi_bootstrap.sh`, `tools/raspi_preflight.py`, & `laporan_uji/JOBDESK_DAN_DOD.md`).

[BATAS KERJA & ATURAN GIT MANDIRI]
- Branch aktif saya: `divisi-2-vacum-safety` (pastikan sudah `git merge origin/main` agar sinkron dengan `main` `v1.5`).
- File yang BOLEH kamu baca sebagai referensi: `decy13_mqtt_kit/raspi_cli/config_hardware.json`, `decy13_mqtt_kit/raspi_cli/modules/base_module.py`, `laporan_uji/README.md`, dan `laporan_uji/JOBDESK_DAN_DOD.md`.
- File yang BOLEH kamu edit HANYA:
  1. `decy13_mqtt_kit/raspi_cli/modules/mod_vacuum_safety.py`
  2. `decy13_mqtt_kit/raspi_cli/01_test_relay_buzzer.py`
  3. `laporan_uji/UJI_DIVISI_2_VAKUM_SAFETY.md` (dan lampiran hasil preflight otomatis di `laporan_uji/bukti/`)
- DILARANG mengedit `README.md` root atau file divisi lain (`04_decy13_mqtt_daemon.py`, `config_hardware.json`, `web_hmi/index.html`, `tools/*`, dll).
- DILARANG menjalankan perintah `git commit` atau `git push` secara otomatis; saya akan menjalankan commit dan push sendiri.
- ATURAN KERAS KARTU UJI: JANGAN mencentang `[x]` pada Tahap B (Uji Fisik RPi) atau memberi status `LULUS_UJI_FISIK` di `UJI_DIVISI_2_VAKUM_SAFETY.md` sebelum saya memberi bukti output terminal / hasil tes nyata dari Raspberry Pi 3B+! Jika baru tes laptop atau masih ada kendala fisik saat saya ingin push dulu, catat status `DRAFT_PUSH_LAPTOP` / `SEDANG_REVISI_HARDWARE` dan tulis masalahnya di Bagian C.

[PERSIAPAN UJI DI RPi 3B+ ANGGOTA (TAHAP B)]
Saat saya akan mengetes rangkaian fisik pada unit RPi 3B+ yang saya pegang/pinjam, arahkan saya menjalankan:
1. `bash tools/raspi_bootstrap.sh` (cukup 1x di RPi baru/pinjaman untuk auto-set Audio OFF, SPI ON, Mosquitto 1883/9001, & paket Python)
2. `python3 tools/raspi_preflight.py --divisi 2` (cek OS & tampilkan peringatan wiring/perintah uji Tahap B Divisi 2)

[KONTRAK YANG WAJIB DIJAGA]
Class `VacuumSafetyModule(HardwareModule)` wajib memiliki `setup() -> bool`, `update(state, dt, now)`, `cleanup()`, fallback `try/except ImportError` untuk `RPi.GPIO` agar aman jalan di laptop Windows, serta memenuhi pengecekan `python tools/cek_integrasi_dan_announcer.py --ci`.

[TUGAS LANJUTAN]
- Jika kamu **AI Web (browser)** yang tidak bisa mengakses folder lokal secara langsung: **JANGAN mengarang isi file** — minta saya meng-upload/mem-paste isi `config_hardware.json`, `base_module.py`, `mod_vacuum_safety.py`, `01_test_relay_buzzer.py`, dan `UJI_DIVISI_2_VAKUM_SAFETY.md` terlebih dahulu, lalu berikan hasil kode **utuh siap copy-paste** serta beri tahu perintah terminal yang harus saya jalankan sendiri.
- Jika kamu **AI IDE/CLI**: baca `mod_vacuum_safety.py`, `01_test_relay_buzzer.py`, dan `UJI_DIVISI_2_VAKUM_SAFETY.md` saat ini terlebih dahulu, lalu bantu saya menyiapkan uji hardware Divisi 2 atau penyempurnaan modul sesuai catatan.
```

</details>

<details>
<summary><b>💡 DIVISI 3 — Prompt Lanjutan Uji Fisik LED WS2812B di RPi (`v1.5` Sudah Merged + Bootstrap/Preflight!)</b></summary>

```text
[KONTEKS TERBARU PROYEK SIKLOTRON DECY-13 — UPDATE v1.5 DIVISI 3]
Saya adalah Anggota Divisi 3 (Sistem LED Strip WS2812B) pada proyek Alat Peraga Siklotron DECY-13 (13 MeV H-) di Raspberry Pi 3 Model B+.
Kode saya (`mod_led_ws2812b.py` & `03_test_led_pixel_finder.py` di commit `ac21a27`) sudah **RESMI DI-MERGE ke `main`**, lolos cek virtual (`ALL DIVISI 3 VIRTUAL TESTS PASSED`), dan Tahap A pada `laporan_uji/UJI_DIVISI_3_LED_WS2812B.md` sudah `5/5 [x]` (`DRAFT_PUSH_LAPTOP`).

[BATAS KERJA & ATURAN GIT MANDIRI]
- Branch kerja saya: tarik `origin/main` terbaru (`git checkout -b divisi-3-uji-fisik origin/main` atau `git merge origin/main` di branch `divisi-3-led-ws2812b-v13`).
- File referensi yang BOLEH dibaca: `decy13_mqtt_kit/raspi_cli/config_hardware.json`, `decy13_mqtt_kit/raspi_cli/modules/base_module.py`, `laporan_uji/README.md`, `laporan_uji/JOBDESK_DAN_DOD.md`.
- File yang BOLEH kamu edit HANYA:
  1. `decy13_mqtt_kit/raspi_cli/modules/mod_led_ws2812b.py`
  2. `decy13_mqtt_kit/raspi_cli/03_test_led_pixel_finder.py`
  3. `laporan_uji/UJI_DIVISI_3_LED_WS2812B.md` (dan lampiran log otomatis di `laporan_uji/bukti/`)
- DILARANG mengedit `README.md` root, `04_decy13_mqtt_daemon.py`, `config_hardware.json`, `tools/*`, dan DILARANG jalankan `git commit` / `git push` otomatis.
- ATURAN KERAS KARTU UJI: JANGAN mencentang `[x]` pada Tahap B (`UJI_DIVISI_3_LED_WS2812B.md`) sebelum saya memberi bukti hasil tes langsung pada LED strip WS2812B fisik di Raspberry Pi 3B+ (`sudo python3 03_test_led_pixel_finder.py --mode finder --hardware` / bersama daemon + LCD SPI0)!

[PERSIAPAN UJI DI RPi 3B+ ANGGOTA (TAHAP B)]
Sebelum tes strip LED fisik di RPi 3B+ yang saya pegang/pinjam, arahkan saya menjalankan:
1. `bash tools/raspi_bootstrap.sh` (auto-set `dtparam=audio=off` & `spi=on` + paket `rpi-ws281x`; butuh reboot bila baru mematikan audio)
2. `python3 tools/raspi_preflight.py --divisi 3` (cek status Audio OFF/DMA GPIO 18 & cetak daftar perintah uji Tahap B Divisi 3)

[TUGAS SEKARANG]
1. Bantu saya menjalankan pengujian fisik di RPi 3B+ (`dtparam=audio=off`, cek urutan piksel 0..63, cek warna RGB/GRB, cek bebas flicker saat LCD SPI0 aktif bersamaan, dan bila perlu perbaikan di `mod_led_ws2812b.py`).
2. Catat hasil pengujian RPi fisik dengan jujur di `laporan_uji/UJI_DIVISI_3_LED_WS2812B.md` dan verifikasi dengan `python tools/cek_integrasi_dan_announcer.py --ci`.
3. Jika kamu **AI Web (browser)** tanpa akses folder lokal, minta saya mem-paste `mod_led_ws2812b.py` & `UJI_DIVISI_3_LED_WS2812B.md` dulu sebelum memberi revisi.
```

</details>

<details>
<summary><b>📟 DIVISI 4 — Prompt Konteks Terbaru Layar LCD TFT SPI (Klik untuk buka & salin)</b></summary>

```text
[KONTEKS TERBARU PROYEK SIKLOTRON DECY-13 — UPDATE v1.5]
Saya adalah Anggota Divisi 4 (Layar Status Lokal LCD TFT SPI ILI9341 320x240) pada Raspberry Pi 3 Model B+.
Hardware LCD memakai SPI0 (`CE0=GPIO 8`, `MOSI=GPIO 10`, `SCLK=GPIO 11`, `DC=GPIO 24`, `RST=GPIO 25`) dengan `luma.lcd` & `Pillow`.

[BATAS KERJA & ATURAN GIT MANDIRI]
- Branch kerja saya: `divisi-4-lcd-ili9341` atau `hmi+tft` (wajib `git merge origin/main` dulu agar sinkron `v1.5`).
- File referensi yang BOLEH dibaca: `decy13_mqtt_kit/raspi_cli/config_hardware.json`, `decy13_mqtt_kit/raspi_cli/modules/base_module.py`, `laporan_uji/README.md`, `laporan_uji/JOBDESK_DAN_DOD.md`.
- File yang BOLEH kamu edit HANYA:
  1. `decy13_mqtt_kit/raspi_cli/modules/mod_lcd_ili9341.py`
  2. `decy13_mqtt_kit/raspi_cli/02_test_lcd_ili9341.py`
  3. `laporan_uji/UJI_DIVISI_4_LCD_ILI9341.md` (dan lampiran hasil preflight otomatis di `laporan_uji/bukti/`)
- DILARANG mengedit `README.md` root, `04_decy13_mqtt_daemon.py`, `config_hardware.json`, `tools/*`, atau file divisi lain, dan DILARANG menjalankan `git commit` / `git push` otomatis.
- ATURAN KERAS KARTU UJI: JANGAN mencentang `[x]` pada Tahap B (Uji Fisik RPi) sebelum ada bukti tes di LCD SPI fisik RPi 3B+! Catat status `DRAFT_PUSH_LAPTOP` / `SEDANG_REVISI_HARDWARE` dan kendala di Bagian C bila push sementara.

[PERSIAPAN UJI DI RPi 3B+ ANGGOTA (TAHAP B)]
Jika saya mengetes LCD fisik di RPi 3B+ yang saya pegang/pinjam, arahkan saya menjalankan:
1. `bash tools/raspi_bootstrap.sh` (auto-set SPI ON `dtparam=spi=on` + pasang `luma.lcd`, `Pillow`, `spidev`)
2. `python3 tools/raspi_preflight.py --divisi 4` (cek `/dev/spidev0.0` & cetak langkah uji Tahap B Divisi 4)

[TUGAS SEKARANG]
Jika kamu **AI Web (browser)** tanpa akses folder lokal, minta saya meng-upload/paste `config_hardware.json`, `base_module.py`, `mod_lcd_ili9341.py`, `02_test_lcd_ili9341.py`, dan `UJI_DIVISI_4_LCD_ILI9341.md` dulu sebelum menulis kode (jangan mengarang!), dan beri kode utuh siap copy-paste. Jika punya akses lokal, baca file tersebut langsung. Pastikan background SPI render thread tetap non-blocking dan aman di Windows tanpa `luma.lcd`, lalu bantu saya menyempurnakan tampilan dashboard 320x240 LCD (warna tema per stage, indikator interlock, progress bar vakum & MeV). Verifikasi / arahkan saya menjalankan `python tools/cek_integrasi_dan_announcer.py --ci`.
```

</details>

<details>
<summary><b>🖥️ DIVISI 5 — Prompt Konteks Terbaru Web HMI SCADA & 2D Canvas (Klik untuk buka & salin)</b></summary>

```text
[KONTEKS TERBARU PROYEK SIKLOTRON DECY-13 — UPDATE v1.5]
Saya adalah Anggota Divisi 5 (Web HMI SCADA & Live 2D Simulator) untuk Mini PC Ruang Kontrol.
Web HMI berkomunikasi dengan RPi 3B+ via Mosquitto MQTT over WebSockets (port 9001):
- Publish perintah ke `decy13/hmi/cmd` (`TOGGLE_POWER`, `TOGGLE_VACUUM`, `TOGGLE_INTERLOCK`, `AUTO_INIT`, `START_BEAM`, `SHOOT`, `EMERGENCY_STOP`, `SET_PARAMS`).
- Subscribe telemetri dari `decy13/rpi/state` dan sinkronisasi melalui `applyRpiState(rpi)`.
- **PENTING (`v1.5` Core Daemon):** `config_hardware.json` kini memiliki `setpoint_limits` (`magnet_a`: `[400..2200]`, `rf_mhz`: `[15..30]`, `rf_kv`: `[0..120]`, `beam_ua`: `[0..100]`). Daemon menolak `SET_PARAMS` di luar rentang atau `0` (sehingga pastikan Web HMI tidak mengirim `magnet_a: 0` saat reconnect/awal koneksi!).

[BATAS KERJA & ATURAN GIT MANDIRI]
- Branch kerja saya: `divisi-5-web-hmi` atau `hmi+tft` (wajib `git merge origin/main` dulu agar sinkron `v1.5`).
- File referensi yang BOLEH dibaca: `decy13_mqtt_kit/raspi_cli/config_hardware.json`, `laporan_uji/README.md`, `laporan_uji/JOBDESK_DAN_DOD.md`.
- File yang BOLEH kamu edit HANYA:
  1. `decy13_mqtt_kit/web_hmi/index.html` (dan aset di `decy13_mqtt_kit/web_hmi/assets/`)
  2. `laporan_uji/UJI_DIVISI_5_WEB_HMI.md` (dan lampiran preflight di `laporan_uji/bukti/`)
- DILARANG mengedit `README.md` root, file Python di `raspi_cli/`, `config_hardware.json`, `tools/*`, atau `nodered/`, dan DILARANG menjalankan `git commit` / `git push` otomatis.
- ATURAN KERAS KARTU UJI: JANGAN mencentang `[x]` pada Tahap B (`UJI_DIVISI_5_WEB_HMI.md`) sebelum Web HMI benar-benar diuji terhubung ke broker MQTT RPi nyata! Jika baru tes simulasi browser di laptop, gunakan status `DRAFT_PUSH_LAPTOP` / `SEDANG_REVISI_HARDWARE`.

[PERSIAPAN UJI KONEKSI KE RPi 3B+ (TAHAP B)]
Jika menguji Web HMI ke RPi Ketua/anggota (catatan: WebSocket aktif di port `9001`), pastikan RPi sudah disiapkan dengan:
- `bash tools/raspi_bootstrap.sh` (bila RPi baru) & `python3 tools/raspi_preflight.py --divisi 5` (tampilkan panduan IP/WebSocket & ceklis Tahap B Divisi 5).

[TUGAS SEKARANG]
Jika kamu **AI Web (browser)** tanpa akses folder lokal, minta saya melampirkan `decy13_mqtt_kit/web_hmi/index.html` (atau bagian kode terkait) serta `config_hardware.json` / `UJI_DIVISI_5_WEB_HMI.md` lebih dulu agar tidak merusak fungsi yang sudah ada, lalu berikan kode yang jelas untuk saya salin ke VS Code. Pertahankan mode State-Driven saat `state.mqttConnected === true`, jaga kesesuaian `setpoint_limits`, dan bantu saya menyempurnakan UI SCADA, grafik, atau simulasi 2D. Setelah selesai, verifikasi / arahkan saya menjalankan `python tools/cek_integrasi_dan_announcer.py --ci`.
```

</details>

<details>
<summary><b>📡 DIVISI 6 — Prompt Konteks Terbaru MQTT QA, Node-RED & Commissioning (Klik untuk buka & salin)</b></summary>

```text
[KONTEKS TERBARU PROYEK SIKLOTRON DECY-13 — UPDATE v1.5 DIVISI 6]
Saya adalah Anggota Divisi 6 (Jaringan MQTT, Node-RED & Commissioning QA) pada proyek DECY-13 (`rekypurnomo`).
Commit `4ed588d` (`06_test_mqtt_healthcheck.py`) dan `b2b42f6` (`flows_mqtt_decy13.json` 18 node tanpa konflik GPIO) sudah **RESMI DI-MERGE ke `main`** dan berstatus `DRAFT_PUSH_LAPTOP` di `laporan_uji/UJI_DIVISI_6_MQTT_QA.md`.
Sistem menggunakan Mosquitto (`1883` TCP & `9001` WebSocket) dengan topic `decy13/hmi/cmd` dan `decy13/rpi/state` (22 field JSON wajib).
- **Update Core `v1.5`:** `config_hardware.json` menambah `setpoint_limits` (`magnet_a`: `[400..2200]`, `rf_mhz`: `[15..30]`, `rf_kv`: `[0..120]`, `beam_ua`: `[0..100]`), dan daemon RPi `sp-aksel` sudah lolos uji `06_test_mqtt_healthcheck.py --duration 5` bare-board (`LULUS=10, GAGAL=0`, `4.97 Hz`).

[BATAS KERJA & ATURAN GIT MANDIRI]
- Branch kerja saya: `divisi-6-mqtt-nodered-qa-testing` (wajib `git merge origin/main` dulu agar tersinkron `v1.5`).
- File referensi yang BOLEH dibaca: `decy13_mqtt_kit/raspi_cli/config_hardware.json`, `decy13_mqtt_kit/raspi_cli/04_decy13_mqtt_daemon.py`, `laporan_uji/README.md`, `laporan_uji/JOBDESK_DAN_DOD.md`.
- File yang BOLEH kamu edit HANYA:
  1. `decy13_mqtt_kit/raspi_cli/06_test_mqtt_healthcheck.py`
  2. `decy13_mqtt_kit/nodered/flows_mqtt_decy13.json`
  3. `instruksi untuk projek sp/CHECKLIST_COMMISSIONING.txt`
  4. `laporan_uji/UJI_DIVISI_6_MQTT_QA.md` (dan lampiran preflight di `laporan_uji/bukti/`)
- DILARANG mengedit `README.md` root, `04_decy13_mqtt_daemon.py`, `modules/*.py`, `tools/*`, atau `web_hmi/index.html`, dan DILARANG menjalankan `git commit` / `git push` otomatis.
- ATURAN KERAS KARTU UJI: JANGAN mencentang `[x]` Tahap B di `UJI_DIVISI_6_MQTT_QA.md` sebelum dijalankan penuh (`--auto --estop`, Node-RED, commissioning) terhadap `04_decy13_mqtt_daemon.py` asli di jaringan Raspberry Pi <-> Mini PC nyata!

[PERSIAPAN UJI JARINGAN KE RPi 3B+ (TAHAP B)]
Sebelum tes di RPi Ketua/anggota: jalankan `bash tools/raspi_bootstrap.sh` (bila RPi baru) dan `python3 tools/raspi_preflight.py --divisi 6` (cek port `1883`/`9001` & tampilkan checklist perintah QA).

[TUGAS SEKARANG]
1. Sesuaikan 3 catatan audit pasca-merge + `setpoint_limits`: (a) di `--auto`, tunggu `pressure <= 1e-3 mbar` sebelum `SEQ-03` mengirim `TOGGLE_INTERLOCK` (atau `--cmd-timeout 10`); (b) cek apakah `--expected-stages` diselaraskan ke 6 nilai integer `stage` daemon (`0, 1, 4, 5, 6, 7`); (c) ingat host broker `flows_mqtt_decy13.json` diset ke IP RPi bila Node-RED berjalan di Mini PC terpisah; (d) patuhi `setpoint_limits` baru bila menguji `SET_PARAMS`.
2. Bantu saya menguji langsung ke RPi + Mini PC nyata dan memperbarui `laporan_uji/UJI_DIVISI_6_MQTT_QA.md`. Jika kamu **AI Web (browser)** tanpa akses folder lokal, minta saya melampirkan `06_test_mqtt_healthcheck.py`, `flows_mqtt_decy13.json`, `04_decy13_mqtt_daemon.py`, dan `UJI_DIVISI_6_MQTT_QA.md` lebih dulu; verifikasi akhir dengan `python tools/cek_integrasi_dan_announcer.py --ci`.
```

</details>

---

## 🛠️ Perintah Rutin Ketua (Divisi 1) Setiap Kali Ada Merge

```powershell
# 1. Tarik & cek branch anggota yang masuk
git fetch origin
git diff --stat main..origin/<nama-branch-divisi>

# 2. Merge branch yang sudah LULUS ke main
git checkout main
git merge origin/<nama-branch-divisi>

# 3. Jalankan cek integrasi & buat teks pengumuman WhatsApp otomatis
python tools/cek_integrasi_dan_announcer.py --versi "v1.4" --catatan "Merge <divisi> ke main"

# 4. Update tabel status & prompt di README.md jika perlu, lalu commit & push sendiri ke main
```
