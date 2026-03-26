from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, ENDPOINT, DEVICE_KEYS, WIFI_KEYS

_LOGGER = logging.getLogger(__name__)


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

    async def _async_update_data(self) -> dict:
        timeout = aiohttp.ClientTimeout(total=10)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                device_data = await self._fetch(session, DEVICE_KEYS)
                wifi_data = await self._fetch(session, WIFI_KEYS)
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with Flybox at {self.host}: {err}") from err

        return {**device_data, **wifi_data}

    async def _fetch(self, session: aiohttp.ClientSession, keys: list[str]) -> dict:
        async with session.post(self._url, json={"keys": keys}) as resp:
            resp.raise_for_status()
            result = await resp.json(content_type=None)
        if result.get("retcode") != 0:
            raise UpdateFailed(f"Flybox API returned error retcode: {result.get('retcode')}")
        return result.get("data", {})

    def get_device_mac(self) -> str | None:
        """Parse MAC address from rt_wwan_conn_info field."""
        if not self.data:
            return None
        conn_info = self.data.get("rt_wwan_conn_info", "")
        parts = conn_info.split(",")
        if len(parts) > 2 and parts[2]:
            return parts[2].upper()
        return None
