# Prompt Anatomy #01 — Startup Configuration Wizard, High-Star Skills, & Industrial Web HMI + Guided Instructor Loop

## 1. Metadata Sesi
- **Tanggal & Waktu:** `2026-11-24 18:58 WIB`
- **Pemberi Instruksi:** Ketua Tim / Divisi 1 (`azfaaksan-hub`)
- **Stasiun Eksekusi:** Mini PC Ruang Kontrol (`C:\sp-aksel-polteknuklir`, branch `main` @ `d34d306`)
- **Target Perangkat Keras:** Raspberry Pi 3B+ (`Debian 13 trixie Lite 64-bit`, user `sp-aksel`, mode **100% Wi-Fi Auto-Link tanpa Ethernet**), 448 LED WS2812B, Relay Kipas 12V + Buzzer, 3 Arduino Uno TFT USB.

---

## 2. Raw Prompt (Teks Asli Pengguna)
> buatkan program konfigurasi dulu saat baru hidup, dimana ada pilihan dulu mau auto setup atau nggak gitu manual, kan ini perlu diatur gitu jadi dari wifi nya yg belum ke detek si kasih arahan full untuk biar raspinya otomatis kekonek dan bisa diatur gitu, terus konfigurasi full nya auto set up gitu. lalu untuk uinya yg di html coba di buatkan lagi dengan menggunakan skill gitu biar ga terlalu terhilat ai banget sama tambahkan instruktur di mode uinya untuk mengarahkan penggunaanya dan ini bisa berulang gitu tiap udah selesai dan kalo ga diselesaiin bakal auto reset ke awal untuk tutorialnya untuk konfigurasinya diatur agar bisa auto gitu ngikut sama program untuk ngatur yang program konfigurasi raspi ke html biar jalannya normal gitu sama disini perlu juga diatur pemberian alurtnya install aja skill2 dari github kayak find skill auat yang anti ai slop gitu atau yang skill yang famous pastikan skill2nya star nya tinggi ribuan keatas gitu lalu penggunaannya pada prompt ini dibuatkan dulu folder log prompt karena prompt ini perlu agar dibuat bentuk prompt anatomy gitu yaaaa baru jalankan ulang perintah yang disuruh tadiii

---

## 3. Bedah Anatomi Prompt (8 Komponen)

### A. Role & Persona
Bertindak sebagai **Lead Control-System Engineer & Industrial HMI Designer** untuk alat peraga akselerator siklotron nuklir **DECY-13 (BRIN / Polteknuklir)** yang menggabungkan otomasi jaringan Windows ↔ Linux (`systemd`/`nmcli`/MQTT) dengan antarmuka ruang kendali berstandar instrumen laboratorium nyata (bukan tampilan template AI generik).

### B. Context & Hardware Constraints
- Mini PC Windows baru menyala tanpa terminal terbuka secara bawaan dan sering menghadapi kondisi Wi-Fi / Hotspot HP yang belum sama atau IP Raspberry Pi yang berubah dinamis (`.158` dengan oktet tengah acak).
- Kabel Ethernet (`eth0`) pada Raspberry Pi 3B+ **dilarang dipasang** karena memicu *under-voltage / brown-out*; seluruh komunikasi wajib **100% Wi-Fi** dan Mosquitto lokal Windows wajib dihentikan agar tidak bentrok.
- Web HMI sebelumnya mengharuskan pengguna menyalin `ws://<IP_RASPI>:9001` secara manual ke *Developer Menu*, masih memetakan 48+16 LED lama (padahal hardware aktual 400+48 = **448 LED**), memakai estetika kartu neon ungu-pink-biru bergaya AI generik, serta panduan kliknya berhenti begitu selesai tanpa siklus ulang atau *auto-reset* saat ditinggal pengguna.

### C. Active Skills Stack (Terpasang di `.agents/skills/` & `~/.gemini/config/skills/`)
Seluruh skill diunduh dari repositori GitHub terverifikasi dengan ribuan hingga ratusan ribu bintang:
1. **`systematic-debugging` & `verification-before-completion`** (`obra/superpowers` — **★ 325.541**): Alur diagnostik bertahap & kewajiban bukti verifikasi nyata sebelum klaim selesai.
2. **`frontend-design`** (`anthropics/skills` — **★ 199.689**): Pemilihan tipografi, struktur informasi nyata, penolakan klise layout/label AI generik.
3. **`hallmark`** (`Nutlope/hallmark` — **★ 60.326**): *Hard floor* anti-AI-slop (semua warna/font via CSS `:root` tokens, dilarang `transition: all`, dilarang gradien ungu-biru/pink, dilarang emoji sebagai ikon UI, wajib `:focus-visible` & `prefers-reduced-motion`).
4. **`find-skills`** (`vercel-labs/skills` — **★ 40.700**): Standar kurasi & instalasi ekosistem skill bereputasi tinggi.
5. **`web-design-guidelines`** (`vercel-labs/agent-skills` — **★ 34.843**): Keterbacaan kontrol, aksesibilitas, dan ketepatan status interaktif.
6. **`antislop` & `antislop-ui`** (`miqdadbadjuber/anti-slop` — **★ 10.004**): Penghapusan *glow* berlebihan, *pill* seragam, kartu seragam tanpa hierarki, dan teks dekoratif kosong.

### D. Core Deliverables (Spesifikasi Fungsional)
1. **Program Konfigurasi Awal Saat Baru Hidup (`tools/decy13_startup_wizard.py` + Launcher `MULAI_DECY13.bat`):**
   - Menampilkan layar sambutan saat Mini PC baru hidup dengan pilihan jelas:
     - **Mode Auto-Setup Penuh** (1 tombol: matikan Mosquitto lokal Windows → deteksi Wi-Fi & IP Raspi otomatis → jalankan update & 4 service `systemd` Raspi `--disable-eth` bila diperlukan → tulis sinkronisasi runtime → hidupkan server Web HMI & buka browser otomatis).
     - **Mode Konfigurasi Manual & Panduan Penuh Wi-Fi** (arahan langkah demi langkah bila Wi-Fi/Raspi belum terdeteksi: cek SSID Mini PC, panduan samakan Hotspot 2.4 GHz, cara tambah Wi-Fi baru ke Raspi via `nmcli` atau `nmtui` layar langsung tanpa Ethernet, scan ulang port TCP subnet, input IP manual, serta cek 3-TFT USB).
     - **Mode Simulasi Mandiri (Offline Pameran/Latihan)** tanpa Raspi.
     - **Pengaturan Auto-Run Windows Startup** (pasang/lepas shortcut otomatis di `shell:startup` agar wizard langsung muncul begitu Mini PC dinyalakan).
2. **Jembatan Sinkronisasi Otomatis Konfigurasi Raspi → Web HMI HTML (`runtime_config.json` & Endpoint `/api/runtime-config`):**
   - Program konfigurasi di Mini PC menyajikan HTTP server lokal (port `8000`) yang menyuplai `/api/runtime-config` (dan file statis fallback `assets/runtime_config.json`) secara *real-time*.
   - Web HMI membaca konfigurasi ini secara otomatis saat dibuka dan secara berkala di latar belakang: begitu IP Raspi ditemukan/berubah di program konfigurasi, Web HMI **otomatis mengisi endpoint `ws://<IP_RASPI>:9001` dan langsung menghubungkan MQTT** tanpa perlu *copy-paste* manual lagi.
3. **Redesign Web HMI (`decy13_mqtt_kit/web_hmi/index.html`) Berstandar Industrial Control Console (Anti-AI-Slop):**
   - Mengganti tampilan neon *gaming/AI-slop* dengan desain **konsol instrumentasi ruang kendali siklotron** (permukaan grafit matte, pembatas presisi 1px, palet sinyal fungsional standar IEC: hijau nominal, kuning/amber prasyarat/vakum, sian telemetri, merah tegas khusus *Emergency Stop*, ikon SVG teknis bersih tanpa dekorasi emoji, angka *tabular-nums* presisi, dan pemetaan akurat **448 LED**: `0..399` spiral + `400..447` ekstraksi).
   - Mempertahankan **100% kompatibilitas kontrak CI & Divisi 1–6**: topik `decy13/hmi/cmd`, `decy13/rpi/state`, fungsi `applyRpiState`, ke-8 perintah wajib (`TOGGLE_POWER`, `TOGGLE_VACUUM`, `TOGGLE_INTERLOCK`, `AUTO_INIT`, `START_BEAM`, `SHOOT`, `EMERGENCY_STOP`, `SET_PARAMS`), serta `assets/usb-panel.js` (Panel 3-TFT USB).
4. **Mode Instruktur Terpandu Berulang + Auto-Reset Inaktivitas:**
   - Panel & sorotan (*spotlight*) **Instruktur Operasi DECY-13** yang memandu pengguna langkah demi langkah dari kondisi awal (*Cold Standby*) hingga ekstraksi berkas target 13 MeV.
   - **Berulang Otomatis (Loop):** Begitu seluruh tahapan selesai, sistem menampilkan konfirmasi keberhasilan eksperimen lalu menghitung mundur singkat untuk **otomatis mengembalikan sistem ke kondisi awal & memulai ulang panduan dari Langkah 1** bagi pengguna berikutnya.
   - **Auto-Reset Saat Tidak Diselesaikan (Idle Timeout):** Bila pengguna berhenti berinteraksi di tengah tutorial melampaui batas waktu tunggu (default 60 detik, dilengkapi indikator hitung mundur yang jelas dan opsi jeda/ubah durasi), sistem **otomatis mengamankan/mematikan subsistem ke keadaan awal (*Cold Standby*)** baik di mode simulasi maupun hardware Raspi (`TOGGLE_POWER` aman tanpa sirene darurat palsu) dan mengembalikan tutorial ke Langkah 1.

### E. Execution Pipeline (Alur Eksekusi)
1. **Tahap 1 (Selesai):** Cari, verifikasi jumlah bintang (>10.000★), dan pasang 8 skill utama dari GitHub ke `.agents/skills/` & `~/.gemini/config/skills/`.
2. **Tahap 2 (Dokumen Ini):** Buat folder `prompt_logs/` dan susun dokumen **Prompt Anatomy** ini terlebih dahulu.
3. **Tahap 3:** Bangun `tools/decy13_startup_wizard.py`, perbarui `tools/minipc_control_hub.py` agar berbagi jembatan `runtime_config` yang sama, dan siapkan launcher klik-2x `MULAI_DECY13.bat`.
4. **Tahap 4:** Bangun ulang `decy13_mqtt_kit/web_hmi/index.html` mengikuti aturan `frontend-design`, `hallmark`, dan `antislop-ui`, lengkap dengan **Auto-Config Sync** dan **Mode Instruktur Berulang + Idle Auto-Reset**.
5. **Tahap 5:** Pastikan `tools/raspi_bootstrap.sh` tetap LF murni (tambahkan `.gitattributes` bila perlu agar Windows tidak mengubahnya menjadi CRLF), lalu jalankan verifikasi menyeluruh (`python tools/cek_integrasi_dan_announcer.py --ci --cek-branch`, uji endpoint `/api/runtime-config`, dan cek kualitas UI) sesuai `verification-before-completion`.

### F. Hard Guardrails (`AGENTS.md`)
- **Dilarang** menjalankan `git commit`, `git push`, `git merge`, atau pindah branch secara otomatis.
- **Dilarang** mengedit kode eksklusif Divisi 2, 3, 4, dan 6 (`mod_*.py`, `01/02/03/06_*.py`, `AKSEL-DECY13/*`, `flows_mqtt_decy13.json`, `qa_divisi6/*`).
- **Dilarang** mencentang ceklis fisik `laporan_uji/` tanpa bukti hardware nyata.

---

## 4. Refined Structured Prompt (Siap Dipakai / Dijalankan Ulang)

```text
Gunakan skill yang terpasang di `.agents/skills/` (`frontend-design`, `hallmark`, `antislop-ui`, `web-design-guidelines`, `systematic-debugging`, `verification-before-completion`) dan patuhi seluruh batas keamanan di `AGENTS.md`:

1. Buat program konfigurasi awal `tools/decy13_startup_wizard.py` beserta launcher `MULAI_DECY13.bat` (dengan opsi pasang ke Windows Startup) yang saat dijalankan memberi pilihan:
   - [1] Auto-Setup Penuh (matikan Mosquitto lokal Windows, deteksi Wi-Fi & IP Raspi 100% Wi-Fi tanpa Ethernet, setup/cek 4 service systemd Raspi, tulis konfigurasi aktif, dan buka Web HMI otomatis).
   - [2] Konfigurasi Manual & Panduan Penuh Wi-Fi (panduan interaktif lengkap saat Wi-Fi/Raspi belum terdeteksi, scan subnet, simpan Wi-Fi baru via nmcli/nmtui, input IP manual).
   - [3] Mode Simulasi Offline Mandiri.
2. Hubungkan program konfigurasi Raspi dengan Web HMI secara otomatis melalui endpoint `/api/runtime-config` (dan `assets/runtime_config.json`) pada server lokal port 8000 sehingga HTML otomatis membaca IP Raspi (`ws://<IP_RASPI>:9001`), langsung auto-connect ke broker MQTT, dan menyesuaikan mode tanpa copy-paste manual.
3. Rancang ulang `decy13_mqtt_kit/web_hmi/index.html` menjadi konsol ruang kendali industri Siklotron DECY-13 yang bebas gaya AI generik (tanpa gradien ungu-pink, tanpa dekorasi emoji, palet & tipografi teknikal presisi via CSS `:root` tokens, mendukung 448 LED penuh, dan menjaga 100% kontrak MQTT `decy13/hmi/cmd`, `decy13/rpi/state`, `applyRpiState`, 8 command wajib, serta `usb-panel.js`).
4. Tambahkan Mode Instruktur Terpandu di Web HMI yang memandu pengoperasian langkah demi langkah, otomatis mengulang dari awal setiap kali satu siklus selesai, dan otomatis me-reset sistem serta tutorial kembali ke awal apabila pengguna tidak menyelesaikannya dalam batas waktu diam (inactivity auto-reset).
5. Verifikasi hasil akhir hingga `python tools/cek_integrasi_dan_announcer.py --ci --cek-branch` lulus `7/7 [LULUS]`.
```
