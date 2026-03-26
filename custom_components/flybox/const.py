DOMAIN = "flybox"
DEFAULT_HOST = "192.168.2.1"
DEFAULT_SCAN_INTERVAL = 30

ENDPOINT = "/goform/get_mgdb_params"

DEVICE_KEYS = [
    "device_uptime",
    "rt_wwan_conn_info",
    "mnet_sysmode",
    "mnet_sig_level",
    "device_battery_charge_status",
    "device_battery_level",
    "device_battery_level_percent",
    "mnet_sim_status",
    "mnet_ca_status",
    "statistics_data_used_r",
    "statistics_used_tx_r",
    "statistics_data_used",
    "statistics_used_tx",
    "dialup_dataswitch",
    "dialup_roamswitch",
    "mnet_roam_status",
    "cm_display_type",
    "mnet_operator_name",
    "statistics_current_bytes",
    "statistics_mgmt_switch",
    "statistics_mgmt_switch_r",
    "statistics_threshold_percent",
    "statistics_threshold_percent_r",
    "statistics_data_limit",
    "statistics_data_limit_r",
    "statistics_data_limit_unit",
    "statistics_data_limit_unit_r",
    "statistics_used_overtake",
    "statistics_used_overtake_r",
]

WIFI_KEYS = [
    "wifi_ssid_0",
    "wifi_ssid_1",
    "wifi_ssid_2",
    "xmg_wifi_psk_0",
    "xmg_wifi_psk_1",
    "xmg_wifi_psk_2",
    "wifi_state_0",
    "wifi_state_1",
    "wifi_state_2",
    "wifi_broadcast_ssid_0",
    "wifi_broadcast_ssid_1",
    "wifi_broadcast_ssid_2",
    "wifi_security_0",
    "wifi_security_1",
    "wifi_security_2",
    "wifi_client_0",
    "wifi_client_1",
    "wifi_client_2",
    "wifi_bandsteer_enable_state",
]
