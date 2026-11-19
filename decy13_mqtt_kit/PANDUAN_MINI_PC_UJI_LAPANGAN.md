# Panduan Stasiun Uji Lapangan (`v1.6`) — Mini PC Ruang Kontrol & Raspberry Pi 3B+

Dokumen ini khusus dibuat untuk **Mini PC Ruang Kontrol** (Windows 8 / 10 / 11) yang terhubung langsung ke **Raspberry Pi 3B+** saat pengujian & operasional penuh alat peraga **Siklotron DECY-13 (`v1.6`)**, agar sesi **Antigravity (AGY)** di Mini PC langsung memahami kondisi arsitektur terbaru tanpa riwayat chat laptop utama.

---

## 1. Pembagian Peran 3 Mesin (Bebas Konflik Git)

| Mesin | Peran Resmi | Branch | File yang BOLEH Diubah | File yang DILARANG Diubah Langsung |
| :--- | :--- | :---: | :--- | :--- |
| **Laptop Utama Ketua** (`azfaaksan-hub`) | Pusat integrasi, review branch, & pembaruan dokumen tim | `main` | `README.md`, `tools/*`, `04_decy13_mqtt_daemon.py`, `config_hardware.json`, `UJI_DIVISI_1_CORE_RASPI.md` | File eksklusif Divisi 2–6 tanpa review |
| **Mini PC Ruang Kontrol** (`Windows 8/10/11`) | **Stasiun Uji Web HMI Offline, Node-RED, QA Healthcheck, & Terminal SSH ke RPi** | `main` *(hanya `git pull --ff-only origin main`)* | Log/bukti lapangan di `laporan_uji/bukti/` (bila perlu) | **Semua file kode Divisi 2–6** (`mod_*.py`, `01/02/03/06_*.py`, `AKSEL-DECY13/*`, `web_hmi/index.html`, `UJI_DIVISI_2..6_*.md`) |
| **Raspberry Pi 3B+** | **Stasiun Eksekusi Core Daemon + Hub USB 3-TFT + Broker Mosquitto** | `main` *(hanya `git pull --ff-only origin main`)* | Konfigurasi OS lokal RPi (`/boot/...`, `/etc/mosquitto/...`, `/etc/udev/...`) | Jangan edit kode Python/HTML lokal di RPi tanpa koordinasi branch |

---

## 2. Status Proyek Terkini (`v1.6` — Commit `18c2603`, Progres `54,2%` / `26/48`)

- **Branch `main` aktif (`v1.6` @ `18c2603`):**
  1. **Divisi 2 (`LULUS_UJI_FISIK`, `7/7`):** Relay Kipas 12V (`GPIO 21`, Active-LOW), Buzzer SFM-27 (`GPIO 17`, Active-HIGH), & `cleanup()` lulus uji fisik bersama tim; E-Stop dijalankan lewat tombol **`EMERGENCY_STOP` HTML Web HMI di Mini PC** *(saklar fisik `GPIO 22` berstatus N/A)*.
  2. **Divisi 3 (`0db6f3b` & `18c2603`, `10/10` ceklis):** Uji isolasi **448 LED WS2812B** (`0..399` spiral 400 LED, `400..447` extraction/beam 48 LED) kini memakai default **`--brightness 10`**, kunci pengaman **`--power-ok`** untuk tes ALL ON/RGB, mode otomatis **`--auto`**, serta integrasi **Buzzer Bersama `GPIO 17`** (`--buzzer-pin 17` / `--no-buzzer`) yang berbunyi `1..9x` per tahap uji LED dan menjalankan `GPIO.cleanup(17)` saat keluar *(status kartu `DRAFT_PUSH_LAPTOP`, menunggu uji serentak bersama daemon asli & sinkronisasi `config_hardware.json` dari `64` ke `448` LED setelah PSU diverifikasi)*.
  3. **Divisi 4 (`207ac04` — 3-LCD TFT Arduino Uno via USB Hub):** `AKSEL-DECY13/raspi/accelerator_hub.py` menyatukan 3 Uno + 3 Shield TFT `MCUFRIEND 320x240` (`/dev/arduino_hmi|sensor|actuator`, `115200 baud`) ke Mosquitto lewat topik **`decy13/usb/state`**, **`decy13/usb/cmd`**, & **`decy13/usb/ack`** (**0 konflik** dengan pin GPIO `17/18/21` RPi!). *(Catatan daya: gunakan **Powered USB Hub 5V >= 2A** untuk 3 Uno + TFT, dan kosongkan slot microSD Uno 2 & 3.)*
  4. **Divisi 5 (`6d37d99` + `usb-panel.js`):** Web HMI (`decy13_mqtt_kit/web_hmi/`) kini **100% Offline** (CSS `console.css`, `mqtt.min.js`, & `usb-panel.js` lokal — tidak perlu internet di ruang kontrol!).
  5. **Divisi 6 (`087e0fb` / `d929400`):** Handover QA komunikasi PC ↔ RPi 3 selesai (`300/300 ONLINE @ 4.99 Hz`, `22/22` field PASS, flow Node-RED `/cyclotron`, `/cyclotron-qa`, `qa_readonly_api.ps1`), ditambah tab opsional `AKSEL-DECY13/raspi/nodered_usb.json` `/api/usb/status`.

---

## 3. Pengaturan Koneksi Mini PC Windows 8 <-> Raspberry Pi

Karena Mini PC memakai **Windows 8**, perhatikan 5 hal khusus ini:
1. **Jangan memakai `.local`** (`sp-aksel.local` / `raspberrypi.local`) karena Windows 8 tidak mendukung resolver mDNS secara bawaan. **Selalu pakai IP angka RPi** (misal `192.168.137.xxx`).
2. **Jangan memakai `ssh` di CMD/PowerShell standar** jika Windows 8 tidak punya OpenSSH Client — gunakan **Git Bash** (klik kanan folder repo → *Open Git Bash here*) atau **PuTTY**.
3. **Jika memakai kabel LAN langsung (Ethernet berstatus *Unidentified network*):**
   - **Cara terbaik (jika Mini PC terhubung Wi-Fi):** buka `Win + R` → `ncpa.cpl` → klik kanan **Wi-Fi** → **Properties** → tab **Sharing** → centang *"Allow other network users..."* → pilih **Ethernet** → **OK**. Windows otomatis mengeset Ethernet ke `192.168.137.1`. Cabut-colok kabel LAN RPi, tunggu 30 detik, lalu cek IP RPi lewat `arp -a` di CMD (`192.168.137.xxx`).
   - **Jika Mini PC tidak punya Wi-Fi:** pakai **Hotspot HP 2.4 GHz (WPA2)** untuk menyambungkan keduanya, atau set IP statik sekelas (mis. Mini PC `192.168.50.1`, RPi `192.168.50.2`).
4. **Jika SSH muncul `REMOTE HOST IDENTIFICATION HAS CHANGED` / `Host key verification failed`:**
   Jalankan di Git Bash Mini PC:
   ```bash
   ssh-keygen -R <IP_RASPI>
   ssh <username_rpi>@<IP_RASPI>
   ```
5. **Browser & Python di Windows 8:**
   - Buka Web HMI dengan **Chrome / Edge versi 109** atau **Firefox 115 ESR** (bukan Internet Explorer). Karena **`web_hmi/` sekarang 100% offline** (`assets/console.css`, `assets/mqtt.min.js`, `assets/usb-panel.js`), ruang kontrol **tidak lagi bergantung pada internet/CDN**.
   - Jika menjalankan skrip Python QA di Mini PC Win 8, gunakan Python **3.8–3.10** + `pip install paho-mqtt`.

### Mode 100% Wi-Fi Auto-Link (Tanpa Kabel Ethernet — Anti Raspi Mati/Drop Daya)
Jika penggunaan kabel Ethernet (`eth0` chip LAN7515) menyebabkan Raspberry Pi 3B+ mengalami *under-voltage* (*brown-out* / mati setelah beberapa saat), **cabut kabel Ethernet** dan gunakan sistem **Auto-Link 100% Wi-Fi**:
1. **Pasang sekali di Raspberry Pi 3B+:**
   ```bash
   cd ~/decy13   # atau ~/sp-aksel-polteknuklir
   git checkout main && git pull --ff-only origin main
   bash tools/raspi_bootstrap.sh --install-service --install-autolink --disable-eth
   ```
   Perintah ini otomatis menonaktifkan `eth0` (hemat daya), mengaktifkan `decy13.service` (`04_decy13_mqtt_daemon.py` auto-start saat boot), dan mengaktifkan **`decy13-autolink.service`** ([`tools/raspi_auto_link.py`](../tools/raspi_auto_link.py)) yang otomatis melaporkan IP Wi-Fi & kesehatan tegangan RPi (`vcgencmd get_throttled`) ke Mini PC.
2. **Jalankan Pusat Kendali di PowerShell Mini PC (tanpa perlu cari/ketik IP Raspi lagi):**
   ```powershell
   python tools/minipc_control_hub.py
   ```
   Skrip [`tools/minipc_control_hub.py`](../tools/minipc_control_hub.py) otomatis menemukan IP Wi-Fi Raspi (`UDP 51313` + fallback *TCP Subnet Scan*) dan menyediakan menu:
   - `[1]` Buka Terminal SSH Raspi otomatis
   - `[2]` Auto-Setup / Restart Daemon Raspi & matikan `eth0`
   - `[3]` Start / Restart Hub 3-TFT Arduino Uno (`accelerator_hub.py`)
   - `[4]` Tambah / Simpan Wi-Fi baru di Raspi langsung dari Mini PC
   - `[5]` Buka Web HMI Offline (`http://127.0.0.1:8000`, anti error 404) + **Auto-Copy `ws://<IP_RASPI>:9001` ke Clipboard**
   - `[6]` Jalankan QA Healthcheck (`06_test_mqtt_healthcheck.py`)

---

## 4. Penyatuan Sambungan Divisi 6 (`qa_divisi6`) dengan Divisi 1–5 (`v1.6`)

Di [`decy13_mqtt_kit/qa_divisi6/PANDUAN_KETUA_UJI_ULANG.md`](qa_divisi6/PANDUAN_KETUA_UJI_ULANG.md), **Divisi 6** mendokumentasikan arsitektur khusus **Audit Simulasi PC ↔ RPi**:
- Mosquitto Windows Service berjalan di Mini PC (`1883` berautentikasi, **tanpa** WebSocket `9001` & dengan `POST /api/control` Node-RED berstatus **Disabled**), RPi memakai Reverse SSH Tunnel `-R 127.0.0.1:1884:<IP_PC>:1883` untuk `decy13_simulator_divisi6.py`, serta Uji C Stage 0–7 memakai broker loopback `127.0.0.1:1885` dan tunnel `-L 127.0.0.1:1886:127.0.0.1:1885` ke `/cyclotron-qa`.

Untuk **Operasional Penuh 6 Divisi** (menyalakan alat fisik `04_decy13_mqtt_daemon.py` + `accelerator_hub.py` + Web HMI Offline + Node-RED secara serentak):
1. **Matikan sementara Mosquitto Windows Service di Mini PC** (`Stop-Service mosquitto` bila terpasang). Alasannya: `config_hardware.json` mengarah ke `192.168.137.1:1883` (IP ICS Mini PC). Jika Mosquitto PC aktif (apalagi berautentikasi), `04_decy13_mqtt_daemon.py` akan terkoneksi ke PC dan gagal terautentikasi atau terpisah dari `accelerator_hub.py`. Saat Mosquitto PC dimatikan, `04_decy13_mqtt_daemon.py` otomatis melakukan **Auto-Fallback ke `127.0.0.1:1883` di RPi** (yang sudah dipasangi TCP `1883` + WebSocket `9001` oleh `bash tools/raspi_bootstrap.sh`), menyatu dengan `accelerator_hub.py --mqtt-host 127.0.0.1`.
2. **Aktifkan `POST /api/control` di Node-RED HANYA bila ingin mengontrol alat dari `/cyclotron`** (dan biarkan **Disabled** bila Node-RED + `qa_readonly_api.ps1` hanya dipakai memantau sementara tombol kontrol dijalankan lewat Web HMI Offline `http://localhost:8000`).
3. **Dua cara menyambungkan Node-RED Divisi 6 di Mini PC ke Broker RPi:**
   - **Cara A (Langsung):** Di editor Node-RED (`http://127.0.0.1:1880`), ubah host node broker `"Local Mosquitto Broker"` pada `flows_mqtt_decy13.json` (dan `nodered_usb.json`) dari `localhost` ke **`<IP_RASPI>`** port `1883`, lalu Deploy.
   - **Cara B (SSH Local Port Forward tanpa ubah flow `localhost`):** Setelah `Stop-Service mosquitto`, buka 1 terminal tunnel di Mini PC: `ssh -N -L 127.0.0.1:1883:127.0.0.1:1883 <username_rpi>@<IP_RASPI>`, maka Node-RED dengan broker `localhost:1883` langsung terhubung ke RPi dan `qa_readonly_api.ps1` siap membaca `http://127.0.0.1:1880/api/status`.

---

## 5. Alur Eksekusi Full Setup Mini PC ↔ Raspberry Pi (`v1.6`)

### A. Di Sisi Mini PC (Windows 8 / 10 / 11)
1. **Tarik update Git terbaru sebelum mulai uji:**
   ```bash
   git checkout main
   git pull --ff-only origin main
   ```
2. **Matikan broker Mosquitto Windows sementara** di Mini PC agar `04_decy13_mqtt_daemon.py` & `accelerator_hub.py` menyatu di broker RPi (`1883` / `9001`):
   ```powershell
   Stop-Service mosquitto -ErrorAction SilentlyContinue
   ```
3. **Jalankan HTTP Server Lokal untuk Web HMI 100% Offline (JANGAN edit `web_hmi/index.html`):**
   ```bash
   python -m http.server 8000 --directory decy13_mqtt_kit/web_hmi
   ```
   Lalu buka browser Chrome / Edge ke **`http://localhost:8000`**.
4. **Sambungkan ke Broker RPi lewat UI browser:**
   - Ubah kotak **WebSocket URL Endpoint** dari default `ws://127.0.0.1:9001` menjadi **`ws://<IP_RASPI>:9001`** → klik **Hubungkan MQTT**.
   - Pastikan badge di atas berubah hijau **`MQTT TERHUBUNG`** dan **Panel tiga TFT · USB Raspberry Pi** di bawah header menampilkan status `TFT 1..3`.
5. **Node-RED & QA Divisi 6 dari Mini PC:**
   - Buka Node-RED (`http://127.0.0.1:1880`), pastikan `flows_mqtt_decy13.json` (`/cyclotron` & `/api/status`) dan opsional `AKSEL-DECY13/raspi/nodered_usb.json` (`/api/usb/status`) mengarah ke `<IP_RASPI>:1883` (atau `127.0.0.1:1883` via SSH forward `-L 127.0.0.1:1883:127.0.0.1:1883`).
   - Cek QA read-only 30/300 sampel lewat API Node-RED:
     ```powershell
     cd .\decy13_mqtt_kit\qa_divisi6\scripts
     .\qa_readonly_api.ps1 -Samples 30
     ```
   - *(Opsional tes CLI QA ke broker RPi):*
     ```powershell
     python decy13_mqtt_kit/raspi_cli/06_test_mqtt_healthcheck.py --host <IP_RASPI> --duration 10 --no-menu
     ```

### B. Di Sisi Raspberry Pi 3B+ (via 2 Tab Git Bash / PowerShell SSH dari Mini PC)
1. **Pastikan RPi sinkron di `main` `v1.6` (`18c2603`+) & lolos Bootstrap/Preflight:**
   ```bash
   cd ~/sp-aksel-polteknuklir
   git checkout main && git pull --ff-only origin main
   hostname -I
   bash tools/raspi_bootstrap.sh   # wajib 1x di RPi baru (Audio OFF, SPI ON, Mosquitto 1883/9001)
   # Jika diminta reboot oleh bootstrap: sudo reboot
   python3 tools/raspi_preflight.py --divisi 1
   ```
2. **Terminal SSH 1 (Core Daemon Siklotron + Relay/Buzzer Divisi 2 + LED WS2812B Divisi 3):**
   ```bash
   cd ~/sp-aksel-polteknuklir/decy13_mqtt_kit/raspi_cli
   sudo python3 04_decy13_mqtt_daemon.py
   ```
   Pastikan status modul mencetak `[HARDWARE AKTIF]` dan `[Auto-Fallback] ... -> 127.0.0.1:1883` (`rc=0`).
3. **Terminal SSH 2 (Hub USB 3 Arduino Uno + 3 Shield TFT Divisi 4):**
   *(Hubungkan ketiga Arduino Uno ke **Powered USB Hub 5V >= 2A** yang dicolok ke USB-A RPi; kosongkan slot microSD Uno 2 & Uno 3.)*
   ```bash
   cd ~/sp-aksel-polteknuklir/AKSEL-DECY13
   sudo apt install -y python3-serial python3-paho-mqtt
   sudo bash raspi/setup_udev.sh   # cukup 1x pasang /dev/arduino_hmi|sensor|actuator
   python3 raspi/accelerator_hub.py --mqtt-host 127.0.0.1 --mqtt-port 1883 --mqtt-control
   ```

---

## 6. Tahapan Uji Fisik 448 LED WS2812B + Buzzer `GPIO 17` & Uji Terintegrasi Serentak

### Cek Wiring Wajib Sebelum Menyalakan Alat (`M3`)

![Gambar Skema Lengkap Wiring Hardware Siklotron DECY-13 v1.6](../instruksi%20untuk%20projek%20sp/wiring_full_decy13_v16.svg)

- `DIN` LED Strip WS2812B → **`GPIO 18` (Pin Fisik `12`)** melalui resistor **330–470 Ohm**.
- Catu daya **PSU 5V eksternal** berarus cukup untuk **448 piksel** *(uji `03_test_led_pixel_finder.py` kini memakai default `--brightness 10` serta kunci `--power-ok` khusus tes All ON/RGB)* dengan **`GND` PSU 5V disatukan (*common ground*) ke Pin `06` (`GND` RPi)**. Jangan sambungkan `+5V` PSU eksternal ke pin `5V` RPi!
- **Relay Kipas 12V (`GPIO 21` Pin 40) & Buzzer (`GPIO 17` Pin 11)** tetap eksklusif di RPi — jangan campur dengan output driver `74HC595` Uno 3. Saat `03_test_led_pixel_finder.py --hardware` dijalankan terpisah (daemon mati), buzzer `GPIO 17` dipakai sementara untuk memberi bunyi sinyal `1..9x` per tahap uji dan dilepas (`GPIO.cleanup(17)`) saat keluar; saat operasional normal, `GPIO 17` dikendalikan penuh oleh `04_decy13_mqtt_daemon.py` (`VacuumSafetyModule`).

### Langkah 1 — Uji Isolasi 448 LED + Buzzer `GPIO 17` (`03_test_led_pixel_finder.py`) *(Matikan Daemon dulu sementara)*
```bash
cd ~/sp-aksel-polteknuklir/decy13_mqtt_kit/raspi_cli
# Mode interaktif aman (brightness 10; tanpa tes All ON/RGB sebelum PSU siap):
sudo python3 03_test_led_pixel_finder.py --mode finder --hardware

# Mode 9 tes otomatis penuh (wajib --power-ok setelah PSU 5V eksternal siap; tambahkan --no-buzzer bila tanpa bunyi):
sudo python3 03_test_led_pixel_finder.py --mode finder --hardware --auto --power-ok
```
Daftar **9 Tahap Uji** & menu perintah interaktif pada commit `0db6f3b`/`18c2603`:
- `1/9` **ALL OFF AWAL**, `2/9` **INDIVIDUAL LED** (`0..447`), `3/9` **ALL LED ON** *(wajib `--power-ok`)*, `4/9` **RGB COLOR TEST** *(wajib `--power-ok`)*, `5/9` **SPIRAL ACCELERATION** (`0..399` + RF Gap), `6/9` **EXTRACTION / SHOOT** (`400..447`), `7/9` **ENERGY CHARGING** (step bunyi per 5 LED), `8/9` **FINAL BEAM SHOT**, `9/9` **ALL OFF FINAL**.
- Menu interaktif: `f` (jalankan semua `1..9`), `s` (tes `5/9` spiral), `e` (tes `6/9` beam), `b` (tes `7/9` charge + `8/9` shot), `<angka>` / `Enter` (nyalakan 1 piksel berurutan), `q` (matikan semua LED, `GPIO.cleanup(17)`, & keluar `ALL OFF - SELESAI`).

### Langkah 2 — Uji Terintegrasi Serentak (`04_decy13_mqtt_daemon.py` + `accelerator_hub.py` + Web HMI Offline + Node-RED)
1. Nyalakan **Terminal SSH 1** (`sudo python3 04_decy13_mqtt_daemon.py`) dan **Terminal SSH 2** (`python3 AKSEL-DECY13/raspi/accelerator_hub.py --mqtt-host 127.0.0.1 --mqtt-port 1883 --mqtt-control`).
2. Di **Web HMI Offline Mini PC** (`MQTT TERHUBUNG` ke `ws://<IP_RASPI>:9001`):
   - Uji sekuens **Power → Vacuum (`<= 1e-3 mbar`) → Interlock → Start Beam → Shoot → Emergency Stop** sambil mengamati Relay Kipas, Buzzer, LED WS2812B, Panel tiga TFT (`decy13/usb/*`), serta Dashboard Node-RED `/cyclotron`.
   - Pastikan **Emergency Stop** via Web HMI memutus `beam`, `vacuum`, `rf`, dan membunyikan alarm 3 detik dengan aman.
3. Simpan/kirim bukti output terminal ke Divisi 1, Divisi 3 (`blufiaa`), Divisi 4 (`HDMrishiki`), atau Divisi 6 (`rekypurnomo`) tanpa mengedit file divisi lain dari Mini PC. *(Catatan: `config_hardware.json` masih default `64` LED sampai uji daya penuh 448 LED + daemon disepakati untuk disinkronkan menjadi `448`.)*

---

## 7. Prompt Siap Copy-Paste untuk Antigravity (AGY) di Mini PC (`v1.6`)

Setelah `git pull --ff-only origin main` di Mini PC, tempelkan prompt ini ke chat baru Antigravity di Mini PC:

```text
Saya Ketua Tim (Divisi 1 / `azfaaksan-hub`) sedang menyiapkan & menguji alat lengkap dari Mini PC Ruang Kontrol (Windows 8/10/11) yang terhubung ke Raspberry Pi 3B+ pada versi `v1.6` (`18c2603`).
Baca `decy13_mqtt_kit/PANDUAN_MINI_PC_UJI_LAPANGAN.md`, `decy13_mqtt_kit/qa_divisi6/PANDUAN_KETUA_UJI_ULANG.md`, dan `README.md`, lalu jalankan `git status -sb` dan `python tools/raspi_preflight.py --divisi 1 --no-save`.
Patuhi seluruh aturan di `PANDUAN_MINI_PC_UJI_LAPANGAN.md`:
- Mini PC hanya sebagai Stasiun Uji (JANGAN edit file kode Divisi 2–6 atau menjalankan `git commit`/`git push` otomatis).
- Divisi 2 (`GPIO 21/17`) sudah `LULUS_UJI_FISIK` (`7/7`, E-Stop via HTML Web HMI Mini PC).
- Divisi 3 memakai `03_test_led_pixel_finder.py` (`18c2603`: **448 LED** `--brightness 10` + kunci `--power-ok` + `--auto` + buzzer bersama `GPIO 17` untuk 9 uji isolasi saat daemon mati).
- Divisi 4 (`AKSEL-DECY13`) memakai 3 Arduino Uno + 3 Shield TFT via Powered USB Hub (`accelerator_hub.py --mqtt-host 127.0.0.1 --mqtt-port 1883 --mqtt-control`), topik `decy13/usb/*`.
- Web HMI di Mini PC (`decy13_mqtt_kit/web_hmi/`) 100% offline (`http://localhost:8000`) + `usb-panel.js`.
- Satukan koneksi Divisi 6 (`qa_divisi6`: Node-RED `/cyclotron` & `/api/status` + `qa_readonly_api.ps1`) ke broker RPi (`1883`/`9001`) dengan mematikan Mosquitto Windows Mini PC (`Stop-Service mosquitto`) agar `04_decy13_mqtt_daemon.py` auto-fallback ke `127.0.0.1:1883`.
Tampilkan: (1) status sinkronisasi repo di Mini PC, (2) panduan langkah berurutan menyalakan RPi (2 terminal SSH) & Web HMI Offline + Node-RED QA di Mini PC, dan (3) perintah verifikasi yang harus saya jalankan sendiri.
```
