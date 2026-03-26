from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfInformation,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import FlyboxCoordinator
from .entity import FlyboxEntity


def _bytes_to_gb(raw: str | None) -> float | None:
    try:
        return round(int(raw) / (1024**3), 3)
    except (ValueError, TypeError):
        return None


def _safe_int(raw: str | None) -> int | None:
    try:
        return int(raw)
    except (ValueError, TypeError):
        return None


def _connection_status(data: dict) -> str | None:
    conn_info = data.get("rt_wwan_conn_info", "")
    parts = conn_info.split(",")
    return parts[0] if parts else None


@dataclass(frozen=True, kw_only=True)
class FlyboxSensorEntityDescription(SensorEntityDescription):
    value_fn: Callable[[dict], Any]


SENSOR_DESCRIPTIONS: tuple[FlyboxSensorEntityDescription, ...] = (
    # --- Network ---
    FlyboxSensorEntityDescription(
        key="mnet_operator_name",
        translation_key="operator_name",
        icon="mdi:office-building-marker",
        value_fn=lambda d: d.get("mnet_operator_name"),
    ),
    FlyboxSensorEntityDescription(
        key="mnet_sysmode",
        translation_key="network_mode",
        icon="mdi:network",
        value_fn=lambda d: d.get("mnet_sysmode"),
    ),
    FlyboxSensorEntityDescription(
        key="cm_display_type",
        translation_key="connection_type",
        icon="mdi:signal-4g",
        value_fn=lambda d: d.get("cm_display_type"),
    ),
    FlyboxSensorEntityDescription(
        key="mnet_sig_level",
        translation_key="signal_level",
        icon="mdi:signal",
        value_fn=lambda d: d.get("mnet_sig_level"),
    ),
    FlyboxSensorEntityDescription(
        key="connection_status",
        translation_key="connection_status",
        icon="mdi:wan",
        value_fn=_connection_status,
    ),
    FlyboxSensorEntityDescription(
        key="mnet_sim_status",
        translation_key="sim_status",
        icon="mdi:sim",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("mnet_sim_status"),
    ),
    FlyboxSensorEntityDescription(
        key="mnet_ca_status",
        translation_key="carrier_aggregation",
        icon="mdi:layers-triple",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("mnet_ca_status"),
    ),
    # --- Uptime ---
    FlyboxSensorEntityDescription(
        key="device_uptime",
        translation_key="uptime",
        icon="mdi:timer-outline",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: _safe_int(d.get("device_uptime")),
    ),
    # --- Data usage ---
    FlyboxSensorEntityDescription(
        key="statistics_data_used",
        translation_key="data_downloaded",
        icon="mdi:download-network",
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: _bytes_to_gb(d.get("statistics_data_used")),
    ),
    FlyboxSensorEntityDescription(
        key="statistics_used_tx",
        translation_key="data_uploaded",
        icon="mdi:upload-network",
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: _bytes_to_gb(d.get("statistics_used_tx")),
    ),
    FlyboxSensorEntityDescription(
        key="statistics_data_used_r",
        translation_key="data_downloaded_roaming",
        icon="mdi:download-network",
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: _bytes_to_gb(d.get("statistics_data_used_r")),
    ),
    FlyboxSensorEntityDescription(
        key="statistics_used_tx_r",
        translation_key="data_uploaded_roaming",
        icon="mdi:upload-network",
        native_unit_of_measurement=UnitOfInformation.GIGABYTES,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: _bytes_to_gb(d.get("statistics_used_tx_r")),
    ),
    # --- Battery ---
    FlyboxSensorEntityDescription(
        key="device_battery_level_percent",
        translation_key="battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _safe_int(d.get("device_battery_level_percent")),
    ),
    FlyboxSensorEntityDescription(
        key="device_battery_charge_status",
        translation_key="battery_charge_status",
        icon="mdi:battery-charging",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("device_battery_charge_status"),
    ),
    # --- WiFi clients ---
    FlyboxSensorEntityDescription(
        key="wifi_client_0",
        translation_key="wifi_clients_24ghz",
        icon="mdi:wifi",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _safe_int(d.get("wifi_client_0")),
    ),
    FlyboxSensorEntityDescription(
        key="wifi_client_1",
        translation_key="wifi_clients_guest",
        icon="mdi:wifi-star",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _safe_int(d.get("wifi_client_1")),
    ),
    FlyboxSensorEntityDescription(
        key="wifi_client_2",
        translation_key="wifi_clients_5ghz",
        icon="mdi:wifi",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _safe_int(d.get("wifi_client_2")),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: FlyboxCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        FlyboxSensor(coordinator, description)
        for description in SENSOR_DESCRIPTIONS
    )


class FlyboxSensor(FlyboxEntity, SensorEntity):
    """A sensor entity for the Flybox integration."""

    entity_description: FlyboxSensorEntityDescription

    def __init__(
        self,
        coordinator: FlyboxCoordinator,
        description: FlyboxSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.data or {})
