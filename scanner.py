import logging
import os
import shutil
import nmap


class NetworkScanner:
    """Nmap host discovery for Linux and Windows."""

    def __init__(self, network, nmap_path="auto"):
        self.network = network

        if nmap_path and str(nmap_path).lower() != "auto":
            executable = nmap_path
        else:
            executable = shutil.which("nmap")

            if not executable:
                candidates = [
                    r"C:\Program Files\Nmap\nmap.exe",
                    r"C:\Program Files (x86)\Nmap\nmap.exe",
                    "/usr/bin/nmap",
                    "/usr/local/bin/nmap",
                ]
                executable = next(
                    (p for p in candidates if os.path.exists(p)),
                    None
                )

        if not executable:
            raise FileNotFoundError(
                "Nmap executable was not found. "
                "Install Nmap or set nmap_path in config.json."
            )

        self.nm = nmap.PortScanner(nmap_search_path=(executable,))

    def discover_hosts(self):
        self.nm.scan(
            hosts=self.network,
            arguments="-sn"
        )

        devices = []

        for ip in self.nm.all_hosts():
            data = self.nm[ip]

            mac = data.get("addresses", {}).get("mac")
            vendor = (
                data.get("vendor", {}).get(mac, "Unknown")
                if mac else "Unknown"
            )
            hostname = data.hostname() or None

            network_vendor_words = (
                "cisco",
                "huawei",
                "alcatel",
                "juniper",
                "mikrotik",
                "aruba",
                "ale international",
            )

            device_type = (
                "network"
                if vendor and any(
                    word in vendor.lower()
                    for word in network_vendor_words
                )
                else "pc"
            )

            device = {
                "ip": ip,
                "mac": mac or "Unknown",
                "vendor": vendor or "Unknown",
                "hostname": hostname,
                "type": device_type,
            }

            devices.append(device)

            logging.info(
                "Found %s | MAC=%s | Vendor=%s | Hostname=%s | Type=%s",
                device["ip"],
                device["mac"],
                device["vendor"],
                device["hostname"] or "Unknown",
                device["type"],
            )

        return devices
