# Quality Assurance Report — Divisi 3 DECY-13

## Periode Pengujian

25-26 November 2026.

## Tujuan

Memastikan animasi LED, komunikasi MQTT, dan driver
PWM/DMA dapat beroperasi tanpa menghambat Core Daemon.

## Temuan Awal

Operasi rendering LED sebelumnya dilakukan ketika
lock modul sedang ditahan. Fault injection membuktikan
bahwa kondisi tersebut dapat menghambat Core update.

Perbaikan menggunakan arsitektur single-writer,
snapshot state, dan pemisahan operasi driver LED.

## Hasil Pengujian

| ID | Pengujian | Hasil |
|---|---|---|
| SW-01 | Python compilation | PASS |
| SW-02 | Git diff check | PASS |
| SW-03 | Virtual regression | 20/20 PASS |
| SW-04 | Fault injection setelah patch | PASS |
| SW-05 | Animasi asinkron | PASS |
| SW-06 | Cleanup virtual | PASS |
| INT-01 | MQTT integration virtual | 10/10 PASS |
| INT-02 | Telemetry virtual | 150/150 PASS |
| INT-03 | MQTT auto-reconnect | PASS |
| HW-01 | Inisialisasi PWM/DMA | PASS |
| HW-02 | Telemetry hardware tanpa beban | 50/50 PASS |
| HW-03 | Stress test tanpa beban LED | 150/150 PASS |
| HW-04 | Shutdown SIGTERM | PASS |
| HMI-01 | Kontrol melalui Web HMI tanpa beban | 7/7 PASS |
| HMI-02 | Mapping indeks MQTT | PASS |
| HW-05 | LED fisik setelah patch | PENDING |
| HW-06 | Stress test dengan beban LED | PENDING |
| HW-07 | Buzzer fisik setelah patch | PENDING |

## Fault Injection

- Blocking sebelum patch: 503 ms.
- Core update setelah patch: 0.075 ms.
- Respons standby virtual: 30.470 ms.
- Respons Emergency Stop virtual: 20.332 ms.

Nilai tersebut merupakan hasil pengujian tertentu,
bukan jaminan batas maksimum latensi sistem.

## Pengujian HMI

- Power ON: PASS.
- Vacuum ON: PASS.
- Safety Interlock simulasi: PASS.
- Start Beam: PASS.
- Shoot: PASS.
- Exposure OFF: PASS.
- Emergency Stop simulasi: PASS.

Temperatur pada audit akhir: 56.9 derajat Celsius.
Throttling: 0x0.
CPU daemon: 6.8 persen.
RAM daemon: 3.3 persen.
Tidak ada disconnect tambahan pada log pengujian HMI.

## Temuan untuk Divisi Terkait

### Kelistrikan

- PSU teridentifikasi 12 V 10 A.
- Output LM2596 terukur 5 V.
- Kapasitas arus kontinu modul belum diverifikasi.
- Arus aktual LED belum terukur.
- Proteksi jalur data dan isolasi solder perlu diperiksa.

Penanganan kelistrikan berada di luar lingkup
perbaikan coding Divisi 3.

### Web HMI Divisi 5

Pada salinan HMI pengujian, mapping indeks 437 LED
sudah sesuai. Namun ditemukan:

- Satu paket partikel, bukan dua.
- Ekor spiral 6 LED, bukan 24.
- LED bar 16 segmen, bukan 48.
- Target belum mengikuti indikator hijau driver.
- RF gap belum direpresentasikan secara setara.

Salinan HMI pengujian tidak termasuk commit Divisi 3.

## Batasan Pengujian

Pengujian PWM/DMA dan HMI setelah patch dilakukan
tanpa beban LED fisik.

Vacuum dan interlock menggunakan mode simulasi.
LCD dan emergency stop hardware tidak diuji.

Brightness driver saat pengujian adalah 10/255,
sedangkan konfigurasi repository masih 45/255.

## Kesimpulan

Software Divisi 3 layak diajukan untuk review dan
integrasi. Penerimaan hardware akhir tetap menunggu
pengujian LED fisik bersama tim.
