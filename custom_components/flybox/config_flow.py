from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .api import FlyboxApiClient, FlyboxApiError
from .const import DOMAIN, DEFAULT_HOST, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

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
    client = FlyboxApiClient(host)
    try:
        await client.async_refresh_csrf_token()
        data = await client.async_fetch(["mnet_operator_name"])
    except FlyboxApiError as err:
        raise CannotConnect(str(err)) from err
    except Exception as err:
        raise CannotConnect(f"Connection failed: {err}") from err
    finally:
        await client.async_close()

    operator = data.get("mnet_operator_name") or "Flybox"
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
