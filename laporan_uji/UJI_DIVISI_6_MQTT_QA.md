# 🧪 Kartu Ceklis Uji Hardware — Divisi 6 (Jaringan MQTT, Node-RED & QA)

- **Divisi:** Divisi 6 — Jaringan MQTT, Node-RED & Commissioning QA (`rekypurnomo`)
- **Branch:** `divisi-6-mqtt-nodered-qa-testing` *(sudah di-merge ke `main`)*
- **File Kode Utama:** `decy13_mqtt_kit/raspi_cli/06_test_mqtt_healthcheck.py`, `decy13_mqtt_kit/nodered/flows_mqtt_decy13.json`, `instruksi untuk projek sp/CHECKLIST_COMMISSIONING.txt`
- **Status Push Saat Ini:** `DRAFT_PUSH_LAPTOP`
- **Terakhir Diuji di Jaringan RPi <-> Mini PC Nyata:** *(Belum — baru diuji end-to-end vs Mosquitto lokal & daemon tiruan `paho-mqtt` 1.x/2.x)*

---

## A. Ceklis Uji Kode & Dry-Run Broker Lokal (Boleh Dicek Bareng AI)
- [x] `06_test_mqtt_healthcheck.py` lolos uji sintaks Python dan memvalidasi 22 field wajib `decy13/rpi/state`.
- [x] `flows_mqtt_decy13.json` valid JSON (18 node tanpa `pi-gpiod`, lolos `NR-02`) dan siap di-import ke Node-RED.
- [x] `python tools/cek_integrasi_dan_announcer.py --ci` lulus tanpa error.

## B. Ceklis Uji Jaringan Fisik Raspberry Pi <-> Mini PC (WAJIB Tes Alat Nyata!)
> **Aturan AI:** JANGAN centang `[x]` bagian B sebelum dijalankan di jaringan nyata antara Raspberry Pi 3B+ dan Mini PC!

- [ ] `python3 06_test_mqtt_healthcheck.py --host 192.168.137.1` terhubung stabil dan mengukur laju paket ~5.0 Hz (`0.2s`) tanpa *packet drop* berlebih.
- [ ] Sekuens otomatis Tahap 1 s.d. Tahap 7 + `EMERGENCY_STOP` lewat MQTT sukses memicu perubahan tahap nyata pada Raspi & Web HMI.
- [ ] Dashboard Node-RED menerima telemetri langsung dari RPi dan tombol Node-RED berhasil mengirim perintah ke `decy13/hmi/cmd`.
- [ ] `instruksi untuk projek sp/CHECKLIST_COMMISSIONING.txt` sudah diverifikasi berpasangan saat uji integrasi seluruh subsistem.

## C. Catatan Masalah / Bukti Output Terminal QA
*(Tempelkan hasil pengukuran Hz/latensi MQTT atau kendala firewall/jaringan antara RPi dan Mini PC di sini.)*
- Commit `4ed588d` (`06_test_mqtt_healthcheck.py`) & `b2b42f6` (`flows_mqtt_decy13.json` 18 node berbasis MQTT nyata tanpa node `pi-gpiod`) oleh `rekypurnomo` sudah di-merge ke `main` dan lolos cek statis `NR-02`.
- **3 catatan penyelarasan sebelum tes alat nyata:**
  1. `SEQ-03` (`TOGGLE_INTERLOCK`) pada daemon baru diterima setelah `pressure <= 1e-3 mbar` (~6–7 detik dari `1013 mbar`), sedangkan `--cmd-timeout` default `5.0 s` dan `SEQ-02b` baru menunggu tekanan turun 50%. Solusi: tunggu `pressure <= 1e-3` sebelum `TOGGLE_INTERLOCK` atau gunakan `--cmd-timeout 10`.
  2. `--expected-stages` default `7`, sedangkan integer `state["stage"]` pada daemon melewati 6 nilai `{0, 1, 4, 5, 6, 7}` (tahap 2 & 3 berupa log).
  3. Broker default di `flows_mqtt_decy13.json` diset ke `localhost:1883` (ganti ke `192.168.137.1` bila Node-RED dijalankan di Mini PC, bukan di RPi yang sama).
- Belum diuji terhadap `04_decy13_mqtt_daemon.py` asli di Raspberry Pi <-> Mini PC nyata.
