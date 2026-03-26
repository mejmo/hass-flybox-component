from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FlyboxCoordinator


class FlyboxEntity(CoordinatorEntity[FlyboxCoordinator]):
    """Base entity for all Flybox entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: FlyboxCoordinator, unique_id_suffix: str) -> None:
        super().__init__(coordinator)
        mac = coordinator.get_device_mac()
        device_id = mac.replace(":", "").lower() if mac else coordinator.host.replace(".", "_")
        self._attr_unique_id = f"{device_id}_{unique_id_suffix}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name="Orange Flybox",
            manufacturer="Orange",
            model="Flybox",
            configuration_url=f"http://{coordinator.host}",
        )
