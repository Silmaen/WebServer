"""Query OpenWrt gateways via the ubus JSON-RPC API.

Reads DHCP leases, host hints (ARP+DHCP+wifi aggregated), and wifi clients
from the router to build a fast, complete picture of the network.

Requires on the router:
  - rpcd + uhttpd-mod-ubus (pre-installed with LuCI)
  - rpcd-mod-luci (for getDHCPLeases / getHostHints)
  - rpcd-mod-iwinfo (optional, for wifi client details)
  - A restricted 'monitor' user with read-only ACL
"""

import logging
from dataclasses import dataclass, field

import requests

logger = logging.getLogger("apps")

# Null session used only for login
_NULL_SESSION = "00000000000000000000000000000000"


@dataclass
class GatewayHost:
    """A host discovered via the gateway."""
    ip: str
    mac: str = ""
    hostname: str = ""
    is_wifi: bool = False
    source: str = ""  # "dhcp", "arp", "both"


class UbusClient:
    """Minimal ubus JSON-RPC client for OpenWrt."""

    def __init__(self, gateway_ip: str, credential, timeout: int = 15):
        scheme = "https" if credential.use_https else "http"
        self.url = f"{scheme}://{gateway_ip}/ubus"
        self.credential = credential
        self.timeout = timeout
        self.verify = credential.verify_ssl
        self._session_token = None
        self._req_id = 0

    def _next_id(self):
        self._req_id += 1
        return self._req_id

    def _call(self, session: str, obj: str, method: str, params: dict | None = None) -> dict:
        """Make a ubus JSON-RPC call."""
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
            raise RuntimeError(f"ubus error: {data['error']}")
        result = data.get("result")
        if not result:
            raise RuntimeError(f"ubus empty result for {obj}.{method}")
        # ubus result format: [status_code, {data}]
        if isinstance(result, list):
            if result[0] != 0:
                raise RuntimeError(f"ubus {obj}.{method} returned status {result[0]}")
            return result[1] if len(result) > 1 else {}
        return result

    def login(self):
        """Authenticate and store session token."""
        result = self._call(
            _NULL_SESSION, "session", "login",
            {"username": self.credential.username, "password": self.credential.password},
        )
        self._session_token = result.get("ubus_rpc_session")
        if not self._session_token:
            raise RuntimeError("Login failed: no session token returned")
        logger.debug("ubus login OK, session=%s...", self._session_token[:8])

    @property
    def token(self):
        if not self._session_token:
            self.login()
        return self._session_token

    def get_dhcp_leases(self) -> list[dict]:
        """Get DHCP leases via luci-rpc."""
        result = self._call(self.token, "luci-rpc", "getDHCPLeases", {})
        return result.get("dhcp_leases", [])

    def get_host_hints(self) -> dict:
        """Get aggregated host info (ARP + DHCP + wifi).

        Returns a dict keyed by MAC address with ipaddrs, ip6addrs, name.
        """
        return self._call(self.token, "luci-rpc", "getHostHints", {})

    def get_wifi_clients(self) -> dict:
        """Get wireless device info including associations."""
        try:
            return self._call(self.token, "luci-rpc", "getWirelessDevices", {})
        except Exception as e:
            logger.debug("getWirelessDevices not available: %s", e)
            return {}


def query_gateway(gateway_ip: str, credential) -> list[GatewayHost]:
    """Query an OpenWrt gateway for connected devices.

    Combines DHCP leases and host hints (ARP table aggregation).
    Returns a merged list of GatewayHost objects.
    """
    client = UbusClient(gateway_ip, credential)
    client.login()

    hosts: dict[str, GatewayHost] = {}

    # 1. DHCP leases — most reliable source for hostname + MAC + IP
    try:
        leases = client.get_dhcp_leases()
        for lease in leases:
            ip = lease.get("ipaddr", "")
            mac = lease.get("macaddr", "").lower()
            hostname = lease.get("hostname", "")
            if ip:
                hosts[ip] = GatewayHost(ip=ip, mac=mac, hostname=hostname, source="dhcp")
        logger.info("Gateway %s: %d DHCP leases", gateway_ip, len(leases))
    except Exception as e:
        logger.warning("Failed to get DHCP leases from %s: %s", gateway_ip, e)

    # 2. Host hints — aggregated from ARP + DHCP + wireless, keyed by MAC
    try:
        hints = client.get_host_hints()
        hint_count = 0
        for mac, info in hints.items():
            mac = mac.lower()
            ipaddrs = info.get("ipaddrs", [])
            name = info.get("name", "")
            for ip in ipaddrs:
                hint_count += 1
                if ip in hosts:
                    hosts[ip].source = "both"
                    if not hosts[ip].hostname and name:
                        hosts[ip].hostname = name
                    if not hosts[ip].mac:
                        hosts[ip].mac = mac
                else:
                    hosts[ip] = GatewayHost(ip=ip, mac=mac, hostname=name, source="arp")
        logger.info("Gateway %s: %d host hints", gateway_ip, hint_count)
    except Exception as e:
        logger.warning("Failed to get host hints from %s: %s", gateway_ip, e)

    # 3. Wifi clients — mark which hosts are connected via wifi
    try:
        wifi_data = client.get_wifi_clients()
        wifi_macs = set()
        for radio_name, radio_info in wifi_data.items():
            interfaces = radio_info.get("interfaces", [])
            for iface in interfaces:
                assoclist = iface.get("assoclist", {})
                for mac_addr in assoclist:
                    wifi_macs.add(mac_addr.lower())
        for host in hosts.values():
            if host.mac in wifi_macs:
                host.is_wifi = True
        if wifi_macs:
            logger.info("Gateway %s: %d wifi clients", gateway_ip, len(wifi_macs))
    except Exception as e:
        logger.debug("Failed to get wifi clients from %s: %s", gateway_ip, e)

    if not hosts:
        raise RuntimeError(f"No data retrieved from gateway {gateway_ip}")

    logger.info("Gateway %s: %d unique hosts total", gateway_ip, len(hosts))
    return sorted(hosts.values(), key=lambda h: tuple(int(p) for p in h.ip.split(".")))
