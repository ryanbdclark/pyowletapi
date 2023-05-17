PROPERTIES = {
    bool: {
        "high_oxygen_alert": "HIGH_OX_ALRT",
        "low_battery_alert": "LOW_BATT_ALRT",
        "low_heart_rate_alert": "LOW_HR_ALRT",
        "low_oxygen_alert": "LOW_OX_ALRT",
        "ppg_log_file": "PPG_LOG_FILE",
        "firmware_update_available": "FW_UPDATE_STATUS",
        "lost_power_alert": "LOST_POWER_ALRT",
        "sock_disconnected": "SOCK_DISCON_ALRT",
        "sock_off": "SOCK_OFF",
    }
}

VITALS = {
    # Additional attributes not implemented
    # Current alerts mask - "alrt" int
    # Firmware update status - "ota" int
    # Sock readings flag - "srf" int
    # Soft brick status - "sb" int
    # Movement bucket - "mvb" int
    # Wellness alert - "onm" int
    # Hardware version - "hw" String
    # Monitoring start time - "mst" int
    # Base station battery status - "bsb" int
    float: {
        "oxygen_saturation": "ox",
        "heart_rate": "hr",
        "battery_percentage": "bat",
        "battery_minutes": "btt",
        "signal_strength": "rsi",
        "oxygen_10_av": "oxta",
    },
    bool: {
        "moving": "mv",
        "alert_paused_status": "aps",
        "charging": "chg",
        "base_station_on": "bso",
    },
    int: {"sock_connection": "sc", "skin_temperature": "st", "sleep_state": "ss"},
    "other": {"last_updated": "data_updated_at"},
}

REGION_INFO = {
    "world": {
        "url_mini": "https://ayla-sso.owletdata.com/mini/",
        "url_signin": "https://user-field-1a2039d9.aylanetworks.com/api/v1/token_sign_in",
        "url_signin": "https://user-field-1a2039d9.aylanetworks.com/users/refresh_token.json",
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
