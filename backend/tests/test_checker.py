"""Monitoring engine tests: HTTP is mocked with httpx.MockTransport (no internet)."""
import httpx
import pytest

from app.monitoring.checker import is_expected, perform_check


def mock_client(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=False)


async def run(handler, url="https://api.example.com/health", expected=None, timeout=5, method="GET"):
    async with mock_client(handler) as c:
        return await perform_check(method, url, timeout, expected, c)


def test_is_expected():
    assert is_expected(200, []) and is_expected(204, None) and not is_expected(301, [])
    assert is_expected(404, [404]) and not is_expected(200, [404])


async def test_up_on_2xx():
    out = await run(lambda r: httpx.Response(200))
    assert out.status == "UP" and out.http_status_code == 200
    assert out.response_time_ms is not None and out.error_message is None


async def test_down_on_500():
    out = await run(lambda r: httpx.Response(500))
    assert out.status == "DOWN" and out.http_status_code == 500
    assert "500" in out.error_message


async def test_expected_codes_make_404_up():
    out = await run(lambda r: httpx.Response(404), expected=[404])
    assert out.status == "UP"


async def test_timeout_is_down():
    def handler(request):
        raise httpx.ReadTimeout("slow", request=request)
    out = await run(handler)
    assert out.status == "DOWN" and "Timeout" in out.error_message and out.http_status_code is None


async def test_connection_error_is_down():
    def handler(request):
        raise httpx.ConnectError("refused", request=request)
    out = await run(handler)
    assert out.status == "DOWN" and "Connection error" in out.error_message


async def test_unexpected_exception_never_raises():
    def handler(request):
        raise RuntimeError("boom")
    out = await run(handler)
    assert out.status == "DOWN" and "Unexpected" in out.error_message


async def test_connects_to_validated_ip_with_host_header():
    seen = {}
    def handler(request):
        seen["host"], seen["url_host"] = request.headers["host"], request.url.host
        return httpx.Response(200)
    await run(handler)
    assert seen == {"host": "api.example.com", "url_host": "93.184.216.34"}


async def test_follows_redirect_and_revalidates_each_hop():
    def handler(request):
        if request.headers["host"] == "api.example.com":
            return httpx.Response(302, headers={"location": "https://other.example.com/ok"})
        return httpx.Response(200)
    out = await run(handler)
    assert out.status == "UP"


async def test_redirect_to_private_network_is_blocked():
    def handler(request):
        return httpx.Response(302, headers={"location": "http://169.254.169.254/latest/meta-data/"})
    out = await run(handler)
    assert out.status == "DOWN" and out.error_message.startswith("Blocked")


async def test_redirect_loop_is_stopped():
    def handler(request):
        return httpx.Response(302, headers={"location": "https://api.example.com/again"})
    out = await run(handler)
    assert out.status == "DOWN" and "redirects" in out.error_message


async def test_private_target_never_requested():
    called = []
    def handler(request):
        called.append(1)
        return httpx.Response(200)
    out = await run(handler, url="https://private.example.com/")
    assert out.status == "DOWN" and not called
