import logging
from logging import Logger
import json
import datetime

logger: Logger = logging.getLogger(__package__)

CHARGING_STATUSES = ['NOT CHARGING', 'CHARGING', 'CHARGED']


class Sock:
    def __init__(self, api, data):
        self._name = data['product_name']
        self._model = data['model']
        self._serial = data['dsn']
        self._oem_model = data['oem_model']
        self._sw_version = data['sw_version']
        self._mac = data['mac']
        self._lan_ip = data['lan_ip']
        self._connection_status = data['connection_status']
        self._device_type = data['device_type']
        self._manuf_model = data['manuf_model']

        self._api = api

        self.raw_properties = {}
        self.properties = {}

    @property
    def name(self):
        return self._name

    @property
    def model(self):
        return self._model

    @property
    def serial(self):
        return self._serial

    @property
    def oem_model(self):
        return self._oem_model

    @property
    def sw_version(self):
        return self._sw_version

    @property
    def mac(self):
        return self._mac

    @property
    def lan_ip(self):
        return self._lan_ip

    @property
    def connection_status(self):
        return self._connection_status

    @property
    def device_type(self):
        return self._device_type

    @property
    def manuf_model(self):
        return self._manuf_model

    def get_property(self, property):
        return self.properties[property]

    def get_properties(self):
        return self.properties

    async def normalise_properties(self, raw_properties):
        properties = {}
        properties['app_active'] = bool(raw_properties["APP_ACTIVE"]["value"])

        properties['high_heart_rate_alert'] = bool(
            raw_properties["HIGH_HR_ALRT"]["value"])
        properties['high_oxygen_alert'] = bool(
            raw_properties["HIGH_OX_ALRT"]["value"])
        properties['low_battery_alert'] = bool(
            raw_properties["LOW_BATT_ALRT"]["value"])
        properties['low_heart_rate_alert'] = bool(
            raw_properties["LOW_HR_ALRT"]["value"])
        properties['low_oxygen_alert'] = bool(
            raw_properties["LOW_OX_ALRT"]["value"])
        properties['ppg_log_file'] = bool(
            raw_properties["PPG_LOG_FILE"]["value"])

        vitals = json.loads(raw_properties["REAL_TIME_VITALS"]["value"])
        properties['oxygen_saturation'] = float(vitals["ox"])
        properties['heart_rate'] = float(vitals["hr"])
        properties['moving'] = bool(vitals["mv"])
        properties['base_station_on'] = True if bool(
            vitals['bso']) or bool(vitals['chg']) else False
        properties['battery_percentage'] = float(vitals["bat"])
        properties['battery_seconds'] = float(vitals["btt"])
        properties['charging'] = CHARGING_STATUSES[int(vitals['chg'])]
        properties['signal_strength'] = float(vitals['rsi'])
        properties['last_updated'] = datetime.datetime.strptime(
            raw_properties["REAL_TIME_VITALS"]["data_updated_at"], '%Y-%m-%dT%H:%M:%SZ').strftime("%Y/%m/%d %H:%M:%S")

        return properties

    async def update_properties(self):
        logging.info(f"Updating properties for device {self.serial}")
        self.raw_properties = await self._api.get_properties(self.serial)
        self.properties = await self.normalise_properties(self.raw_properties)

        return (self.raw_properties, self.properties)
