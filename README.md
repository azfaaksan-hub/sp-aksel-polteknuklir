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
4. **🖥️ Panduan Stasiun Uji Mini PC Ruang Kontrol (Windows 8/10/11 <-> Raspi):**
   Buka [`decy13_mqtt_kit/PANDUAN_MINI_PC_UJI_LAPANGAN.md`](decy13_mqtt_kit/PANDUAN_MINI_PC_UJI_LAPANGAN.md) untuk setting koneksi Mini PC Win 8 <-> Raspberry Pi, urutan uji lapangan terbaru, dan **Prompt AGY Mini PC siap *copy-paste***.

> 🛡️ **ATURAN WAJIB KOLABORASI MANDIRI:**
> 1. AI milikmu (ChatGPT / Claude / Cursor / Gemini) **HANYA** membantu menulis isi file milik divisimu.
> 2. **DILARANG** menyuruh AI menjalankan `git commit` atau `git push` secara otomatis — **setiap anggota wajib melakukan `branch`, `pull`, `commit`, dan `push` sendiri** agar paham alur GitHub.
> 3. **DILARANG** mengedit file milik divisi lain agar tidak bentrok (*Merge Conflict*).

---

## 📢 Papan Pengumuman & Update Terbaru (`main`)

| Info | Keterangan |
| :--- | :--- |
| **Versi / Status `main`** | **`v1.5.1` — Progres Terverifikasi `34,7%` (`17/49` ceklis) • Divisi 6 (`6d3f8f5`) Sudah Merged! Fokus Uji Fisik LED Divisi 3, Konfirmasi Kartu Divisi 2, & Kejar Branch `hmi+tft`!** |
| **Pengumuman Ketua** | 1. **Panduan Stasiun Uji Mini PC Windows 8 <-> RPi (`PANDUAN_MINI_PC_UJI_LAPANGAN.md`):** Dibuat khusus agar Mini PC Ruang Kontrol tinggal `git pull origin main` untuk mendapat panduan Ethernet ICS/Git Bash SSH Win 8, data yang harus disiapkan di Mini PC vs RPi, dan **Prompt AGY Mini PC**.<br>2. **Status Uji Lapangan Divisi 2 → Lanjut Divisi 3:** Pengujian sistem vakum Divisi 2 selesai di lapangan *(commit `41a3352` belum menyertakan update kartu — menunggu konfirmasi & push kartu [`UJI_DIVISI_2_VAKUM_SAFETY.md`](laporan_uji/UJI_DIVISI_2_VAKUM_SAFETY.md) oleh `dzakimumtazi` setelah `git merge origin/main`)*. Fokus pengujian fisik sekarang berlanjut ke **Divisi 3 (LED WS2812B `GPIO 18`)**: jalankan `sudo python3 03_test_led_pixel_finder.py --mode finder --hardware` lalu ketik `s` (spiral) & `e` (shoot).<br>3. **Update Branch Terbaru (`18 Nov`):** Branch `divisi-6-mqtt-nodered-qa-testing` (`b8605fb` — QA simulasi `11/11 PASS` & route Node-RED `/cyclotron`, CI ✅) **sudah di-merge ke `main`** (`6d3f8f5`). Branch **`origin/hmi+tft` (Divisi 4 & 5)** kini tertinggal **14 commit** (`045c321`).<br>4. **Tetap Berlaku (`v1.5`):** Validasi `setpoint_limits` di `config_hardware.json` (`magnet_a` `[400..2200]`, `rf_mhz` `[15..30]`, `rf_kv` `[0..120]`, `beam_ua` `[0..100]`) dan cek OS RPi via `bash tools/raspi_bootstrap.sh` + `python3 tools/raspi_preflight.py --divisi <1..6>`. |
| **Cara Tarik Update Terbaru** | **GitHub Desktop:** Pastikan di branch divisimu → klik *Fetch origin* → menu *Branch* → *Update from main*.<br>**Terminal / Git Bash:** `git fetch origin` lalu `git merge origin/main` *(di Mini PC/RPi cukup `git checkout main && git pull origin main`)* |

---

## 📊 Progres Nyata Proyek & Tabel Rapor 6 Divisi

> **📈 Posisi Progres Nyata Proyek Saat Ini (Terukur dari 6 Kartu [`laporan_uji/`](laporan_uji/README.md)):**
> - **Progres Total Terverifikasi (`Tahap A + Tahap B`):** **`34,7%` (`17 / 49` butir ceklis)** `[████░░░░░░]`
> - **Tahap A — Kesiapan Kode & Simulasi Laptop:** **`63,6%` (`14 / 22` butir)** *(Divisi 1, 2, 3, 6 sudah `100%` Tahap A; Divisi 4 & 5 masih `0/4` di kartu)*
> - **Tahap B — Uji Fisik Alat Nyata (RPi 3B+ & Mini PC):** **`11,1%` (`3 / 27` butir)** *(baru `3/5` bare-board Core RPi Divisi 1; uji fisik vakum Divisi 2 & koneksi Mini PC belum tertulis di kartu divisi)*
>
> **🧭 Posisi Milestone (`M1` s.d. `M5` — lihat [`JOBDESK_DAN_DOD.md`](laporan_uji/JOBDESK_DAN_DOD.md)):**
> - **M1** *(Bootstrap, Preflight & Bare-Board RPi)*: ✅ **Tercapai di unit `sp-aksel`** (`4.97 Hz`, 0 packet drop; tinggal kestabilan daya/jaringan unit uji lab)
> - **M2** *(Uji Isolasi Fisik Aktuator `01`, `02`, `03`)*: 🔄 **~25%** *(vakum lapangan menunggu push kartu Divisi 2; LED Divisi 3 mulai uji fisik; LCD Divisi 4 belum mulai)*
> - **M3** *(Integrasi Penuh Daemon + Divisi 2, 3, 4 serentak di RPi)*: ⏳ **0%** *(menunggu M2 & update Divisi 4)*
> - **M4** *(Integrasi Mini PC Web HMI & QA Healthcheck)*: 🔄 **~25%** *(simulasi Divisi 6 `11/11 PASS` & route `/cyclotron` sudah ter-merge `6d3f8f5`, tetapi kartu Tahap B Divisi 5 & 6 masih `0/4`)*
> - **M5** *(Commissioning Final & 6/6 Kartu `LULUS_UJI_FISIK`)*: ⏳ **0%**

Setiap anggota yang melakukan `git push` akan diperiksa oleh **Satpam Otomatis (GitHub Actions)** (tanda ✅/❌) dan direview oleh Ketua sebelum di-*merge* ke `main`.

| Divisi | Penanggung Jawab | Branch Wajib | File Eksklusif (Boleh Diedit) | Status Audit Kode / CI | Status Uji Hardware RPi & Progres Kartu |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Divisi 1 (Ketua)** | `azfaaksan-hub` | `main` / `core-raspi-backend` | `04_decy13_mqtt_daemon.py`, `05_laptop_dryrun_simulator.py`, `config_hardware.json`, `modules/base_module.py`, `tools/*`, `laporan_uji/UJI_DIVISI_1_CORE_RASPI.md` | ✅ **Core Aktif** *(`setpoint_limits`, `connect_async`, `SIGTERM`, bootstrap & preflight siap)* | 🟡 [`DRAFT_PUSH_LAPTOP`](laporan_uji/UJI_DIVISI_1_CORE_RASPI.md) **`75%` (`6/8`)** *(3/3 Laptop, **3/5 RPi bare-board** `192.168.137.66`)* |
| **Divisi 2** | `dzakimumtazi` | `divisi-2-vacum-safety` | `decy13_mqtt_kit/raspi_cli/modules/mod_vacuum_safety.py`, `01_test_relay_buzzer.py`, `laporan_uji/UJI_DIVISI_2_VAKUM_SAFETY.md` | ✅ **Merged ke `main`** *(Catatan: push baru `41a3352` hanya 1 spasi & belum merge `main`)* | 🟡 [`DRAFT_PUSH_LAPTOP`](laporan_uji/UJI_DIVISI_2_VAKUM_SAFETY.md) **`37,5%` (`3/8`)** *(3/3 Laptop, 0/5 RPi tercatat — uji vakum lapangan menunggu konfirmasi & push kartu)* |
| **Divisi 3** | `blufiaa` | `divisi-3-led-ws2812b-v13` | `decy13_mqtt_kit/raspi_cli/modules/mod_led_ws2812b.py`, `03_test_led_pixel_finder.py`, `laporan_uji/UJI_DIVISI_3_LED_WS2812B.md` | ✅ **Sudah Di-Merge ke `main`** *(`ac21a27` — GPIO 18 `rpi_ws281x`, virtual test PASS)* | 🟡 [`DRAFT_PUSH_LAPTOP`](laporan_uji/UJI_DIVISI_3_LED_WS2812B.md) **`50%` (`5/10`)** *(5/5 Laptop, 0/5 RPi — **fokus uji fisik LED `GPIO 18` sekarang**)* |
| **Divisi 4** | *(Anggota 4 / `HDMrishiki`?)* | `divisi-4-lcd-ili9341` *(atau `hmi+tft`)* | `decy13_mqtt_kit/raspi_cli/modules/mod_lcd_ili9341.py`, `02_test_lcd_ili9341.py`, `laporan_uji/UJI_DIVISI_4_LCD_ILI9341.md` | ⏳ **Branch `hmi+tft` masih di `045c321` (tertinggal 14 commit) — Harap Merge `main` & Push** | ⏳ [`BELUM_MULAI`](laporan_uji/UJI_DIVISI_4_LCD_ILI9341.md) **`0%` (`0/8`)** *(0/4 Laptop, 0/4 RPi)* |
| **Divisi 5** | *(Anggota 5 / `HDMrishiki`?)* | `divisi-5-web-hmi` *(atau `hmi+tft`)* | `decy13_mqtt_kit/web_hmi/index.html`, `laporan_uji/UJI_DIVISI_5_WEB_HMI.md` | ⏳ **Branch `hmi+tft` masih di `045c321` (tertinggal 14 commit) — Harap Merge `main` & Push** | ⏳ [`BELUM_MULAI`](laporan_uji/UJI_DIVISI_5_WEB_HMI.md) **`0%` (`0/8`)** *(0/4 Laptop, 0/4 Alat)* |
| **Divisi 6** | `rekypurnomo` | `divisi-6-mqtt-nodered-qa-testing` | `06_test_mqtt_healthcheck.py`, `flows_mqtt_decy13.json`, `CHECKLIST_COMMISSIONING.txt`, `laporan_uji/UJI_DIVISI_6_MQTT_QA.md` | ✅ **Sudah Di-Merge ke `main`** *(`6d3f8f5`: QA `11/11` simulasi PASS & route `/cyclotron`)* | 🟡 [`DRAFT_PUSH_LAPTOP`](laporan_uji/UJI_DIVISI_6_MQTT_QA.md) **`42,9%` (`3/7`)** *(3/3 Laptop, 0/4 Alat Nyata — uji RPi belum dijalankan)* |

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

### 🛠️ Alat Auto-Setup, Preflight RPi, & Panduan Stasiun Uji Mini PC
- **Jika menguji di Raspberry Pi 3B+ sendiri** (username/hostname bebas, bukan harus `pi@raspberrypi`), baca [`laporan_uji/JOBDESK_DAN_DOD.md`](laporan_uji/JOBDESK_DAN_DOD.md) dan jalankan 2 perintah ini di RPi setelah menarik kode terbaru:
  ```bash
  bash tools/raspi_bootstrap.sh                    # auto-set SPI0, Audio OFF, Mosquitto 1883/9001, 6 paket Python
  python3 tools/raspi_preflight.py --divisi <1..6> # cek kesiapan OS + tampilkan batas file & perintah uji Tahap B divisimu
  ```
  *(Skrip preflight otomatis menyimpan log ke `laporan_uji/bukti/` sebagai lampiran Bagian C tanpa pernah mencentang `[x]` otomatis.)*
- **Jika membuka repo dari Mini PC Ruang Kontrol (khususnya Windows 8) untuk uji langsung ↔ Raspberry Pi:** baca [`decy13_mqtt_kit/PANDUAN_MINI_PC_UJI_LAPANGAN.md`](decy13_mqtt_kit/PANDUAN_MINI_PC_UJI_LAPANGAN.md) untuk pengaturan Ethernet ICS/SSH Win 8, tahapan uji fisik Divisi 3 (LED WS2812B), batas file anti-konflik, serta **Prompt AGY Mini PC siap *copy-paste***.

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

### 📂 Di Mana File Pengumuman & Tugas Baru untuk Tiap Divisi?
Setiap kali prompt dieksekusi, AI milikmu diinstruksikan membaca **3 sumber pengumuman & tugas resmi** ini (atau menjalankan `python tools/raspi_preflight.py --divisi <1..6> --no-save`) lalu **wajib menampilkannya kepadamu**:
1. **`README.md` (File ini):** Papan Pengumuman Utama, Tabel Rapor 6 Divisi, & Catatan Penyelarasan.
2. **`tools/jobdesk_divisi.json` & [`laporan_uji/JOBDESK_DAN_DOD.md`](laporan_uji/JOBDESK_DAN_DOD.md):** Menyimpan field `current_announcement` (pengumuman khusus divisimu) dan `current_tasks` (daftar tugas baru divisimu saat ini) serta *Definition of Done*.
3. **`laporan_uji/UJI_DIVISI_<1..6>_*.md`:** Kartu ceklis progres Tahap A (Laptop) & Tahap B (Fisik RPi) milik divisimu.

> 💡 **Pakai AI Web (ChatGPT / Gemini / Claude di Browser) vs AI IDE/CLI (Cursor / Antigravity / Copilot)? Keduanya BISA & AMAN!**
> - **Kalau pakai AI Web (di browser):** AI di browser **tidak bisa membuka folder laptopmu atau menjalankan terminal** secara otomatis. Jadi saat membuka chat baru: **(1)** *paste* prompt divisimu, **(2)** sekaligus **upload atau *copy-paste* isi file pengumuman/referensi (`README.md`, `tools/jobdesk_divisi.json`, `config_hardware.json`, `laporan_uji/UJI_DIVISI_X_*.md`) + file kode divisimu** agar AI bisa membacakan tugas barumu tanpa mengarang, lalu **(3)** salin kode lengkap dari AI ke VS Code dan jalankan perintah tes di terminal laptopmu sendiri (`python tools/cek_integrasi_dan_announcer.py --ci`).
> - **Kalau pakai AI IDE/CLI (di VS Code / terminal):** AI bisa langsung membaca file pengumuman, menjalankan `python tools/raspi_preflight.py --divisi <N> --no-save`, dan menampilkan perubahan kode, tetapi **tetap DILARANG** melakukan `git commit` / `git push` otomatis. Kamu wajib commit & push sendiri!

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

[TUGAS LANJUTAN & KEWAJIBAN TAMPILKAN PERUBAHAN (SHOW CHANGES + TUGAS BARU)]
- Lokasi file pengumuman & tugas baru Divisi 2: `README.md`, `tools/jobdesk_divisi.json` (field `current_announcement` & `current_tasks` Divisi 2), `laporan_uji/JOBDESK_DAN_DOD.md`, dan `laporan_uji/UJI_DIVISI_2_VAKUM_SAFETY.md`.
- Jika kamu **AI IDE/CLI**: jalankan `python tools/raspi_preflight.py --divisi 2 --no-save` serta baca file di atas. Jika kamu **AI Web (browser)**: minta saya meng-upload/mem-paste file tersebut lebih dulu (JANGAN mengarang!).
- **WAJIB TAMPILKAN 4 BLOK INI KEPADA SAYA SETIAP KALI EKSEKUSI PROMPT / SELESAI EDIT KODE:**
  1. **📢 Pengumuman Ketua & Tugas Baru Divisi 2:** Bacakan isi pengumuman terbaru & rincian tugas baru yang harus saya kerjakan sekarang.
  2. **🔍 Show Perubahan Kode (`git status` / `git diff --stat`):** Tampilkan daftar file yang berubah serta bagian fungsi/baris apa yang ditambah atau diubah dibanding `origin/main`.
  3. **🤖 Apa yang Dilakukan oleh AI:** Jelaskan secara singkat & mudah dipahami apa saja yang baru kamu (AI) kerjakan di balik layar.
  4. **🧑‍💻 Apa yang Harus Saya (Anggota) Lakukan Sendiri Sekarang:** Berikan urutan perintah terminal (uji alat/preflight, `--ci`, dan `git add`/`commit`/`push` manual) yang harus saya ketik sendiri.
```

</details>

<details>
<summary><b>💡 DIVISI 3 — Prompt Lanjutan Uji Fisik LED WS2812B di RPi (`v1.5.1` Sudah Merged + Panduan Mini PC!)</b></summary>

```text
[KONTEKS TERBARU PROYEK SIKLOTRON DECY-13 — UPDATE v1.5.1 DIVISI 3]
Saya adalah Anggota Divisi 3 (Sistem LED Strip WS2812B) pada proyek Alat Peraga Siklotron DECY-13 (13 MeV H-) di Raspberry Pi 3 Model B+.
Kode saya (`mod_led_ws2812b.py` & `03_test_led_pixel_finder.py` di commit `ac21a27`) sudah **RESMI DI-MERGE ke `main`**, lolos cek virtual (`ALL DIVISI 3 VIRTUAL TESTS PASSED`), dan Tahap A pada `laporan_uji/UJI_DIVISI_3_LED_WS2812B.md` sudah `5/5 [x]` (`DRAFT_PUSH_LAPTOP`).
Catatan penting uji fisik: `03_test_led_pixel_finder.py` hanya menerima `--mode test` dan `--mode finder` (ditambah `--hardware`); di dalam `--mode finder --hardware`, gunakan `Enter` untuk cek piksel `#0..#63`, `s` untuk spiral (`0..47` + RF gap `[11,23,35,47]`), `e` untuk shoot (`48..63`), dan amati apakah urutan warna RGB/GRB sudah benar! Panduan uji dari Mini PC <-> RPi juga tersedia di `decy13_mqtt_kit/PANDUAN_MINI_PC_UJI_LAPANGAN.md`.

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

[TUGAS SEKARANG & KEWAJIBAN TAMPILKAN PERUBAHAN (SHOW CHANGES + TUGAS BARU)]
- Lokasi file pengumuman & tugas baru Divisi 3: `README.md`, `tools/jobdesk_divisi.json` (field `current_announcement` & `current_tasks` Divisi 3), `laporan_uji/JOBDESK_DAN_DOD.md`, dan `laporan_uji/UJI_DIVISI_3_LED_WS2812B.md`.
- Jika kamu **AI IDE/CLI**, jalankan `python tools/raspi_preflight.py --divisi 3 --no-save` & baca file di atas. Jika kamu **AI Web (browser)** tanpa akses lokal, minta saya mem-paste file tersebut lebih dulu.
- Bantu saya menjalankan pengujian fisik di RPi 3B+ (`dtparam=audio=off`, cek urutan piksel 0..63, cek warna RGB/GRB, cek bebas flicker saat LCD SPI0 aktif bersamaan) dan memperbarui `laporan_uji/UJI_DIVISI_3_LED_WS2812B.md`.
- **WAJIB TAMPILKAN 4 BLOK INI KEPADA SAYA SETIAP KALI EKSEKUSI PROMPT / SELESAI EDIT KODE:**
  1. **📢 Pengumuman Ketua & Tugas Baru Divisi 3:** Ringkaskan pengumuman terbaru & daftar tugas baru Divisi 3 saat ini.
  2. **🔍 Show Perubahan Kode (`git status` / `git diff --stat`):** Tunjukkan file apa yang berubah dan baris/logika apa yang ditambah atau diubah.
  3. **🤖 Apa yang Dilakukan oleh AI:** Jelaskan dengan bahasa sederhana apa yang baru saja kamu (AI) kerjakan agar saya paham.
  4. **🧑‍💻 Apa yang Harus Saya (Anggota) Lakukan Sendiri Sekarang:** Berikan langkah uji RPi/laptop (`--ci`) & perintah `git add`/`commit`/`push` manual untuk saya jalankan sendiri.
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

[TUGAS SEKARANG & KEWAJIBAN TAMPILKAN PERUBAHAN (SHOW CHANGES + TUGAS BARU)]
- Lokasi file pengumuman & tugas baru Divisi 4: `README.md`, `tools/jobdesk_divisi.json` (field `current_announcement` & `current_tasks` Divisi 4), `laporan_uji/JOBDESK_DAN_DOD.md`, dan `laporan_uji/UJI_DIVISI_4_LCD_ILI9341.md`.
- Jika kamu **AI IDE/CLI**, jalankan `python tools/raspi_preflight.py --divisi 4 --no-save` & baca file di atas. Jika kamu **AI Web (browser)** tanpa akses lokal, minta saya meng-upload/paste file tersebut dulu sebelum menulis kode (jangan mengarang!), dan beri kode utuh siap copy-paste.
- Pastikan background SPI render thread tetap non-blocking dan aman di Windows tanpa `luma.lcd`, lalu bantu saya menyempurnakan tampilan dashboard 320x240 LCD.
- **WAJIB TAMPILKAN 4 BLOK INI KEPADA SAYA SETIAP KALI EKSEKUSI PROMPT / SELESAI EDIT KODE:**
  1. **📢 Pengumuman Ketua & Tugas Baru Divisi 4:** Ringkaskan pengumuman terbaru & daftar tugas baru Divisi 4 saat ini.
  2. **🔍 Show Perubahan Kode (`git status` / `git diff --stat`):** Tunjukkan file apa yang berubah dan bagian apa yang ditambah/diperbaiki.
  3. **🤖 Apa yang Dilakukan oleh AI:** Jelaskan dengan bahasa sederhana apa yang baru saja kamu (AI) kerjakan agar saya paham.
  4. **🧑‍💻 Apa yang Harus Saya (Anggota) Lakukan Sendiri Sekarang:** Berikan langkah uji (`python tools/cek_integrasi_dan_announcer.py --ci`, tes LCD RPi) & perintah `git add`/`commit`/`push` manual untuk saya jalankan sendiri.
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

[TUGAS SEKARANG & KEWAJIBAN TAMPILKAN PERUBAHAN (SHOW CHANGES + TUGAS BARU)]
- Lokasi file pengumuman & tugas baru Divisi 5: `README.md`, `tools/jobdesk_divisi.json` (field `current_announcement` & `current_tasks` Divisi 5), `laporan_uji/JOBDESK_DAN_DOD.md`, dan `laporan_uji/UJI_DIVISI_5_WEB_HMI.md`.
- Jika kamu **AI IDE/CLI**, jalankan `python tools/raspi_preflight.py --divisi 5 --no-save` & baca file di atas. Jika kamu **AI Web (browser)** tanpa akses lokal, minta saya melampirkan `decy13_mqtt_kit/web_hmi/index.html` serta file pengumuman/konfigurasi di atas lebih dulu agar tidak merusak fungsi yang sudah ada.
- Pertahankan mode State-Driven saat `state.mqttConnected === true`, jaga kesesuaian `setpoint_limits`, dan bantu saya menyempurnakan UI SCADA, grafik, atau simulasi 2D.
- **WAJIB TAMPILKAN 4 BLOK INI KEPADA SAYA SETIAP KALI EKSEKUSI PROMPT / SELESAI EDIT KODE:**
  1. **📢 Pengumuman Ketua & Tugas Baru Divisi 5:** Ringkaskan pengumuman terbaru (termasuk `setpoint_limits`) & daftar tugas baru Divisi 5 saat ini.
  2. **🔍 Show Perubahan Kode (`git status` / `git diff --stat`):** Tunjukkan bagian `web_hmi/index.html` atau file apa yang berubah dan mengapa diubah.
  3. **🤖 Apa yang Dilakukan oleh AI:** Jelaskan dengan bahasa sederhana apa yang baru saja kamu (AI) kerjakan agar saya paham.
  4. **🧑‍💻 Apa yang Harus Saya (Anggota) Lakukan Sendiri Sekarang:** Berikan langkah uji (`python tools/cek_integrasi_dan_announcer.py --ci`, tes browser Mini PC) & perintah `git add`/`commit`/`push` manual untuk saya jalankan sendiri.
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

[TUGAS SEKARANG & KEWAJIBAN TAMPILKAN PERUBAHAN (SHOW CHANGES + TUGAS BARU)]
- Lokasi file pengumuman & tugas baru Divisi 6: `README.md`, `tools/jobdesk_divisi.json` (field `current_announcement` & `current_tasks` Divisi 6), `laporan_uji/JOBDESK_DAN_DOD.md`, dan `laporan_uji/UJI_DIVISI_6_MQTT_QA.md`.
- Jika kamu **AI IDE/CLI**, jalankan `python tools/raspi_preflight.py --divisi 6 --no-save` & baca file di atas. Jika kamu **AI Web (browser)** tanpa akses lokal, minta saya melampirkan `06_test_mqtt_healthcheck.py`, `flows_mqtt_decy13.json`, `04_decy13_mqtt_daemon.py`, dan `UJI_DIVISI_6_MQTT_QA.md` lebih dulu.
- Sesuaikan 3 catatan audit pasca-merge + `setpoint_limits` (`pressure <= 1e-3 mbar` sebelum `SEQ-03` `TOGGLE_INTERLOCK`, `--expected-stages` 6 nilai integer stage daemon `0,1,4,5,6,7`, host broker Node-RED, dan batas `setpoint_limits`), lalu bantu uji langsung ke RPi + Mini PC nyata.
- **WAJIB TAMPILKAN 4 BLOK INI KEPADA SAYA SETIAP KALI EKSEKUSI PROMPT / SELESAI EDIT KODE:**
  1. **📢 Pengumuman Ketua & Tugas Baru Divisi 6:** Ringkaskan pengumuman terbaru & daftar tugas baru Divisi 6 saat ini.
  2. **🔍 Show Perubahan Kode (`git status` / `git diff --stat`):** Tunjukkan file apa yang berubah dan bagian fungsi/logika apa yang ditambah/diperbaiki.
  3. **🤖 Apa yang Dilakukan oleh AI:** Jelaskan dengan bahasa sederhana apa yang baru saja kamu (AI) kerjakan agar saya paham.
  4. **🧑‍💻 Apa yang Harus Saya (Anggota) Lakukan Sendiri Sekarang:** Berikan langkah uji (`python tools/cek_integrasi_dan_announcer.py --ci`, uji QA ke RPi) & perintah `git add`/`commit`/`push` manual untuk saya jalankan sendiri.
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
