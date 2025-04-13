import logging
from logging import Logger
import json
import datetime
import time
from .api import OwletAPI, TokenDict
from .const import PROPERTIES, VITALS_3, VITALS_2
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
        self._name = data.get("product_name", "Owlet Baby Monitors")
        self._model = data.get("model", "")
        self._serial = data.get("dsn", "Unkown")
        self._oem_model = data.get("oem_model", "Unknown")
        self._sw_version = data.get("sw_version", "Unknown")
        self._mac = data.get("mac", "")
        self._lan_ip = data.get("lan_ip", "")
        self._connection_status = data.get("connection_status", "Unknown")
        self._device_type = data.get("device_type", "Wifi")
        self._manuf_model = data.get("manuf_model", "Unknown")
        self._version = None
        self._revision = None

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

    @property
    def revision(self) -> int:
        return self._revision

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

    async def _normalise_properties(self) -> dict[str : Union[bool, str, float]]:
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
            for key, property in properties_tmp.items():
                try:
                    properties[key] = type(self._raw_properties[property]["value"])
                except KeyError:
                    pass

        if self._version == 3:
            vitals = json.loads(self._raw_properties["REAL_TIME_VITALS"]["value"])

            for type, vitals_list in VITALS_3.items():
                for vital_desc, vital_key in vitals_list.items():
                    match vital_desc:
                        case "base_station_on":
                            try:
                                properties[vital_desc] = vitals["bso"]
                            except KeyError:
                                pass
                        case "last_updated":
                            try:
                                properties[vital_desc] = datetime.datetime.strptime(
                                    self._raw_properties["REAL_TIME_VITALS"][
                                        "data_updated_at"
                                    ],
                                    "%Y-%m-%dT%H:%M:%SZ",
                                ).strftime("%Y/%m/%d %H:%M:%S")
                            except KeyError:
                                pass
                        case _:
                            try:
                                properties[vital_desc] = type(vitals[vital_key])
                            except KeyError:
                                pass

        if self._version == 2:
            for type, vitals_list in VITALS_2.items():
                for vital_desc, vital_key in vitals_list.items():
                    try:
                        properties[vital_desc] = type(
                            self._raw_properties[vital_key]["value"]
                        )
                    except KeyError:
                        pass

        return properties

    async def _check_version(self) -> None:
        version = 0
        if "REAL_TIME_VITALS" in self._raw_properties:
            version = 3
        elif "CHARGE_STATUS" in self._raw_properties:
            version = 2
        self._version = version

    async def _check_revision(self) -> None:
        revision_json = json.loads(self._raw_properties["oem_sock_version"]["value"])
        self._revision = revision_json["rev"]

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
        logger.info(f"Updating properties for device {self.serial}")
        properties = await self._api.get_properties(self.serial)
        self._raw_properties = properties["response"]
        if self._version is None:
            await self._check_version()
        if self._revision is None and self._version == 3:
            await self._check_revision()
        self._properties = await self._normalise_properties()

        response = {
            "raw_properties": self._raw_properties,
            "properties": self._properties,
        }

        if "tokens" in properties:
            response["tokens"] = properties["tokens"]

        return response

    async def control_base_station(self, on: bool) -> bool:
        """
        Calls the Owlet api to turn the base station on or off, returns a bool if this was successful

        Returns
        -------
        (bool):Was the command successful
        """

        logging.info(f"Amend base station status {self.serial}")
        value = json.dumps({"ts": int(time.time()), "val": "true" if on else "false"})
        data = {"datapoint": {"metadata": {}, "value": value}}

        response = await self._api.post_command(
            self.serial, "BASE_STATION_ON_CMD", data
        )

        return True if response else False
