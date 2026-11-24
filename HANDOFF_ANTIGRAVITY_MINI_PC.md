# 🤖 HANDOFF KONTEKS PENUH — ANTIGRAVITY (AGY) MINI PC RUANG KONTROL

> **Tujuan file ini:** Memindahkan seluruh konteks percakapan, konfigurasi nyata di lapangan, temuan troubleshooting, dan langkah lanjutan dari **Laptop Utama Ketua** ke **Antigravity (AGY) di Mini PC** melalui GitHub (`git pull`). Begitu dibuka di Mini PC, sesi Antigravity baru bisa langsung melanjutkan koordinasi tanpa mengulang dari awal.
>
> **Terakhir diperbarui:** `2026-11-24` • **Acuan commit `main` sebelumnya:** `7cb592c` (`v1.6`) • **Repositori:** `https://github.com/azfaaksan-hub/sp-aksel-polteknuklir`

---

## 1. Peran, Mesin, & Aturan Kerja Keras (WAJIB DIPATUHI AGY MINI PC)

1. **User adalah Ketua Tim / Divisi 1 (`azfaaksan-hub`)** proyek **Alat Peraga Siklotron DECY-13 (13 MeV H⁻)**, Politeknik Teknologi Nuklir Indonesia (BRIN).
2. **Bahasa & gaya komunikasi:** Balas dalam **Bahasa Indonesia**, ringkas, praktis, tidak bertele-tele. User di Mini PC lebih nyaman memakai **CMD / PowerShell** (bukan wajib Git Bash).
3. **Aturan Git Mandiri (KERAS):** **DILARANG** menjalankan `git commit`, `git push`, `git merge`, atau ganti branch secara otomatis. Selalu berikan perintah terminal agar user menjalankannya sendiri.
4. **Batas File Anti-Konflik 6 Divisi:**
   - **Wilayah Ketua (Divisi 1):** `README.md`, `AGENTS.md`, `HANDOFF_ANTIGRAVITY_MINI_PC.md`, `PANDUAN_OPERASIONAL_PASCA_WIRING.md`, `decy13_mqtt_kit/PANDUAN_MINI_PC_UJI_LAPANGAN.md`, `decy13_mqtt_kit/raspi_cli/04_decy13_mqtt_daemon.py`, `decy13_mqtt_kit/raspi_cli/config_hardware.json`, `tools/*`, `laporan_uji/UJI_DIVISI_1_CORE_RASPI.md`.
   - **JANGAN edit file kode milik Divisi 2–6** langsung dari Mini PC tanpa izin eksplisit user (`mod_vacuum_safety.py`, `01_test_relay_buzzer.py`, `mod_led_ws2812b.py`, `03_test_led_pixel_finder.py`, `AKSEL-DECY13/*`, `web_hmi/index.html`, `qa_divisi6/*`, `flows_mqtt_decy13.json`).
   - **Aturan Ceklis Jujur (`laporan_uji/`):** DILARANG mencentang `[x]` pada Tahap B (Uji Fisik) atau mengubah status ke `LULUS_UJI_FISIK` tanpa bukti output/pengamatan hardware nyata.
   - Setiap kali ada edit di `tools/raspi_bootstrap.sh`, **WAJIB akhir baris LF murni** (tanpa CRLF `\r\n`) dan wajib lolos `python tools/cek_integrasi_dan_announcer.py --ci --cek-branch`.

---

## 2. Profil Hardware & Jaringan Nyata Unit Lapangan (Hasil Observasi Langsung)

### A. Raspberry Pi 3 Model B+ (Unit Aktual Tim)
- **OS:** **Debian GNU/Linux 13 (`trixie`) — Raspberry Pi OS Lite 64-bit** *(TIDAK ada GUI desktop, langsung terminal hitam teks; memakai `NetworkManager` / `nmcli` / `nmtui`, BUKAN `dhcpcd`)*.
- **Username SSH:** **`sp-aksel`** (Port `22` aktif).
- **Folder repo di RPi:** **`~/decy13`** *(catatan: folder uji simulasi lama Divisi 6 ada di `~/decy13-test` dengan `.venv`; pastikan simulator lama mati sebelum daemon jalan)*.
- **TEMUAN KRITIS DAYA / ETHERNET:**
  - **JANGAN pakai kabel Ethernet (`eth0`) di Raspi 3B+ ini!** Chip Ethernet `LAN7515` menarik arus tambahan yang memicu *brown-out* / Raspi mati sendiri beberapa saat kemudian.
  - Sistem resmi sekarang berjalan **100% Wi-Fi Auto-Link (`--disable-eth`)**!
  - Wajib cek kesehatan adaptor 5V RPi lewat `vcgencmd get_throttled` (target **`0x0`**; bila bukan `0x0`, adaptor/kabel micro-USB 5V drop dan harus diganti ke adaptor **5V 2.5A–3A** kabel pendek tebal).
- **Pola IP Hotspot HP Android:**
  - Saat pakai Hotspot HP Android, buntut IP Raspi cenderung tetap **`.158`** *(pernah `10.211.191.158`, terakhir `10.128.143.158`)*, tetapi 2 oktet tengah diacak HP setiap kali Hotspot dimatikan & dinyalakan ulang.
  - **JANGAN di-lock static manual di `wlan0`** kalau memakai Hotspot HP Android (nanti gagal konek saat subnet HP berubah). Gunakan **`python tools\minipc_control_hub.py`** di Mini PC yang otomatis menemukan IP Raspi lewat UDP `51313` + fallback TCP subnet scan!
  - *(Jangan gunakan `hostname -i` huruf kecil di RPi karena mengeluarkan `127.0.1.1`; gunakan `hostname -I` huruf besar atau `ip -4 addr show wlan0`.)*

### B. 4 Layanan `systemd` Auto-Start di Raspberry Pi (`tools/raspi_bootstrap.sh`)
Saat `bash tools/raspi_bootstrap.sh --install-service --install-autolink --install-usb-service --disable-eth` dijalankan, 4 service berikut menyala otomatis setiap boot:
1. **`mosquitto.service`** — Broker tunggal terpusat (`0.0.0.0:1883` TCP & `0.0.0.0:9001` WebSocket, `allow_anonymous true`).
2. **`decy13.service`** — `sudo python3 ~/decy13/decy13_mqtt_kit/raspi_cli/04_decy13_mqtt_daemon.py` (`User=root`, `Restart=always`).
3. **`decy13-autolink.service`** — `python3 ~/decy13/tools/raspi_auto_link.py` (`User=sp-aksel`, UDP `51313`/`51314`, melapor IP Wi-Fi, status 3 layanan, suhu CPU, & `vcgencmd get_throttled` ke Mini PC).
4. **`decy13-usb-hub.service`** — `python3 ~/decy13/AKSEL-DECY13/raspi/accelerator_hub.py --mqtt-host 127.0.0.1 --mqtt-port 1883 --mqtt-control` (`User=sp-aksel`, `SupplementaryGroups=dialout`, `Restart=always`).

### C. Pengaturan Mini PC Ruang Kontrol (Windows 8 / 10 / 11)
- **WAJIB matikan Mosquitto Windows Service** (`Stop-Service mosquitto` / `net stop mosquitto`) saat operasional penuh 6 divisi agar tidak bentrok dengan broker RPi (`tools/minipc_control_hub.py` sudah otomatis mematikannya).
- **Pusat Kendali CMD/PowerShell:** `python tools\minipc_control_hub.py` di root folder `sp-aksel-polteknuklir`:
  - `[1]` Buka Terminal SSH Raspi otomatis (fallback otomatis ke Git `ssh.exe` untuk Windows 8).
  - `[2]` Auto-Update & Reset Bersih `~/decy13` di Raspi ke `origin/main` + jalankan `raspi_bootstrap.sh --install-service --install-autolink --install-usb-service --disable-eth` + restart seluruh 3 service + cetak status.
  - `[3]` Restart `decy13-usb-hub.service` & tampilkan 20 baris log terakhir (`journalctl`).
  - `[4]` Tambah / simpan Wi-Fi baru di Raspi langsung dari Mini PC (`nmcli`).
  - `[5]` Jalankan server Web HMI 100% Offline di `http://127.0.0.1:8000` (langsung dari `decy13_mqtt_kit/web_hmi`, bebas error 404) + **Auto-Copy `ws://<IP_RASPI>:9001`** ke Clipboard + buka browser.
  - `[6]` Jalankan QA Healthcheck (`06_test_mqtt_healthcheck.py --host <IP_RASPI> --duration 10 --no-menu`).
  - `[R]` Scan ulang IP Raspi | `[M]` Input IP Raspi manual.
- **Node-RED Divisi 6 (`http://127.0.0.1:1880`):** Import `decy13_mqtt_kit/nodered/flows_mqtt_decy13.json` (`/cyclotron` & `/api/status`) dan opsional `AKSEL-DECY13/raspi/nodered_usb.json` (`/api/usb/status`). Arahkan host node broker ke **`<IP_WIFI_RASPI>:1883`**. Audit API read-only pakai `decy13_mqtt_kit/qa_divisi6/scripts/qa_readonly_api.ps1 -Samples 30`.

---

## 3. Status Kode, Branch GitHub, & Wiring 6 Divisi (`main` @ `7cb592c`+)

- **Audit Branch GitHub:** Seluruh kode final 6 divisi **SUDAH MASUK DI `main`** (`7/7 [LULUS]` CI). Tidak ada branch anggota yang tertinggal fitur baru (`divisi-2-vacum-safety` hanya selisih 1 spasi kosong; `divisi-4-tft` hanya menyisakan file mentah `.patch` yang isinya sudah masuk `main`; `divisi-3-led-ws2812b` adalah branch v1 usang berkonflik — JANGAN di-merge).
- **Konfigurasi Terbaru `decy13_mqtt_kit/raspi_cli/config_hardware.json` (SUDAH DISINKRONKAN di `7cb592c`):**
  - `"broker_host": "127.0.0.1"`
  - `"estop_hardware_enabled": false` *(E-Stop resmi lewat tombol Web HMI; menutup risiko noise `GPIO 22`)*
  - `"total_leds": 448`, `"brightness": 15`, `"spiral_start_idx": 0`, `"spiral_end_idx": 399`, `"rf_gap_indices": [99, 199, 299, 399]`, `"shoot_start_idx": 400`, `"shoot_end_idx": 447`.
- **Peta Wiring Lengkap (0 Tabrakan I/O — lihat gambar [`instruksi untuk projek sp/wiring_full_decy13_v16.svg`](instruksi%20untuk%20projek%20sp/wiring_full_decy13_v16.svg)):**
  - **Divisi 1 (Core & Broker):** RPi 3B+ `Mosquitto :1883/:9001` + `04_decy13_mqtt_daemon.py` (`decy13/rpi/state`, `decy13/hmi/cmd`). Kartu: `6/8` (`DRAFT_PUSH_LAPTOP`).
  - **Divisi 2 (Vakum & Safety — `LULUS_UJI_FISIK` `7/7`):** Buzzer `GPIO 17` (`Pin 11`, GND `Pin 09`), Relay Kipas 12V Active-LOW `GPIO 21` (`Pin 40`, VCC 5V `Pin 02`, GND `Pin 39`), Adaptor 12V terisolasi di `COM` → `NO` → Kipas 12V.
  - **Divisi 3 (448 LED WS2812B — `10/10` ceklis, status `DRAFT_PUSH_LAPTOP`):** `GPIO 18` (`Pin 12`, PWM0/DMA10, wajib `dtparam=audio=off`) → Resistor `330–470 Ω` → `DIN`; **PSU Eksternal 5V** (`+5V` hanya ke LED, **`-` GND wajib Common Ground ke `GND` LED + `Pin 06` RPi**). Uji isolasi `03_test_led_pixel_finder.py` (`18c2603`: 9 tes + buzzer `GPIO 17`, `--brightness 10`, `--power-ok`, `--auto`) dijalankan hanya saat `decy13.service` dihentikan sementara.
  - **Divisi 4 (3 Arduino Uno + 3 Shield TFT 2.4" MCUFRIEND `USE_LOCAL_TFT = 1` — kartu `0/8`):** Shield ditancap langsung ke Uno (`D2–D9, A0–A4`, Touch `XP=6, XM=A2, YP=A1, YM=7`), **slot microSD Uno 2 & 3 KOSONG**, ke-3 Uno dicolok ke **Powered USB Hub 5V (≥ 2A)** → port USB-A RPi (`accelerator_hub.py`, topik `decy13/usb/state|cmd|ack`).
    - Uno 1 (`/dev/arduino_hmi`): HMI lokal 3 halaman.
    - Uno 2 (`/dev/arduino_sensor`): IC `74HC4051` (`Z→A5, S0→D11, S1→D13, D10=HIGH, S2/INH/VEE/VSS→GND, Kontak→D12 & GND`).
    - Uno 3 (`/dev/arduino_actuator`): IC `74HC595` (`DS→D11, SHCP→D13, STCP→D12, /OE→D10 + Pull-Up 10kΩ→5V, /MR→5V`, **Interlock NC `A5 ↔ GND` wajib tertutup `LOW`** agar tombol `Mulai`/`Uji` di TFT & Web HMI tidak abu-abu!). Output `Q0..Q6` terpisah dari Relay/Buzzer RPi.
  - **Divisi 5 (Web HMI 100% Offline — kartu `0/8`):** `decy13_mqtt_kit/web_hmi/index.html` + `assets/console.css`, `mqtt.min.js`, `usb-panel.js` (sudah terpasang di `index.html` baris 1398).
  - **Divisi 6 (MQTT, Node-RED & QA — kartu `3/7` `DRAFT_PUSH_LAPTOP`):** Handover QA simulasi `300/300 ONLINE @ 4.99 Hz` selesai di `decy13_mqtt_kit/qa_divisi6/`. Sisa uji terhadap daemon asli + hardware nyata.

---

## 4. Posisi Terakhir Percakapan & Daftar Lanjutan Langsung di Mini PC

**Titik terakhir yang dicapai pada sesi Laptop Ketua (`2026-11-20`):**
- `minipc_control_hub.py` sudah berjalan lancar di CMD Mini PC dan langsung mendeteksi Raspi di Wi-Fi Hotspot (`10.128.143.158`).
- Web HMI Offline sudah terbuka di Mini PC dan terhubung ke Raspi (tombol **Vacuum** di Web HMI berhasil menyalakan **modul Relay** di Raspi!).
- Ketiga port USB Arduino Uno (`3 port`) sudah terbaca di Raspberry Pi, dan user sudah sempat menjalankan `setup_udev.sh`.
- **Masalah terakhir yang sedang dibereskan (Lanjutkan dari SINI!):**
  1. **Error terakhir: `Failed to restart decy13-usb-hub.service` (`not found`)** — Penyebabnya `~/decy13` di RPi belum ter-update ke `7cb592c` karena bug `|| true;` pada menu `[2]` `minipc_control_hub.py` lama (sekarang **SUDAH DIPERBAIKI** menjadi `git fetch origin && git checkout main && git reset --hard origin/main`).
     - **Aksi pertama di Mini PC:** `git pull --ff-only origin main` → jalankan `python tools\minipc_control_hub.py` → tekan **`2`** → pastikan `git log -1` di Raspi terbaru dan ketiga service (`decy13`, `decy13-autolink`, `decy13-usb-hub`) berstatus `active (running)`!
  2. **Verifikasi urutan 3 USB Arduino Uno (`/dev/arduino_hmi`, `sensor`, `actuator`):**
     - Tekan **`3`** di menu `minipc_control_hub.py` untuk lihat log `decy13-usb-hub.service`.
     - Target: **`USB hmi=OK sensor=OK actuator=OK`**. Bila 2 di antaranya masih `--`, cukup **tukar fisik colokan 2 kabel USB Uno tersebut di lubang USB Hub** (karena `udev` mengikat ke port fisik hub) atau ulang `sudo bash ~/decy13/AKSEL-DECY13/raspi/setup_udev.sh`.
     - Pasang jumper/saklar **Interlock NC `A5 ↔ GND` di Uno 3** supaya tombol di Panel 3-TFT Web HMI aktif (tidak abu-abu).
  3. **Bereskan Kipas 12V di Relay Divisi 2:**
     - Relay sudah hidup saat Vacuum diklik, tapi kipas 12V belum berputar → cek adaptor 12V, polaritas `(+)`/`(-)` kipas DC, dan kekencangan terminal `COM` + `NO` pada modul relay.
  4. **Cek Kesehatan Daya 5V Raspi (`vcgencmd get_throttled`) & 448 LED:**
     - Pastikan `Daya 5V` di dashboard `minipc_control_hub.py` = **`0x0`** (tidak *under-voltage* saat Relay + LED + Powered USB Hub aktif bersamaan).
     - Uji penuh **448 LED (`brightness=15`)** melalui Web HMI (menu **`5`**): **Power → Vacuum → Interlocks → Start Beam (400 LED spiral) → Shoot (48 LED beam) → EMERGENCY_STOP**.
  5. **Uji QA Divisi 6 & Lengkapi Kartu Laporan (`laporan_uji/`):**
     - Jalankan menu **`6`** (`06_test_mqtt_healthcheck.py`) + Node-RED `/cyclotron` + `qa_readonly_api.ps1 -Samples 30` terhadap daemon & hardware nyata.
     - Kumpulkan bukti terminal/foto nyata untuk menaikkan progres kartu dari `54,2%` (`26/48`) menuju `100%` (Milestone M3–M5).

---

## 5. Cara Melanjutkan di Antigravity (AGY) Mini PC (1 Kalimat!)

1. Di Mini PC, tarik update terbaru dulu di CMD/PowerShell:
   ```cmd
   cd C:\path\ke\sp-aksel-polteknuklir
   git checkout main
   git pull --ff-only origin main
   ```
2. Buka folder `sp-aksel-polteknuklir` di **Antigravity (AGY) pada Mini PC** (file `AGENTS.md` di root otomatis memuat konteks ini!).
3. Cukup ketik **1 kalimat pendek ini** di chat Antigravity Mini PC:
   ```text
   Baca HANDOFF_ANTIGRAVITY_MINI_PC.md lalu cek git status dan lanjutkan koordinasi setup serta troubleshooting hardware Raspi dari Mini PC ini.
   ```
