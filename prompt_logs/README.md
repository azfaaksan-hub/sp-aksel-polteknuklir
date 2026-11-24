# Folder Log & Anatomi Prompt (`prompt_logs/`) — Proyek DECY-13

Folder ini menyimpan catatan terstruktur (**Prompt Anatomy**) untuk setiap instruksi arsitektur dan pembaruan besar pada stasiun kendali **Siklotron DECY-13 (13 MeV H⁻)**.

## Tujuan
1. Mendokumentasikan maksud asli (*raw prompt*) menjadi komponen anatomi yang terukur sebelum eksekusi kode dimulai.
2. Mencatat daftar *Agent Skills* (`.agents/skills/`) yang dipakai beserta aturan kualitas (*Anti-AI-Slop*, kontrak MQTT, keselamatan hardware) yang mengikat eksekusi.
3. Menyediakan versi **Structured Replay Prompt** yang rapi dan siap dijalankan ulang lintas sesi/mesin.

## Struktur Anatomi Standar
Setiap log di folder ini membedah prompt ke dalam 8 bagian:
1. **Metadata & Konteks Sesi**
2. **Raw Prompt (Asli)**
3. **Role & Persona**
4. **System Context & Hardware Constraints**
5. **Active Skills & Anti-Slop Design Floor**
6. **Deliverables & Functional Specification**
7. **Execution Pipeline (Urutan Kerja)**
8. **Refined Reusable Prompt (Siap Jalankan Ulang)**

## Daftar Log Prompt
- [2026-11-24_01_startup_wizard_dan_ui_instruktur_antislop.md](./2026-11-24_01_startup_wizard_dan_ui_instruktur_antislop.md) — Program Konfigurasi Awal Mini PC ↔ Raspi (Auto/Manual + Panduan Wi-Fi + Auto-Sync ke HTML), Instalasi High-Star GitHub Skills, Redesign Web HMI Industrial SCADA Anti-AI-Slop, serta Mode Instruktur Berulang & Auto-Reset Inaktivitas.
- [2026-11-24_02_audit_end_to_end_kode_rangkaian_raspi_dan_html.md](./2026-11-24_02_audit_end_to_end_kode_rangkaian_raspi_dan_html.md) — Audit Menyeluruh Keterhubungan Kode End-to-End terhadap Rangkaian Hardware, Pemeriksaan/Update Kode di Raspberry Pi, dan Penyelarasan Penuh Digital Twin 448 LED 2-Fase pada Web HMI HTML.
