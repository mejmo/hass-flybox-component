from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, ENDPOINT, DEVICE_KEYS, WIFI_KEYS

_LOGGER = logging.getLogger(__name__)

LOGIN_ENDPOINT = "/goform/get_login_info"
REFERER = "http://{host}/home/index.html"


class FlyboxCoordinator(DataUpdateCoordinator[dict]):
    """Coordinator to fetch all Flybox data from both endpoints."""

    def __init__(self, hass: HomeAssistant, host: str, scan_interval: int) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.host = host
        self._url = f"http://{host}{ENDPOINT}"
        self._login_url = f"http://{host}{LOGIN_ENDPOINT}"
        self._referer = REFERER.format(host=host)
        self._csrf_token: str | None = None
        self._session: aiohttp.ClientSession | None = None

    def _make_headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": self._referer,
            "Origin": f"http://{self.host}",
        }
        if self._csrf_token:
            headers["X-Csrf-Token"] = self._csrf_token
        return headers

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=10)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def _refresh_csrf_token(self) -> None:
        """Fetch a fresh CSRF token from the login endpoint."""
        session = await self._ensure_session()
        try:
            async with session.post(
                self._login_url, headers=self._make_headers()
            ) as resp:
                resp.raise_for_status()
                token = resp.headers.get("X-Csrf-Token")
                if not token:
                    raise UpdateFailed("No X-Csrf-Token in login response headers")
                self._csrf_token = token
                _LOGGER.debug("Refreshed CSRF token from Flybox")
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Failed to fetch CSRF token: {err}") from err

    async def _async_update_data(self) -> dict:
        # Always refresh the token before each poll to keep the session alive
        await self._refresh_csrf_token()

        try:
            session = await self._ensure_session()
            device_data = await self._fetch(session, DEVICE_KEYS)
            wifi_data = await self._fetch(session, WIFI_KEYS)
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with Flybox at {self.host}: {err}") from err

        return {**device_data, **wifi_data}

    async def _fetch(self, session: aiohttp.ClientSession, keys: list[str]) -> dict:
        async with session.post(
            self._url, json={"keys": keys}, headers=self._make_headers()
        ) as resp:
            resp.raise_for_status()
            result = await resp.json(content_type=None)
        if result.get("retcode") != 0:
            raise UpdateFailed(f"Flybox API returned error retcode: {result.get('retcode')}")
        return result.get("data", {})

    async def async_shutdown(self) -> None:
        """Close the persistent session on unload."""
        if self._session and not self._session.closed:
            await self._session.close()
        await super().async_shutdown()

    def get_device_mac(self) -> str | None:
        """Parse MAC address from rt_wwan_conn_info field."""
        if not self.data:
            return None
        conn_info = self.data.get("rt_wwan_conn_info", "")
        parts = conn_info.split(",")
        if len(parts) > 2 and parts[2]:
            return parts[2].upper()
        return None
