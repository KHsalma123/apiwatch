"""The check itself: one HTTP request, measured, with SSRF protection.

perform_check() NEVER raises: every failure becomes a DOWN outcome.
check_monitor() = perform_check() + saving the result/incidents (shared by worker and API).
"""
import asyncio
import time
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urljoin

import httpx

from app.core.config import get_settings
from app.security.ssrf import UnsafeURLError, assert_url_is_public
from app.services.common import utcnow
from app.services.incidents import process_result

REDIRECT_CODES = {301, 302, 303, 307, 308}
USER_AGENT = "APIWatch/1.0 (+uptime monitor)"


@dataclass
class CheckOutcome:
    status: str  # "UP" | "DOWN"
    http_status_code: int | None
    response_time_ms: int | None
    error_message: str | None
    checked_at: datetime


def is_expected(code: int, expected: list[int] | None) -> bool:
    """Default (no codes configured): any 2xx is UP."""
    if not expected:
        return 200 <= code <= 299
    return code in expected


async def _request_once(client: httpx.AsyncClient, method: str, url: str, timeout: float):
    """One hop. Validates the URL, then connects to the validated IP (anti DNS-rebinding)."""
    scheme, host, _port, ips = await assert_url_is_public(url)
    parsed = httpx.URL(url)
    pinned = parsed.copy_with(host=ips[0])
    host_header = host if parsed.port is None else f"{host}:{parsed.port}"
    extensions = {"sni_hostname": host} if scheme == "https" else {}
    async with client.stream(
        method,
        pinned,
        headers={"Host": host_header, "User-Agent": USER_AGENT},
        extensions=extensions,
        timeout=timeout,
    ) as response:  # body is NOT downloaded: only status and headers matter
        return response.status_code, response.headers.get("location")


async def perform_check(
    method: str,
    url: str,
    timeout_seconds: int,
    expected_status_codes: list[int] | None,
    client: httpx.AsyncClient,
) -> CheckOutcome:
    max_redirects = get_settings().max_redirects
    started = time.perf_counter()
    code: int | None = None
    error: str | None = None
    try:
        async with asyncio.timeout(timeout_seconds):
            current_url, current_method = url, method
            for _ in range(max_redirects + 1):
                code, location = await _request_once(client, current_method, current_url, timeout_seconds)
                if code in REDIRECT_CODES and location:
                    current_url = urljoin(current_url, location)
                    if code == 303:
                        current_method = "GET"
                    code = None
                    continue
                break
            else:
                error = f"Too many redirects (more than {max_redirects})"
    except UnsafeURLError as e:
        code, error = None, f"Blocked: {e}"
    except (TimeoutError, httpx.TimeoutException):
        code, error = None, f"Timeout after {timeout_seconds}s"
    except httpx.ConnectError as e:
        code, error = None, f"Connection error: {str(e)[:150] or 'could not connect'}"
    except httpx.HTTPError as e:
        code, error = None, f"HTTP error: {type(e).__name__}: {str(e)[:150]}"
    except Exception as e:  # a bug must never kill the worker
        code, error = None, f"Unexpected error: {type(e).__name__}"

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    now = utcnow()
    if error is not None:
        return CheckOutcome("DOWN", None, None, error, now)
    if is_expected(code, expected_status_codes):
        return CheckOutcome("UP", code, elapsed_ms, None, now)
    return CheckOutcome("DOWN", code, elapsed_ms, f"Unexpected HTTP status {code}", now)


def new_client() -> httpx.AsyncClient:
    # follow_redirects=False: we follow redirects ourselves so each hop is validated.
    return httpx.AsyncClient(follow_redirects=False, trust_env=False)


async def check_monitor(db, monitor: dict, client: httpx.AsyncClient) -> CheckOutcome:
    outcome = await perform_check(
        monitor["method"],
        monitor["url"],
        monitor["timeout_seconds"],
        monitor.get("expected_status_codes"),
        client,
    )
    await process_result(db, monitor, outcome)
    return outcome
