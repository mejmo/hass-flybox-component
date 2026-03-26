from __future__ import annotations

import json
import logging
import random

import aiohttp

from .const import ENDPOINT, DEVICE_KEYS, WIFI_KEYS

_LOGGER = logging.getLogger(__name__)

CSRF_ENDPOINT = "/goform/x_csrf_token"


def _log_request(method: str, url: str, headers: dict, body: dict | None = None) -> None:
    msg = f">>> {method} {url}\nHeaders: {json.dumps(dict(headers), indent=2)}"
    if body is not None:
        msg += f"\nBody: {json.dumps(body, indent=2)}"
    _LOGGER.debug(msg)


def _log_response(status: int, headers: aiohttp.CIMultiDictProxy, body: dict | None = None) -> None:
    msg = f"<<< HTTP {status}\nHeaders: {json.dumps(dict(headers), indent=2)}"
    if body is not None:
        msg += f"\nBody: {json.dumps(body, indent=2)}"
    _LOGGER.debug(msg)


class FlyboxApiClient:
    """Low-level HTTP client for the Flybox router API. No HA dependencies."""

    def __init__(self, host: str) -> None:
        self.host = host
        self._url = f"http://{host}{ENDPOINT}"
        self._csrf_url = f"http://{host}{CSRF_ENDPOINT}"
        self._csrf_token: str | None = None
        self._session: aiohttp.ClientSession | None = None

    def _make_headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "X-Frame-Options": "SAMEORIGIN",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
        }
        if self._csrf_token:
            headers["X-Csrf-Token"] = self._csrf_token
        return headers

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10),
                cookie_jar=aiohttp.CookieJar(unsafe=True),
            )
        return self._session

    async def async_refresh_csrf_token(self) -> None:
        """Fetch a fresh CSRF token. Response also sets the session cookie."""
        session = await self._ensure_session()
        url = f"{self._csrf_url}?v={random.random()}"
        headers = self._make_headers()
        if _LOGGER.isEnabledFor(logging.DEBUG):
            _log_request("GET", url, headers)
        async with session.get(url, headers=headers) as resp:
            resp.raise_for_status()
            if _LOGGER.isEnabledFor(logging.DEBUG):
                _log_response(resp.status, resp.headers)
            token = resp.headers.get("X-Csrf-Token")
            if not token:
                raise FlyboxApiError("No X-Csrf-Token in response headers")
            self._csrf_token = token
            _LOGGER.debug("CSRF token acquired: %s", token)

    async def async_fetch(self, keys: list[str]) -> dict:
        """POST to get_mgdb_params and return the data dict."""
        session = await self._ensure_session()
        body = {"keys": keys}
        headers = self._make_headers()
        if _LOGGER.isEnabledFor(logging.DEBUG):
            _log_request("POST", self._url, headers, body)
        async with session.post(self._url, json=body, headers=headers) as resp:
            resp.raise_for_status()
            result = await resp.json(content_type=None)
            if _LOGGER.isEnabledFor(logging.DEBUG):
                _log_response(resp.status, resp.headers, result)
        if result.get("retcode") != 0:
            raise FlyboxApiError(f"Router returned error retcode: {result.get('retcode')}")
        return result.get("data", {})

    async def async_get_data(self) -> dict:
        """Refresh CSRF token then fetch all device and WiFi data."""
        await self.async_refresh_csrf_token()
        device_data = await self.async_fetch(DEVICE_KEYS)
        wifi_data = await self.async_fetch(WIFI_KEYS)
        return {**device_data, **wifi_data}

    async def async_close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()


class FlyboxApiError(Exception):
    """Raised when the Flybox API returns an unexpected response."""
