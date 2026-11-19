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
| **Versi / Status `main`** | **`v1.5.2` — Progres Terverifikasi `43,8%` (`21/48` ceklis) • Divisi 2 Resmi `LULUS_UJI_FISIK` (`7/7`)! Fokus Uji Fisik LED Divisi 3 & Kejar Branch `hmi+tft`!** |
| **Pengumuman Ketua** | 1. **Divisi 2 Resmi `LULUS_UJI_FISIK` (`4/4` Tahap B, `7/7` Total):** Uji fisik Relay Kipas 12V (`GPIO 21`), Buzzer (`GPIO 17`), serta `cleanup()` pada RPi 3B+ telah diuji bersama seluruh tim (Ketua & PJ Divisi 2 `dzakimumtazi`) dan dilaporkan lulus di grup WhatsApp. *(Butir saklar fisik E-Stop `GPIO 22` dikecualikan/N/A karena tidak ada saklar fisik — fungsi E-Stop dipindah ke HTML Web HMI di Mini PC).*<br>2. **Fokus Uji Fisik Sekarang — Divisi 3 (LED WS2812B `GPIO 18`) & Stasiun Mini PC (`PANDUAN_MINI_PC_UJI_LAPANGAN.md`):** Jalankan `sudo python3 03_test_led_pixel_finder.py --mode finder --hardware` lalu ketik `s` (spiral) & `e` (shoot). Mini PC Windows 8 ruang kontrol cukup `git pull origin main` untuk panduan Ethernet ICS/SSH & **Prompt AGY Mini PC**.<br>3. **Update Branch Lain:** Branch `divisi-6-mqtt-nodered-qa-testing` (`b8605fb` — QA simulasi `11/11 PASS` & route Node-RED `/cyclotron`, CI ✅) **sudah di-merge ke `main`** (`6d3f8f5`). Branch **`origin/hmi+tft` (Divisi 4 & 5)** masih di commit `v1.2` (`045c321`) dan wajib `git merge origin/main`!<br>4. **Tetap Berlaku (`v1.5`):** Validasi `setpoint_limits` di `config_hardware.json` (`magnet_a` `[400..2200]`, `rf_mhz` `[15..30]`, `rf_kv` `[0..120]`, `beam_ua` `[0..100]`) dan cek OS RPi via `bash tools/raspi_bootstrap.sh` + `python3 tools/raspi_preflight.py --divisi <1..6>`. |
| **Cara Tarik Update Terbaru** | **GitHub Desktop:** Pastikan di branch divisimu → klik *Fetch origin* → menu *Branch* → *Update from main*.<br>**Terminal / Git Bash:** `git fetch origin` lalu `git merge origin/main` *(di Mini PC/RPi cukup `git checkout main && git pull origin main`)* |

---

## 📊 Progres Nyata Proyek & Tabel Rapor 6 Divisi

> **📈 Posisi Progres Nyata Proyek Saat Ini (Terukur dari 6 Kartu [`laporan_uji/`](laporan_uji/README.md)):**
> - **Progres Total Terverifikasi (`Tahap A + Tahap B`):** **`43,8%` (`21 / 48` butir ceklis)** `[████░░░░░░]`
> - **Tahap A — Kesiapan Kode & Simulasi Laptop:** **`63,6%` (`14 / 22` butir)** *(Divisi 1, 2, 3, 6 sudah `100%` Tahap A; Divisi 4 & 5 masih `0/4` di kartu)*
> - **Tahap B — Uji Fisik Alat Nyata (RPi 3B+ & Mini PC):** **`26,9%` (`7 / 26` butir)** *(Divisi 2 sudah `4/4` lulus uji fisik RPi; Divisi 1 `3/5` bare-board Core RPi; Divisi 3–6 belum selesai uji alat nyata)*
>
> **🧭 Posisi Milestone (`M1` s.d. `M5` — lihat [`JOBDESK_DAN_DOD.md`](laporan_uji/JOBDESK_DAN_DOD.md)):**
> - **M1** *(Bootstrap, Preflight & Bare-Board RPi)*: ✅ **Tercapai di unit `sp-aksel`** (`4.97 Hz`, 0 packet drop; tinggal kestabilan daya/jaringan unit uji lab)
> - **M2** *(Uji Isolasi Fisik Aktuator `01`, `02`, `03`)*: 🔄 **~33%** *(Divisi 2 `01_test_relay_buzzer.py` & aktuator fisik `GPIO 21`/`17` selesai `LULUS_UJI_FISIK`; LED Divisi 3 mulai uji fisik; LCD Divisi 4 belum mulai)*
> - **M3** *(Integrasi Penuh Daemon + Divisi 2, 3, 4 serentak di RPi)*: ⏳ **0%** *(menunggu M2 LED Divisi 3 & update LCD Divisi 4)*
> - **M4** *(Integrasi Mini PC Web HMI & QA Healthcheck)*: 🔄 **~25%** *(simulasi Divisi 6 `11/11 PASS` & route `/cyclotron` sudah ter-merge `6d3f8f5`, tetapi kartu Tahap B Divisi 5 & 6 masih `0/4`)*
> - **M5** *(Commissioning Final & 6/6 Kartu `LULUS_UJI_FISIK`)*: ⏳ **0%** *(1/6 kartu lulus penuh: Divisi 2)*

Setiap anggota yang melakukan `git push` akan diperiksa oleh **Satpam Otomatis (GitHub Actions)** (tanda ✅/❌) dan direview oleh Ketua sebelum di-*merge* ke `main`.

| Divisi | Penanggung Jawab | Branch Wajib | File Eksklusif (Boleh Diedit) | Status Audit Kode / CI | Status Uji Hardware RPi & Progres Kartu |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Divisi 1 (Ketua)** | `azfaaksan-hub` | `main` / `core-raspi-backend` | `04_decy13_mqtt_daemon.py`, `05_laptop_dryrun_simulator.py`, `config_hardware.json`, `modules/base_module.py`, `tools/*`, `laporan_uji/UJI_DIVISI_1_CORE_RASPI.md` | ✅ **Core Aktif** *(`setpoint_limits`, `connect_async`, `SIGTERM`, bootstrap & preflight siap)* | 🟡 [`DRAFT_PUSH_LAPTOP`](laporan_uji/UJI_DIVISI_1_CORE_RASPI.md) **`75%` (`6/8`)** *(3/3 Laptop, **3/5 RPi bare-board** `192.168.137.66`)* |
| **Divisi 2** | `dzakimumtazi` | `divisi-2-vacum-safety` | `decy13_mqtt_kit/raspi_cli/modules/mod_vacuum_safety.py`, `01_test_relay_buzzer.py`, `laporan_uji/UJI_DIVISI_2_VAKUM_SAFETY.md` | ✅ **Merged ke `main`** *(siap integrasi M3)* | 🟢 [`LULUS_UJI_FISIK`](laporan_uji/UJI_DIVISI_2_VAKUM_SAFETY.md) **`100%` (`7/7`)** *(3/3 Laptop, **4/4 RPi fisik** bersama tim; E-Stop via Web HMI HTML — tanpa saklar fisik `GPIO 22`)* |
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

## ⚡ Rangkaian Keseluruhan (Full Wiring Integration) & Audit Anti-Tabrakan I/O

### 🔍 Apakah I/O Saling Tabrakan Ketika Semua Wiring Disatukan?
**Jawabannya: TIDAK TABRAKAN (`0` Konflik Pin GPIO & `0` Konflik Bus Periferal).**
Seluruh modul perangkat keras dari **Divisi 2, Divisi 3, dan Divisi 4** telah dirancang agar dapat dipasang dan dijalankan **serentak** pada satu unit **Raspberry Pi 3 Model B+** oleh `04_decy13_mqtt_daemon.py`:

1. **Bebas Tabrakan Pin Fisik & GPIO (BCM):**
   - **Divisi 2 (Vakum & Safety):** memakai `GPIO 17` (`Pin 11`), `GPIO 21` (`Pin 40`), dan reservasi `GPIO 22` (`Pin 15`).
   - **Divisi 3 (LED WS2812B):** memakai `GPIO 18` (`Pin 12`).
   - **Divisi 4 (LCD TFT ILI9341):** memakai `GPIO 8` (`Pin 24`), `GPIO 10` (`Pin 19`), `GPIO 11` (`Pin 23`), `GPIO 24` (`Pin 18`), `GPIO 25` (`Pin 22`), serta reservasi `SPI0 MISO` pada `GPIO 9` (`Pin 21`).
   - **Pin Daya & Ground (`GND`):** Header 40-pin RPi 3B+ menyediakan **2 pin `3.3V`**, **2 pin `5V`**, dan **8 pin `GND`**, sehingga kabel tiap divisi mendapat pin header masing-masing tanpa menumpuk di satu lubang pin.
2. **Bebas Tabrakan Bus Internal SoC (`PWM0/DMA10` vs `Hardware SPI0`):**
   - **LED Strip WS2812B (Divisi 3)** digerakkan oleh **`PWM0` + `DMA Channel 10`** (`rpi_ws281x`, `800 kHz`) pada `GPIO 18` — **bukan** lewat bus SPI.
   - **Layar LCD ILI9341 (Divisi 4)** digerakkan oleh **`Hardware SPI0`** (`luma.lcd`, `16 MHz`) pada `GPIO 8/10/11` + kontrol `GPIO 24/25`.
   - **Potensi Konflik Audio Onboard Sudah Ditutup:** Secara bawaan, audio analog RPi (`snd_bcm2835`) memakai jalur `PWM0` yang sama dengan `GPIO 18`. Skrip `bash tools/raspi_bootstrap.sh` otomatis mengeset **`dtparam=audio=off`** dan **`dtparam=spi=on`** di `/boot/config.txt` (`/boot/firmware/config.txt`), sehingga jalur `PWM0/DMA10` murni eksklusif untuk LED WS2812B (bebas *flicker*).
3. **Bebas Tabrakan Loop & Threading (*Non-Blocking*):**
   - Loop utama Core Daemon (`5 Hz` / `200 ms`), *worker thread* animasi LED (`40 FPS` / `25 ms`), dan *worker thread* render SPI LCD (`~4 FPS` / `250 ms` dengan *dirty-signature check*) berjalan paralel menggunakan `threading.Lock()` tanpa saling memblokir.

---

### 🗺️ Skema Rangkaian Keseluruhan Sistem DECY-13 (6 Divisi)

```text
+======================================================================================+
|                    MINI PC RUANG KONTROL (DIVISI 5 & DIVISI 6)                       |
|  - Web HMI SCADA & Simulator 2D (Browser -> ws://192.168.137.1:9001)                 |
|  - Tombol E-Stop Operasional (HTML EMERGENCY_STOP -> decy13/hmi/cmd)                 |
|  - Dashboard Node-RED (/cyclotron) & QA Healthcheck (tcp://192.168.137.1:1883)       |
+==========================================+===========================================+
                                           |
                        LAN Ethernet (ICS) / Wi-Fi Lokal
                   MQTT TCP :1883  &  MQTT over WebSocket :9001
                                           |
+==========================================v===========================================+
|                RASPBERRY PI 3 MODEL B+ — CORE BACKEND (DIVISI 1)                     |
|         Mosquitto Broker + 04_decy13_mqtt_daemon.py (State & Physics Loop 5 Hz)      |
|             Konfigurasi OS: dtparam=audio=off  |  dtparam=spi=on                     |
+-----------------------+--------------------------+-----------------------------------+
                        |                          |
        +---------------+                          +-------------------+
        |                                                              |
        v (GPIO Digital: RPi.GPIO)             (PWM0 + DMA10: 800kHz)  v
+-------+--------------------------------+   +-------------------------+---------------+
|   DIVISI 2: VAKUM, BUZZER & SAFETY     |   |   DIVISI 3: LED STRIP WS2812B (64 LED)  |
|                                        |   |                                         |
| - Pin 11 (GPIO 17) --> (+) Buzzer      |   | - Pin 12 (GPIO 18) --[R 330-470 Ohm]--+ |
| - Pin 09 (GND)     --> (-) Buzzer      |   |                                       v |
|                                        |   |   DIN Strip WS2812B (#0..#47 Spiral,    |
| - Pin 02 (5V)      --> VCC Modul Relay |   |   RF Gap [11,23,35,47], #48..#63 Shoot) |
| - Pin 40 (GPIO 21) --> IN Relay        |   |                                         |
|                        (Active-LOW)    |   | - PSU Eksternal 5V 3A:                  |
| - Pin 39 (GND)     --> GND Modul Relay |   |   (+) 5V  --> VCC (5V) LED Strip        |
|                                        |   |   (-) GND --> GND LED Strip             |
|   [Sisi Kontak Saklar Relay Terisolasi]|   |               + Pin 06 (GND RPi)        |
|   Adaptor 12V (+) ---> COM Relay       |   |               (WAJIB COMMON GROUND!)    |
|   Kipas 12V   (+) <--- NO  Relay       |   +-----------------------------------------+
|   Kipas 12V   (-) ---> Adaptor 12V (-) |
|                                        |             (Hardware SPI0: 16 MHz)
| - Pin 15 (GPIO 22) & Pin 14 (GND):     |   +-----------------------------------------+
|   Reservasi E-Stop Fisik (Pull-Up;     |   |   DIVISI 4: LCD TFT SPI ILI9341 320x240 |
|   N/A karena E-Stop via Web HMI HTML)  |   |                                         |
+----------------------------------------+   | - Pin 17 (3.3V)    --> VCC LCD          |
                                             |                    --> LED Backlight    |
                                             |                        (via R 100 Ohm)  |
                                             | - Pin 20 (GND)     --> GND LCD          |
                                             | - Pin 24 (GPIO 8)  --> CS  (SPI0 CE0)   |
                                             | - Pin 19 (GPIO 10) --> SDI/MOSI (SPI0)  |
                                             | - Pin 23 (GPIO 11) --> SCK/SCLK (SPI0)  |
                                             | - Pin 18 (GPIO 24) --> DC / RS          |
                                             | - Pin 22 (GPIO 25) --> RESET            |
                                             | - Pin 21 (GPIO 9)  --> SDO/MISO (Ops.)  |
                                             +-----------------------------------------+
```

---

### 📌 Peta Distribusi 40-Pin Header Raspberry Pi 3B+ (Semua Divisi Terpasang)

Setiap pin daya (`3.3V`/`5V`), `GND`, dan `GPIO` di bawah ini sudah dibagi agar **tidak ada dua modul yang berebut pin fisik yang sama**:

```text
                     RASPBERRY PI 3B+ (40-PIN HEADER)
            Sisi Kiri (Pin Ganjil)      Sisi Kanan (Pin Genap)
            ----------------------      ----------------------
               (Cadangan) 3.3V [01] || [02] 5V  ---> [DIV 2] VCC Modul Relay Kipas
             (I2C1 SDA) GPIO 2 [03] || [04] 5V  ---> (Cadangan / Jangan bebani 64 LED!)
             (I2C1 SCL) GPIO 3 [05] || [06] GND ---> [DIV 3] Common GND LED & PSU 5V 3A
                        GPIO 4 [07] || [08] GPIO 14 (UART TXD)
  [DIV 2] (-) Buzzer <---  GND [09] || [10] GPIO 15 (UART RXD)
  [DIV 2] (+) Buzzer <- GPIO17 [11] || [12] GPIO 18 ---> [DIV 3] LED WS2812B DIN (via R 330-470Ω)
                       GPIO 27 [13] || [14] GND     ---> [DIV 2] Reservasi COM E-Stop
  [DIV 2] (Res. E-Stop) GPIO22 [15] || [16] GPIO 23
  [DIV 4] VCC & BL LCD <- 3.3V [17] || [18] GPIO 24 ---> [DIV 4] LCD DC (Data/Command)
  [DIV 4] LCD MOSI <--- GPIO10 [19] || [20] GND     ---> [DIV 4] GND Layar LCD ILI9341
  [DIV 4] (MISO Ops.) <- GPIO9 [21] || [22] GPIO 25 ---> [DIV 4] LCD RST (Reset)
  [DIV 4] LCD SCLK <--- GPIO11 [23] || [24] GPIO 8  ---> [DIV 4] LCD CS (SPI0 CE0)
               (Cadangan)  GND [25] || [26] GPIO 7  (SPI0 CE1 - Bebas)
             (ID_SD)    GPIO 0 [27] || [28] GPIO 1  (ID_SC)
                        GPIO 5 [29] || [30] GND     (Cadangan)
                        GPIO 6 [31] || [32] GPIO 12
                       GPIO 13 [33] || [34] GND     (Cadangan)
                       GPIO 19 [35] || [36] GPIO 16
                       GPIO 26 [37] || [38] GPIO 20
  [DIV 2] GND Relay  <---  GND [39] || [40] GPIO 21 ---> [DIV 2] IN Relay Kipas 12V (Active-LOW)
```

---

### 📋 Tabel Master Pemetaan Pin & Audit Konflik Seluruh Divisi (`config_hardware.json`)

| Divisi | Komponen & Sinyal | GPIO (BCM) | Pin Fisik RPi | Pasangan Daya & Pin `GND` | Bus / Periferal SoC | Status Audit Konflik |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| **Divisi 2** | **Buzzer SFM-27 (`+`)** | `GPIO 17` | **Pin `11`** | `GND` di **Pin `09`** | Digital Output (`Active-HIGH`) | ✅ **Aman** (Eksklusif Divisi 2) |
| **Divisi 2** | **IN Modul Relay Kipas 12V** | `GPIO 21` | **Pin `40`** | `VCC 5V` di **Pin `02`**, `GND` di **Pin `39`** *(Kontak `COM`/`NO` ke PSU `12V` Kipas)* | Digital Output (`Active-LOW`, `initial=HIGH`) | ✅ **Aman** (Eksklusif Divisi 2; jalur `12V` terisolasi kontak relay) |
| **Divisi 2** | **Reservasi Tombol E-Stop** | `GPIO 22` | **Pin `15`** | `GND` di **Pin `14`** *(Tidak dipasang fisik; E-Stop via Web HMI HTML)* | Digital Input (`PUD_UP` internal pull-up) | ✅ **Aman** (Idle `HIGH`, tidak memicu interupsi palsu) |
| **Divisi 3** | **Data IN (`DIN`) 64 LED WS2812B** | `GPIO 18` | **Pin `12`** *(via R `330–470 Ω`)* | `VCC 5V` dari **PSU Eksternal `5V 3A`**, `Common GND` di **Pin `06`** | **`PWM0` + `DMA Ch. 10`** (`800 kHz`, `rpi_ws281x`) | ✅ **Aman** (Tidak memakai SPI; wajib `dtparam=audio=off`) |
| **Divisi 4** | **LCD `CS` (Chip Select)** | `GPIO 8` | **Pin `24`** | `VCC 3.3V` di **Pin `17`**, `GND` di **Pin `20`** | **Hardware `SPI0 CE0`** (`16 MHz`, `luma.lcd`) | ✅ **Aman** (Bus `SPI0` terpisah dari `PWM0` LED) |
| **Divisi 4** | **LCD `SDI / MOSI` (Data SPI)** | `GPIO 10` | **Pin `19`** | *(Sama dengan atas)* | **Hardware `SPI0 MOSI`** (`16 MHz`) | ✅ **Aman** (Eksklusif `SPI0`) |
| **Divisi 4** | **LCD `SCK / SCLK` (Clock SPI)** | `GPIO 11` | **Pin `23`** | *(Sama dengan atas)* | **Hardware `SPI0 SCLK`** (`16 MHz`) | ✅ **Aman** (Eksklusif `SPI0`) |
| **Divisi 4** | **LCD `DC / RS` (Data/Cmd)** | `GPIO 24` | **Pin `18`** | *(Sama dengan atas)* | Digital Output (`luma.lcd`) | ✅ **Aman** (Eksklusif Divisi 4) |
| **Divisi 4** | **LCD `RESET`** | `GPIO 25` | **Pin `22`** | *(Sama dengan atas)* | Digital Output (`luma.lcd`) | ✅ **Aman** (Eksklusif Divisi 4) |
| **Divisi 4** | **LCD `SDO / MISO` *(Opsional)*** | `GPIO 9` | **Pin `21`** | *(Sama dengan atas)* | **Hardware `SPI0 MISO`** | ✅ **Aman** (Tidak dipakai divisi lain) |

---

### ⚠️ 4 Aturan Keselamatan Elektrik Saat Semua Wiring Disatukan (`Milestone M3`)
1. **Wajib *Common Ground* (`GND` RPi ↔ `GND` PSU 5V LED):** Hubungkan kutub **`(-)` PSU Eksternal 5V 3A** ke **`GND` LED Strip** sekaligus ke **Pin Fisik `06` (`GND` RPi)**. Tanpa *common ground*, sinyal data `3.3V` dari `GPIO 18` (`Pin 12`) akan mengambang (*floating*) dan menyebabkan LED berkedip acak (*flicker*).
2. **Jangan Cabang `+5V` PSU Eksternal ke Pin `5V` RPi:** Kutub **`(+)` PSU Eksternal 5V 3A** hanya dihubungkan ke **`VCC (5V)` LED Strip WS2812B** (jangan disambung ke `Pin 02` atau `Pin 04` RPi apabila RPi sudah mendapat daya dari adaptor Micro-USB sendiri, agar dua regulator 5V tidak saling bertabrakan).
3. **Isolasi Tegangan `+12V` Kipas Vakum:** Tegangan `+12V` dari adaptor kipas **hanya boleh masuk ke terminal saklar `COM` dan `NO` pada modul relay** (sisi tegangan tinggi). Jangan pernah menghubungkan jalur `12V` ke pin header RPi.
4. **Pastikan `dtparam=audio=off` & `dtparam=spi=on` Aktif Sebelum Uji Serentak:** Jalankan `python3 tools/raspi_preflight.py --divisi 1` di RPi untuk memastikan `/dev/spidev0.0` aktif dan modul audio analog tidak merebut `PWM0` (`GPIO 18`) saat `sudo python3 04_decy13_mqtt_daemon.py` dijalankan.

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
[KONTEKS TERBARU PROYEK SIKLOTRON DECY-13 — UPDATE v1.5.2]
Saya adalah Anggota Divisi 2 (Sistem Vakum & Buzzer Indikator) pada repo `sp-aksel-polteknuklir`.
Status kode saya di branch `divisi-2-vacum-safety` sudah **RESMI DI-MERGE ke `main`** dan kartu `laporan_uji/UJI_DIVISI_2_VAKUM_SAFETY.md` kini berstatus **`LULUS_UJI_FISIK` (`7/7`: `3/3` Tahap A, `4/4` Tahap B)** setelah diuji langsung oleh seluruh tim (Ketua & PJ Divisi 2).
Catatan desain: **tidak ada saklar E-Stop fisik (`GPIO 22`)** yang dipasang — fungsi Emergency Stop dijalankan melalui tombol HTML Web HMI di Mini PC.
Fokus berikutnya adalah mendampingi uji integrasi penuh M3 (`04_decy13_mqtt_daemon.py` bersama LED Divisi 3 & LCD Divisi 4) setelah menyinkronkan branch ke `main`.

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
