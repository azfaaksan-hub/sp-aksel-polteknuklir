# Panduan Stasiun Uji Lapangan — Mini PC Ruang Kontrol & Raspberry Pi 3B+

Dokumen ini khusus dibuat untuk **Mini PC Ruang Kontrol** (termasuk **Windows 8 / 10 / 11**) yang terhubung langsung ke **Raspberry Pi 3B+** saat pengujian alat fisik **Siklotron DECY-13**, agar sesi **Antigravity (AGY)** di Mini PC langsung paham konteks proyek tanpa membutuhkan riwayat percakapan dari laptop utama.

---

## 1. Pembagian Peran 3 Mesin (Wajib Dijaga Supaya Bebas Konflik Git)

| Mesin | Peran Resmi | Branch | File yang BOLEH Diubah | File yang DILARANG Diubah Langsung |
| :--- | :--- | :---: | :--- | :--- |
| **Laptop Utama Ketua** (`azfaaksan-hub`) | Pusat integrasi, review branch, & pembaruan dokumen tim | `main` | `README.md`, `tools/*`, `04_decy13_mqtt_daemon.py`, `config_hardware.json`, `UJI_DIVISI_1_CORE_RASPI.md` | File eksklusif Divisi 2–6 tanpa review |
| **Mini PC Ruang Kontrol** (`Windows 8`) | **Stasiun Uji Web HMI, QA Healthcheck, & Terminal SSH ke RPi** | `main` *(hanya `git pull origin main`)* | Log/bukti lapangan di `laporan_uji/bukti/` (bila perlu) | **Semua file kode Divisi 2–6** (`mod_*.py`, `01/02/03/06_*.py`, `web_hmi/index.html`, `UJI_DIVISI_2..6_*.md`) |
| **Raspberry Pi 3B+** | **Stasiun Eksekusi Hardware & Broker Mosquitto** | `main` *(hanya `git pull origin main`)* | File konfigurasi OS lokal RPi (`/boot/...`, `/etc/mosquitto/...`) | Jangan edit kode Python/HTML lokal di RPi tanpa koordinasi branch |

---

## 2. Status Proyek Terkini Saat Dokumen Ini Ditulis

- **Branch `main` aktif (`v1.5.1`):** sudah berisi modul lengkap **Divisi 2** (`66930bb`), **Divisi 3** (`ac21a27` via `divisi-3-led-ws2812b-v13`), dan **Divisi 6** (`4ed588d` + `b2b42f6`).
- **Divisi 2 (Vakum, Relay Kipas 12V, Buzzer, E-Stop):** pengujian sistem vakum selesai di lapangan, namun masih dalam proses konfirmasi dan **belum di-push updatenya oleh `dzakimumtazi`**. **JANGAN** mengubah `mod_vacuum_safety.py`, `01_test_relay_buzzer.py`, atau `laporan_uji/UJI_DIVISI_2_VAKUM_SAFETY.md` dari Mini PC.
- **Fokus Pengujian Aktif Sekarang — Divisi 3 (LED Strip WS2812B, `GPIO 18`):**
  - Gunakan **`main`** (kode Divisi 3 versi terbaru `divisi-3-led-ws2812b-v13` sudah di-merge ke `main`; abaikan branch usang `origin/divisi-3-led-ws2812b`).
- **Divisi 4 (`LCD ILI9341`) & Divisi 5 (`Web HMI SCADA`):** branch `origin/hmi+tft` masih tertinggal di `045c321` dan menunggu anggota (`HDMrishiki`) menarik `origin/main` serta men-push update mereka.

---

## 3. Pengaturan Koneksi Mini PC Windows 8 <-> Raspberry Pi

Karena Mini PC memakai **Windows 8**, perhatikan 4 hal khusus ini:
1. **Jangan memakai `.local`** (`sp-aksel.local` / `raspberrypi.local`) karena Windows 8 tidak mendukung resolver mDNS secara bawaan. **Selalu pakai IP angka RPi** (misal `192.168.137.xxx`).
2. **Jangan memakai `ssh` di CMD/PowerShell standar** jika Windows 8 tidak punya OpenSSH Client — gunakan **Git Bash** (klik kanan folder repo → *Open Git Bash here*) atau **PuTTY**.
3. **Jika memakai kabel LAN langsung (Ethernet berstatus *Unidentified network*):**
   - **Cara terbaik (jika Mini PC terhubung Wi-Fi internet):** buka `Win + R` → `ncpa.cpl` → klik kanan **Wi-Fi** → **Properties** → tab **Sharing** → centang *"Allow other network users..."* → pilih **Ethernet** → **OK**. Windows otomatis mengeset Ethernet ke `192.168.137.1`. Cabut-colok kabel LAN RPi, tunggu 30 detik, lalu cek IP RPi lewat `arp -a` di CMD (`192.168.137.xxx`).
   - **Jika Mini PC tidak punya Wi-Fi:** pakai **Hotspot HP 2.4 GHz (WPA2)** untuk menyambungkan keduanya, atau set IP statik sekelas (mis. Mini PC `192.168.50.1`, RPi `192.168.50.2`).
4. **Jika SSH muncul `REMOTE HOST IDENTIFICATION HAS CHANGED` / `Host key verification failed`:**
   Jalankan di Git Bash Mini PC:
   ```bash
   ssh-keygen -R <IP_RASPI>
   ssh <username_rpi>@<IP_RASPI>
   ```
   *(Menghapus key hanya me-reset sidik jari IP di Mini PC — file di RPi dan repo tetap utuh 100%.)*
5. **Browser & Python di Windows 8:**
   - Buka Web HMI dengan **Chrome / Edge versi 109** atau **Firefox 115 ESR** (bukan Internet Explorer), dengan koneksi internet aktif agar CDN Tailwind & `mqtt@5.3.4` termuat.
   - Jika menjalankan skrip Python QA di Mini PC Win 8, gunakan Python **3.8–3.10** + `pip install paho-mqtt`.

---

## 4. Data & Perintah yang Harus Disiapkan Saat Uji Lapangan

### A. Di Sisi Mini PC (Windows 8)
1. **Tarik update Git terbaru sebelum mulai uji:**
   ```bash
   git checkout main
   git pull origin main
   ```
2. **Ubah endpoint WebSocket di UI browser saja (JANGAN edit isi file `web_hmi/index.html`):**
   - Buka `decy13_mqtt_kit/web_hmi/index.html` di Chrome/Edge (atau jalankan `python -m http.server 8000 --directory decy13_mqtt_kit/web_hmi` lalu buka `http://localhost:8000`).
   - Di panel koneksi MQTT Web HMI, ubah kotak **WebSocket URL Endpoint** dari default `ws://127.0.0.1:9001` menjadi **`ws://<IP_RASPI>:9001`**, lalu klik **Hubungkan MQTT**.
   - Pastikan badge di atas berubah hijau: **`MQTT TERHUBUNG - RPi 3B+`**.
3. **Pastikan TIDAK ada broker Mosquitto Windows berjalan di Mini PC** saat sedang menghubungkan HMI ke Mosquitto RPi.
4. *(Opsional tes QA dari Mini PC):*
   ```powershell
   python decy13_mqtt_kit/raspi_cli/06_test_mqtt_healthcheck.py --host <IP_RASPI> --duration 5 --no-menu
   ```

### B. Di Sisi Raspberry Pi 3B+ (via Git Bash SSH dari Mini PC)
1. **Pastikan folder kerja adalah repo Git di branch `main` terbaru:**
   ```bash
   cd ~/sp-aksel-polteknuklir   # sesuaikan dengan lokasi hasil clone di RPi
   git rev-parse --show-toplevel
   git fetch origin && git checkout main && git pull origin main
   hostname -I
   ```
2. **Bootstrap (wajib 1x bila pindah/pinjam unit RPi baru):**
   ```bash
   bash tools/raspi_bootstrap.sh
   # Jika skrip meminta reboot agar dtparam=audio=off & spi=on aktif, jalankan:
   sudo reboot
   ```
3. **Preflight Divisi 3 (membuat bukti log otomatis di `laporan_uji/bukti/`):**
   ```bash
   python3 tools/raspi_preflight.py --divisi 3
   grep -E '^dtparam=(audio=off|spi=on)' /boot/firmware/config.txt /boot/config.txt 2>/dev/null
   ```

---

## 5. Tahapan Uji Fisik Divisi 3 (LED Strip WS2812B — `GPIO 18`)

### Cek Wiring Wajib Sebelum Menyalakan LED
- `DIN` LED Strip WS2812B → **`GPIO 18` (Pin Fisik `12`)** melalui resistor **330 Ohm**.
- Catu daya **64 piksel LED** memakai **PSU 5V 3A eksternal**, dan **`GND` PSU 5V wajib disatukan (*common ground*) dengan `GND` Raspberry Pi**.
- **`dtparam=audio=off` sudah aktif dan RPi sudah reboot** (wajib, karena audio onboard memakai PWM0 pada `GPIO 18`).

### Langkah 1 — Uji Isolasi Piksel & Warna (`03_test_led_pixel_finder.py`)
Jalankan di RPi dengan **`sudo`** (wajib untuk akses DMA `rpi_ws281x`):
```bash
cd ~/sp-aksel-polteknuklir/decy13_mqtt_kit/raspi_cli
sudo python3 03_test_led_pixel_finder.py --mode finder --hardware
```
> **Penting:** Skrip ini hanya menerima `--mode test` (virtual) dan `--mode finder` (fisik dengan `--hardware`). Menu uji spiral & shoot dijalankan langsung di dalam mode `finder` lewat tombol huruf di bawah ini.

Di prompt `LED #0 >`:
1. **Tekan `Enter` berulang (atau ketik nomor indeks `0`..`63`)** → pastikan seluruh 64 piksel menyala biru muda berurutan tanpa loncat/mati tengah.
2. **Ketik `s` lalu `Enter`** → uji animasi **Spiral Acceleration** (`0..47` biru muda + titik RF Gap `[11, 23, 35, 47]` kuning terang).
3. **Ketik `e` lalu `Enter`** → uji jalur **Extraction / Shoot** (`48..63` oranye).
4. **Cek kesesuaian warna:** bila warna biru/kuning/oranye tampak tertukar (misal merah tertukar hijau — ciri khas strip GRB pada `PixelStrip` default), **catat temuan tersebut**.
5. **Ketik `q` atau `Ctrl+C`** → pastikan semua 64 LED padam total.

### Langkah 2 — Uji Terintegrasi Daemon + Web HMI Mini PC
1. Di RPi, nyalakan daemon utama:
   ```bash
   cd ~/sp-aksel-polteknuklir/decy13_mqtt_kit/raspi_cli
   sudo python3 04_decy13_mqtt_daemon.py
   ```
   Pastikan pada output inisialisasi muncul **`- LedStripModule         : [HARDWARE AKTIF]`**.
2. Di **Web HMI Mini PC** (status hijau `MQTT TERHUBUNG - RPi 3B+`), jalankan urutan tombol:
   - `Power` → LED awal menyala redup biru (*standby*).
   - `Vacuum` → tunggu tekanan turun sampai `<= 1.0e-3 mbar` (~6–7 detik; LED ungu menyala).
   - `Interlock` → status *Beam Ready* (marker sumber + RF gap menyala).
   - `Start Beam` → **komet LED spiral (`0..47`) berputar di alat fisik sekaligus sinkron dengan kanvas Web HMI!**
   - `Shoot` → **LED extraction (`48..63`) aktif**.
   - `Emergency Stop` atau tekan `Ctrl+C` di RPi → **seluruh LED padam bersih**.

### Penanganan Data Hasil Uji (Anti-Konflik)
- Salin output terminal `raspi_preflight.py --divisi 3` & `03_test_led_pixel_finder.py` beserta catatan urutan indeks/warna (RGB/GRB) lalu kirim ke **Divisi 3 (`blufiaa`)** agar dia melengkapi Bagian B/C pada `laporan_uji/UJI_DIVISI_3_LED_WS2812B.md` melalui branch-nya.
- Jika urutan indeks LED fisik (`spiral_start_idx..end_idx`, `rf_gap_indices`, `shoot_start_idx..end_idx`) ternyata berbeda dari `0..47` dan `48..63`, **catat dulu indeks pastinya** lalu koordinasikan perubahan `config_hardware.json` dari **Laptop Utama Ketua** agar seluruh divisi menerimanya serentak.

---

## 6. Prompt Siap Copy-Paste untuk Antigravity (AGY) di Mini PC

Setelah `git pull origin main` di Mini PC, kamu cukup membuka file ini dan menempelkan prompt singkat di bawah ini ke chat baru Antigravity di Mini PC:

```text
Saya Ketua Tim (Divisi 1 / `azfaaksan-hub`) sedang menguji alat langsung dari Mini PC Ruang Kontrol (Windows 8) yang terhubung ke Raspberry Pi 3B+.
Baca file `decy13_mqtt_kit/PANDUAN_MINI_PC_UJI_LAPANGAN.md`, `README.md`, dan jalankan `python tools/raspi_preflight.py --divisi 3 --no-save` (serta `git status -sb`).
Patuhi seluruh aturan di `PANDUAN_MINI_PC_UJI_LAPANGAN.md`:
- Mini PC hanya sebagai Stasiun Uji (JANGAN edit file Divisi 2–6 atau menjalankan git commit/push otomatis).
- Divisi 2 (Vakum) masih proses konfirmasi & belum di-push oleh Divisi 2 -> JANGAN sentuh file Divisi 2.
- Fokus sekarang memandu uji fisik Divisi 3 (LED WS2812B GPIO 18) di RPi + integrasinya dengan Web HMI di Mini PC Windows 8 (pakai Git Bash & IP angka RPi, tanpa .local).
Tampilkan: (1) status repo Mini PC & hal yang perlu dicek, (2) panduan langkah berikutnya di RPi dan Mini PC, dan (3) perintah terminal/SSH persis untuk saya jalankan sendiri.
```
