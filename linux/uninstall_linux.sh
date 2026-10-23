#!/usr/bin/env bash
set -euo pipefail

sudo systemctl disable --now network-monitor 2>/dev/null || true
sudo rm -f /etc/systemd/system/network-monitor.service
sudo systemctl daemon-reload
sudo rm -rf /opt/network-monitor

echo "Network Security Monitor removed."
echo "Nmap/tcpdump/Python packages were not removed."
