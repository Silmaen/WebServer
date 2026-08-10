"""Monitoring check executors.

Pluggable architecture: BaseCheck with execute() -> CheckOutput.
Registry maps check_type to concrete class.
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
    success: bool
    response_time_ms: float = 0.0
    output: str = ""
    error: str = ""

    @property
    def status(self):
        return "up" if self.success else "down"


class BaseCheck:
    def execute(self, ip: str, config: dict, timeout: int) -> CheckOutput:
        raise NotImplementedError


class ICMPCheck(BaseCheck):
    """Ping check using fping, with TCP fallback on known ports."""

    # Common ports to try if ICMP fails (includes Windows: 135/139/445)
    FALLBACK_PORTS = [80, 443, 22, 445, 139, 135, 8080, 8443, 53, 3389]

    def _ping(self, ip: str, count: int, timeout: int) -> CheckOutput | None:
        """Try ICMP ping. Returns CheckOutput on success, None on failure."""
        try:
            result = subprocess.run(
                ["fping", "-c", str(count), "-t", str(timeout * 1000), "-q", ip],
                capture_output=True,
                text=True,
                timeout=timeout + 5,
            )
            elapsed_per = (time.time() - self._start) * 1000 / count
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
        """Try TCP connect on the ports, all at once. First one to answer wins.

        This used to walk the list serially with a 3 s timeout each, and that was the
        single most expensive thing in the lab's monitoring. Ten ports at three
        seconds meant **thirty seconds of pure waiting for every device that does not
        answer ICMP** -- and with 41 such devices on a 300 s interval, that one loop
        accounted for ~1 230 s of work against 1 200 s of worker capacity. The queue
        could only grow; it had reached 5 670 messages.

        Concurrently it costs one budget instead of ten and concludes exactly the
        same thing, because the ports are independent and only the first answer
        matters. Measured on this lab: a down device went from ~27 s to a few
        seconds.

        Non-blocking connects plus one selector, rather than threads: ten sockets
        waiting on a timeout need no parallelism, only no serialisation.
        """
        budget = min(timeout, 3)
        selector = selectors.DefaultSelector()
        pending = {}
        try:
            for port in ports:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setblocking(False)
                try:
                    # EINPROGRESS is the normal answer here; anything else (a RST,
                    # an unreachable network) means this port is already decided.
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
                    # A writable socket means the connect finished -- successfully or
                    # not. SO_ERROR is what tells the two apart.
                    if sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR) == 0:
                        return CheckOutput(
                            success=True,
                            response_time_ms=(time.time() - start) * 1000,
                            output=f"ICMP failed, alive via TCP:{port}",
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
        count = config.get("count", 3)
        self._start = time.time()

        # 1. Try ICMP
        result = self._ping(ip, count, timeout)
        if result:
            return result

        # 2. ICMP failed — try TCP fallback on known ports from device, then common ports
        fallback_ports = list(config.get("fallback_ports", []))
        if not fallback_ports:
            # Try to get known open ports from the device
            try:
                from apps.devices.models import Device
                device = Device.objects.filter(ip_address=ip).first()
                if device and device.open_ports:
                    fallback_ports = [p["port"] for p in device.open_ports[:5]]
            except Exception:
                pass
        if not fallback_ports:
            fallback_ports = self.FALLBACK_PORTS

        result = self._tcp_probe(ip, fallback_ports, timeout)
        if result:
            return result

        # 3. Everything failed
        elapsed = (time.time() - self._start) * 1000
        return CheckOutput(success=False, response_time_ms=elapsed, error="ICMP + TCP fallback failed")


class TCPCheck(BaseCheck):
    """TCP port connectivity check."""

    def execute(self, ip: str, config: dict, timeout: int) -> CheckOutput:
        port = config.get("port", 80)
        start = time.time()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            elapsed = (time.time() - start) * 1000
            sock.close()
            if result == 0:
                return CheckOutput(success=True, response_time_ms=elapsed, output=f"Port {port} open")
            return CheckOutput(success=False, response_time_ms=elapsed, error=f"Port {port} closed (errno={result})")
        except socket.timeout:
            elapsed = (time.time() - start) * 1000
            return CheckOutput(success=False, response_time_ms=elapsed, error=f"Port {port} timeout")
        except OSError as e:
            elapsed = (time.time() - start) * 1000
            return CheckOutput(success=False, response_time_ms=elapsed, error=str(e))


class HTTPCheck(BaseCheck):
    """HTTP/HTTPS endpoint check."""

    def execute(self, ip: str, config: dict, timeout: int) -> CheckOutput:
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
            resp = requests.request(method, url, timeout=timeout, verify=verify_ssl, allow_redirects=True)
            elapsed = (time.time() - start) * 1000
            success = resp.status_code == expected_status
            output = f"HTTP {resp.status_code} ({elapsed:.0f}ms)"
            if not success:
                return CheckOutput(success=False, response_time_ms=elapsed, error=f"Expected {expected_status}, got {resp.status_code}")
            return CheckOutput(success=True, response_time_ms=elapsed, output=output)
        except requests.exceptions.Timeout:
            elapsed = (time.time() - start) * 1000
            return CheckOutput(success=False, response_time_ms=elapsed, error="HTTP timeout")
        except requests.exceptions.RequestException as e:
            elapsed = (time.time() - start) * 1000
            return CheckOutput(success=False, response_time_ms=elapsed, error=str(e))


class DNSCheck(BaseCheck):
    """DNS resolution check."""

    def execute(self, ip: str, config: dict, timeout: int) -> CheckOutput:
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
            return CheckOutput(success=True, response_time_ms=elapsed, output=f"{record_type} {query_name}: {', '.join(records)}")
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            return CheckOutput(success=False, response_time_ms=elapsed, error=str(e))


# Registry
CHECK_REGISTRY = {
    "icmp": ICMPCheck(),
    "tcp": TCPCheck(),
    "http": HTTPCheck(),
    "dns": DNSCheck(),
}


def run_check(check_type: str, ip: str, config: dict, timeout: int = 10) -> CheckOutput:
    """Run a check by type. Returns CheckOutput."""
    executor = CHECK_REGISTRY.get(check_type)
    if not executor:
        return CheckOutput(success=False, error=f"Unknown check type: {check_type}")
    return executor.execute(ip, config, timeout)
