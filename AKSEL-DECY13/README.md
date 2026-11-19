# DECY-13 · Hub USB tiga Arduino Uno

Raspberry Pi 3B+ menghubungkan tiga Uno melalui USB serial 115200 baud. Setiap Uno memiliki satu TFT 320×240. TFT 1 menampilkan pengukuran dari Node 2 dan keadaan aktuator yang dikonfirmasi Node 3. TFT 2 dan TFT 3 menampilkan data lokal masing-masing. Sistem ini bisa dijalankan sendiri tanpa daemon MQTT. Hub menjadi satu-satunya proses yang membuka ketiga port.

~~~text
                            Raspberry Pi 3B+
                         raspi/accelerator_hub.py
                           |       |       |
       USB-A ke USB-B      |       |       |      USB-A ke USB-B
            +--------------+       |       +------------------+
            |                      |                          |
     /dev/arduino_hmi       /dev/arduino_sensor       /dev/arduino_actuator
       Uno 1 + TFT 1           Uno 2 + TFT 2             Uno 3 + TFT 3
       tap / geser             sensor via 4051           driver via 595
       cmd -> Pi               telemetri -> Pi            cmd <- Pi
       status <- Pi            kalibrasi <- Pi            ACK/status -> Pi
~~~

## Touchscreen pada ketiga Uno

Ketiga sketch memakai kelas `CalibratedTouch` dengan rotasi landscape 1, pin XP=6, XM=A2, YP=A1, YM=7, serta pemetaan yang sama: `p.y: 920 → 187` untuk X=0–319 dan `p.x: 894 → 146` untuk Y=0–239. Pengukuran tersebut berasal dari shield Node 1. Jika memasang panel fisik lain, cek tekan-lepas di sisi kiri, tengah, dan kanan. Jika meleset, jalankan contoh `TouchScreen_Calibr_native` pada panel itu untuk membandingkan hasilnya.

Ketiga sketch langsung mengaktifkan TFT. Unggah satu sketch sesuai peran ke setiap Uno. Geser ke kiri/kanan atau ketuk **MODE >** di kanan atas untuk pindah halaman pada layar tersebut. Setiap layar memiliki nomor halaman 1/3 sampai 3/3 dan navigasi sendiri.

| TFT | Halaman 1 | Halaman 2 | Halaman 3 |
|---|---|---|---|
| Uno 1 · HMI | Dasbor RPM dan sensor | Target, laju, mulai otomatis | Pemantauan dan uji keluaran lewat hub |
| Uno 2 · Sensor | Pantau pengukuran dan kontak | Kalibrasi suhu awal, offset, dan hasil | Input ADC mentah tiga kanal dan kontak digital |
| Uno 3 · Aktuator | Proses, kipas, relai, jeda | Keluaran dan uji lampu, alarm, katup | Interlok, heartbeat, watchdog dan jeda |

[Pratinjau sembilan halaman TFT](simulasi/sembilan-halaman-tft.png)

**Sebelum mengunggah ke Uno 2 atau 3 yang memakai rangkaian lama**, putuskan daya dan pindahkan sambungan sensor/driver ke profil TFT pada tabel berikut. Nilai bawaan `USE_LOCAL_TFT` sekarang **1**. Khusus Uno yang akan dipakai tanpa shield dan tetap memakai kabel langsung, pilih `#define USE_LOCAL_TFT 0` di sketch perannya sebelum unggah.

| Node | Rangkaian tambahan untuk profil TFT (1) | Aksi sentuh |
|---|---|---|
| 2 | **74HC4051** pada 5 V. Pin common/Z → A5; S0 → D11; S1 → D13; S2, INH, VEE dan GND/VSS → GND. Y0/Y1/Y2 menerima potensiometer vakum/tegangan/suhu (0–5 V). Kontak digital → D12 dan GND. D10 ditahan HIGH. | **−1 C**, **Nol**, **+1 C** mengatur offset suhu. Perubahan muncul di layar dan pada telemetri USB. |
| 3 | **74HC595** pada 5 V. DS/SER → D11; SHCP/SRCLK → D13; STCP/RCLK → D12; /OE → D10 dengan pull-up eksternal 10 kΩ ke 5 V; /MR (/SRCLR) → 5 V. **Interlock NC → A5 dan GND.** | **Kipas**, **Relai**, **Jeda**. Uji kipas, relai, lampu, alarm, dan katup memakai pemeriksaan heartbeat Pi, interlock, serta mode manual yang sama dengan perintah USB. Jeda mematikan keluaran. |

Pada Node 3 profil TFT, Q0–Q6 berturut-turut menuju input driver relai, katup, kipas, buzzer, LED hijau, kuning, merah. Q7 dicadangkan. Pertahankan input driver pada level OFF dengan resistor selama /OE HIGH (pull-down untuk driver aktif-HIGH). Beri catu dan GND bersama pada IC; ambil pin melalui stacking header/breakout jika tertutup shield. Kosongkan slot SD pada kedua shield tambahan: profil TFT memakai jalur D10–D13 untuk I/O. Shield standar memakai D2–D9 dan A0–A4 untuk LCD. [Peta pin MCUFRIEND](https://github.com/prenticedavid/MCUFRIEND_kbv/blob/master/utility/mcufriend_shield.h) · [74HC4051](https://www.ti.com/product/CD74HC4051) · [74HC595](https://www.ti.com/product/SN74HC595)

Uji tanpa beban terlebih dahulu. Pada Node 2, sentuh **+1 C** lalu **Nol** dan lihat `offset_dc` berubah menjadi 10 lalu 0 di CSV. Pada Node 3, uji **Relai** dengan interlock terbuka (keluaran tetap mati), lalu dengan heartbeat aktif, kontak tertutup dan sistem dijeda (keluaran berubah). Tekan **Jeda** untuk memadamkan keluaran.

## Firmware dan koneksi (profil kabel langsung)

| Node | Sketch | Fungsi |
|---|---|---|
| 1 | `firmware/node1_hmi/node1_hmi.ino` | Dasbor RPM dengan 24 segmen, telemetri sensor, pengaturan dan uji keluaran. Geser kiri/kanan. |
| 2 | `firmware/node2_sensor/node2_sensor.ino` | Sampel setiap 200 ms. Tiga potensiometer dapat digunakan sebagai sensor simulasi. |
| 3 | `firmware/node3_actuator/node3_actuator.ino` | Pemilik mode operasi, RPM simulasi, target, keluaran, interlock, dan watchdog. |

**Node 1.** Pasang shield paralel MCUFRIEND langsung di Uno. Kalibrasi perangkat ini adalah XP=6, XM=A2, YP=A1, YM=7. Dalam posisi landscape, X dipetakan dari `p.y` 920–187 dan Y dari `p.x` 894–146. Halaman 1 menampilkan tekanan dalam Pa, tegangan simulasi dalam V, suhu dalam °C, dan input digital. Tampilan menandai telemetri sensor atau aktuator yang berhenti selama 1,2 detik.

**Node 2.** Hubungkan kedua ujung tiap potensiometer ke 5 V dan GND Uno 2. Hubungkan terminal tengahnya ke input berikut. Pin tegangan tinggi di sini menerima **tegangan potensiometer 0–5 V**. Nilai hingga 1000 V pada layar adalah skala simulasi.

| Pin | Pembacaan |
|---|---|
| A0 | 0–101325 Pa, linear |
| A1 | 0–1000 V simulasi, linear |
| A2 | 0–100 °C, ditambah offset kalibrasi |
| D2 | Kontak ke GND, pull-up internal, kontak tertutup menghasilkan `din=1` |

**Node 3.** Semua keluaran memakai logika aktif-HIGH secara default. Untuk modul dengan polaritas berbeda, cocokkan driver dan level OFF sebelum menghubungkan beban. Konstanta `OUTPUT_ON` dan `OUTPUT_OFF` berlaku untuk seluruh keluaran. Hubungkan beban melalui driver yang sesuai, pasokan beban tersendiri, dan proteksi induktif pada kumparan. USB menyediakan komunikasi dan daya logika Uno. Jika suplai USB Pi turun ketika tiga board dan backlight tersambung, gunakan hub USB berdaya eksternal.

| Pin | Fungsi |
|---|---|
| D2 | Kontak interlock normally closed ke GND, `INPUT_PULLUP`. Terbuka atau kabel lepas memutus keluaran. |
| D4 / D5 | Input driver relai 1 / katup solenoid |
| D6 / D7 | Input driver kipas / buzzer aktif |
| D8 / D9 / D10 | LED hijau / kuning / merah, masing-masing dengan resistor seri |

Interlock terbuka langsung mematikan semua keluaran. Kontak harus stabil tertutup selama 50 ms sebelum perintah ON diterima. Jika heartbeat Pi hilang lebih dari 3000 ms, Node 3 mematikan semua keluaran, menjeda sistem, mengembalikan RPM ke nol dan menonaktifkan mulai otomatis. Pulihnya USB atau kontak hanya mengembalikan izin menerima perintah. Uji pertama dengan LED atau indikator driver. Watchdog ini untuk alat peraga dan bergantung pada firmware Uno yang tetap berjalan.

## Unggah dari Arduino IDE

1. Salin folder `firmware/libraries/AcceleratorLink` ke folder `libraries` di sketchbook Arduino. Folder tersebut berisi `library.properties` dan `src/AcceleratorLink.h`. Buka ulang Arduino IDE agar pustaka dikenali.
2. Untuk setiap Uno yang memakai TFT, instal **MCUFRIEND_kbv**, **Adafruit GFX Library** beserta **Adafruit BusIO**, dan **Adafruit TouchScreen**. Pada profil kabel langsung, Node 2 dan 3 cukup memakai AcceleratorLink dan core Arduino AVR. Jika AcceleratorLink sudah pernah disalin, perbarui seluruh folder agar `CalibratedTouch.h` dan `NodePanel.h` ikut terpasang.
3. Hubungkan satu Uno ke komputer pemrograman. Pilih **Arduino Uno**, port yang sesuai, buka sketch node tersebut, lalu **Upload**. Beri label Uno dan ulangi untuk dua node lainnya.
4. Tutup Serial Monitor sebelum menjalankan hub. Hubungkan ketiga Uno ke Pi dengan kabel data USB.

Alternatif kompilasi dari akar proyek dengan Arduino CLI dan core `arduino:avr` terpasang:

~~~sh
for node in node1_hmi node2_sensor node3_actuator; do
    arduino-cli compile --fqbn arduino:avr:uno --libraries firmware/libraries "firmware/$node" || break
done
~~~

## Jalankan di Raspberry Pi OS

Salin folder `raspi/` ke Pi. Jalankan dari direktori induknya:

~~~sh
sudo apt install python3-serial
sudo bash raspi/setup_udev.sh
ls -l /dev/arduino_{hmi,sensor,actuator}
python3 raspi/accelerator_hub.py --console --csv accelerator_telemetry.csv
~~~

Script udev menampilkan nama TTY, VID:PID, serial, dan port fisik untuk setiap perangkat. Pilih perangkat berlabel **hmi**, **sensor**, lalu **actuator**. Gunakan `ls -l /dev/serial/by-path/` atau cabut/pasang satu per satu sebelum menjalankan skrip untuk mengenali kabel. Periksa pratinjau dan jawab `y` untuk memasang `/etc/udev/rules.d/99-accelerator-arduinos.rules`. Skrip memuat ulang aturan dan memeriksa ketiga tujuan symlink. Jika verifikasi gagal, skrip mengembalikan isi aturan sebelumnya.

Mode default mengikat peran ke **soket USB fisik**. Pertahankan kabel pada soket Pi/hub yang sama setelah reboot. Mode serial unik mendukung perpindahan soket jika setiap board memiliki nomor serial yang benar-benar unik. Untuk clone dengan serial identik atau kosong, skrip memakai port fisik. Selain pemetaan udev, hub memeriksa identitas firmware dari telemetri sebelum mengirim perintah ke port.

Jika akses TTY ditolak, jalankan `sudo usermod -aG dialout "$USER"`, lalu keluar dan masuk kembali. Hub menunggu perangkat yang belum terpasang dan membuka ulang port setelah kabel kembali. Uno dapat reset saat port dibuka. Hentikan hub dengan Ctrl+C. Opsi `--hmi`, `--sensor`, dan `--actuator` dapat mengganti path untuk pengujian.

Dengan `--console`, ketik `CAL_TEMP -15` lalu Enter untuk offset −1,5 °C. Rentangnya −200 sampai 200 dalam satuan 0,1 °C. Ketik `RESET` di konsol untuk menghapus offset **Node 2**. Kalibrasi disimpan di RAM. Tombol **ULANG** di TFT mereset proses **Node 3**. CSV ditambahi baris UTC untuk setiap telemetri yang diproses, termasuk kolom sumber. Status koneksi, perintah, ACK, dan ringkasan sensor tampil di terminal.

## Integrasi dengan Mini PC dan Node-RED

Jalankan hub Uno dan daemon MQTT tim di Raspberry Pi. Gunakan broker yang dipakai oleh daemon. Untuk pemasangan dengan broker di Pi, endpoint browser Mini PC adalah `ws://<IP_RASPI>:9001`. Untuk susunan QA dengan broker di Mini PC, gunakan alamat broker atau ujung tunnel yang sudah dikonfigurasi pada instalasi itu. Kedua HMI dalam repo memakai panel tiga TFT dari koneksi MQTT yang sama.

~~~sh
sudo apt install python3-serial python3-paho-mqtt
python3 raspi/accelerator_hub.py --mqtt-host 127.0.0.1 --mqtt-port 1883
~~~

Hub memerlukan Paho MQTT 2.x untuk integrasi. Jalankan dari direktori `AKSEL-DECY13`. Untuk broker dengan autentikasi, atur variabel lingkungan `DECY13_USB_MQTT_USER` dan `DECY13_USB_MQTT_PASSWORD` pada proses hub. Gunakan `--mqtt-control` bila Mini PC perlu mengirim perintah ke Uno simulasi melalui broker yang mengatur akses tulis ke topik perintah.

| Topik | Isi |
|---|---|
| `decy13/rpi/state` dan `decy13/hmi/cmd` | Kontrak daemon dan HMI siklotron milik tim |
| `decy13/usb/state` | Status tiga node dan telemetri USB setiap 200 ms. Sensor memakai Pa, tegangan simulasi, dan suhu dalam 0,1 °C. |
| `decy13/usb/cmd` | Permintaan web ke Uno aktuator dengan `request`, `target`, `action`, dan `val`. |
| `decy13/usb/ack` | Konfirmasi dari hub berdasarkan hasil serial, dengan `request`, `ok`, dan `code`. |

Hub menolak perintah MQTT retained dan membatasi umur antrean. Node 3 tetap memeriksa interlock dan watchdog. Panel USB mendeteksi telemetri kedaluwarsa setelah dua detik. Tombol siklotron di HMI tetap menggunakan kontrak daemon.

Impor `raspi/nodered_usb.json` sebagai tab tambahan jika Node-RED perlu memantau tiga Uno. Pilih broker tim untuk node MQTT pada tab tersebut. Endpoint baca status tersedia di `/api/usb/status`. Flow tim tetap menyediakan `/cyclotron` dan `/api/status` untuk telemetri siklotron.

## Operasi HMI

- **Dasbor.** MULAI mengirim START. JEDA mematikan keluaran dan menahan angka RPM. ULANG mengembalikan RPM ke nol dan mode siaga.
- **Pengaturan.** Target 2000–9000 RPM dengan langkah 500. Laju lambat/normal/cepat menentukan perubahan RPM simulasi per 35 ms. Mulai otomatis 10 detik **mati saat boot**. Aktifkan di halaman ini ketika hub dan interlock siap. Hitung mundur berjalan saat siaga. Jika sudah dijeda, tekan ULANG untuk kembali ke siaga.
- **Keluaran.** Saat siaga atau dijeda, Uji mengirim nilai absolut untuk lampu, kipas, buzzer, relai, atau katup. Lampu berputar melalui mati, hijau, kuning, dan merah. Saat proses berjalan, relai aktif, kipas aktif di atas 3500 RPM, LED kuning mulai 50% target, merah mulai 80%, dan buzzer aktif mulai 85%. Katup hanya untuk uji manual.
- HMI menunggu konfirmasi sebelum menerima aksi tombol berikutnya. Badge menunjukkan **perintah keluaran yang diterapkan firmware**, bukan umpan balik mekanis kontak relai/katup. Kehilangan Node 2 atau HMI ditandai oleh hub. Watchdog Node 3 secara khusus mengawasi heartbeat **Pi ke Node 3**.

## Protokol

115200 baud, 8N1. Satu objek JSON ASCII datar per baris LF. Penerima juga menerima CRLF. Maksimum 182 byte isi, 16 field, nilai berupa bilangan bulat atau string ASCII biasa tanpa escape. `node` selalu salah satu dari `hmi`, `sensor`, `actuator`. Untuk pesan dari Uno, `node` adalah pengirim. Ketika Pi mengirim instruksi ke Uno, `node` adalah pemilik endpoint dan `src:"pi"` menandai Pi. Telemetri dan ACK yang diteruskan ke HMI mempertahankan identitas node asal.

~~~json
{"node":"hmi","type":"cmd","target":"actuator","id":41,"action":"RELAY_1","val":1}
{"node":"actuator","type":"cmd","src":"pi","id":7,"action":"RELAY_1","val":1}
{"node":"actuator","type":"ack","id":7,"ok":1,"code":0,"bits":16}
{"node":"actuator","type":"ack","id":41,"ok":1,"code":0,"bits":16}
{"node":"actuator","type":"heartbeat","src":"pi"}
{"node":"sensor","type":"cmd","src":"pi","id":8,"action":"CAL_TEMP","val":-15}
{"node":"sensor","type":"telemetry","vac_pa":750,"hv_v":500,"temp_dc":253,"din":1,"offset_dc":-15}
{"node":"actuator","type":"telemetry","rpm":0,"target":6000,"mode":2,"rate":1,"auto":0,"left":0,"bits":16,"guard":1,"link":1}
~~~

| Field atau aksi | Makna |
|---|---|
| `type` | `telemetry`, `cmd`, `ack`, `heartbeat` |
| `id`, `ok`, `code` | ID perintah 1–32767. Hub menerjemahkan ID untuk setiap transaksi dan mengembalikan ID asal ke HMI. `ok=1` berarti diterima. Kode 0 sukses, 1 argumen salah, 2 heartbeat belum aktif, 3 interlock terbuka, 4 uji manual terkunci, 5 tujuan tidak siap/antrean penuh, 6 hasil belum terkonfirmasi. |
| `mode`, `rate`, `auto`, `left` | Mode 0 siaga / 1 berjalan / 2 jeda. Laju 0–2, mulai otomatis 0/1 dan sisa detik. |
| `bits` | Bit 0–1 berisi warna LED 0–3. Bit 2 kipas, 3 buzzer, 4 relai, 5 katup. |
| `guard`, `link` | Kontak interlock tertutup stabil / heartbeat Pi aktif di Node 3. |
| `START`, `STOP`, `RESET` | Kirim `val:1`. |
| `TARGET`, `RATE`, `AUTO` | Target RPM, laju 0–2, mulai otomatis 0/1. |
| `LED`, `RELAY_1`, `VALVE`, `FAN`, `BUZZER` | Warna LED 0–3 atau keadaan biner 0/1. |
| `page`, `valid` | Telemetri HMI setiap 100 ms memuat halaman 0–2 dan salinan keluaran terakhir. `valid=0` berarti salinan sudah kedaluwarsa. CSV menyimpan halaman HMI dan pengukuran langsung dari node sumber. |

Tiap port memiliki thread baca/tulis sendiri. Hub mengirim heartbeat setiap detik setelah identitas terverifikasi. Antrean telemetri ke TFT menyimpan sampel terbaru per sumber. Perintah dibatasi umur 0,7 detik sebelum dikirim. ACK dicocokkan menurut node, sesi USB dan ID. Hub menghapus antrean koneksi lama dan tidak mengulang perintah ON lintas reconnect. Jika hasil perintah kedaluwarsa, periksa telemetri terbaru sebelum mengirim perintah baru.

## Uji meja

1. Hidupkan sistem dengan kontak D2 Uno 3 terbuka. Periksa semua keluaran mati. MULAI harus menghasilkan ACK ditolak.
2. Tutup kontak interlock dan tunggu heartbeat. Putar potensiometer Node 2. Periksa perubahan pada TFT dan CSV.
3. Di halaman keluaran, uji relai atau katup menggunakan indikator driver. Lepaskan kontak D2. Pastikan keluaran mati dan menutup kembali kontak tidak menyalakannya.
4. Aktifkan satu keluaran lagi dan hentikan hub **dengan Uno 3 tetap mendapat daya**. Periksa keluaran padam setelah lebih dari 3 detik sejak heartbeat terakhir. Mencabut kabel yang sekaligus memutus daya Uno tidak menguji timer watchdog.
5. Jalankan lagi hub, cabut/pasang Node 2, lalu Node 3. Periksa label putus koneksi pada TFT, kembalinya sampel, dan keluaran tetap mati sampai ada perintah baru.
