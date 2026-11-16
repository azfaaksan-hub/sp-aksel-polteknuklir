# 🧪 Kartu Ceklis Uji Hardware — Divisi 2 (Vakum, Buzzer & Safety E-Stop)

- **Divisi:** Divisi 2 — Sistem Vakum, Buzzer & Safety E-Stop (`dzakimumtazi`)
- **Branch:** `divisi-2-vacum-safety`
- **File Kode Utama:** `decy13_mqtt_kit/raspi_cli/modules/mod_vacuum_safety.py`, `decy13_mqtt_kit/raspi_cli/01_test_relay_buzzer.py`
- **Status Push Saat Ini:** `DRAFT_PUSH_LAPTOP`
- **Terakhir Diuji di Raspi Fisik:** *(Belum ada bukti uji fisik RPi 3B+ — baru lulus audit kode & merge ke `main`)*

---

## A. Ceklis Uji Kode & Simulasi di Laptop (Boleh Dicek Bareng AI)
- [x] `python tools/cek_integrasi_dan_announcer.py --ci` lulus tanpa error.
- [x] Class `VacuumSafetyModule(HardwareModule)` mempertahankan `setup()`, `update(state, dt, now)`, `cleanup()` serta fallback `try/except ImportError` untuk `RPi.GPIO`.
- [x] Hanya mengedit file milik Divisi 2 (tanpa mengubah `04_decy13_mqtt_daemon.py` / `config_hardware.json`).

## B. Ceklis Uji Fisik Hardware Raspberry Pi 3B+ (WAJIB Tes Alat Nyata!)
> **Aturan AI:** JANGAN centang `[x]` bagian B sebelum anggota menguji langsung di RPi 3B+ fisik dan menempelkan outputnya di Bagian C!

- [ ] Saat `python3 01_test_relay_buzzer.py` baru dijalankan, relay kipas `GPIO 21` (`Active-LOW`) langsung **OFF** (tidak menyala sesaat saat inisialisasi).
- [ ] Menu `[2]` & `[3]` menyalakan dan mematikan kipas DC 12V fisik dengan stabil tanpa relay berkedip.
- [ ] Menu `[1]` & pola daemon membunyikan Buzzer `GPIO 17` dengan jelas (Power ON 5 detik, beep saat Shoot, alarm saat E-Stop).
- [ ] Menu `[4] Tes E-Stop` pada `GPIO 22` (`Active-LOW`, NC ke GND) terbaca akurat saat tombol ditekan & dilepas, tanpa *false-trigger* ketika kipas 12V hidup/mati.
- [ ] Saat program dihentikan (`Ctrl+C` / `cleanup()`), relay kipas dan buzzer langsung mati total dengan aman.

## C. Catatan Masalah / Bukti Output Terminal Raspi
*(Anggota/AI wajib mengisi bagian ini dengan jujur sebelum push: tempelkan output RPi saat dites, atau tuliskan bug yang masih terjadi kalau Ketua menyuruh push progres dulu.)*
- Kode `mod_vacuum_safety.py` & `01_test_relay_buzzer.py` sudah di-merge ke `main` (`473a7d5`), namun menunggu laporan uji langsung di RPi 3B+ + modul relay/buzzer/E-Stop fisik.
