import logging
import socket
import threading
from datetime import datetime

from scapy.all import sniff, IP, TCP, conf


class ConnectionMonitor:
    """Continuous TCP SYN monitoring for Linux and Windows.

    Linux: Scapy uses raw sockets/libpcap.
    Windows: install Npcap first.
    """

    def __init__(self, server_ip, ports, interface="auto"):
        self.server_ip = server_ip
        self.ports = {int(p): str(name) for p, name in ports.items()}
        self.interface = self._resolve_interface(interface)
        self.stop_event = threading.Event()
        self.on_alert = None
        self._seen = set()

    def _resolve_interface(self, interface):
        if interface and str(interface).lower() != "auto":
            return interface

        try:
            route = conf.route.route(self.server_ip)
            if route and len(route) >= 3 and route[2]:
                logging.info("Auto-selected interface: %s", route[2])
                return route[2]
        except Exception:
            logging.exception("Could not auto-detect capture interface")

        # Fallback: discover the local IP used to reach the server.
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.connect((self.server_ip, 1))
            local_ip = sock.getsockname()[0]
        finally:
            sock.close()

        logging.warning(
            "Could not determine interface automatically. Local IP is %s.",
            local_ip
        )
        return None

    def _packet_handler(self, packet):
        try:
            if not packet.haslayer(IP) or not packet.haslayer(TCP):
                return

            ip = packet[IP]
            tcp = packet[TCP]

            if ip.dst != self.server_ip:
                return
            if tcp.dport not in self.ports:
                return

            # SYN without ACK = beginning of a TCP connection.
            if not (tcp.flags & 0x02) or (tcp.flags & 0x10):
                return

            key = (
                ip.src,
                int(tcp.sport),
                ip.dst,
                int(tcp.dport),
            )

            if key in self._seen:
                return

            self._seen.add(key)
            if len(self._seen) > 5000:
                self._seen.clear()

            alert = {
                "source_ip": ip.src,
                "source_port": int(tcp.sport),
                "server_ip": ip.dst,
                "server_port": int(tcp.dport),
                "service": self.ports[tcp.dport],
                "protocol": "TCP",
                "time": datetime.now(),
            }

            logging.warning(
                "Connection attempt detected: %s:%s -> %s:%s (%s)",
                alert["source_ip"],
                alert["source_port"],
                alert["server_ip"],
                alert["server_port"],
                alert["service"],
            )

            if self.on_alert:
                self.on_alert(alert)

        except Exception:
            logging.exception("Packet processing error")

    def detect_attempts(self, on_alert):
        if not self.ports:
            raise RuntimeError("No monitored ports configured.")

        self.on_alert = on_alert

        bpf = (
            f"tcp and dst host {self.server_ip} and "
            "(" + " or ".join(
                f"dst port {port}" for port in self.ports
            ) + ")"
        )

        logging.info(
            "Starting packet monitoring: %s -> %s",
            self.interface or "auto",
            self.server_ip,
        )
        logging.info("Capture filter: %s", bpf)

        kwargs = {
            "filter": bpf,
            "prn": self._packet_handler,
            "store": False,
        }

        if self.interface:
            kwargs["iface"] = self.interface

        sniff(**kwargs)

    def stop(self):
        self.stop_event.set()
