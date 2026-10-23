# Network Security Monitor

A small Python utility for monitoring a server and selected TCP ports on a network you own or are authorized to administer. It combines periodic Nmap host discovery, TCP SYN monitoring with Scapy, and optional email alerts. Linux systemd and Windows Scheduled Task installers are included.

## Features

- Periodic network host discovery through Nmap.
- Monitoring of TCP connection attempts to configured server ports.
- Server reachability checks with UP/DOWN and recovery notifications.
- Optional email notifications using SMTP.
- Automatic startup on Linux or Windows.
- No database is required by this package.

## Repository safety

- Never commit `.env`, passwords, app passwords, API keys, private keys, or other secrets.
- `.env.example` contains only blank credential fields and is safe to copy as a template.
- `config.json` contains documentation-only example addresses from `192.0.2.0/24`. Replace them with your own authorized lab/network values locally before running the monitor. Do not commit private network addresses, hostnames, MAC addresses, or customer data.
- Runtime logs, packet captures, databases, virtual environments, and generated reports are excluded by `.gitignore`. Review `git status` and the staged diff before every push.

## Requirements

- Python 3.11 or newer recommended.
- Nmap installed and available on `PATH` (or set `nmap_path` in `config.json`).
- Npcap on Windows for packet capture.
- Elevated privileges may be needed for packet capture and network discovery.
- Network access and permission to monitor the target systems.

Install Python dependencies:

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Install Nmap separately using the package manager or official installer for your operating system. On Windows, install Npcap as well.

## Configuration

1. Copy `.env.example` to `.env`.
2. Add your SMTP credentials to `.env` if email alerts are needed. For Gmail, use an app password where required, not your normal account password.
3. Edit `config.json` for the network you are authorized to monitor. Set `target_network`, `target_server`, the interface if needed, monitored `ports`, `scan_interval` (seconds), and `email_cooldown` (seconds).

Example `.env` keys:

```dotenv
EMAIL_ENABLED=yes
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=
EMAIL_PASSWORD=
EMAIL_RECIPIENT=
```

Keep `.env` private. Do not paste its contents into issues or public chats.

## Run manually

From the project directory, with the virtual environment active:

```bash
python main.py
```

Run with the privileges required for packet capture. Stop with `Ctrl+C`.

## Linux service installation

From the project directory:

```bash
sudo ./linux/install_linux.sh
```

Then configure the installed files and restart the service:

```bash
sudo nano /opt/network-monitor/config.json
sudo nano /opt/network-monitor/.env
sudo chmod 600 /opt/network-monitor/.env
sudo systemctl restart network-monitor
sudo systemctl status network-monitor --no-pager
```

Follow service output with:

```bash
sudo journalctl -u network-monitor -f
```

The installer enables the service at boot.

## Windows service startup

Open PowerShell as Administrator, ensure Python, Nmap, and Npcap are installed, then run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\windows\install_windows.ps1
```

Edit `C:\Program Files\NetworkMonitor\config.json` and `C:\Program Files\NetworkMonitor\.env` after installation. The installer registers a Scheduled Task to start at system startup.

## Architecture

- `scanner.py`: periodic Nmap host discovery.
- `connection_monitor.py`: Scapy-based TCP SYN detection.
- `email_notifier.py`: optional SMTP notifications.
- `main.py`: configuration, orchestration, reachability checks, and logging.
- `linux/`: systemd unit and Linux install/uninstall scripts.
- `windows/`: Windows installation script.

## Limitations and privacy

The monitor observes connection metadata for configured TCP ports. It is not a packet-payload inspection tool and is not designed to collect passwords or message contents. Logs may contain IP addresses, hostnames, and connection metadata, so treat them as operational data and protect them accordingly.

## Before publishing

```bash
git status --short
git diff --cached
```

Review all staged files and scan for secrets/private data before pushing. `.gitignore` prevents many accidental additions, but it does not remove files already tracked by Git and is not a substitute for reviewing changes.
