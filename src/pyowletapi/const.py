from typing import Literal, TypedDict

PropertyKey = Literal[
    "high_oxygen_alert",
    "low_battery_alert",
    "low_heart_rate_alert",
    "high_heart_rate_alert",
    "low_oxygen_alert",
    "ppg_log_file",
    "firmware_update_available",
    "lost_power_alert",
    "sock_disconnected",
    "sock_off",
    "oxygen_saturation",
    "heart_rate",
    "battery_percentage",
    "battery_minutes",
    "signal_strength",
    "oxygen_10_av",
    "base_station_on",
    "sock_connection",
    "skin_temperature",
    "sleep_state",
    "movement",
    "alert_paused_status",
    "charging",
    "alerts_mask",
    "update_status",
    "readings_flag",
    "brick_status",
    "movement_bucket",
    "wellness_alert",
    "monitoring_start_time",
    "base_battery_status",
    "hardware_version",
    "last_updated",
    "critical_battery_alert",
    "critical_oxygen_alert",
]


class Properties(TypedDict, total=False):
    critical_battery_alert: bool
    critical_oxygen_alert: bool
    high_oxygen_alert: bool
    low_battery_alert: bool
    low_heart_rate_alert: bool
    high_heart_rate_alert: bool
    low_oxygen_alert: bool
    ppg_log_file: bool
    firmware_update_available: bool
    lost_power_alert: bool
    sock_disconnected: bool
    sock_off: bool
    oxygen_saturation: float
    heart_rate: float
    battery_percentage: float
    battery_minutes: float
    signal_strength: float
    oxygen_10_av: float
    base_station_on: int
    sock_connection: int
    skin_temperature: int
    sleep_state: int
    movement: int
    alert_paused_status: int
    charging: int
    alerts_mask: int
    update_status: int
    readings_flag: int
    brick_status: int
    movement_bucket: int
    wellness_alert: int
    monitoring_start_time: int
    base_battery_status: int
    hardware_version: str
    last_updated: str


PROPERTIES: dict[type, dict[PropertyKey, str]] = {
    bool: {
        "high_oxygen_alert": "HIGH_OX_ALRT",
        "low_battery_alert": "LOW_BATT_ALRT",
        "low_heart_rate_alert": "LOW_HR_ALRT",
        "high_heart_rate_alert": "HIGH_HR_ALRT",
        "low_oxygen_alert": "LOW_OX_ALRT",
        "ppg_log_file": "PPG_LOG_FILE",
        "firmware_update_available": "FW_UPDATE_STATUS",
        "lost_power_alert": "LOST_POWER_ALRT",
        "sock_disconnected": "SOCK_DISCON_ALRT",
        "sock_off": "SOCK_OFF",
        "critical_battery_alert": "CRIT_BATT_ALRT",
        "critical_oxygen_alert": "CRIT_OX_ALRT",
    },
}

VITALS_3: dict[type, dict[PropertyKey, str]] = {
    float: {
        "oxygen_saturation": "ox",
        "heart_rate": "hr",
        "battery_percentage": "bat",
        "battery_minutes": "btt",
        "signal_strength": "rsi",
        "oxygen_10_av": "oxta",
    },
    bool: {
        "base_station_on": "bso",
    },
    int: {
        "sock_connection": "sc",
        "skin_temperature": "st",
        "sleep_state": "ss",
        "movement": "mv",
        "alert_paused_status": "aps",
        "charging": "chg",
        "alerts_mask": "alrt",
        "update_status": "ota",
        "readings_flag": "srf",
        "brick_status": "sb",
        "movement_bucket": "mvb",
        "wellness_alert": "onm",
        "monitoring_start_time": "mst",
        "base_battery_status": "bsb",
    },
    str: {
        "hardware_version": "hw",
    },
}

VITALS_3_OTHER: dict[PropertyKey, str] = {
    "last_updated": "data_updated_at",
}

VITALS_2: dict[type, dict[PropertyKey, str]] = {
    float: {
        "signal_strength": "BLE_RSSI",
    },
    bool: {
        "base_station_on": "BASE_STATION_ON",
        "sock_connection": "SOCK_CONNECTION",
    },
    int: {
        "oxygen_saturation": "OXYGEN_LEVEL",
        "heart_rate": "HEART_RATE",
        "battery_percentage": "BATT_LEVEL",
        "movement": "MOVEMENT",
        "charging": "CHARGE_STATUS",
        "update_status": "OTA_STATUS",
    },
    str: {
        "hardware_version": "oem_sock_version",
    },
}

REGION_INFO: dict[str, dict[str, str]] = {
    "world": {
        "url_mini": "https://ayla-sso.owletdata.com/mini/",
        "url_signin": "https://user-field-1a2039d9.aylanetworks.com/api/v1/token_sign_in",
        "url_refresh": "https://user-field-1a2039d9.aylanetworks.com/users/refresh_token.json",
        "url_base": "https://ads-field-1a2039d9.aylanetworks.com/apiv1",
        "apiKey": "AIzaSyCsDZ8kWxQuLJAMVnmEhEkayH1TSxKXfGA",
        "app_id": "sso-prod-3g-id",
        "app_secret": "sso-prod-UEjtnPCtFfjdwIwxqnC0OipxRFU",
    },
    "europe": {
        "url_mini": "https://ayla-sso.eu.owletdata.com/mini/",
        "url_signin": "https://user-field-eu-1a2039d9.aylanetworks.com/api/v1/token_sign_in",
        "url_refresh": "https://user-field-eu-1a2039d9.aylanetworks.com/users/refresh_token.json",
        "url_base": "https://ads-field-eu-1a2039d9.aylanetworks.com/apiv1",
        "apiKey": "AIzaSyDm6EhV70wudwN3iOSq3vTjtsdGjdFLuuM",
        "app_id": "OwletCare-Android-EU-fw-id",
        "app_secret": "OwletCare-Android-EU-JKupMPBoj_Npce_9a95Pc8Qo0Mw",
    },
}
