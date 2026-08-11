"""Exécuteurs de checks de supervision.

Architecture ouverte : chaque type dérive de `BaseCheck` et rend un `CheckOutput`.
`CHECK_REGISTRY` associe le type déclaré sur le check à sa classe.
"""

import logging
import selectors
import socket
import subprocess
import time
from dataclasses import dataclass

import requests

logger = logging.getLogger("apps")


@dataclass
class CheckOutput:
    """Le résultat d'un check : succès, temps de réponse, sortie ou erreur."""

    success: bool
    response_time_ms: float = 0.0
    output: str = ""
    error: str = ""

    @property
    def status(self):
        """L'état correspondant, tel que stocké dans `CheckResult`."""
        return "up" if self.success else "down"


class BaseCheck:
    """Contrat commun aux exécuteurs de checks."""

    def execute(self, ip: str, config: dict, timeout: int) -> CheckOutput:
        """Exécute le check sur `ip` et rend son résultat."""
        raise NotImplementedError


class ICMPCheck(BaseCheck):
    """Ping via fping, avec repli sur une connexion TCP."""

    # Ports tentés quand ICMP échoue : les plus courants, Windows compris
    # (135/139/445), pour distinguer un appareil muet d'un appareil éteint.
    FALLBACK_PORTS = [80, 443, 22, 445, 139, 135, 8080, 8443, 53, 3389]

    @staticmethod
    def _ping(ip: str, count: int, timeout: int, start: float) -> CheckOutput | None:
        """Tente un ping ICMP. Rend un `CheckOutput` en cas de succès, sinon None."""
        try:
            result = subprocess.run(
                ["fping", "-c", str(count), "-t", str(timeout * 1000), "-q", ip],
                capture_output=True,
                text=True,
                timeout=timeout + 5,
            )
            elapsed_per = (time.time() - start) * 1000 / count
            stderr = result.stderr.strip()
            if result.returncode == 0:
                avg_ms = elapsed_per
                if "/" in stderr:
                    parts = stderr.split("=")
                    if len(parts) >= 3:
                        try:
                            avg_ms = float(parts[-1].strip().split("/")[1])
                        except (IndexError, ValueError):
                            pass
                return CheckOutput(success=True, response_time_ms=avg_ms, output=stderr)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return None

    def _tcp_probe(self, ip: str, ports: list[int], timeout: int) -> CheckOutput | None:
        """Tente une connexion TCP sur tous les ports d'un coup ; le premier gagne.

        Les tenter en série coûtait un timeout par port, soit une trentaine de
        secondes par appareil muet à ICMP — assez pour que la file de checks ne se
        vide plus jamais. Concurremment cela coûte un seul budget et conclut la même
        chose, les ports étant indépendants.
        """
        budget = min(timeout, 3)
        selector = selectors.DefaultSelector()
        pending = {}
        try:
            for port in ports:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setblocking(False)
                try:
                    # EINPROGRESS est la réponse normale ; toute autre (RST, réseau
                    # injoignable) signifie que ce port est déjà décidé.
                    sock.connect_ex((ip, port))
                    selector.register(sock, selectors.EVENT_WRITE)
                    pending[sock] = port
                except (OSError, ValueError):
                    sock.close()

            start = time.time()
            deadline = start + budget
            while pending:
                remaining = deadline - time.time()
                if remaining <= 0:
                    break
                ready = selector.select(remaining)
                if not ready:
                    break
                for key, _ in ready:
                    sock = key.fileobj
                    port = pending.pop(sock, None)
                    selector.unregister(sock)
                    # Un socket inscriptible signifie que le connect est terminé, avec
                    # ou sans succès : SO_ERROR distingue les deux.
                    if sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR) == 0:
                        return CheckOutput(
                            success=True,
                            response_time_ms=(time.time() - start) * 1000,
                            output=f"ICMP muet, joignable via TCP:{port}",
                        )
        finally:
            for sock in list(pending):
                try:
                    selector.unregister(sock)
                except (KeyError, ValueError):
                    pass
                sock.close()
            selector.close()
        return None

    def execute(self, ip: str, config: dict, timeout: int) -> CheckOutput:
        """Ping, puis repli TCP sur les ports connus, puis les ports courants."""
        count = config.get("count", 3)
        start = time.time()

        result = self._ping(ip, count, timeout, start)
        if result:
            return result

        result = self._tcp_probe(ip, self._ports_de_repli(ip, config), timeout)
        if result:
            return result

        elapsed = (time.time() - start) * 1000
        return CheckOutput(
            success=False, response_time_ms=elapsed,
            error="ICMP et repli TCP tous deux sans réponse",
        )

    def _ports_de_repli(self, ip: str, config: dict) -> list[int]:
        """Ports à tenter en TCP : ceux du check, ceux de l'appareil, puis les courants."""
        ports = list(config.get("fallback_ports", []))
        if ports:
            return ports
        try:
            from apps.devices.models import Device
            device = Device.objects.filter(ip_address=ip).first()
            if device and device.open_ports:
                ports = [p["port"] for p in device.open_ports[:5]]
        except Exception:
            pass
        return ports or self.FALLBACK_PORTS


class TCPCheck(BaseCheck):
    """Vérification de l'ouverture d'un port TCP."""

    def execute(self, ip: str, config: dict, timeout: int) -> CheckOutput:
        """Tente une connexion sur le port configuré (80 par défaut)."""
        port = config.get("port", 80)
        start = time.time()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            elapsed = (time.time() - start) * 1000
            sock.close()
            if result == 0:
                return CheckOutput(
                    success=True, response_time_ms=elapsed, output=f"Port {port} ouvert",
                )
            return CheckOutput(
                success=False, response_time_ms=elapsed,
                error=f"Port {port} fermé (errno={result})",
            )
        except TimeoutError:
            elapsed = (time.time() - start) * 1000
            return CheckOutput(
                success=False, response_time_ms=elapsed, error=f"Port {port} : délai dépassé",
            )
        except OSError as e:
            elapsed = (time.time() - start) * 1000
            return CheckOutput(success=False, response_time_ms=elapsed, error=str(e))


class HTTPCheck(BaseCheck):
    """Vérification d'un endpoint HTTP(S)."""

    def execute(self, ip: str, config: dict, timeout: int) -> CheckOutput:
        """Appelle l'URL configurée et compare le code au code attendu."""
        url = config.get("url", "")
        if not url:
            scheme = config.get("scheme", "http")
            port = config.get("port", 80 if scheme == "http" else 443)
            path = config.get("path", "/")
            url = f"{scheme}://{ip}:{port}{path}"
        method = config.get("method", "GET").upper()
        expected_status = config.get("expected_status", 200)
        verify_ssl = config.get("verify_ssl", False)
        start = time.time()
        try:
            resp = requests.request(
                method, url, timeout=timeout, verify=verify_ssl, allow_redirects=True,
            )
            elapsed = (time.time() - start) * 1000
            if resp.status_code != expected_status:
                return CheckOutput(
                    success=False, response_time_ms=elapsed,
                    error=f"Code {expected_status} attendu, {resp.status_code} reçu",
                )
            return CheckOutput(
                success=True, response_time_ms=elapsed,
                output=f"HTTP {resp.status_code} ({elapsed:.0f} ms)",
            )
        except requests.exceptions.Timeout:
            elapsed = (time.time() - start) * 1000
            return CheckOutput(
                success=False, response_time_ms=elapsed, error="HTTP : délai dépassé",
            )
        except requests.exceptions.RequestException as e:
            elapsed = (time.time() - start) * 1000
            return CheckOutput(success=False, response_time_ms=elapsed, error=str(e))


class DNSCheck(BaseCheck):
    """Vérification d'un résolveur DNS."""

    def execute(self, ip: str, config: dict, timeout: int) -> CheckOutput:
        """Interroge le résolveur sur un nom connu et rend les enregistrements."""
        # Importé ici : dnspython n'est utile qu'à ce check.
        import dns.resolver

        query_name = config.get("query", "google.com")
        record_type = config.get("record_type", "A")
        start = time.time()
        try:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = [ip]
            resolver.timeout = timeout
            resolver.lifetime = timeout
            answers = resolver.resolve(query_name, record_type)
            elapsed = (time.time() - start) * 1000
            records = [str(r) for r in answers]
            return CheckOutput(
                success=True, response_time_ms=elapsed,
                output=f"{record_type} {query_name} : {', '.join(records)}",
            )
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            return CheckOutput(success=False, response_time_ms=elapsed, error=str(e))


CHECK_REGISTRY = {
    "icmp": ICMPCheck(),
    "tcp": TCPCheck(),
    "http": HTTPCheck(),
    "dns": DNSCheck(),
}


def run_check(check_type: str, ip: str, config: dict, timeout: int = 10) -> CheckOutput:
    """Exécute le check du type demandé et rend son `CheckOutput`."""
    executor = CHECK_REGISTRY.get(check_type)
    if not executor:
        return CheckOutput(success=False, error=f"Type de check inconnu : {check_type}")
    return executor.execute(ip, config, timeout)
