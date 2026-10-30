"""SSRF protection.

SSRF = Server-Side Request Forgery: tricking OUR server into calling internal
addresses (localhost, a private network, the cloud metadata service...).

Defence layers implemented here:
  1. validate_url_syntax(): http/https only, no credentials, allowed ports only,
     blocked hostnames (localhost, *.internal, ...).
  2. resolve_host(): WE resolve DNS (so the check cannot be bypassed by odd notations
     such as 2130706433 or 0x7f.1, which resolve to 127.0.0.1).
  3. is_forbidden_ip(): EVERY resolved IP must be public.
  4. The checker connects to the validated IP (no second DNS lookup => no DNS rebinding)
     and re-validates every redirect hop.
"""
import asyncio
import ipaddress
import socket
from urllib.parse import urlsplit

from app.core.config import get_settings

BLOCKED_HOSTNAMES = {"localhost", "metadata.google.internal", "metadata"}
BLOCKED_SUFFIXES = (".localhost", ".local", ".internal", ".lan", ".home", ".corp", ".intranet")
MAX_URL_LENGTH = 2048


class UnsafeURLError(ValueError):
    """Raised when a URL is not allowed to be monitored."""


def is_forbidden_ip(ip: str) -> bool:
    addr = ipaddress.ip_address(ip)
    if addr.version == 6 and addr.ipv4_mapped is not None:  # ::ffff:127.0.0.1
        addr = addr.ipv4_mapped
    return (
        not addr.is_global
        or addr.is_loopback
        or addr.is_link_local  # 169.254.0.0/16 includes cloud metadata 169.254.169.254
        or addr.is_multicast
        or addr.is_reserved
        or addr.is_unspecified
    )


def validate_url_syntax(url: str) -> tuple[str, str, int]:
    """Return (scheme, hostname, port) or raise UnsafeURLError."""
    if len(url) > MAX_URL_LENGTH:
        raise UnsafeURLError("URL is too long")
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError:
        raise UnsafeURLError("URL is malformed")
    if parts.scheme not in ("http", "https"):
        raise UnsafeURLError("Only http and https URLs are allowed")
    if not parts.hostname:
        raise UnsafeURLError("URL must contain a host name")
    if parts.username or parts.password:
        raise UnsafeURLError("URLs must not contain credentials")
    host = parts.hostname.lower().rstrip(".")
    if host in BLOCKED_HOSTNAMES or host.endswith(BLOCKED_SUFFIXES):
        raise UnsafeURLError("This host name is not allowed")
    port = port or (443 if parts.scheme == "https" else 80)
    if port not in get_settings().allowed_port_set:
        raise UnsafeURLError(f"Port {port} is not allowed")
    return parts.scheme, host, port


async def resolve_host(host: str, port: int) -> list[str]:
    """Resolve a host name to IP strings. IP literals are returned unchanged.

    This is the only function that performs DNS, so tests can replace it.
    """
    try:
        ipaddress.ip_address(host)
        return [host]
    except ValueError:
        pass
    loop = asyncio.get_running_loop()
    try:
        infos = await loop.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror:
        raise UnsafeURLError("Host name could not be resolved")
    return list(dict.fromkeys(info[4][0] for info in infos))


async def assert_url_is_public(url: str) -> tuple[str, str, int, list[str]]:
    """Full validation. Returns (scheme, host, port, public_ips)."""
    scheme, host, port = validate_url_syntax(url)
    ips = await resolve_host(host, port)
    if not ips:
        raise UnsafeURLError("Host name could not be resolved")
    for ip in ips:
        if is_forbidden_ip(ip):
            raise UnsafeURLError("This URL points to a private or reserved network address")
    return scheme, host, port, ips
