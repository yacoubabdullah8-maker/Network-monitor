import json
import logging
import os
import platform
import subprocess
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta

from dotenv import load_dotenv

from scanner import NetworkScanner
from connection_monitor import ConnectionMonitor
from email_notifier import EmailNotifier


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)


def load_config():
    path = os.path.join(BASE_DIR, "config.json")

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"config.json not found: {path}"
        )

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def ping_host(ip, timeout=2):
    system = platform.system().lower()

    try:
        if system == "windows":
            command = [
                "ping",
                "-n", "1",
                "-w", str(timeout * 1000),
                ip
            ]
        else:
            command = [
                "ping",
                "-c", "1",
                "-W", str(timeout),
                ip
            ]

        result = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout + 2
        )

        return result.returncode == 0

    except Exception:
        logger.exception(
            "Ping failed for %s",
            ip
        )
        return False


def build_connection_message(attempt):
    return (
        "🚨 SECURITY ALERT\n\n"
        "🔴 Incoming TCP connection attempt detected!\n\n"

        "👤 SOURCE DEVICE\n"
        f"🌐 IP: {attempt['source_ip']}\n"
        f"📤 Source Port: {attempt['source_port']}\n\n"

        "🎯 TARGET SERVER\n"
        f"🖥️ IP: {attempt['server_ip']}\n"
        f"🔌 Port: {attempt['server_port']}\n"
        f"⚙️ Service: {attempt['service']}\n"
        f"📡 Protocol: {attempt['protocol']}\n"
        f"🕒 Time: {attempt['time'].strftime('%Y-%m-%d %H:%M:%S')}\n"
    )


def build_server_down_message(server_ip):
    return (
        "🔴 SERVER DOWN\n\n"
        f"🖥️ Server IP: {server_ip}\n"
        "❌ Status: OFFLINE\n"
        "⚠️ The server is unreachable."
    )


def build_server_recovered_message(server_ip):
    return (
        "🟢 SERVER RECOVERED\n\n"
        f"🖥️ Server IP: {server_ip}\n"
        "✅ Status: ONLINE\n"
        "🎉 The server is reachable again."
    )


def monitor_server(server_ip, email, state):
    online = ping_host(server_ip)
    previous = state.get(server_ip)

    if previous is None:
        state[server_ip] = online

        if online:
            logger.info(
                "SERVER UP: %s",
                server_ip
            )
        else:
            logger.warning(
                "SERVER DOWN: %s",
                server_ip
            )
            email.send_message(
                "🔴 SERVER DOWN",
                build_server_down_message(server_ip)
            )

        return

    if previous is True and online is False:
        state[server_ip] = False

        logger.warning(
            "SERVER STATE CHANGED: UP -> DOWN | %s",
            server_ip
        )

        email.send_message(
            "🔴 SERVER DOWN",
            build_server_down_message(server_ip)
        )

    elif previous is False and online is True:
        state[server_ip] = True

        logger.info(
            "SERVER STATE CHANGED: DOWN -> UP | %s",
            server_ip
        )

        email.send_message(
            "🟢 SERVER RECOVERED",
            build_server_recovered_message(server_ip)
        )


def main():
    config = load_config()
    load_dotenv(
        os.path.join(BASE_DIR, ".env")
    )

    network = config.get(
        "target_network"
    )

    server_ip = config.get(
        "target_server"
    )

    interface = config.get(
        "interface",
        "auto"
    )

    nmap_path = config.get(
        "nmap_path",
        "auto"
    )

    ports_config = config.get(
        "ports",
        {}
    )

    scan_interval = int(
        config.get(
            "scan_interval",
            300
        )
    )

    cooldown = int(
        config.get(
            "email_cooldown",
            60
        )
    )

    ports = {
        int(port): name
        for port, name in ports_config.items()
    }

    if not network:
        raise ValueError(
            "target_network is missing"
        )

    if not server_ip:
        raise ValueError(
            "target_server is missing"
        )

    if not ports:
        raise ValueError(
            "No monitored ports configured"
        )

    email = EmailNotifier(
        os.path.join(BASE_DIR, ".env")
    )

    email.validate()

    scanner = NetworkScanner(
        network,
        nmap_path
    )

    connection_monitor = ConnectionMonitor(
        server_ip,
        ports,
        interface
    )

    server_state = {}

    last_alert = defaultdict(
        lambda: datetime.min
    )

    def handle_connection(attempt):
        key = (
            attempt["source_ip"],
            attempt["server_port"]
        )

        now = datetime.now()

        if now - last_alert[key] < timedelta(
            seconds=cooldown
        ):
            logger.info(
                "Email suppressed by cooldown: %s -> %s:%s",
                attempt["source_ip"],
                attempt["server_ip"],
                attempt["server_port"]
            )
            return

        last_alert[key] = now

        email.send_message(
            "🚨 Server Connection Alert",
            build_connection_message(attempt)
        )

    logger.info("=" * 58)
    logger.info(
        "NETWORK SECURITY MONITOR STARTED"
    )
    logger.info(
        "OS: %s",
        platform.system()
    )
    logger.info(
        "Network: %s",
        network
    )
    logger.info(
        "Protected Server: %s",
        server_ip
    )
    logger.info(
        "Interface: %s",
        interface
    )
    logger.info(
        "Monitored Ports: %s",
        ports
    )
    logger.info(
        "Scan Interval: %s seconds",
        scan_interval
    )
    logger.info(
        "Email Cooldown: %s seconds",
        cooldown
    )
    logger.info(
        "SQL Server: DISABLED"
    )
    logger.info("=" * 58)

    capture_thread = threading.Thread(
        target=connection_monitor.detect_attempts,
        args=(handle_connection,),
        daemon=True,
        name="connection-monitor"
    )

    capture_thread.start()

    while True:
        cycle_start = time.time()

        try:
            monitor_server(
                server_ip,
                email,
                server_state
            )
        except Exception:
            logger.exception(
                "Server monitoring error"
            )

        try:
            devices = scanner.discover_hosts()
            logger.info(
                "Discovered %d devices.",
                len(devices)
            )
        except Exception:
            logger.exception(
                "Network discovery failed"
            )

        elapsed = time.time() - cycle_start

        logger.info(
            "Monitoring cycle completed in %.2f seconds.",
            elapsed
        )

        logger.info(
            "Waiting %s seconds for next network scan...",
            scan_interval
        )

        time.sleep(
            max(
                1,
                scan_interval - int(elapsed)
            )
        )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info(
            "Network Security Monitor stopped."
        )
    except Exception:
        logger.exception(
            "Fatal application error"
        )
        raise
