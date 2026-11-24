# Prompt Anatomy #02 — Audit Menyeluruh Kode, Rangkaian Hardware, Sinkronisasi Raspberry Pi, & Penyelarasan Digital Twin HTML

## 1. Metadata Sesi
- **Tanggal & Waktu:** `2026-11-24 21:39 WIB`
- **Pemberi Instruksi:** Ketua Tim / Divisi 1 (`azfaaksan-hub`)
- **Stasiun Eksekusi:** Mini PC Ruang Kontrol (`C:\sp-aksel-polteknuklir`, branch `main` @ `baea951` + perbaikan lokal anti-konflik `GPIO 18`)
- **Cakupan Sistem:** Mini PC (`decy13_startup_wizard.py`, `minipc_control_hub.py`, `decy13_raspi_mcp.py`, `web_hmi/index.html`) ↔ Broker Mosquitto (`:1883` / `:9001`) ↔ Raspberry Pi 3B+ (`04_decy13_mqtt_daemon.py`, `config_hardware.json`, `mod_vacuum_safety.py`, `mod_led_ws2812b.py`, `accelerator_hub.py`) ↔ Rangkaian Fisik (Relay Kipas 12V, Buzzer SFM-27, 448 LED WS2812B, 3 Arduino Uno TFT USB).

---

## 2. Raw Prompt (Teks Asli Pengguna)
> coba pastikan ulang keseluruhan kode untuk berjalan lalu untuk ke rangkaian juga. pastikan kode2 memang saling terhubung lalu di raspinya juga di cek untuk di update juga atau tidak disesuaikan juga ke yang html juga ya kode yang berjalan seharusnya gmn gitu nah dari sini buat dulu prompt anatomi lalu ya seperti prompt panjang sebelum2 nya yang baru kamu proses sendiri prompt itu

---

## 3. Bedah Anatomi Prompt (8 Komponen)

### A. Role & Persona
Bertindak sebagai **Chief Systems Integrator & Verification Lead** proyek **Siklotron DECY-13 (13 MeV H⁻)** yang bertanggung jawab memastikan kesatuan end-to-end antara perangkat lunak Mini PC, tampilan Digital Twin HTML, daemon serta layanan di Raspberry Pi 3B+, hingga kecocokan sinyal listrik pada rangkaian perangkat keras fisik.

### B. Context & Hardware Constraints
- Sebelumnya ditemukan dua akar kendala kritis pada pengujian lapangan:
  1. Konflik pin `GPIO 18` di mana `LcdDisplayModule` (`luma.lcd.device.ili9341` default `gpio_LIGHT=18`) menimpa pin PWM0 WS2812B menjadi `OUTPUT HIGH` (`op hi`), yang telah diatasi di sisi Mini PC melalui `lcd_spi_enabled: false` di `config_hardware.json` dan `04_decy13_mqtt_daemon.py`.
  2. Gejala `throttled=0x50005` (*under-voltage*) pada catu daya 5V Raspberry Pi 3B+ yang sempat membuat unit restart/offline.
- Revisi animasi **448 LED 2-Fase (`brightness: 45`)** di `mod_led_ws2812b.py` kini memiliki perilaku spesifik per tahap (Stage 0 padam, Stage 1–3 sumber ion `0..15` biru, Stage 4 vakum `0..99` ungu-biru, Stage 5 sumber ion cyan + 4 blok RF Gap `99/199/299/399` kuning, Stage 6 Fase 1 dua komet cyan berekor 25 LED berseberangan `80–300 LED/dtk` + kilatan RF Gap, Stage 7 Fase 2 komet ekstraksi `400..447` oranye-emas berekor 16 LED + kilatan dampak hijau-emas 8 LED ujung `440..447`).
- Tampilan kanvas Digital Twin di `decy13_mqtt_kit/web_hmi/index.html` perlu diselaraskan penuh agar merepresentasikan perilaku **kode LED 2-fase yang sebenarnya berjalan di Raspi** (termasuk nyala Stage 1–5, 2 komet berseberangan + 4 titik RF Gap di Fase 1, kilatan dampak 8 LED ujung di Fase 2, dan rumus kecepatan simulasi yang identik).

### C. Active Skills Stack
1. **`systematic-debugging` & `verification-before-completion`** (`obra/superpowers` — ★ 325.541): Verifikasi lintas komponen (kode ↔ MQTT ↔ SSH Raspi ↔ rangkaian) berbasis bukti eksekusi nyata.
2. **`frontend-design`** (`anthropics/skills` — ★ 199.689), **`hallmark`** (`Nutlope/hallmark` — ★ 60.326), & **`antislop-ui`** (`miqdadbadjuber/anti-slop` — ★ 10.004): Menjaga konsistensi visual konsol industri bebas *AI slop* saat memperbarui kanvas Digital Twin di `web_hmi/index.html`.
3. **`web-design-guidelines`** (`vercel-labs/agent-skills` — ★ 34.843): Keterbacaan status perangkat keras & kejelasan umpan balik operator.

### D. Core Deliverables & Checklist Audit
1. **Audit Keterhubungan Kode Lintas Komponen (End-to-End):**
   - Verifikasi kecocokan kontrak JSON, nama field, batas setpoint (`setpoint_limits`), topik MQTT (`decy13/hmi/cmd`, `decy13/rpi/state`, `decy13/usb/state|cmd|ack`), dan jembatan `/api/runtime-config` antara `decy13_startup_wizard.py` / `minipc_control_hub.py` ↔ `web_hmi/index.html` ↔ `04_decy13_mqtt_daemon.py` ↔ `mod_vacuum_safety.py` + `mod_led_ws2812b.py` + `AKSEL-DECY13/raspi/accelerator_hub.py`.
2. **Audit Kesesuaian Kode terhadap Rangkaian Fisik:**
   - Verifikasi nomor pin BCM vs Pin Fisik 40-pin RPi 3B+, logika `Active-LOW` (Relay `GPIO 21` = `HIGH` saat mati, `LOW` saat pompa aktif), `Active-HIGH` (Buzzer `GPIO 17`), `PWM0/DMA10` (`GPIO 18` bebas konflik `luma.lcd` & `snd_bcm2835`), `estop_hardware_enabled: false`, pemisahan catu daya 5V RPi vs PSU 5V LED vs 12V Kipas vs Powered USB Hub 3-Uno, serta syarat Interlock `A5 ↔ GND` Uno 3.
3. **Penyelarasan Penuh `web_hmi/index.html` dengan Perilaku Aktual Kode Raspi:**
   - Memperbarui `drawCyclotronSimulator()`, `renderStrip()`, rumus kecepatan simulasi lokal, dan teks referensi teknis di `decy13_mqtt_kit/web_hmi/index.html` agar 100% mencerminkan perilaku nyata `04_decy13_mqtt_daemon.py` + `mod_led_ws2812b.py` (Stage 0 s.d. Stage 7 2-Fase, 2 komet spiral berseberangan, 4 blok RF Gap `[99,199,299,399]`, dampak ujung target `440..447`, `brightness: 45`, `lcd_spi_enabled: false`).
4. **Pemeriksaan & Sinkronisasi Langsung ke Raspberry Pi:**
   - Memeriksa status online Raspberry Pi via UDP `51313` & SSH key (`sp-aksel`).
   - Jika Raspberry Pi online: memeriksa apakah file di `~/decy13` masih tertinggal dari Mini PC (khususnya perbaikan anti-konflik `GPIO 18` di `04_decy13_mqtt_daemon.py`, `config_hardware.json`, & `tools/raspi_bootstrap.sh`), menyalin pembaruan file via `scp`, serta memeriksa `pinctrl get 18` dan `vcgencmd get_throttled`.
   - Jika Raspberry Pi masih offline (sedang perapian adaptor/wiring): memastikan skrip sinkronisasi 1-klik (`MULAI_DECY13.bat` → `[1]` atau `[2] -> [S]`) sudah mencakup seluruh file terbaru sehingga siap pakai seketika saat Raspi dinyalakan.
5. **Verifikasi Akhir Berlapis:**
   - Uji sintaks seluruh skrip Python (`raspi_cli/` & `tools/`), uji virtual Divisi 3 (`03_test_led_pixel_finder.py --mode test`), audit anti-slop HTML, uji endpoint `/api/runtime-config`, dan `python tools/cek_integrasi_dan_announcer.py --ci --cek-branch` hingga `7/7 [LULUS]`.

### E. Execution Pipeline (Urutan Kerja)
1. **Tahap 1 (Dokumen Ini):** Simpan Prompt Anatomy #02 di `prompt_logs/` dan perbarui `prompt_logs/README.md`.
2. **Tahap 2:** Periksa keterhubungan seluruh file kode (`04_decy13_mqtt_daemon.py`, `mod_vacuum_safety.py`, `mod_led_ws2812b.py`, `accelerator_hub.py`, `minipc_control_hub.py`, `decy13_startup_wizard.py`) terhadap skema rangkaian & kontrak MQTT.
3. **Tahap 3:** Perbarui `decy13_mqtt_kit/web_hmi/index.html` agar simulasi & visualisasi Digital Twin 448 LED-nya identik dengan algoritma 2-fase di Raspi.
4. **Tahap 4:** Cek koneksi Raspberry Pi saat ini via MCP / SSH; sinkronkan file terbaru ke `~/decy13` bila Raspi online dan laporkan status nyatanya.
5. **Tahap 5:** Jalankan seluruh rangkaian pengujian verifikasi (`0` warning, `ALL DIVISI 3 VIRTUAL TESTS PASSED`, `7/7 [LULUS]`) dan sajikan peta hasil audit lengkap beserta langkah eksekusi berikutnya.

### F. Hard Guardrails (`AGENTS.md`)
- **Dilarang** menjalankan `git commit`, `git push`, `git merge`, atau pindah branch secara otomatis.
- **Dilarang** mengubah file eksklusif Divisi 2 (`mod_vacuum_safety.py`, `01_test_relay_buzzer.py`), Divisi 4 (`AKSEL-DECY13/*`, `mod_lcd_ili9341.py`), dan Divisi 6 (`flows_mqtt_decy13.json`, `qa_divisi6/*`).
- Pastikan `tools/raspi_bootstrap.sh` tetap **LF murni** tanpa CRLF.

---

## 4. Refined Structured Prompt (Yang Langsung Diproses Sekarang)

```text
Berdasarkan Prompt Anatomy #02 dan aturan AGENTS.md:
1. Audit menyeluruh keterhubungan kode end-to-end (Startup Wizard & Control Hub -> Web HMI HTML -> Broker MQTT -> Core Daemon RPi -> Modul Vakum/Buzzer Divisi 2, Modul 448 LED 2-Fase Divisi 3, & Hub 3-TFT USB Divisi 4) serta verifikasi kecocokannya dengan rangkaian hardware fisik (pinout, Active-LOW/HIGH, isolasi GPIO 18 PWM0 dari luma.lcd & snd_bcm2835, serta pemisahan catu daya).
2. Selaraskan Web HMI (`decy13_mqtt_kit/web_hmi/index.html`) agar visualisasi Digital Twin kamar Dee & jalur ekstraksi menampilkan perilaku identik dengan kode Raspi terbaru:
   - Stage 0 / E-Stop: semua LED padam.
   - Stage 1-3: sumber ion (0..15) biru cerah.
   - Stage 4 (Vakum): 1/4 awal spiral (0..99) ungu-biru terang.
   - Stage 5 (Beam Ready): sumber ion cyan + 4 blok RF Gap [99, 199, 299, 399] kuning.
   - Stage 6 (Fase 1): 2 komet cyan berseberangan berekor proporsional (80-300 LED/dtk) + kilatan kuning emas saat melintas 4 RF Gap.
   - Stage 7 (Fase 2): spiral tetap aktif + komet ekstraksi 400..447 oranye-emas + kilatan dampak hijau-emas di 8 LED ujung target (440..447).
3. Cek status Raspberry Pi saat ini via UDP/SSH: bila online, cek versi kode di `~/decy13`, salin file pembaruan yang belum masuk, dan periksa `pinctrl get 18` serta `vcgencmd get_throttled`; bila offline, pastikan mekanisme update otomatis di Mini PC siap 100%.
4. Jalankan seluruh verifikasi wajib (`py_compile`, `03_test_led_pixel_finder.py --mode test`, audit anti-slop HTML, dan `cek_integrasi_dan_announcer.py --ci --cek-branch` hingga `7/7 [LULUS]`) lalu laporkan hasil lengkapnya secara ringkas dan praktis.
```
