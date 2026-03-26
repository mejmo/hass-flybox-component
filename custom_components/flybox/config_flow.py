from __future__ import annotations

import logging
import random

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, DEFAULT_HOST, DEFAULT_SCAN_INTERVAL, ENDPOINT

_LOGGER = logging.getLogger(__name__)

CSRF_ENDPOINT = "/goform/x_csrf_token"

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("host", default=DEFAULT_HOST): str,
        vol.Optional("scan_interval", default=DEFAULT_SCAN_INTERVAL): vol.All(
            int, vol.Range(min=10, max=300)
        ),
    }
)


async def validate_connection(hass: HomeAssistant, host: str) -> str:
    """Validate router connectivity and return a title string."""
    csrf_url = f"http://{host}{CSRF_ENDPOINT}?v={random.random()}"
    data_url = f"http://{host}{ENDPOINT}"
    referer = f"http://{host}/home/index.html"
    timeout = aiohttp.ClientTimeout(total=10)

    try:
        async with aiohttp.ClientSession(
            timeout=timeout,
            cookie_jar=aiohttp.CookieJar(unsafe=True),
        ) as session:
            # Step 1: obtain CSRF token
            async with session.get(
                csrf_url,
                headers={
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": referer,
                },
            ) as csrf_resp:
                csrf_resp.raise_for_status()
                csrf_token = csrf_resp.headers.get("X-Csrf-Token")
                if not csrf_token:
                    raise CannotConnect("No CSRF token in response")

            # Step 2: fetch operator name
            async with session.post(
                data_url,
                json={"keys": ["mnet_operator_name"]},
                headers={
                    "Content-Type": "application/json",
                    "X-Requested-With": "XMLHttpRequest",
                    "X-Csrf-Token": csrf_token,
                    "Referer": referer,
                    "Origin": f"http://{host}",
                },
            ) as resp:
                resp.raise_for_status()
                result = await resp.json(content_type=None)
    except aiohttp.ClientError as err:
        raise CannotConnect(f"Connection failed: {err}") from err

    if result.get("retcode") != 0:
        raise CannotConnect("Router returned a non-zero retcode")

    operator = result.get("data", {}).get("mnet_operator_name") or "Flybox"
    return f"{operator} Flybox"


class FlyboxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Orange Flybox."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                title = await validate_connection(self.hass, user_input["host"])
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during Flybox config flow")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(user_input["host"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    pass
