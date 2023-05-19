import logging
from logging import Logger
import json
import datetime
from .api import OwletAPI, TokenDict
from .const import PROPERTIES, VITALS
from typing import Union, TypedDict

logger: Logger = logging.getLogger(__package__)


class PropertiesDict(TypedDict):
    raw_properties: dict
    properties: dict
    tokens: Union[None, TokenDict]

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
        self._version = None

        self._raw_properties = {}
        self._properties = {}

    @property
    def api(self) -> OwletAPI:
        return self._api

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

    @property
    def properties(self) -> dict[str:str]:
        return self._properties

    @property
    def raw_properties(self) -> dict:
        return self._raw_properties

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
        return self._properties[property]

    async def normalise_properties(self) -> dict[str : Union[bool, str, float]]:
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

        for type, properties_tmp in PROPERTIES.items():
            properties = {
                key: type(self._raw_properties[property]["value"])
                for key, property in properties_tmp.items()
            }

        if self._version == 3:
            vitals = json.loads(self._raw_properties["REAL_TIME_VITALS"]["value"])

            for type, vitals_tmp in VITALS.items():
                for key, property in vitals_tmp.items():
                    match key:
                        case "base_station_on":
                            properties[key] = bool(vitals["bso"]) or bool(vitals["chg"])
                        case "last_updated":
                            properties[key] = datetime.datetime.strptime(
                                self._raw_properties["REAL_TIME_VITALS"][
                                    "data_updated_at"
                                ],
                                "%Y-%m-%dT%H:%M:%SZ",
                            ).strftime("%Y/%m/%d %H:%M:%S")
                        case _:
                            properties[key] = type(vitals[property])

        return properties

    async def _check_version(self) -> None:
        version = 0
        if "REAL_TIME_VITALS" in self._raw_properties:
            version = 3
        elif "CHARGE_STATUS" in self._raw_properties:
            version = 2
        self._version = version

    async def update_properties(
        self,
    ) -> PropertiesDict:
        """
        Calls the Owlet api to update the properties and then returns the raw response dict, the formatted dict from
        normalise_properties and any new api tokens if they have changed

        Returns
        -------
        (dict):Dictionary containing three dictionaries, one with the raw json response from the API and another with the stripped down
        properties from normalise_properties, the third will contain the new api tokens if they have changed, if they haven't changed this will be None
        """
        logging.info(f"Updating properties for device {self.serial}")
        properties = await self._api.get_properties(self.serial)
        self._raw_properties = properties["response"]
        if self._version is None:
            await self._check_version()
        self._properties = await self.normalise_properties()

        return {
            "raw_properties": self._raw_properties,
            "properties": self._properties,
            "tokens": properties["tokens"],
        }
