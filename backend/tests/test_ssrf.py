import pytest

from app.security import ssrf
from app.security.ssrf import UnsafeURLError, assert_url_is_public, is_forbidden_ip, validate_url_syntax


@pytest.mark.parametrize("ip", [
    "127.0.0.1", "10.1.2.3", "172.16.0.1", "192.168.1.1", "169.254.169.254", "0.0.0.0",
    "100.64.0.1", "224.0.0.1", "::1", "fe80::1", "fc00::1", "::ffff:127.0.0.1",
])
def test_forbidden_ips(ip):
    assert is_forbidden_ip(ip)


@pytest.mark.parametrize("ip", ["8.8.8.8", "93.184.216.34", "2606:4700:4700::1111"])
def test_public_ips(ip):
    assert not is_forbidden_ip(ip)


@pytest.mark.parametrize("url", [
    "ftp://example.com", "file:///etc/passwd", "gopher://example.com", "javascript:alert(1)",
    "http://user:pw@example.com", "http://localhost/", "http://foo.localhost/",
    "http://metadata.google.internal/", "http://example.com:22/", "http:///nohost", "not a url",
])
def test_syntax_rejected(url):
    with pytest.raises(UnsafeURLError):
        validate_url_syntax(url)


def test_syntax_ok():
    assert validate_url_syntax("https://api.example.com/x?y=1") == ("https", "api.example.com", 443)
    assert validate_url_syntax("http://example.com:8080")[2] == 8080


@pytest.mark.parametrize("url", [
    "http://127.0.0.1/", "http://169.254.169.254/latest/meta-data/", "http://[::1]/",
    "http://10.0.0.1/", "http://2130706433/",  # decimal form of 127.0.0.1 is an IP literal after parsing? see below
    "https://private.example.com/",  # name resolving to a private IP (fake_dns)
])
async def test_assert_public_rejects(url, monkeypatch):
    if "2130706433" in url:
        async def _r(host, port):
            return ["127.0.0.1"]  # what getaddrinfo returns for this notation
        monkeypatch.setattr(ssrf, "resolve_host", _r)
    with pytest.raises(UnsafeURLError):
        await assert_url_is_public(url)


async def test_assert_public_accepts():
    scheme, host, port, ips = await assert_url_is_public("https://api.example.com/")
    assert (scheme, host, port, ips) == ("https", "api.example.com", 443, ["93.184.216.34"])


async def test_mixed_dns_answer_is_rejected(monkeypatch):
    async def _r(host, port):
        return ["93.184.216.34", "10.0.0.1"]  # one private IP is enough to reject
    monkeypatch.setattr(ssrf, "resolve_host", _r)
    with pytest.raises(UnsafeURLError):
        await assert_url_is_public("https://api.example.com/")
