from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FlyboxApiClient, FlyboxApiError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class FlyboxCoordinator(DataUpdateCoordinator[dict]):
    """Coordinator that polls the Flybox router via FlyboxApiClient."""

    def __init__(self, hass: HomeAssistant, host: str, scan_interval: int) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.host = host
        self._client = FlyboxApiClient(host)

    async def _async_update_data(self) -> dict:
        try:
            return await self._client.async_get_data()
        except FlyboxApiError as err:
            raise UpdateFailed(str(err)) from err
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Flybox at {self.host}: {err}") from err

    async def async_shutdown(self) -> None:
        await self._client.async_close()
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
