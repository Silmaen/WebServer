"""Découverte des appareils d'un réseau.

Enchaîne les sondes du plus large au plus coûteux : scan ARP (scapy) pour les hôtes
vivants et leurs MAC, balayage ping (fping) pour ceux qui ignorent l'ARP, recherche
du fabricant par OUI, DNS inverse, puis scan de ports nmap et déduction de la
catégorie.
"""

import logging
import socket
import subprocess
from dataclasses import dataclass, field
from ipaddress import IPv4Network

logger = logging.getLogger("apps")

# Heuristiques port → catégorie. **L'ordre compte** : la première règle dont un port
# est présent gagne, donc les signatures les plus spécifiques viennent d'abord.
CATEGORY_RULES = [
    # (ports présents, ports absents, catégorie)
    ({"53"}, set(), "server"),  # DNS
    ({"80", "443", "8443"}, set(), "network"),  # interface web de pare-feu/routeur
    ({"23"}, set(), "network"),  # telnet (switch administrable)
    ({"161"}, set(), "network"),  # SNMP
    ({"80", "443", "8080"}, set(), "server"),  # serveur web
    ({"22", "80"}, set(), "server"),  # SSH + web
    ({"22"}, set(), "server"),  # SSH seul
    ({"631"}, set(), "printer"),  # IPP
    ({"9100"}, set(), "printer"),  # impression brute
    ({"515"}, set(), "printer"),  # LPR
    ({"554"}, set(), "camera"),  # RTSP
    ({"8554"}, set(), "camera"),  # RTSP, port alternatif
    ({"5060"}, set(), "phone"),  # SIP
    ({"5061"}, set(), "phone"),  # SIP TLS
    ({"5353"}, set(), "other"),  # mDNS
    ({"8080"}, set(), "iot"),  # interface web d'objet connecté
    ({"1883", "8883"}, set(), "iot"),  # MQTT
]

# Mots-clés cherchés dans l'OS deviné par nmap, dans l'ordre d'examen.
OS_KEYWORDS = [
    (("router", "routeros", "mikrotik", "cisco ios", "switch", "catalyst",
      "firewall", "pfsense", "opnsense", "fortigate"), "network"),
    (("printer", "jetdirect"), "printer"),
    (("linux", "ubuntu", "debian", "centos", "windows server"), "server"),
    (("windows",), "workstation"),
    (("access point", "unifi", "aruba"), "ap"),
    (("camera", "ipc", "hikvision", "dahua", "reolink", "doorbell", "visiophone"), "camera"),
    (("phone", "android", "iphone", "ios"), "phone"),
]


@dataclass
class DiscoveredHost:
    """Un hôte trouvé par le scan, avant d'être rapproché d'un `Device`."""

    ip: str
    mac: str = ""
    hostname: str = ""
    manufacturer: str = ""
    open_ports: list = field(default_factory=list)
    guessed_category: str = "unknown"
    extra_data: dict = field(default_factory=dict)


def _split_into_subnets(cidr: str, max_prefix: int = 24) -> list[str]:
    """Découpe un réseau en sous-réseaux (/24 par défaut) pour le scanner."""
    network = IPv4Network(cidr, strict=False)
    if network.prefixlen >= max_prefix:
        return [str(network)]
    return [str(subnet) for subnet in network.subnets(new_prefix=max_prefix)]


def _doit_journaliser(index: int, total: int) -> bool:
    """Ne journaliser que le premier, le dernier et un sous-réseau sur dix."""
    return total > 1 and (index == 1 or index % 10 == 0 or index == total)


def arp_scan(cidr: str) -> dict[str, str]:
    """Scan ARP du réseau. Rend {ip: mac}, en découpant les grands réseaux en /24."""
    results = {}
    subnets = _split_into_subnets(cidr)
    try:
        from scapy.all import ARP, Ether, srp
    except Exception:
        logger.warning("scapy indisponible, scan ARP ignoré pour %s", cidr)
        return results

    for i, subnet in enumerate(subnets, 1):
        try:
            if _doit_journaliser(i, len(subnets)):
                logger.info("Scan ARP du sous-réseau %d/%d : %s", i, len(subnets), subnet)
            ans, _ = srp(
                Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=subnet),
                timeout=5,
                verbose=False,
            )
            for _, rcv in ans:
                results[rcv.psrc] = rcv.hwsrc
        except Exception as e:
            logger.warning("Scan ARP en échec sur %s : %s", subnet, e)
    logger.info("Scan ARP de %s : %d hôtes", cidr, len(results))
    return results


def ping_sweep(cidr: str) -> set[str]:
    """Balayage ping via fping. Rend les IP vivantes, par tranches de /24."""
    live = set()
    subnets = _split_into_subnets(cidr)
    for i, subnet in enumerate(subnets, 1):
        try:
            if _doit_journaliser(i, len(subnets)):
                logger.info("Balayage ping du sous-réseau %d/%d : %s", i, len(subnets), subnet)
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
            logger.warning("fping introuvable, balayage ping ignoré")
            return live
        except subprocess.TimeoutExpired:
            logger.warning("Balayage ping expiré sur %s", subnet)
    logger.info("Balayage ping de %s : %d hôtes", cidr, len(live))
    return live


def resolve_hostname(ip: str) -> str:
    """Résolution DNS inverse ; chaîne vide si l'adresse n'a pas de nom."""
    try:
        hostname, _, _ = socket.gethostbyaddr(ip)
        return hostname
    except (socket.herror, socket.gaierror, OSError):
        return ""


def lookup_mac_vendor(mac: str) -> str:
    """Fabricant déduit de l'adresse MAC, via scapy puis la base OUI de nmap."""
    if not mac:
        return ""
    try:
        from scapy.all import conf

        manufacturer = conf.manufdb._resolve_MAC(mac)
        if manufacturer and manufacturer != mac:
            return manufacturer
    except Exception:
        pass
    # Repli sur la table de nmap, présente dans l'image.
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
    """Scan de ports nmap et détection d'OS.

     :param mode : "quick" (top 100 TCP/UDP, ~30 s) ou "deep" (tous les TCP, ~5-15 min).
     :return : (liste des ports ouverts, informations d'OS).
    """
    ports = []
    try:
        # Importé ici : nmap n'est présent que dans l'image Docker.
        import nmap

        nm = nmap.PortScanner()
        if mode == "deep":
            arguments = "-sS -sU -p T:1-65535,U:1-1000 -T4 --open -O --osscan-guess -sV"
            timeout = 900
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
                os_extra = {
                    "os_matches": [
                        {"name": m["name"], "accuracy": m["accuracy"]} for m in os_matches[:3]
                    ],
                }
                return ports, os_extra
        return ports, {}
    except Exception as e:
        logger.warning("Scan de ports (%s) en échec sur %s : %s", mode, ip, e)
        return ports, {}


def guess_category(open_ports: list[dict], os_info: dict | None = None) -> str:
    """Devine la catégorie d'un appareil depuis ses ports et son OS."""
    # L'OS est le meilleur indice quand nmap a su le deviner.
    if os_info and os_info.get("os_matches"):
        os_name = os_info["os_matches"][0]["name"].lower()
        for keywords, category in OS_KEYWORDS:
            if any(kw in os_name for kw in keywords):
                return category

    port_set = {str(p["port"]) for p in open_ports}
    for required_ports, excluded_ports, category in CATEGORY_RULES:
        if required_ports.intersection(port_set) and not excluded_ports.intersection(port_set):
            return category

    return "unknown"


def _hotes_vivants(cidr: str):
    """Les adresses vivantes du réseau et les MAC relevées par l'ARP.

     :return : (adresses triées, {ip: mac}), ou (None, {}) si le CIDR est invalide.
    """
    try:
        network = IPv4Network(cidr, strict=False)
    except ValueError:
        logger.error("CIDR invalide : %s", cidr)
        return None, {}

    macs = arp_scan(cidr)
    all_ips = set(macs.keys()) | ping_sweep(cidr)
    all_ips -= {str(network.network_address), str(network.broadcast_address)}
    ips = sorted(all_ips, key=lambda x: tuple(int(p) for p in x.split(".")))
    return ips, macs


def _decrire(ip: str, macs: dict[str, str]) -> DiscoveredHost:
    """Un hôte avec son MAC, son fabricant et son nom résolu."""
    host = DiscoveredHost(ip=ip)
    host.mac = macs.get(ip, "")
    host.manufacturer = lookup_mac_vendor(host.mac)
    host.hostname = resolve_hostname(ip) or ip
    return host


def quick_scan(cidr: str) -> list[DiscoveredHost]:
    """Scan de présence : ARP + ping seulement, sans ports ni OS.

    Tient en quelques secondes même sur un /16, d'où son usage périodique.
    """
    logger.info("Scan rapide de %s", cidr)
    ips, macs = _hotes_vivants(cidr)
    if ips is None:
        return []

    hosts = [_decrire(ip, macs) for ip in ips]
    logger.info("Scan rapide de %s terminé : %d hôtes", cidr, len(hosts))
    return hosts


def full_scan(cidr: str) -> list[DiscoveredHost]:
    """Découverte complète : ARP + ping + scan de ports + détection d'OS.

    Lent (des minutes par hôte), réservé à la découverte initiale ou au scan manuel.
    """
    logger.info("Scan complet de %s", cidr)
    ips, macs = _hotes_vivants(cidr)
    if ips is None:
        return []

    logger.info("%d hôtes vivants sur %s, début du scan de ports", len(ips), cidr)

    hosts = []
    total = len(ips)
    for i, ip in enumerate(ips, 1):
        host = _decrire(ip, macs)
        if i == 1 or i % 10 == 0 or i == total:
            logger.info("Scan de ports de l'hôte %d/%d (%s)", i, total, ip)
        host.open_ports, os_info = scan_ports(ip)
        if os_info:
            host.extra_data["os_detection"] = os_info
        host.guessed_category = guess_category(host.open_ports, os_info)
        hosts.append(host)

    logger.info("Scan complet de %s terminé : %d hôtes", cidr, len(hosts))
    return hosts


def discover_network(cidr: str) -> list[DiscoveredHost]:
    """Alias historique de `full_scan`, conservé pour les appels existants."""
    return full_scan(cidr)
