#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="/opt/network-monitor"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[1/7] Installing Linux packages..."
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip nmap tcpdump libpcap-dev

echo "[2/7] Copying project..."
sudo mkdir -p "$INSTALL_DIR"
sudo cp -r "$SCRIPT_DIR"/. "$INSTALL_DIR"/

echo "[3/7] Creating virtual environment..."
sudo python3 -m venv "$INSTALL_DIR/.venv"

echo "[4/7] Installing Python packages..."
sudo "$INSTALL_DIR/.venv/bin/pip" install --upgrade pip
sudo "$INSTALL_DIR/.venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

echo "[5/7] Creating .env..."
if [ ! -f "$INSTALL_DIR/.env" ]; then
    sudo cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
    sudo chmod 600 "$INSTALL_DIR/.env"
fi

echo "[6/7] Installing systemd service..."
sudo cp "$INSTALL_DIR/linux/network-monitor.service" \
    /etc/systemd/system/network-monitor.service

sudo systemctl daemon-reload
sudo systemctl enable network-monitor

echo "[7/7] Installation complete."

echo
echo "Edit:"
echo "  sudo nano $INSTALL_DIR/config.json"
echo "  sudo nano $INSTALL_DIR/.env"
echo
echo "Then:"
echo "  sudo systemctl restart network-monitor"
echo
echo "Check:"
echo "  sudo systemctl status network-monitor --no-pager"
echo
echo "Logs:"
echo "  sudo journalctl -u network-monitor -f"
