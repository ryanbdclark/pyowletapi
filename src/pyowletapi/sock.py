import logging
from logging import Logger
import json
import datetime
from .api import OwletAPI
from typing import Union

logger: Logger = logging.getLogger(__package__)

CHARGING_STATUSES = ["NOT CHARGING", "CHARGING", "CHARGED"]


class Sock:
    """
    Class representing a Owlet sock device

    Attributes
    ----------
    name : str
        The product name
    mode: str
        the product model
    serial : str
        the serial number of the device
    oem_model : str
        The oem model of the device
    sw_version : str
        The software version of the device
    mac : str
        The mac address the device
    lan_ip : str
        The current lan ip address of the device
    connection_status : str
        The current connection status of the device
    device_type : str
        The device type
    manuf_model : str
        The manunfacturer's model number
    api : OwletAPI
        The current OwletAPI object being used to call the Owlet API
    raw_properties : dict
        A dictionionary containing the raw response from the device properties api call
    properties : dict
        A formatted, cut down version of the current device properties

    Methods
    -------
    get_property:
        returns a specific property for the device
    get_properties:
        returns all the properties for the current device
    normalise_properties:
        takes the raw_properties and strips out only the most important properties making the dict object smaller and easier to use
    update_properties
        usees the OwletAPI object to call the Owlet server and return the current properties of the device.
    """

    def __init__(
        self, api: OwletAPI, data: dict[str : Union[str, int, bool, list]]
    ) -> None:
        """
        Constructs an Owlet sock object representing the owlet sock device

        Parameters
        ----------
        api (OwletAPI):OwletAPI object used to call the Owlet API
        data (dict):Data returned from the Owlet API showing the details of the sock
        """
        self._api = api

        self._name = data["product_name"]
        self._model = data["model"]
        self._serial = data["dsn"]
        self._oem_model = data["oem_model"]
        self._sw_version = data["sw_version"]
        self._mac = data["mac"]
        self._lan_ip = data["lan_ip"]
        self._connection_status = data["connection_status"]
        self._device_type = data["device_type"]
        self._manuf_model = data["manuf_model"]
        self._version = 0

        self.raw_properties = {}
        self.properties = {}


    @property
    def version(self) -> int:
        return self._version
    @property
    def name(self) -> str:
        return self._name

    @property
    def model(self) -> str:
        return self._model

    @property
    def serial(self) -> str:
        return self._serial

    @property
    def oem_model(self) -> str:
        return self._oem_model

    @property
    def sw_version(self) -> str:
        return self._sw_version

    @property
    def mac(self) -> str:
        return self._mac

    @property
    def lan_ip(self) -> str:
        return self._lan_ip

    @property
    def connection_status(self) -> str:
        return self._connection_status

    @property
    def device_type(self) -> str:
        return self._device_type

    @property
    def manuf_model(self) -> str:
        return self._manuf_model

    def get_property(self, property: str) -> str:
        """
        Returns the specific property based on the property argument passed in

        Parameters
        ----------
        property (str):The required property

        Returns
        -------
        (str):Request property as a string
        """
        return self.properties[property]

    def get_properties(self) -> dict[str:str]:
        """
        Returns all properties for the Owlet sock object

        Returns
        -------
        (dict):Request properties as a dict
        """
        return self.properties

    async def normalise_properties(
        self, raw_properties: dict[str:dict]
    ) -> dict[str : Union[bool, str, float]]:
        """
        Takes the raw properties dictionary returned from the API and formats it into another dict that is more stripped down and easier to work with

        Parameters
        ----------
            raw_properties (dict[str:dict]):The raw properties returned from the API call

        Returns
        -------
            (dict):Returns the stripped down properties as a dict
        """
        properties = {}
        properties["app_active"] = bool(raw_properties["APP_ACTIVE"]["value"])

        properties["high_heart_rate_alert"] = bool(
            raw_properties["HIGH_HR_ALRT"]["value"]
        )
        properties["high_oxygen_alert"] = bool(raw_properties["HIGH_OX_ALRT"]["value"])
        properties["low_battery_alert"] = bool(raw_properties["LOW_BATT_ALRT"]["value"])
        properties["low_heart_rate_alert"] = bool(
            raw_properties["LOW_HR_ALRT"]["value"]
        )
        properties["low_oxygen_alert"] = bool(raw_properties["LOW_OX_ALRT"]["value"])
        properties["ppg_log_file"] = bool(raw_properties["PPG_LOG_FILE"]["value"])
        properties["firmware_update_available"] = bool(
            raw_properties["FW_UPDATE_STATUS"]["value"]
        )
        properties["lost_power_alert"] = bool(
            raw_properties["LOST_POWER_ALRT"]["value"]
        )
        properties["sock_disconnected"] = bool(
            raw_properties["SOCK_DISCON_ALRT"]["value"]
        )
        properties["sock_off"] = bool(raw_properties["SOCK_OFF"]["value"])

        if self._version == 3:
            vitals = json.loads(raw_properties["REAL_TIME_VITALS"]["value"])
            properties["oxygen_saturation"] = float(vitals["ox"])
            properties["heart_rate"] = float(vitals["hr"])
            properties["moving"] = bool(vitals["mv"])
            properties["base_station_on"] = (
                True if bool(vitals["bso"]) or bool(vitals["chg"]) else False
            )
            properties["battery_percentage"] = float(vitals["bat"])
            properties["battery_minutes"] = float(vitals["btt"])
            properties["charging"] = True if int(vitals["chg"]) in [1, 2] else False
            properties["signal_strength"] = float(vitals["rsi"])
            properties["last_updated"] = datetime.datetime.strptime(
                raw_properties["REAL_TIME_VITALS"]["data_updated_at"], "%Y-%m-%dT%H:%M:%SZ"
            ).strftime("%Y/%m/%d %H:%M:%S")

        return properties

    async def update_properties(
        self,
    ) -> tuple[dict[str, dict], dict[str : Union[bool, str, float]]]:
        """
        Calls the Owlet api to update the properties and then returns both the raw response dict and the formatted dict from
        normalise_properties

        Returns
        -------
        (tuple):Tuple containing two dictionaries, one with the raw json response from the API and another with the stripped down properties from normalise_properties
        """
        logging.info(f"Updating properties for device {self.serial}")
        self.raw_properties = await self._api.get_properties(self.serial)
        self._version = await self._api.check_sock_version(self.raw_properties)
        self.properties = await self.normalise_properties(self.raw_properties)

        return (self.raw_properties, self.properties)
