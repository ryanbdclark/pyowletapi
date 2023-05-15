import aiohttp
import time
import logging
from logging import Logger
from aiohttp.client_exceptions import ClientResponseError
from typing import Union, TypedDict

from .exceptions import (
    OwletAuthenticationError,
    OwletConnectionError,
    OwletDevicesError,
    OwletError,
    OwletPasswordError,
    OwletEmailError
)

logger: Logger = logging.getLogger(__package__)


class TokenDict(TypedDict):
    api_token: str
    expiry: float

class OwletAPI:
    """
    A class that creates an API object, to be used to call against the Owlet baby Monitor API

    Attributes
    ----------
    region : str
        region of user account, either world or europe
    user : str
        username (email) of user logging in
    password : str
        password of user logging in
    auth_token : str
        once autherntiacted the auth token will be stored in the object to be used for future api calls
    expiry : str
        the expiry date of the connection is stored such that if the connection is expired the object reauthenticates
    session : aiohttp.ClientSession
        The aiohttp session is stored to be called against
    headers : dict
        The api headers are stored as a dict, once authenticated this contains the authkey in the correct format for future api calls
    devices : dict
        Once retrieved the list of user devices (Owlet socks) are stored
    region_info : dict
        A constant storing the API urls for each region
    api_url : str
        A constant storing the base API url dependent on the region passed in

    Methods
    -------
    authenticate:
        Authenticates against the Owlet API using the provided region, username and password, the connection is then stored in the session variable
    close:
        Closes the aiohttp ClientSession that is stored in the session variable
    get_devices
        Returns a dictionary containing the API response with a list of devices
    activate:
        Turns on the base station, API requires that APP_ACTIVE be set to 1 to respond
    get_properties(device: str):
        For a provided device serial number this returns a dict of the current properties for this device from the API
    request(method: str, url: str, data: dict = None):
        method used for all the subsequent api calls after the original authenticate call, rather than repeating the same code multiple times
        takes a method string which should either be 'GET' or 'POST', a url string for the relevant API endpoint and a dictionary containing
        any data required to be passed to the api
    """

    def __init__(
        self,
        region: str,
        user: str,
        password: str,
        token: str = None,
        expiry: float = None,
        session: aiohttp.ClientSession = None,
    ) -> None:
        """
        Sets all the necessary variables for the API caller based on the passed in information, if a session is not passed in then one is created

        Parameters
        ---------
        region (str):Region of user account, either world or europe
        user (str):Username (email) of user logging in
        password (str):Password of user logging in
        auth_token (str):Once authentiacted the auth token will be stored in the object to be used for future api calls
        expiry (str):The expiry date of the connection is stored such that if the connection is expired the object reauthenticates
        session (aiohttp.ClientSession), optional:The aiohttp session is stored to be called against
        """
        self._region = region
        self._user = user
        self._password = password
        self._auth_token: str = token
        self._expiry: float = expiry
        self.session = session
        self.headers = {}
        self.devices = {}

        self._region_info = {
            "world": {
                "url_mini": "https://ayla-sso.owletdata.com/mini/",
                "url_signin": "https://user-field-1a2039d9.aylanetworks.com/api/v1/token_sign_in",
                "url_base": "https://ads-field-1a2039d9.aylanetworks.com/apiv1",
                "apiKey": "AIzaSyCsDZ8kWxQuLJAMVnmEhEkayH1TSxKXfGA",
                "app_id": "sso-prod-3g-id",
                "app_secret": "sso-prod-UEjtnPCtFfjdwIwxqnC0OipxRFU",
            },
            "europe": {
                "url_mini": "https://ayla-sso.eu.owletdata.com/mini/",
                "url_signin": "https://user-field-eu-1a2039d9.aylanetworks.com/api/v1/token_sign_in",
                "url_base": "https://ads-field-eu-1a2039d9.aylanetworks.com/apiv1",
                "apiKey": "AIzaSyDm6EhV70wudwN3iOSq3vTjtsdGjdFLuuM",
                "app_id": "OwletCare-Android-EU-fw-id",
                "app_secret": "OwletCare-Android-EU-JKupMPBoj_Npce_9a95Pc8Qo0Mw",
            },
        }

        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def authenticate(self) -> Union[None, TokenDict]:
        """
        Authentiactes the user against the Owlet api using the provided details

        Sets the values of the headers and expiry time variables on the object

        Returns
        -------
        None: if auth_token and expiry in object are ok then returns none
        dict: If auth token generated then dict with the new token returned
        """
        if self._region not in ["europe", "world"]:
            raise OwletAuthenticationError("Supplied region not valid")

        self._api_url = self._region_info[self._region]["url_base"]

        if self._auth_token is not None and self._expiry > time.time():
            self.headers["Authorization"] = "auth_token " + self._auth_token
        else:
            api_key = self._region_info[self._region]["apiKey"]
            async with self.session.request(
                "POST",
                f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={api_key}",
                data={
                    "email": self._user,
                    "password": self._password,
                    "returnSecureToken": True,
                },
                headers={
                    "X-Android-Package": "com.owletcare.owletcare",
                    "X-Android-Cert": "2A3BC26DB0B8B0792DBE28E6FFDC2598F9B12B74",
                },
            ) as response:
                
                response_json = await response.json()
                if response.status != 200:
                    match response.status:
                        case 400:
                            message = response_json['error']['message']
                            match message.split(':')[0]:
                                case 'INVALID_PASSWORD':
                                    raise OwletPasswordError("Incorrect Password")
                                case 'INVALID_EMAIL':
                                    raise OwletEmailError("Invalid email")                          
                                case 'EMAIL_NOT_FOUND':
                                    raise OwletEmailError("Email address not found")
                                case 'TOO_MANY_ATTEMPTS_TRY_LATER':
                                    raise OwletAuthenticationError("Too many incorrect attempts")
                                case ['API key not valid. Please pass a valid API key.', "MISSING_EMAIL", "MISSING_PASSWORD"]:
                                    #Should never happen, report anyway
                                    raise OwletAuthenticationError("Identitytoolkit API failure 400, contact dev")
                                case _:
                                    raise OwletAuthenticationError("Generic indentitytoolkit error, contact dev")
                        case 403:
                            #Should never happen, report anyway
                            raise OwletAuthenticationError("API failure 403, contact dev")
                        case 404:
                            #Should never happen, report anyway
                            raise OwletAuthenticationError("IdentityToolkit API failure 404, contact dev")
                        case _:
                            raise OwletAuthenticationError(f"Generic error contact dev, {response.status}, {response.text}")
      
                id_token = response_json["idToken"]

            async with self.session.request(
                "GET",
                self._region_info[self._region]["url_mini"],
                headers={"Authorization": id_token,}
            ) as response:
                
                if response.status != 200:
                    match response.status:
                        case 401:
                            raise OwletAuthenticationError("Invalid id token")
                        case _:
                            raise OwletAuthenticationError("Generic ayla mini error, contact dev")
                            

                response_json = await response.json()
                mini_token = response_json["mini_token"]

                async with self.session.request(
                    "POST",
                    self._region_info[self._region]["url_signin"],
                    json={
                        "app_id": self._region_info[self._region]["app_id"],
                        "app_secret": self._region_info[self._region]["app_secret"],
                        "provider": "owl_id",
                        "token": mini_token,
                    },
                ) as response:

                    response_json = await response.json()

                    if response.status != 200:
                        message = response.json['errors']
                        match response.status:
                            case 401:
                                raise OwletAuthenticationError("Invalid mini token")
                            case 404:
                                raise OwletAuthenticationError("Ayla 404 error contact dev")
                            case _:
                                raise OwletAuthenticationError("Generic ayla endpoint error, contact dev")

                    response = await response.json()
                    self._auth_token = response["access_token"]
                    self.headers["Authorization"] = "auth_token " + self._auth_token
                    self._expiry = time.time()-60 + response["expires_in"]

                    return {'api_token':self._auth_token, 'expiry': self._expiry}

        return None

    async def close(self) -> None:
        """
        Closes the aiohttp ClientSession

        Returns
        -------
        None
        """
        if self.session:
            await self.session.close()

    async def get_devices(self, versions: list[int] = None) -> dict:
        """
        Returns a list of devices from the Owlet API, if the current time is after the expiry date of the connection the first re authenticate

        Parameters
        ----------
        versions: takes a list of integers representing sock versions, will only return socks where the version is in the supplied list

        Returns
        ------
        dict: Dictionary containing the json response
        """
        if self._expiry <= time.time():
            await self.authenticate()

        devices = await self.request("GET", ("/devices.json"))
        if versions:
            for idx, device in enumerate(devices):

                properties = await self.get_properties(device['device']['dsn'])
                version=0
                if "REAL_TIME_VITALS" in properties:
                    version=3
                elif "CHARGE_STATUS" in properties:
                    version= 2
                if version not in versions or version == 0:
                    devices.pop(idx)

        if len(devices) < 1:
            raise OwletDevicesError("No devices found")

        return devices

    async def activate(self, device_serial: str) -> None:
        """
        Owlet API requires the APP_ACITVE be set to 1 to return properties, this sets that

        Parameters
        ---------
        device_serial (str):The serial number of the device being activated

        Returns
        -------
        None
        """

        if self._expiry <= time.time():
            await self.authenticate()

        data = {"datapoint": {"metadata": {}, "value": 1}}
        await self.request(
            "POST",
            f"/dsns/{device_serial}/properties/APP_ACTIVE/datapoints.json",
            data=data,
        )

    async def get_properties(self, device: str) -> dict[str:list]:
        """
        Calls the Owlet API to get the current properties for a given device

        Parameters
        ----------
        device (str):The serial number of the device to get the properties of

        Returns
        ------
        (dict):A dictionary containing all the current properties for the request device
        """
        properties = {}
        await self.activate(device)
        response = await self.request("GET", f"/dsns/{device}/properties.json")

        for property in response:
            properties[property["property"]["name"]] = property["property"]
        return properties

    async def request(self, method: str, url: str, data: dict = None) -> dict:
        """
        Method for calling the Owlet API once authenticate has already been completed

        Parameters
        ---------
        method (str):The method to call, either 'GET' or 'POST'
        url (str):The API url to call against
        data (dict):A dictionary with the data to send to the API, only used when the activate method is called

        Returns
        ------
        dict: Dictionary containing the response
        """
        try:
            async with self.session.request(
                method, self._api_url + url, headers=self.headers, json=data
            ) as response:
                return await response.json()
        except ClientResponseError as error:
            raise OwletConnectionError from error
        except Exception as error:
            raise OwletError from error
