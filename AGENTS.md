# AGENTS.md — Instruksi Otomatis Antigravity / AI di Repositori DECY-13

Repositori ini adalah proyek **Alat Peraga Akselerator Siklotron DECY-13 (13 MeV H⁻)** Politeknik Teknologi Nuklir Indonesia (BRIN) dengan arsitektur kolaborasi **6 Divisi** (`azfaaksan-hub` = Ketua / Divisi 1).

## Wajib Dilakukan Saat Memulai Sesi Baru (Khususnya di Mini PC Ruang Kontrol)
1. **Baca [`HANDOFF_ANTIGRAVITY_MINI_PC.md`](HANDOFF_ANTIGRAVITY_MINI_PC.md)** terlebih dahulu untuk mendapatkan seluruh konteks lanjutan percakapan, profil unit Raspberry Pi 3B+ (`Debian 13 trixie Lite 64-bit`, user `sp-aksel`, folder `~/decy13`, mode **100% Wi-Fi Auto-Link tanpa Ethernet**), serta daftar tugas troubleshooting aktif.
2. Baca [`PANDUAN_OPERASIONAL_PASCA_WIRING.md`](PANDUAN_OPERASIONAL_PASCA_WIRING.md) dan [`decy13_mqtt_kit/PANDUAN_MINI_PC_UJI_LAPANGAN.md`](decy13_mqtt_kit/PANDUAN_MINI_PC_UJI_LAPANGAN.md) bila menangani langkah operasional atau koneksi Divisi 6.

## Aturan Keras Workspace
- **Bahasa:** Selalu balas dalam **Bahasa Indonesia** yang ringkas, jelas, dan praktis (user di Mini PC lebih suka perintah **CMD / PowerShell**).
- **Git Mandiri (DILARANG OTOMATIS):** JANGAN pernah menjalankan `git commit`, `git push`, `git merge`, atau pindah branch secara otomatis. Selalu tampilkan perintahnya agar user menjalankan sendiri.
- **Batas File 6 Divisi:** Dari Mini PC (Stasiun Uji / Divisi 1), JANGAN mengedit file kode eksklusif Divisi 2–6 (`mod_vacuum_safety.py`, `01_test_relay_buzzer.py`, `mod_led_ws2812b.py`, `03_test_led_pixel_finder.py`, `AKSEL-DECY13/*`, `web_hmi/index.html`, `qa_divisi6/*`, `flows_mqtt_decy13.json`) tanpa instruksi eksplisit Ketua.
- **Anti-Hardware Brown-Out:** JANGAN menyarankan pemasangan kabel Ethernet (`eth0`) pada RPi 3B+ unit ini karena terbukti memicu *under-voltage* / mati mendadak; gunakan `python tools\minipc_control_hub.py` (100% Wi-Fi Auto-Link) dan pastikan Mosquitto Windows Mini PC mati (`Stop-Service mosquitto`).
- **Validasi Wajib:** Setelah mengubah file kode/skrip/config di `tools/` atau `raspi_cli/`, pastikan `tools/raspi_bootstrap.sh` tetap **LF murni** (tanpa CRLF) dan jalankan `python tools/cek_integrasi_dan_announcer.py --ci --cek-branch` hingga `7/7 [LULUS]`.
- **Integritas Laporan (`laporan_uji/`):** DILARANG mencentang `[x]` pada ceklis Tahap B (Uji Fisik) atau mengubah status ke `LULUS_UJI_FISIK` tanpa bukti nyata dari hardware.
