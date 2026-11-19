#!/usr/bin/env bash
# ==============================================================================
#  SKRIP AUTO-KONFIGURASI RASPBERRY PI 3B+ — TIM 6 DIVISI SIKLOTRON DECY-13
# ==============================================================================
#  Dirancang agar BISA DIJALANKAN DI RPi MANAPUN (tidak bergantung pada username
#  'pi' atau hostname tertentu, bebas bug CRLF Windows, dan idempoten).
#
#  Cara pakai di Raspberry Pi 3B+:
#    bash tools/raspi_bootstrap.sh
#    bash tools/raspi_bootstrap.sh --install-service
#    bash tools/raspi_bootstrap.sh --install-service --install-autolink --disable-eth
# ==============================================================================
set -euo pipefail

INSTALL_SERVICE=0
INSTALL_AUTOLINK=0
DISABLE_ETH=0
for arg in "$@"; do
    case "$arg" in
        --install-service)  INSTALL_SERVICE=1; INSTALL_AUTOLINK=1 ;;
        --install-autolink) INSTALL_AUTOLINK=1 ;;
        --disable-eth)      DISABLE_ETH=1 ;;
    esac
done

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
info() { echo -e "${CYAN}[..]${NC} $1"; }
warn() { echo -e "${YELLOW}[PERINGATAN]${NC} $1"; }
err()  { echo -e "${RED}[GAGAL]${NC} $1"; }

# Deteksi user & folder aktual secara otomatis (bukan hardcode /home/pi)
TARGET_USER="${SUDO_USER:-$(logname 2>/dev/null || id -un)}"
TARGET_HOME="$(getent passwd "$TARGET_USER" | cut -d: -f6)"
if [ -z "$TARGET_HOME" ]; then
    TARGET_HOME="/home/$TARGET_USER"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
if [ -d "$REPO_ROOT/decy13_mqtt_kit/raspi_cli" ]; then
    RASPI_CLI_DIR="$REPO_ROOT/decy13_mqtt_kit/raspi_cli"
elif [ -d "$TARGET_HOME/decy13/raspi_cli" ]; then
    RASPI_CLI_DIR="$TARGET_HOME/decy13/raspi_cli"
else
    RASPI_CLI_DIR="$TARGET_HOME/decy13/raspi_cli"
    mkdir -p "$RASPI_CLI_DIR"
fi

echo "=================================================================="
echo "  AUTO-BOOTSTRAP RASPBERRY PI 3B+ — SIKLOTRON DECY-13 (6 DIVISI)"
echo "  Hostname   : $(hostname)"
echo "  User Aktif : $TARGET_USER ($TARGET_HOME)"
echo "  Folder CLI : $RASPI_CLI_DIR"
echo "=================================================================="

# 1. Konfigurasi /boot/firmware/config.txt atau /boot/config.txt (Audio OFF & SPI ON)
BOOT_CFG="/boot/firmware/config.txt"
if [ ! -f "$BOOT_CFG" ]; then
    BOOT_CFG="/boot/config.txt"
fi

NEED_REBOOT=0
if [ -f "$BOOT_CFG" ]; then
    info "Memeriksa konfigurasi kernel di $BOOT_CFG ..."
    if command -v raspi-config >/dev/null 2>&1; then
        sudo raspi-config nonint do_spi 0 || true
    fi
    if grep -q "^dtparam=audio=on" "$BOOT_CFG"; then
        sudo sed -i 's/^dtparam=audio=on/dtparam=audio=off/' "$BOOT_CFG"
        NEED_REBOOT=1
        ok "dtparam=audio=off diaktifkan (mencegah konflik DMA GPIO 18 LED WS2812B)."
    elif ! grep -q "^dtparam=audio=off" "$BOOT_CFG"; then
        echo "dtparam=audio=off" | sudo tee -a "$BOOT_CFG" >/dev/null
        NEED_REBOOT=1
        ok "dtparam=audio=off ditambahkan ke $BOOT_CFG."
    else
        ok "Audio onboard sudah OFF (dtparam=audio=off)."
    fi

    if ! grep -q "^dtparam=spi=on" "$BOOT_CFG"; then
        echo "dtparam=spi=on" | sudo tee -a "$BOOT_CFG" >/dev/null
        NEED_REBOOT=1
        ok "dtparam=spi=on ditambahkan ke $BOOT_CFG."
    else
        ok "Interface SPI0 sudah ON (dtparam=spi=on)."
    fi
else
    warn "File $BOOT_CFG tidak ditemukan (bukan OS Raspberry Pi standar?)."
fi

# 2. Install paket sistem & Mosquitto Broker
info "Memastikan paket sistem (mosquitto, python3-pip, python3-pil, python3-spidev) terpasang..."
sudo apt-get update -qq
sudo apt-get install -y mosquitto mosquitto-clients python3-pip python3-dev python3-pil python3-spidev git -qq
ok "Paket sistem & Mosquitto terpasang."

# 3. Tulis konfigurasi Mosquitto murni LF (bebas bug CRLF Windows)
info "Menulis /etc/mosquitto/conf.d/decy13.conf (TCP 1883 & WebSocket 9001)..."
printf 'allow_anonymous true\n\nlistener 1883 0.0.0.0\nprotocol mqtt\n\nlistener 9001 0.0.0.0\nprotocol websockets\n' \
    | sudo tee /etc/mosquitto/conf.d/decy13.conf >/dev/null

sudo systemctl enable mosquitto >/dev/null 2>&1 || true
sudo systemctl restart mosquitto
sleep 1

if sudo systemctl is-active --quiet mosquitto; then
    ok "Service mosquitto aktif."
else
    err "Mosquitto gagal dijalankan! Cek: sudo journalctl -u mosquitto -n 20 --no-pager"
    exit 1
fi

if sudo ss -tulnp | grep -q ':1883 ' && sudo ss -tulnp | grep -q ':9001 '; then
    ok "Port MQTT 1883 (TCP) dan 9001 (WebSocket) keduanya TERBUKA."
else
    warn "Salah satu port 1883/9001 belum terlihat di ss -tulnp. Cek sudo ss -tulnp | grep mosquitto"
fi

# 4. Install ke-6 library Python untuk sudo/root maupun user biasa
info "Memasang library Python (paho-mqtt, RPi.GPIO, rpi-ws281x, luma.lcd, Pillow, spidev)..."
sudo pip3 install --break-system-packages -q paho-mqtt RPi.GPIO rpi-ws281x luma.lcd Pillow spidev \
    || sudo pip3 install -q paho-mqtt RPi.GPIO rpi-ws281x luma.lcd Pillow spidev

sudo python3 -c "import paho.mqtt.client, RPi.GPIO, rpi_ws281x, luma.lcd, PIL, spidev"
ok "Ke-6 library Python terverifikasi dapat di-import oleh sudo python3."

# Pastikan kepemilikan folder proyek sesuai user aktif
if [ -d "$RASPI_CLI_DIR" ]; then
    sudo chown -R "$TARGET_USER:$TARGET_USER" "$(dirname "$RASPI_CLI_DIR")" || true
fi

# 5. Pastikan SSH aktif & opsional matikan eth0 (mode 100% Wi-Fi anti drop daya)
sudo systemctl enable --now ssh >/dev/null 2>&1 || true

if [ "$DISABLE_ETH" -eq 1 ]; then
    info "Menonaktifkan profil Ethernet (eth0) agar RPi berjalan 100% via Wi-Fi (hemat daya)..."
    sudo nmcli con mod lan-minipc connection.autoconnect no >/dev/null 2>&1 || true
    sudo nmcli con down lan-minipc >/dev/null 2>&1 || true
    sudo nmcli dev disconnect eth0 >/dev/null 2>&1 || true
    ok "Ethernet (eth0) dinonaktifkan — RPi fokus pada Wi-Fi."
fi

# 6. Opsional: pasang systemd service otomatis sesuai path user aktif
if [ "$INSTALL_SERVICE" -eq 1 ]; then
    info "Memasang systemd service /etc/systemd/system/decy13.service ..."
    printf '[Unit]\nDescription=DECY-13 Cyclotron MQTT Hardware Daemon\nAfter=network.target mosquitto.service\nRequires=mosquitto.service\n\n[Service]\nExecStart=/usr/bin/python3 %s/04_decy13_mqtt_daemon.py\nWorkingDirectory=%s\nRestart=always\nRestartSec=5\nUser=root\n\n[Install]\nWantedBy=multi-user.target\n' \
        "$RASPI_CLI_DIR" "$RASPI_CLI_DIR" | sudo tee /etc/systemd/system/decy13.service >/dev/null
    sudo systemctl daemon-reload
    sudo systemctl enable --now decy13.service
    ok "Service decy13.service aktif untuk path $RASPI_CLI_DIR."
fi

if [ "$INSTALL_AUTOLINK" -eq 1 ] && [ -f "$SCRIPT_DIR/raspi_auto_link.py" ]; then
    info "Memasang systemd service /etc/systemd/system/decy13-autolink.service (Auto-Discovery Wi-Fi ke Mini PC)..."
    printf '[Unit]\nDescription=DECY-13 Raspi Wi-Fi Auto-Link & Discovery Agent\nAfter=network-online.target mosquitto.service\nWants=network-online.target\n\n[Service]\nExecStart=/usr/bin/python3 %s/raspi_auto_link.py\nWorkingDirectory=%s\nRestart=always\nRestartSec=3\nUser=%s\n\n[Install]\nWantedBy=multi-user.target\n' \
        "$SCRIPT_DIR" "$REPO_ROOT" "$TARGET_USER" | sudo tee /etc/systemd/system/decy13-autolink.service >/dev/null
    sudo systemctl daemon-reload
    sudo systemctl enable --now decy13-autolink.service
    ok "Service decy13-autolink.service aktif (otomatis lapor IP Wi-Fi ke Mini PC)."
fi

# 7. Cek /dev/spidev0.0
if ls /dev/spidev* >/dev/null 2>&1; then
    ok "Device SPI terdeteksi: $(ls /dev/spidev* | tr '\n' ' ')"
else
    warn "/dev/spidev0.0 belum muncul (Anda WAJIB menjalankan 'sudo reboot' terlebih dahulu)."
    NEED_REBOOT=1
fi

IP_NOW="$(hostname -I 2>/dev/null | awk '{print $1}')"
echo ""
echo "=================================================================="
echo "  BOOTSTRAP SELESAI!"
echo "  IP RPi Saat Ini      : ${IP_NOW:-127.0.0.1}"
echo "  Endpoint WebSocket   : ws://${IP_NOW:-192.168.137.1}:9001"
if [ "$NEED_REBOOT" -eq 1 ]; then
    echo -e "  ${YELLOW}TINDAKAN WAJIB       : Jalankan 'sudo reboot' sekarang agar SPI & Audio OFF aktif!${NC}"
fi
echo "  Langkah Uji Divisimu : python3 tools/raspi_preflight.py --divisi <1..6>"
echo "=================================================================="
