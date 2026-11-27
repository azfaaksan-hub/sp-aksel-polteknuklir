# ⚡ Panduan Setup & Operasional Lengkap Siklotron DECY-13 (Pasca-Wiring 6 Divisi)

Panduan ringkas siap pakai untuk menyalakan, menguji, dan mematikan seluruh rangkaian alat peraga **Siklotron DECY-13 (`v1.6`)** pada mode **100% Wi-Fi Auto-Link (tanpa kabel Ethernet)** setelah seluruh kabel wiring terpasang sesuai gambar di bawah ini.

![Gambar Skema Lengkap Wiring Hardware Siklotron DECY-13 v1.6](instruksi%20untuk%20projek%20sp/wiring_full_decy13_v16.svg)

> 📄 **Buka gambar wiring ukuran penuh:** [`instruksi untuk projek sp/wiring_full_decy13_v16.svg`](instruksi%20untuk%20projek%20sp/wiring_full_decy13_v16.svg)

---

## 0. Cek Keselamatan Wiring (WAJIB 1 Menit Sebelum Colok Listrik)

Pastikan kondisi **semua adaptor masih mati**, lalu periksa 6 titik wajib ini:
- [ ] **Kabel Ethernet RPi DICABUT** *(mode 100% Wi-Fi agar chip LAN7515 tidak memicu drop daya/restart pada RPi 3B+)*.
- [ ] **Common Ground LED (Divisi 3):** `(-)` GND PSU Eksternal 5V / `LM2596` sudah tersambung ke `GND` LED Strip **DAN** `Pin 39` / `Pin 06` (`GND` RPi). **`(+)` 5V PSU LED TIDAK BOLEH menyentuh `Pin 02`/`04` RPi!**
- [ ] **Resistor Data LED (PIN BARU — Pin 12 Rusak!):** Resistor `330–470 Ω` terpasang seri antara **`Pin Fisik 32` (`GPIO 12` / `BCM 12`, PWM0)** → `DIN` LED Strip WS2812B *(JANGAN tancap ke `Pin Fisik 12` / `GPIO 18` karena pin tersebut rusak)*.
- [ ] **Relay & Buzzer (Divisi 2):** `Pin 11` (`GPIO 17`) → Buzzer `(+)`, `Pin 09` → Buzzer `(-)`, `Pin 40` (`GPIO 21`) → `IN` Relay, `Pin 02` (`5V`) → `VCC` Relay, `Pin 39` → `GND` Relay. Tegangan **12V hanya di terminal `COM`/`NO` Relay + Kipas 12V**.
- [ ] **3 Arduino Uno + 3 Shield TFT (Divisi 4):**
  - Ketiga Uno tercolok ke **Powered USB Hub 5V (≥ 2A)** *(bukan langsung ke port USB RPi)*.
  - **Slot microSD Uno 2 & Uno 3 KOSONG**.
  - **Interlock Uno 3 (`A5 ↔ GND`):** pastikan saklar Interlock NC (atau kabel jumper uji ke `GND`) terpasang pada pin **`A5` Uno 3**, jika kosong layar TFT 3 terkunci di `Interlok terbuka` dan tombol Panel 3-TFT tidak aktif.
  - Pull-up eksternal **`10 kΩ`** dari `/OE` (`D10`) IC `74HC595` ke `5V` sudah terpasang, dan **output `Q0..Q6` Uno 3 tidak dicampur ke Relay/Buzzer `GPIO 21/17` RPi**.
- [ ] **Hotspot / Wi-Fi Bersama:** Hotspot HP / Wi-Fi yang sudah tersimpan di Raspi menyala, dan **Mini PC terhubung ke Wi-Fi / Hotspot yang sama**.

---

## 1. Urutan Menyalakan Listrik Alat

Nyalakan daya dengan urutan berikut:
1. Nyalakan **Adaptor Powered USB Hub 5V (≥ 2A)** *(3 Arduino Uno + 3 LCD TFT menyala)*.
2. Nyalakan **PSU Eksternal 5V LED Strip** dan **Adaptor 12V Kipas Vakum**.
3. Nyalakan **Adaptor 5V Raspberry Pi 3B+** *(disarankan 5V 2.5A–3A, tanpa monitor/keyboard/Ethernet)*.
4. Tunggu **±30–45 detik** — Raspi otomatis menyambung ke Wi-Fi serta menyalakan **Mosquitto (`:1883` / `:9001`)**, **`decy13.service` (`04_decy13_mqtt_daemon.py`)**, **`decy13-autolink.service` (`raspi_auto_link.py`)**, dan **`decy13-usb-hub.service` (`accelerator_hub.py`)** di background.

---

## 2. Membuka Pusat Kendali di Mini PC (CMD / PowerShell)

Buka **CMD** atau **PowerShell** di Mini PC, masuk ke folder utama `sp-aksel-polteknuklir`, lalu jalankan:

```cmd
cd C:\path\ke\sp-aksel-polteknuklir
python tools\minipc_control_hub.py
```

**Yang wajib dicek pada tampilan dashboard Mini PC:**
- **Status Raspi:** `[ONLINE] via UDP Auto-Link (51313)` *(bila belum langsung muncul karena hotspot memblokir broadcast, tekan **`R`** untuk scan ulang, atau tekan **`M`** untuk memasukkan IP Wi-Fi Raspi manual)*.
- **Layanan Raspi:** `Mosquitto 1883=AKTIF, 9001=AKTIF | Daemon=AKTIF | USB-Hub=AKTIF` *(bila ada service yang belum aktif, tekan **`2`** → Enter → masukkan password Raspi untuk auto-setup ulang semua service)*.
- **Daya 5V & Suhu:** target **`0x0 (Tegangan 5V Stabil / Normal)`**. *(Jika muncul peringatan `UNDER-VOLTAGE`, segera ganti adaptor/kabel micro-USB Raspi.)*

---

## 3. Menjalankan Web HMI Offline & Uji Divisi 1, 2, 3, 5

Di menu `minipc_control_hub.py` pada Mini PC:
1. Ketik **`5`** → tekan **Enter**.
   - Server Web HMI Offline otomatis aktif di `http://127.0.0.1:8000` (anti 404).
   - Alamat **`ws://<IP_WIFI_RASPI>:9001`** otomatis disalin ke Clipboard Windows.
   - Browser Chrome / Edge terbuka otomatis.
2. Di browser Web HMI:
   - Klik tombol biru **`Developer Menu`** (pojok kanan atas).
   - Klik kotak **Koneksi Broker Mosquitto (WebSocket Port 9001)** → tekan **`Ctrl + A`** lalu **`Ctrl + V`**.
   - Klik **`Hubungkan MQTT`** → pastikan muncul log **`✅ MQTT TERHUBUNG`** dan badge berubah hijau.
3. Tutup popup Developer Menu, lalu uji sekuens penuh alat nyata:
   1. Klik **`Power`** → Buzzer `GPIO 17` berbunyi 5 detik, Stage `1`.
   2. Klik **`Vacuum`** → Relay `GPIO 21` aktif & **Kipas Vakum 12V berputar**, tekanan turun hingga `<= 1e-3 mbar` (Stage `4`).
   3. Klik **`Interlocks`** → Stage `5` (*Beam Ready*).
   4. Klik **`Start Beam`** → LED Strip WS2812B spiral menyala (Stage `6`).
   5. Klik **`Shoot`** → LED beam/extraction menyala & arus target aktif (Stage `7`).
   6. Klik tombol merah **`EMERGENCY_STOP`** → **Kipas Vakum langsung mati, LED padam total, RF/Beam terputus, & Buzzer alarm berbunyi 3 detik!**

---

## 4. Mengaktifkan & Menguji 3-LCD TFT Arduino Uno (Divisi 4)

### A. Pemasangan Symlink USB `udev` (Cukup 1x Seumur Hidup)
1. Di menu `minipc_control_hub.py`, ketik **`1`** → **Enter** (masuk SSH Raspi).
2. Jalankan:
   ```bash
   cd ~/decy13/AKSEL-DECY13
   sudo apt install -y python3-serial python3-paho-mqtt
   sudo bash raspi/setup_udev.sh
   ls -l /dev/arduino_{hmi,sensor,actuator}
   exit
   ```
   *(Ikuti petunjuk di layar untuk memilih port USB fisik Uno 1 `hmi`, Uno 2 `sensor`, dan Uno 3 `actuator`. Jangan tukar posisi colokan kabel USB pada hub setelah disimpan.)*

### B. Status Bridge USB → MQTT (`decy13/usb/*`)
1. Jika service `decy13-usb-hub.service` sudah dipasang lewat menu **`2`**, Hub 3-TFT menyala otomatis setiap boot. Jika ingin restart atau cek log Hub 3-TFT, cukup ketik **`3`** → **Enter** di menu `minipc_control_hub.py`.
2. Cek di **Web HMI Mini PC** (`http://127.0.0.1:8000`):
   - **Panel tiga TFT · USB Raspberry Pi** di bawah header menampilkan status `TFT 1`, `TFT 2`, dan `TFT 3` aktif.
   - Pastikan **Uno 3 memiliki interlock `A5 ↔ GND` tertutup** (`guard=1`), lalu uji sentuh layar TFT Uno 1–3 atau tombol Panel 3-TFT di Web HMI.

---

## 5. Menghubungkan Node-RED & Uji QA (Divisi 6)

1. **Uji QA Cepat CLI (22 Field JSON & ~5 Hz):**
   Di menu `minipc_control_hub.py`, ketik **`6`** → **Enter** *(menjalankan `06_test_mqtt_healthcheck.py --host <IP_RASPI> --duration 10 --no-menu`)*.
2. **Dashboard Node-RED (`/cyclotron`, `/api/status`, `/api/usb/status`):**
   - Pastikan **Mosquitto Windows di Mini PC tetap MATI** (`Stop-Service mosquitto`).
   - Buka editor Node-RED di Mini PC: `http://127.0.0.1:1880`.
   - Import `decy13_mqtt_kit/nodered/flows_mqtt_decy13.json` (dan opsional `AKSEL-DECY13/raspi/nodered_usb.json`).
   - Klik 2x node broker **`Local Mosquitto Broker`** → ubah Server menjadi **`<IP_WIFI_RASPI>`** port **`1883`** → klik **Deploy**.
   - Buka `http://127.0.0.1:1880/cyclotron` *(target: **`Telemetry ONLINE`**)*.
   - Jalankan audit 30 / 300 sampel di PowerShell Mini PC:
     ```powershell
     cd .\decy13_mqtt_kit\qa_divisi6\scripts
     .\qa_readonly_api.ps1 -Samples 30
     ```

---

## 6. Uji Isolasi Penuh 448 LED + Buzzer `GPIO 17` (Divisi 3)

> **Catatan:** Mulai versi ini, `config_hardware.json` sudah disinkronkan penuh ke **448 LED (`0..399` spiral + `400..447` beam, `brightness: 15`)**, `estop_hardware_enabled: false`, dan `broker_host: 127.0.0.1`, sehingga **Core Daemon langsung mengendalikan seluruh 448 LED saat `Start Beam` & `Shoot`**. Jika tetap ingin menjalankan uji isolasi `03_test_led_pixel_finder.py` secara terpisah, hentikan sementara `decy13.service` agar tidak berebut pin `GPIO 18` & `GPIO 17`.

1. Di menu `minipc_control_hub.py`, ketik **`1`** → **Enter** (SSH ke Raspi).
2. Jalankan:
   ```bash
   sudo systemctl stop decy13.service
   cd ~/decy13/decy13_mqtt_kit/raspi_cli

   # Mode interaktif aman (default brightness=10; menu: f=semua, s=spiral, e=beam, b=charge+shot, q=keluar):
   sudo python3 03_test_led_pixel_finder.py --mode finder --hardware

   # Atau 9 tes otomatis penuh (tambahkan --power-ok HANYA setelah PSU 5V untuk 448 LED siap):
   # sudo python3 03_test_led_pixel_finder.py --mode finder --hardware --auto --power-ok
   ```
3. Setelah selesai tekan **`q`** *(LED mati & `GPIO.cleanup(17)` otomatis)*, lalu nyalakan kembali daemon utama:
   ```bash
   sudo systemctl start decy13.service
   exit
   ```

---

## 7. Prosedur Mematikan Alat dengan Aman (*Shutdown*)

1. Tekan **`EMERGENCY_STOP`** di Web HMI (pastikan kipas, LED, dan keluaran Uno 3 padam).
2. Matikan Raspberry Pi secara halus lewat menu `minipc_control_hub.py` → ketik **`1`** (SSH) → jalankan:
   ```bash
   sudo poweroff
   ```
3. Tunggu **±15 detik** sampai lampu hijau (ACT) di board Raspberry Pi berhenti berkedip dan mati total.
4. Cabut/matikan seluruh catu daya: Adaptor Raspi, PSU Eksternal 5V LED, Adaptor 12V Kipas, dan Adaptor Powered USB Hub.

---

## 8. Troubleshooting Kilat di Lapangan

| Kendala | Solusi Cepat |
| :--- | :--- |
| **Ganti Wi-Fi / Hotspot baru** | Pastikan Raspi masih terhubung ke hotspot lama dulu → di menu `minipc_control_hub.py` ketik **`4`** → masukkan Nama & Password Wi-Fi baru agar tersimpan otomatis di Raspi. |
| **Status Raspi `[BELUM TERDETEKSI]`** | Pastikan Wi-Fi Mini PC sama dengan Raspi → tekan **`R`** (*Scan Ulang*). Jika hotspot memblokir scan, lihat IP Raspi di daftar *Connected Devices* HP → tekan **`M`** lalu ketik IP-nya. |
| **Muncul peringatan `UNDER-VOLTAGE`** | Jangan lanjutkan beban penuh! Ganti adaptor/kabel micro-USB Raspi dengan **5V 2.5A–3A** yang lebih stabil, pastikan kabel Ethernet dicabut, dan pastikan 3 Uno memakai **Powered USB Hub** beradaptor sendiri. |
| **Panel 3-TFT tidak muncul / port Uno tertukar** | Pastikan kabel 3 Uno tidak berpindah soket di USB Hub. Jalankan ulang `sudo bash ~/decy13/AKSEL-DECY13/raspi/setup_udev.sh` via menu **`1`**, lalu nyalakan ulang menu **`3`**. |
| **Web HMI gagal konek ke `ws://...:9001`** | Cek di menu `minipc_control_hub.py` apakah `Mosquitto 9001=AKTIF` dan tidak ada Mosquitto lokal Windows yang hidup. Jika `9001=MATI`, tekan **`2`** untuk perbaikan otomatis. |
