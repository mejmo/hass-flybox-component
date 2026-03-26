from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import FlyboxCoordinator
from .entity import FlyboxEntity


@dataclass(frozen=True, kw_only=True)
class FlyboxBinarySensorEntityDescription(BinarySensorEntityDescription):
    value_fn: Callable[[dict], bool | None]


BINARY_SENSOR_DESCRIPTIONS: tuple[FlyboxBinarySensorEntityDescription, ...] = (
    FlyboxBinarySensorEntityDescription(
        key="internet_connected",
        translation_key="internet_connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_fn=lambda d: d.get("rt_wwan_conn_info", "").split(",")[0] == "connected",
    ),
    FlyboxBinarySensorEntityDescription(
        key="dialup_dataswitch",
        translation_key="mobile_data",
        icon="mdi:signal-cellular-3",
        value_fn=lambda d: d.get("dialup_dataswitch") == "on",
    ),
    FlyboxBinarySensorEntityDescription(
        key="mnet_roam_status",
        translation_key="roaming",
        icon="mdi:earth",
        value_fn=lambda d: d.get("mnet_roam_status") == "on",
    ),
    FlyboxBinarySensorEntityDescription(
        key="wifi_state_0",
        translation_key="wifi_24ghz",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_fn=lambda d: d.get("wifi_state_0") != "ap_disable",
    ),
    FlyboxBinarySensorEntityDescription(
        key="wifi_state_1",
        translation_key="wifi_guest",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_fn=lambda d: d.get("wifi_state_1") != "ap_disable",
    ),
    FlyboxBinarySensorEntityDescription(
        key="wifi_state_2",
        translation_key="wifi_5ghz",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_fn=lambda d: d.get("wifi_state_2") != "ap_disable",
    ),
    FlyboxBinarySensorEntityDescription(
        key="wifi_bandsteer_enable_state",
        translation_key="band_steering",
        icon="mdi:wifi-arrow-left-right",
        value_fn=lambda d: d.get("wifi_bandsteer_enable_state") == "bandsteer_enable",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: FlyboxCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        FlyboxBinarySensor(coordinator, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
    )


class FlyboxBinarySensor(FlyboxEntity, BinarySensorEntity):
    """A binary sensor entity for the Flybox integration."""

    entity_description: FlyboxBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: FlyboxCoordinator,
        description: FlyboxBinarySensorEntityDescription,
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.value_fn(self.coordinator.data or {})
