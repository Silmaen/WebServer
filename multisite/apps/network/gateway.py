"""Interrogation des gateways OpenWrt via l'API JSON-RPC ubus.

Lit les baux DHCP, les « host hints » (agrégat ARP + DHCP + wifi) et les clients
wifi du routeur, ce qui donne une vue du réseau plus rapide et plus complète qu'un
scan. Nécessite sur le routeur rpcd, uhttpd-mod-ubus, rpcd-mod-luci (et
rpcd-mod-iwinfo pour le wifi), avec un utilisateur « monitor » en lecture seule.
"""

import logging
from dataclasses import dataclass

import requests

logger = logging.getLogger("apps")

# Session nulle, utilisée uniquement pour se connecter.
_NULL_SESSION = "00000000000000000000000000000000"


@dataclass
class GatewayHost:
    """Un hôte vu par la gateway."""

    ip: str
    mac: str = ""
    hostname: str = ""
    is_wifi: bool = False
    source: str = ""  # "dhcp", "arp" ou "both"


class UbusClient:
    """Client JSON-RPC ubus minimal pour OpenWrt."""

    def __init__(self, gateway_ip: str, credential, timeout: int = 15):
        scheme = "https" if credential.use_https else "http"
        self.url = f"{scheme}://{gateway_ip}/ubus"
        self.credential = credential
        self.timeout = timeout
        self.verify = credential.verify_ssl
        self._session_token = None
        self._req_id = 0

    def _next_id(self):
        """Numéro de requête suivant, exigé par JSON-RPC."""
        self._req_id += 1
        return self._req_id

    def _call(self, session: str, obj: str, method: str, params: dict | None = None) -> dict:
        """Effectue un appel JSON-RPC ubus et rend son résultat."""
        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "call",
            "params": [session, obj, method, params or {}],
        }
        resp = requests.post(self.url, json=payload, timeout=self.timeout, verify=self.verify)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise RuntimeError(f"erreur ubus : {data['error']}")
        result = data.get("result")
        if not result:
            raise RuntimeError(f"résultat ubus vide pour {obj}.{method}")
        # Format de réponse ubus : [code_de_statut, {données}].
        if isinstance(result, list):
            if result[0] != 0:
                raise RuntimeError(f"ubus {obj}.{method} a répondu le statut {result[0]}")
            return result[1] if len(result) > 1 else {}
        return result

    def login(self):
        """S'authentifie et retient le jeton de session."""
        result = self._call(
            _NULL_SESSION, "session", "login",
            {"username": self.credential.username, "password": self.credential.password},
        )
        self._session_token = result.get("ubus_rpc_session")
        if not self._session_token:
            raise RuntimeError("Connexion refusée : aucun jeton de session renvoyé")
        logger.debug("connexion ubus OK, session=%s...", self._session_token[:8])

    @property
    def token(self):
        """Le jeton de session, en se connectant à la première demande."""
        if not self._session_token:
            self.login()
        return self._session_token

    def get_dhcp_leases(self) -> list[dict]:
        """Les baux DHCP, via luci-rpc."""
        result = self._call(self.token, "luci-rpc", "getDHCPLeases", {})
        return result.get("dhcp_leases", [])

    def get_host_hints(self) -> dict:
        """Les hôtes agrégés (ARP + DHCP + wifi), indexés par adresse MAC."""
        return self._call(self.token, "luci-rpc", "getHostHints", {})

    def get_wifi_clients(self) -> dict:
        """Les radios wifi et leurs associations, ou {} si rpcd-mod-iwinfo manque."""
        try:
            return self._call(self.token, "luci-rpc", "getWirelessDevices", {})
        except Exception as e:
            logger.debug("getWirelessDevices indisponible : %s", e)
            return {}


def _ajouter_baux(client, gateway_ip, hosts):
    """Les baux DHCP : la source la plus fiable pour nom + MAC + IP."""
    try:
        leases = client.get_dhcp_leases()
    except Exception as e:
        logger.warning("baux DHCP illisibles sur %s : %s", gateway_ip, e)
        return
    for lease in leases:
        ip = lease.get("ipaddr", "")
        if ip:
            hosts[ip] = GatewayHost(
                ip=ip,
                mac=lease.get("macaddr", "").lower(),
                hostname=lease.get("hostname", ""),
                source="dhcp",
            )
    logger.info("Gateway %s : %d baux DHCP", gateway_ip, len(leases))


def _ajouter_hints(client, gateway_ip, hosts):
    """Les « host hints » complètent les baux avec ce que l'ARP a vu."""
    try:
        hints = client.get_host_hints()
    except Exception as e:
        logger.warning("host hints illisibles sur %s : %s", gateway_ip, e)
        return
    hint_count = 0
    for mac, info in hints.items():
        mac = mac.lower()
        name = info.get("name", "")
        for ip in info.get("ipaddrs", []):
            hint_count += 1
            known = hosts.get(ip)
            if known is None:
                hosts[ip] = GatewayHost(ip=ip, mac=mac, hostname=name, source="arp")
                continue
            known.source = "both"
            known.hostname = known.hostname or name
            known.mac = known.mac or mac
    logger.info("Gateway %s : %d host hints", gateway_ip, hint_count)


def _marquer_wifi(client, gateway_ip, hosts):
    """Marque les hôtes associés à une radio wifi."""
    try:
        wifi_data = client.get_wifi_clients()
    except Exception as e:
        logger.debug("clients wifi illisibles sur %s : %s", gateway_ip, e)
        return
    wifi_macs = set()
    for radio_info in wifi_data.values():
        for iface in radio_info.get("interfaces", []):
            for mac_addr in iface.get("assoclist", {}):
                wifi_macs.add(mac_addr.lower())
    for host in hosts.values():
        if host.mac in wifi_macs:
            host.is_wifi = True
    if wifi_macs:
        logger.info("Gateway %s : %d clients wifi", gateway_ip, len(wifi_macs))


def query_gateway(gateway_ip: str, credential) -> list[GatewayHost]:
    """Interroge une gateway OpenWrt et rend ses hôtes connectés, triés par adresse."""
    client = UbusClient(gateway_ip, credential)
    client.login()

    hosts: dict[str, GatewayHost] = {}
    _ajouter_baux(client, gateway_ip, hosts)
    _ajouter_hints(client, gateway_ip, hosts)
    _marquer_wifi(client, gateway_ip, hosts)

    if not hosts:
        raise RuntimeError(f"aucune donnée obtenue de la gateway {gateway_ip}")

    logger.info("Gateway %s : %d hôtes uniques au total", gateway_ip, len(hosts))
    return sorted(hosts.values(), key=lambda h: tuple(int(p) for p in h.ip.split(".")))
