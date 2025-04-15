PROPERTIES: dict[type, dict[str, str]] = {
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

VITALS_3: dict[type, dict[str, str]] = {
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

VITALS_3_OTHER: dict[str, str] = {
    "last_updated": "data_updated_at",
}

VITALS_2: dict[type, dict[str, str]] = {
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
