# Panduan Eksekusi Lokal CLI & Try-and-Error Siklotron DECY-13 (MQTT Edition)

Paket ini berisi seluruh kode dan konfigurasi untuk melanjutkan pengembangan sistem instrumen simulasi **Siklotron DECY-13** secara lokal menggunakan **CLI** dengan arsitektur **MQTT State-Driven** (simulasi di Web HMI mengikuti kondisi nyata dari Raspberry Pi 3 Model B+).

## 1. Daftar Isi Paket ZIP
* `PROMPT_LANJUTAN_CLI.md` — Prompt siap *copy-paste* untuk asisten AI di CLI lokal kamu.
* `raspi_cli/config_hardware.json` — Konfigurasi pin GPIO BCM, indeks piksel LED strip, dan alamat broker MQTT.
* `raspi_cli/01_test_relay_buzzer.py` — Uji mandiri Relay Kipas Vakum (`GPIO 21`) & Buzzer (`GPIO 17`).
* `raspi_cli/02_test_lcd_ili9341.py` — Uji mandiri Layar LCD TFT 2.4/2.8" SPI (`ILI9341`).
* `raspi_cli/03_test_led_pixel_finder.py` — Alat bantu cari nomor urut piksel LED `WS2812B` (`GPIO 18`).
* `raspi_cli/04_decy13_mqtt_daemon.py` — Program utama Daemon MQTT di Raspberry Pi 3B+.
* `raspi_cli/mosquitto_decy13.conf` — Konfigurasi broker Mosquitto (`port 1883` TCP & `port 9001` Web).
* `web_hmi/index.html` — Web HMI SCADA + Simulasi 2D yang merespons telemetri nyata dari `decy13/rpi/state`.
* `nodered/flows_mqtt_decy13.json` — File import Node-RED yang sudah terhubung ke MQTT dan bebas *bug*.

## 2. Persiapan Awal di Raspberry Pi 3 Model B+
1. Aktifkan SPI dan matikan audio bawaan (agar DMA PWM `GPIO 18` untuk LED strip tidak bentrok) di `/boot/config.txt`:
   ```bash
   sudo sed -i 's/^dtparam=audio=on/dtparam=audio=off/' /boot/config.txt
   echo "dtparam=spi=on" | sudo tee -a /boot/config.txt
   sudo reboot
   ```
2. Pasang Mosquitto Broker & dependensi Python:
   ```bash
   sudo apt update && sudo apt install -y mosquitto mosquitto-clients python3-pip python3-pil
   sudo cp raspi_cli/mosquitto_decy13.conf /etc/mosquitto/conf.d/decy13.conf
   sudo systemctl restart mosquitto
   sudo pip3 install -r raspi_cli/requirements.txt --break-system-packages
   ```

## 3. Urutan Try-and-Error di CLI
1. **Tes Kipas & Buzzer:** `python3 raspi_cli/01_test_relay_buzzer.py`
2. **Tes LCD TFT SPI:** `python3 raspi_cli/02_test_lcd_ili9341.py`
3. **Cari Indeks LED Spiral & Shoot:** `sudo python3 raspi_cli/03_test_led_pixel_finder.py` (lalu catat hasilnya ke `config_hardware.json`).
4. **Jalankan Daemon MQTT Utama:** `sudo python3 raspi_cli/04_decy13_mqtt_daemon.py`
5. **Buka Web HMI:** Buka `web_hmi/index.html` di browser Mini PC (atau import `nodered/flows_mqtt_decy13.json` ke Node-RED).
