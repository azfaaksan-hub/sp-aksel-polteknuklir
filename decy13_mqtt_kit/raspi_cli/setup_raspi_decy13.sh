#!/bin/bash
# ==============================================================================
#  SKRIP AUTO-SETUP RASPBERRY PI 3B+ — PROYEK DECY-13 CYCLOTRON
#  Jalankan SATU KALI di RPi setelah OS baru terinstall:
#    chmod +x setup_raspi_decy13.sh
#    sudo bash setup_raspi_decy13.sh
# ==============================================================================
set -e  # Hentikan jika ada error

DECY_DIR="/home/pi/decy13/raspi_cli"
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
info() { echo -e "${YELLOW}[..] $1${NC}"; }
err()  { echo -e "${RED}[!!] $1${NC}"; }

echo ""
echo "=============================================="
echo "  DECY-13 Cyclotron — Auto Setup RPi 3B+"
echo "=============================================="
echo ""

# 1. Nonaktifkan audio & aktifkan SPI
info "Mengkonfigurasi /boot/config.txt (audio=off, SPI=on)..."
if grep -q "^dtparam=audio=on" /boot/config.txt; then
    sed -i 's/^dtparam=audio=on/dtparam=audio=off/' /boot/config.txt
    ok "Audio dinonaktifkan (dtparam=audio=off)"
elif grep -q "^dtparam=audio=off" /boot/config.txt; then
    ok "Audio sudah off, tidak ada perubahan."
else
    echo "dtparam=audio=off" >> /boot/config.txt
    ok "dtparam=audio=off ditambahkan."
fi

if ! grep -qxF "dtparam=spi=on" /boot/config.txt; then
    echo "dtparam=spi=on" >> /boot/config.txt
    ok "SPI diaktifkan (dtparam=spi=on)"
else
    ok "SPI sudah aktif, tidak ada perubahan."
fi

# 2. Update & install paket sistem
info "Update paket sistem (harap tunggu)..."
apt-get update -qq
apt-get install -y mosquitto mosquitto-clients python3-pip python3-pil git -qq
ok "Mosquitto, Python3, Pillow terinstall."

# 3. Konfigurasi Mosquitto
info "Membuat konfigurasi Mosquitto untuk DECY-13..."
cat > /etc/mosquitto/conf.d/decy13.conf << 'EOF'
# Konfigurasi Mosquitto Broker DECY-13 Cyclotron

listener 1883
protocol mqtt
allow_anonymous true

listener 9001
protocol websockets
allow_anonymous true

log_type error
log_type warning
log_type information
EOF
ok "File /etc/mosquitto/conf.d/decy13.conf dibuat."

systemctl enable mosquitto
systemctl restart mosquitto
sleep 2
if systemctl is-active --quiet mosquitto; then
    ok "Mosquitto berjalan di port 1883 (MQTT) dan 9001 (WebSocket)."
else
    err "Mosquitto gagal start! Cek: sudo journalctl -u mosquitto"
fi

# 4. Install dependensi Python
info "Menginstall library Python (paho-mqtt, RPi.GPIO, rpi-ws281x, luma.lcd, spidev)..."
pip3 install paho-mqtt RPi.GPIO rpi-ws281x luma.lcd Pillow spidev --break-system-packages -q
ok "Library Python terinstall."

# 5. Buat folder proyek
info "Membuat folder proyek $DECY_DIR ..."
mkdir -p "$DECY_DIR"
chown -R pi:pi /home/pi/decy13
ok "Folder $DECY_DIR siap."

# 6. Verifikasi SPI
if ls /dev/spidev* >/dev/null 2>&1; then
    ok "SPI device tersedia: $(ls /dev/spidev*)"
else
    WARN "SPI device belum terdeteksi. Perlu REBOOT!"
fi

# 7. Buat systemd service daemon DECY-13 (auto-start saat boot)
info "Membuat systemd service decy13.service ..."
cat > /etc/systemd/system/decy13.service << 'EOF'
[Unit]
Description=DECY-13 Cyclotron MQTT Hardware Daemon
After=network.target mosquitto.service
Requires=mosquitto.service

[Service]
ExecStart=/usr/bin/python3 /home/pi/decy13/raspi_cli/04_decy13_mqtt_daemon.py
WorkingDirectory=/home/pi/decy13/raspi_cli
Restart=always
RestartSec=5
User=root
StandardOutput=append:/var/log/decy13.log
StandardError=append:/var/log/decy13.log

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
ok "Service decy13.service terdaftar (belum diaktifkan — tunggu file Python tersalin)."

# 8. Ringkasan hasil
echo ""
echo "=============================================="
echo "  SETUP SELESAI — Ringkasan Status"
echo "=============================================="
echo ""
ok "Audio: OFF (GPIO 18 bebas untuk WS2812B DMA)"
ok "SPI  : ON  (LCD ILI9341 bisa digunakan)"
ok "Mosquitto: Berjalan di TCP:1883 & WS:9001"
ok "Python libraries: Terinstall"
ok "Folder proyek: $DECY_DIR"
echo ""
echo -e "${YELLOW}LANGKAH SELANJUTNYA:${NC}"
echo "  1. Salin file Python ke RPi:"
echo "     scp raspi_cli/*.py raspi_cli/*.json pi@$(hostname -I | awk '{print $1}'):$DECY_DIR/"
echo ""
echo "  2. REBOOT RPi agar SPI & audio config aktif:"
echo "     sudo reboot"
echo ""
echo "  3. Setelah reboot, uji hardware:"
echo "     python3 $DECY_DIR/01_test_relay_buzzer.py"
echo "     python3 $DECY_DIR/02_test_lcd_ili9341.py"
echo "     sudo python3 $DECY_DIR/03_test_led_pixel_finder.py"
echo "     sudo python3 $DECY_DIR/04_decy13_mqtt_daemon.py"
echo ""
echo "  4. Aktifkan daemon auto-start (SETELAH uji hardware OK):"
echo "     sudo systemctl enable decy13.service"
echo "     sudo systemctl start decy13.service"
echo ""
IP=$(hostname -I | awk '{print $1}')
echo -e "  ${GREEN}IP Raspberry Pi ini: $IP${NC}"
echo "  MQTT WebSocket untuk Web HMI: ws://$IP:9001"
echo ""
