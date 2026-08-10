"""Network discovery service.

Discovers devices on a network using multiple probes:
1. ARP scan (scapy) — finds live hosts + MAC addresses
2. Ping sweep (fping fallback) — finds hosts that don't respond to ARP
3. MAC vendor lookup (OUI) — identifies manufacturer
4. Reverse DNS — resolves hostnames
5. Port scan (nmap) — identifies open ports and services
6. Service fingerprinting — guesses device category from open ports
"""

import logging
import re
import socket
import subprocess
from dataclasses import dataclass, field
from ipaddress import IPv4Network

logger = logging.getLogger("apps")

# Port-to-category heuristics
CATEGORY_RULES = [
    # (ports_present, ports_absent, category)
    ({"53"}, set(), "server"),  # DNS server
    ({"80", "443", "8443"}, set(), "network"),  # Firewall/router web UI on 8443
    ({"23"}, set(), "network"),  # Telnet (managed switch)
    ({"161"}, set(), "network"),  # SNMP (managed switch/router)
    ({"80", "443", "8080"}, set(), "server"),  # Web server
    ({"22", "80"}, set(), "server"),  # SSH + Web
    ({"22"}, set(), "server"),  # SSH only
    ({"631"}, set(), "printer"),  # IPP
    ({"9100"}, set(), "printer"),  # RAW printing
    ({"515"}, set(), "printer"),  # LPR
    ({"554"}, set(), "camera"),  # RTSP (IP camera)
    ({"8554"}, set(), "camera"),  # RTSP alt port
    ({"5060"}, set(), "phone"),  # SIP
    ({"5061"}, set(), "phone"),  # SIP TLS
    ({"5353"}, set(), "other"),  # mDNS
    ({"8080"}, set(), "iot"),  # IoT web interface
    ({"1883", "8883"}, set(), "iot"),  # MQTT
]


@dataclass
class DiscoveredHost:
    ip: str
    mac: str = ""
    hostname: str = ""
    manufacturer: str = ""
    open_ports: list = field(default_factory=list)
    guessed_category: str = "unknown"
    extra_data: dict = field(default_factory=dict)


def _split_into_subnets(cidr: str, max_prefix: int = 24) -> list[str]:
    """Split a network into smaller subnets (default /24) for scanning."""
    network = IPv4Network(cidr, strict=False)
    if network.prefixlen >= max_prefix:
        return [str(network)]
    return [str(subnet) for subnet in network.subnets(new_prefix=max_prefix)]


def arp_scan(cidr: str) -> dict[str, str]:
    """ARP scan a network. Returns {ip: mac}. Splits large networks into /24 chunks."""
    results = {}
    subnets = _split_into_subnets(cidr)
    try:
        from scapy.all import ARP, Ether, srp
    except Exception:
        logger.warning("scapy not available, skipping ARP scan for %s", cidr)
        return results

    for i, subnet in enumerate(subnets, 1):
        try:
            if len(subnets) > 1 and (i == 1 or i % 10 == 0 or i == len(subnets)):
                logger.info("ARP scan subnet %d/%d: %s", i, len(subnets), subnet)
            ans, _ = srp(
                Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=subnet),
                timeout=5,
                verbose=False,
            )
            for _, rcv in ans:
                results[rcv.psrc] = rcv.hwsrc
        except Exception as e:
            logger.warning("ARP scan failed for subnet %s: %s", subnet, e)
    logger.info("ARP scan of %s found %d hosts", cidr, len(results))
    return results


def ping_sweep(cidr: str) -> set[str]:
    """Ping sweep using fping. Returns set of live IPs. Splits large networks into /24 chunks."""
    live = set()
    subnets = _split_into_subnets(cidr)
    for i, subnet in enumerate(subnets, 1):
        try:
            if len(subnets) > 1 and (i == 1 or i % 10 == 0 or i == len(subnets)):
                logger.info("Ping sweep subnet %d/%d: %s", i, len(subnets), subnet)
            result = subprocess.run(
                ["fping", "-a", "-g", subnet, "-q", "-r", "1"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            for line in result.stdout.strip().splitlines():
                ip = line.strip()
                if ip:
                    live.add(ip)
        except FileNotFoundError:
            logger.warning("fping not found, skipping ping sweep")
            return live
        except subprocess.TimeoutExpired:
            logger.warning("Ping sweep timed out for subnet %s", subnet)
    logger.info("Ping sweep of %s found %d hosts", cidr, len(live))
    return live


def resolve_hostname(ip: str) -> str:
    """Reverse DNS lookup."""
    try:
        hostname, _, _ = socket.gethostbyaddr(ip)
        return hostname
    except (socket.herror, socket.gaierror, OSError):
        return ""


def lookup_mac_vendor(mac: str) -> str:
    """Lookup manufacturer from MAC address using scapy's OUI database."""
    if not mac:
        return ""
    try:
        from scapy.all import conf

        oui = mac.upper().replace(":", "").replace("-", "")[:6]
        manufacturer = conf.manufdb._resolve_MAC(mac)
        if manufacturer and manufacturer != mac:
            return manufacturer
    except Exception:
        pass
    # Fallback: try /usr/share/nmap/nmap-mac-prefixes if available
    try:
        oui = mac.upper().replace(":", "").replace("-", "")[:6]
        with open("/usr/share/nmap/nmap-mac-prefixes") as f:
            for line in f:
                if line.startswith(oui):
                    return line.split(" ", 1)[1].strip()
    except (FileNotFoundError, OSError):
        pass
    return ""


def scan_ports(ip: str, mode: str = "quick") -> tuple[list[dict], dict]:
    """Nmap port scan + OS detection.

    mode="quick": top 100 TCP + UDP ports (~30s)
    mode="deep":  all 65535 TCP ports + top 100 UDP (~5-15min)

    Returns (ports_list, os_info_dict).
    """
    ports = []
    try:
        import nmap

        nm = nmap.PortScanner()
        if mode == "deep":
            arguments = "-sS -sU -p T:1-65535,U:1-1000 -T4 --open -O --osscan-guess -sV"
            timeout = 900  # 15 min max
        else:
            arguments = "-sS -sU --top-ports 100 -T4 --open -O --osscan-guess"
            timeout = 60

        nm.scan(hosts=ip, arguments=arguments, timeout=timeout)

        if ip in nm.all_hosts():
            host = nm[ip]
            os_matches = host.get("osmatch", [])
            for proto in ["tcp", "udp"]:
                if proto in host:
                    for port_num, port_info in host[proto].items():
                        if port_info.get("state") == "open":
                            ports.append({
                                "port": port_num,
                                "protocol": proto,
                                "service": port_info.get("name", ""),
                                "product": port_info.get("product", ""),
                                "version": port_info.get("version", ""),
                            })
            if os_matches:
                os_extra = {"os_matches": [{"name": m["name"], "accuracy": m["accuracy"]} for m in os_matches[:3]]}
                return ports, os_extra
        return ports, {}
    except Exception as e:
        logger.warning("Port scan (%s) failed for %s: %s", mode, ip, e)
        return ports, {}


def guess_category(open_ports: list[dict], os_info: dict | None = None) -> str:
    """Guess device category from open ports and OS info."""
    port_set = {str(p["port"]) for p in open_ports}

    # Check OS-based hints first
    if os_info and os_info.get("os_matches"):
        os_name = os_info["os_matches"][0]["name"].lower()
        if any(kw in os_name for kw in ["router", "routeros", "mikrotik", "cisco ios", "switch", "catalyst", "firewall", "pfsense", "opnsense", "fortigate"]):
            return "network"
        if any(kw in os_name for kw in ["printer", "jetdirect"]):
            return "printer"
        if any(kw in os_name for kw in ["linux", "ubuntu", "debian", "centos", "windows server"]):
            return "server"
        if any(kw in os_name for kw in ["windows"]):
            return "workstation"
        if any(kw in os_name for kw in ["access point", "unifi", "aruba"]):
            return "ap"
        if any(kw in os_name for kw in ["camera", "ipc", "hikvision", "dahua", "reolink", "doorbell", "visiophone"]):
            return "camera"
        if any(kw in os_name for kw in ["phone", "android", "iphone", "ios"]):
            return "phone"

    # Port-based heuristics
    for required_ports, excluded_ports, category in CATEGORY_RULES:
        if required_ports.intersection(port_set) and not excluded_ports.intersection(port_set):
            return category

    return "unknown"


def quick_scan(cidr: str) -> list[DiscoveredHost]:
    """Fast presence scan: ARP + ping only. No port scan, no OS detection.

    Runs in seconds even on /16. Used for frequent presence tracking.
    """
    logger.info("Quick scan of %s", cidr)

    try:
        network = IPv4Network(cidr, strict=False)
    except ValueError:
        logger.error("Invalid CIDR: %s", cidr)
        return []

    arp_results = arp_scan(cidr)
    ping_results = ping_sweep(cidr)

    all_ips = set(arp_results.keys()) | ping_results
    all_ips -= {str(network.network_address), str(network.broadcast_address)}

    hosts = []
    for ip in sorted(all_ips, key=lambda x: tuple(int(p) for p in x.split("."))):
        host = DiscoveredHost(ip=ip)
        host.mac = arp_results.get(ip, "")
        host.manufacturer = lookup_mac_vendor(host.mac)
        host.hostname = resolve_hostname(ip) or ip
        hosts.append(host)

    logger.info("Quick scan of %s complete: %d hosts found", cidr, len(hosts))
    return hosts


def full_scan(cidr: str) -> list[DiscoveredHost]:
    """Full discovery: ARP + ping + port scan + OS detection.

    Slow (minutes per host). Used for initial discovery or manual deep scan.
    """
    logger.info("Full scan of %s", cidr)

    try:
        network = IPv4Network(cidr, strict=False)
    except ValueError:
        logger.error("Invalid CIDR: %s", cidr)
        return []

    arp_results = arp_scan(cidr)
    ping_results = ping_sweep(cidr)

    all_ips = set(arp_results.keys()) | ping_results
    all_ips -= {str(network.network_address), str(network.broadcast_address)}

    logger.info("%d live hosts on %s, starting port scan...", len(all_ips), cidr)

    hosts = []
    total = len(all_ips)
    for i, ip in enumerate(sorted(all_ips, key=lambda x: tuple(int(p) for p in x.split("."))), 1):
        host = DiscoveredHost(ip=ip)
        host.mac = arp_results.get(ip, "")
        host.manufacturer = lookup_mac_vendor(host.mac)
        host.hostname = resolve_hostname(ip) or ip

        if i == 1 or i % 10 == 0 or i == total:
            logger.info("Port scanning host %d/%d (%s)...", i, total, ip)
        port_result = scan_ports(ip)
        if isinstance(port_result, tuple):
            host.open_ports, os_info = port_result
        else:
            host.open_ports, os_info = port_result, {}

        if os_info:
            host.extra_data["os_detection"] = os_info

        host.guessed_category = guess_category(host.open_ports, os_info)
        hosts.append(host)

    logger.info("Full scan of %s complete: %d hosts found", cidr, len(hosts))
    return hosts


# Keep backward compatibility
def discover_network(cidr: str) -> list[DiscoveredHost]:
    """Alias for full_scan."""
    return full_scan(cidr)
