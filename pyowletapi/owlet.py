import logging

from logging import Logger
from aiohttp import ClientSession
from .api import OwletAPI
from .sock import Sock

from .exceptions import OwletDevicesError

logger: Logger = logging.getLogger(__package__)


class Owlet:
    """
    Class representing a wrapper for the API

    Attributes
    ----------
    session : aiohttp.ClientSession
        The aiohttp ClientSession to be used for all API calls
    username : str
        username (email) of user logging in
    region : str
        region of user account, either world or europe
    api : OwletAPI
        An instance of an OwletAPI object that will be used to communicate with the Owlet API   

    Methods
    -------
    authenticate:
        calls the authenticate method on the OwletAPI object telling it to authenticate
    devices:
        Calls the get_devices method on the OwletAPI object, returns a dictionary with the device serial numbers as the key
        and sock objects as the values
    close:
        Calls the close method on the OwletAPI object, closes the ClientSession   
    """

    def __init__(self, region: str, username: str, password: str, session: ClientSession = None) -> None:
        """
        Sets all the necessary variables for the API caller based on the passed in information

        Parameters
        --------
        region (str):Region of user account, either world or europe
        username (str):Username (email) of user logging in
        password (str):Password of user logging in
        session (aiohttp.ClientSession), optional:The aiohttp session is stored to be called against
        """
        self._session = session
        self.username = username
        self.region = region

        logger.info(f"Creating API object for {username}, region: {region}")
        self._api = OwletAPI(region, username, password, self._session)

    async def authenticate(self) -> bool:
        """
        Method that calls the authenticate method on the OwletAPI object

        Returns
        ------
        (bool):Boolean showing the status of the authentication
        """
        logger.info(
            f"attempting login for {self.username}, region {self.region}")
        if(await self._api.authenticate()):
            logger.info("Authentication succesful")
            return True

    async def get_devices(self) -> dict[str:Sock]:
        """
        Method that calls the get devices method on the OwletAPI and returns a dictionary of the results

        Returns
        -------
        (dict):Dictionary, the keys being the serial number of each device, the values are then a sock object for that device which contains all the relevant device
        properties
        """
        try:
            logger.info("retrieving devices")
            devices = await self._api.get_devices()
            
            if len(devices) < 1:
                raise OwletDevicesError

            return {device['device']['dsn']: Sock(self._api, device['device']) for device in devices}
        except OwletDevicesError("No devices exist for user"):
            logger.degug(
                f"No devices exist for user {self.username}, region: {self.region}")
            
    async def check_device_exists(self, serial : str) -> bool:
        """
        Method that calls that checks if a specified device is valid for the current user

        Returns
        ------
        (bool):Boolean showing the result of the check, if True the device is valid otherwise an OwletDeviceError will be raised
        """
        if serial in self.devices().keys():
            return True
        else:
            raise OwletDevicesError("Supplied serial number not valid")

    async def close(self) -> None:
        """
        Calls the close method on the OwletAPI object to close the ClientSession

        Returns
        -------
        None
        """
        await self._api.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self) -> None:
        await self.close()
