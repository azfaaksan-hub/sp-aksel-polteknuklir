# 🧪 Kartu Ceklis Uji Hardware — Divisi 2 (Vakum, Buzzer & Safety E-Stop)

- **Divisi:** Divisi 2 — Sistem Vakum, Buzzer & Safety E-Stop (`dzakimumtazi`)
- **Branch:** `divisi-2-vacum-safety`
- **File Kode Utama:** `decy13_mqtt_kit/raspi_cli/modules/mod_vacuum_safety.py`, `decy13_mqtt_kit/raspi_cli/01_test_relay_buzzer.py`
- **Status Push Saat Ini:** `LULUS_UJI_FISIK`
- **Terakhir Diuji di Raspi Fisik:** `2026-11-18` *(Diuji langsung bersama oleh seluruh tim — Ketua & PJ Divisi 2 `dzakimumtazi`, hasil dilaporkan baik di grup WhatsApp. Catatan: tombol fisik E-Stop `GPIO 22` tidak dipasang/diuji karena E-Stop dipindah ke HTML Web HMI di Mini PC)*

---

## A. Ceklis Uji Kode & Simulasi di Laptop (Boleh Dicek Bareng AI)
- [x] `python tools/cek_integrasi_dan_announcer.py --ci` lulus tanpa error.
- [x] Class `VacuumSafetyModule(HardwareModule)` mempertahankan `setup()`, `update(state, dt, now)`, `cleanup()` serta fallback `try/except ImportError` untuk `RPi.GPIO`.
- [x] Hanya mengedit file milik Divisi 2 (tanpa mengubah `04_decy13_mqtt_daemon.py` / `config_hardware.json`).

## B. Ceklis Uji Fisik Hardware Raspberry Pi 3B+ (WAJIB Tes Alat Nyata!)
> **Aturan AI:** JANGAN centang `[x]` bagian B sebelum anggota menguji langsung di RPi 3B+ fisik dan menempelkan outputnya di Bagian C!

- [x] Saat `python3 01_test_relay_buzzer.py` baru dijalankan, relay kipas `GPIO 21` (`Active-LOW`) langsung **OFF** (tidak menyala sesaat saat inisialisasi).
- [x] Menu `[2]` & `[3]` menyalakan dan mematikan kipas DC 12V fisik dengan stabil tanpa relay berkedip.
- [x] Menu `[1]` & pola daemon membunyikan Buzzer `GPIO 17` dengan jelas (Power ON 5 detik, beep saat Shoot, alarm saat E-Stop).
- [x] Saat program dihentikan (`Ctrl+C` / `cleanup()`), relay kipas dan buzzer langsung mati total dengan aman.
- *(Dikecualikan / N/A — Tidak Diuji Fisik)* Menu `[4] Tes E-Stop` pada `GPIO 22`: tidak ada saklar E-Stop fisik yang dipasang; fungsi Emergency Stop dijalankan melalui tombol HTML Web HMI di Mini PC sesuai catatan Divisi 1.

## C. Catatan Masalah / Bukti Output Terminal Raspi
*(Anggota/AI wajib mengisi bagian ini dengan jujur sebelum push: tempelkan output RPi saat dites, atau tuliskan bug yang masih terjadi kalau Ketua menyuruh push progres dulu.)*
- Kode `mod_vacuum_safety.py` & `01_test_relay_buzzer.py` sudah di-merge ke `main` (`473a7d5`).
- **Hasil Uji Fisik RPi 3B+ (`2026-11-18`, diuji bersama oleh seluruh tim — Ketua & PJ Divisi 2 `dzakimumtazi`; laporan hasil di grup WhatsApp):**
  1. Relay kipas vakum `GPIO 21` (`Active-LOW`) langsung berada pada kondisi **OFF** saat program baru dijalankan dan kembali mati total saat `Ctrl+C` / `cleanup()`.
  2. Kontrol ON/OFF kipas vakum DC 12V melalui relay fisik berjalan stabil tanpa relay berkedip.
  3. Buzzer `GPIO 17` berbunyi jelas sesuai uji isolasi maupun pola daemon.
  4. **Pengecualian E-Stop fisik (`GPIO 22`):** tidak diuji karena memang tidak ada saklar fisik E-Stop yang dipasang — fungsi Emergency Stop ditangani melalui HTML Web HMI di Mini PC.
