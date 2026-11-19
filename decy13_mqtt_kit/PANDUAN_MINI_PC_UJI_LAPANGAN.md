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

## 2. Status Proyek Terkini (`v1.6` — Progres `54,2%` / `26/48`)

- **Branch `main` aktif (`v1.6`):**
  1. **Divisi 2 (`LULUS_UJI_FISIK`, `7/7`):** Relay Kipas 12V (`GPIO 21`, Active-LOW), Buzzer (`GPIO 17`, Active-HIGH), & `cleanup()` lulus uji fisik bersama tim; E-Stop dijalankan lewat tombol **`EMERGENCY_STOP` HTML Web HMI di Mini PC** *(saklar fisik `GPIO 22` berstatus N/A)*.
  2. **Divisi 3 (`f6c367d`, `10/10` ceklis):** Uji fisik **448 LED WS2812B** (`0..399` spiral 400 LED, `400..447` shoot/extraction 48 LED, `brightness=20`, menu `t/a/r/s/e/p/b/x/q`) sudah terintegrasi (`DRAFT_PUSH_LAPTOP`, tinggal verifikasi akhir bersama LCD/daemon asli & sinkronisasi `config_hardware.json` dari `64` ke `448` LED).
  3. **Divisi 4 (`207ac04` — 3-LCD TFT Arduino Uno via USB Hub):** `AKSEL-DECY13/raspi/accelerator_hub.py` menyatukan 3 Uno + 3 Shield TFT `MCUFRIEND 320x240` (`/dev/arduino_hmi|sensor|actuator`, `115200 baud`) ke Mosquitto lewat topik **`decy13/usb/state`**, **`decy13/usb/cmd`**, & **`decy13/usb/ack`** (**0 konflik** dengan pin GPIO `17/18/21` RPi!). *(Catatan daya: gunakan **Powered USB Hub 5V >= 2A** untuk 3 Uno + TFT.)*
  4. **Divisi 5 (`6d37d99` + `usb-panel.js`):** Web HMI (`decy13_mqtt_kit/web_hmi/`) kini **100% Offline** (CSS `console.css`, `mqtt.min.js`, & `usb-panel.js` lokal — tidak perlu internet di ruang kontrol!).
  5. **Divisi 6 (`087e0fb` / `d929400`):** Handover QA komunikasi PC ↔ RPi 3 selesai (`300/300 ONLINE @ 4.99 Hz`, `22/22` field PASS, flow Node-RED `/cyclotron`, ditambah tab opsional `AKSEL-DECY13/raspi/nodered_usb.json` `/api/usb/status`).

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

---

## 4. Alur Eksekusi Full Setup Mini PC ↔ Raspberry Pi (`v1.6`)

### A. Di Sisi Mini PC (Windows 8 / 10 / 11)
1. **Tarik update Git terbaru sebelum mulai uji:**
   ```bash
   git checkout main
   git pull --ff-only origin main
   ```
2. **Pastikan TIDAK ada broker Mosquitto Windows berjalan di Mini PC** saat sedang menghubungkan HMI ke Mosquitto RPi.
3. **Jalankan HTTP Server Lokal untuk Web HMI 100% Offline (JANGAN edit `web_hmi/index.html`):**
   ```bash
   python -m http.server 8000 --directory decy13_mqtt_kit/web_hmi
   ```
   Lalu buka browser ke **`http://localhost:8000`**.
4. **Sambungkan ke Broker RPi lewat UI browser:**
   - Ubah kotak **WebSocket URL Endpoint** dari default `ws://127.0.0.1:9001` menjadi **`ws://<IP_RASPI>:9001`** → klik **Hubungkan MQTT**.
   - Pastikan badge di atas berubah hijau **`MQTT TERHUBUNG`** dan **Panel tiga TFT · USB Raspberry Pi** di bawah header menampilkan status `TFT 1..3`.
5. *(Opsional tes QA dari Mini PC):*
   ```powershell
   python decy13_mqtt_kit/raspi_cli/06_test_mqtt_healthcheck.py --host <IP_RASPI> --duration 10 --no-menu
   ```

### B. Di Sisi Raspberry Pi 3B+ (via 2 Tab Git Bash SSH dari Mini PC)
1. **Pastikan RPi sinkron di `main` `v1.6` & lolos Bootstrap/Preflight:**
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
   Pastikan status modul mencetak `[HARDWARE AKTIF]` dan terhubung ke `127.0.0.1:1883 (rc=0)`.
3. **Terminal SSH 2 (Hub USB 3 Arduino Uno + 3 Shield TFT Divisi 4):**
   *(Hubungkan ketiga Arduino Uno ke **Powered USB Hub 5V >= 2A** yang dicolok ke USB-A RPi; kosongkan slot microSD Uno 2 & Uno 3.)*
   ```bash
   cd ~/sp-aksel-polteknuklir/AKSEL-DECY13
   sudo apt install -y python3-serial python3-paho-mqtt
   sudo bash raspi/setup_udev.sh   # cukup 1x pasang /dev/arduino_hmi|sensor|actuator
   python3 raspi/accelerator_hub.py --mqtt-host 127.0.0.1 --mqtt-port 1883 --mqtt-control
   ```

---

## 5. Tahapan Uji Fisik 448 LED WS2812B Divisi 3 & Uji Terintegrasi Serentak

### Cek Wiring Wajib Sebelum Menyalakan Alat (`M3`)
- `DIN` LED Strip WS2812B → **`GPIO 18` (Pin Fisik `12`)** melalui resistor **330–470 Ohm**.
- Catu daya **PSU 5V eksternal** berarus cukup untuk **448 piksel** *(uji `03_test_led_pixel_finder.py` memakai default `brightness=20` agar konsumsi arus tetap aman)* dengan **`GND` PSU 5V disatukan (*common ground*) ke Pin `06` (`GND` RPi)**. Jangan sambungkan `+5V` PSU eksternal ke pin `5V` RPi!
- **Relay Kipas 12V (`GPIO 21` Pin 40) & Buzzer (`GPIO 17` Pin 11)** tetap eksklusif di RPi — jangan campur dengan output driver `74HC595` Uno 3.

### Langkah 1 — Uji Isolasi 448 LED (`03_test_led_pixel_finder.py`) *(Matikan Daemon dulu sementara)*
```bash
cd ~/sp-aksel-polteknuklir/decy13_mqtt_kit/raspi_cli
sudo python3 03_test_led_pixel_finder.py --mode finder --hardware --total-leds 448 --spiral-leds 400 --brightness 20
```
Menu perintah di mode `finder`:
- `t` : tes satu per satu (`0..447`)
- `a` : nyalakan semua LED putih (3 detik)
- `r` : tes warna RGB + putih
- `s` : uji **Spiral Acceleration** (`0..399` + RF Gap)
- `e` : uji **Extraction / Beam** (`400..447`)
- `p` : ulangi spiral + beam 3 kali
- `b` : animasi **Final Beam Shot**
- `x` : jalankan semua tes berurutan (`t -> a -> r -> s -> e -> p -> b -> off`)
- `q` : matikan semua LED & keluar (`ALL OFF - SELESAI`)

### Langkah 2 — Uji Terintegrasi Serentak (`04_decy13_mqtt_daemon.py` + `accelerator_hub.py` + Web HMI Offline)
1. Nyalakan **Terminal SSH 1** (`sudo python3 04_decy13_mqtt_daemon.py`) dan **Terminal SSH 2** (`python3 AKSEL-DECY13/raspi/accelerator_hub.py --mqtt-host 127.0.0.1 --mqtt-port 1883 --mqtt-control`).
2. Di **Web HMI Offline Mini PC** (`MQTT TERHUBUNG`):
   - Uji sekuens **Power → Vacuum (`<= 1e-3 mbar`) → Interlock → Start Beam → Shoot → Emergency Stop** sambil mengamati Relay Kipas, Buzzer, LED WS2812B, dan Panel tiga TFT (`decy13/usb/*`).
   - Pastikan **Emergency Stop** via Web HMI memutus `beam`, `vacuum`, `rf`, dan membunyikan alarm 3 detik dengan aman.
3. Simpan/kirim bukti output terminal ke Divisi 1, Divisi 3 (`blufiaa`), atau Divisi 4 (`HDMrishiki`) tanpa mengedit file divisi lain dari Mini PC. *(Catatan: bila `config_hardware.json` masih `64` LED saat uji serentak daemon, koordinasikan ke Laptop Ketua untuk sinkronisasi ke `448` LED setelah uji stabilitas daya aman.)*

---

## 6. Prompt Siap Copy-Paste untuk Antigravity (AGY) di Mini PC (`v1.6`)

Setelah `git pull --ff-only origin main` di Mini PC, tempelkan prompt ini ke chat baru Antigravity di Mini PC:

```text
Saya Ketua Tim (Divisi 1 / `azfaaksan-hub`) sedang menyiapkan & menguji alat lengkap dari Mini PC Ruang Kontrol (Windows 8/10/11) yang terhubung ke Raspberry Pi 3B+ pada versi `v1.6`.
Baca `decy13_mqtt_kit/PANDUAN_MINI_PC_UJI_LAPANGAN.md` dan `README.md`, lalu jalankan `git status -sb` dan `python tools/raspi_preflight.py --divisi 1 --no-save`.
Patuhi seluruh aturan di `PANDUAN_MINI_PC_UJI_LAPANGAN.md`:
- Mini PC hanya sebagai Stasiun Uji (JANGAN edit file kode Divisi 2–6 atau menjalankan `git commit`/`git push` otomatis).
- Divisi 2 (`GPIO 21/17`) sudah `LULUS_UJI_FISIK` (`7/7`, E-Stop via HTML Web HMI Mini PC).
- Divisi 3 memakai konfigurasi uji fisik **448 LED** (`--total-leds 448 --spiral-leds 400 --brightness 20`, ceklis `10/10` di `f6c367d`).
- Divisi 4 (`AKSEL-DECY13`) memakai 3 Arduino Uno + 3 Shield TFT via Powered USB Hub (`accelerator_hub.py --mqtt-host 127.0.0.1 --mqtt-port 1883 --mqtt-control`), topik `decy13/usb/*`.
- Web HMI di Mini PC (`decy13_mqtt_kit/web_hmi/`) kini 100% offline (`http://localhost:8000`) + dilengkapi `usb-panel.js`.
Tampilkan: (1) status sinkronisasi repo di Mini PC, (2) panduan langkah berurutan untuk menyalakan RPi (2 terminal: daemon + USB hub) & Web HMI offline Mini PC (pakai Git Bash & IP angka RPi, tanpa `.local`), dan (3) perintah verifikasi yang harus saya jalankan sendiri.
```
