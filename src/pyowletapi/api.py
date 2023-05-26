import aiohttp
import time
import logging
from logging import Logger
from aiohttp.client_exceptions import ClientResponseError
from typing import Union, TypedDict

from .exceptions import (
    OwletCredentialsError,
    OwletAuthenticationError,
    OwletConnectionError,
    OwletDevicesError,
    OwletError,
    OwletPasswordError,
    OwletEmailError,
)
from .const import REGION_INFO

logger: Logger = logging.getLogger(__package__)


class TokenDict(TypedDict):
    api_token: str
    expiry: float
    refresh: str


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
        user: str = None,
        password: str = None,
        token: str = None,
        expiry: float = None,
        refresh: str = None,
        session: aiohttp.ClientSession = None,
    ) -> None:
        """
        Sets all the necessary variables for the API caller based on the passed in information, if a session is not passed in then one is created

        Parameters
        ---------
        region (str):Region of user account, either world or europe
        user (str):Username (email) of user logging in
        password (str):Password of user logging in
        token (str):Once authentiacted the auth token will be stored in the object to be used for future api calls
        expiry (str):The expiry date of the connection is stored such that if the connection is expired the object reauthenticates
        refresh (str):The refresh token for the api, this can be passed if in known, if not passed then the api will authenticate and store the new refresh token for future use
        session (aiohttp.ClientSession), optional:The aiohttp session is stored to be called against
        """
        self._region = region
        self._user = user
        self._password = password
        self._auth_token: str = token
        self._expiry: float = expiry
        self._refresh: str = refresh
        self._tokens_changed: bool = False
        self._has_authenticated: bool = False
        self.session = session
        self.headers = {}
        self.devices = {}

        self._api_url = REGION_INFO[self._region]["url_base"]

        if self._region not in ["europe", "world"]:
            raise OwletAuthenticationError("Supplied region not valid")

        if self.session is None:
            self.session = aiohttp.ClientSession()

    @property
    def tokens(self) -> TokenDict:
        """Returns a TokenDict object with current auth token, expiry and refresh token"""
        return {
            "api_token": self._auth_token,
            "expiry": self._expiry,
            "refresh": self._refresh,
        }

    async def password_verification(self) -> None:
        """
        Will attempt to use the users username and password to login to the identitytoolkit api if authentication fails
        for any reason the relevent error is thrown, otherwise the returned refresh token will be stored
        """
        api_key = REGION_INFO[self._region]["apiKey"]
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
                        message = response_json["error"]["message"]
                        match message.split(":")[0]:
                            case "INVALID_PASSWORD":
                                raise OwletPasswordError("Incorrect Password")
                            case "INVALID_EMAIL":
                                raise OwletEmailError("Invalid email")
                            case "EMAIL_NOT_FOUND":
                                raise OwletEmailError("Email address not found")
                            case "INVALID_LOGIN_CREDENTIALS":
                                raise OwletCredentialsError(
                                    "Invalid login credentials"
                                )
                            case "TOO_MANY_ATTEMPTS_TRY_LATER":
                                raise OwletAuthenticationError(
                                    "Too many incorrect attempts"
                                )
                            case [
                                "API key not valid. Please pass a valid API key.",
                                "MISSING_EMAIL",
                                "MISSING_PASSWORD",
                            ]:
                                # Should never happen, report anyway
                                raise OwletAuthenticationError(
                                    "Identitytoolkit API failure 400, contact dev"
                                )
                            case _:
                                raise OwletAuthenticationError(
                                    "Generic indentitytoolkit error, contact dev"
                                )
                    case 403:
                        # Should never happen, report anyway
                        raise OwletAuthenticationError("API failure 403, contact dev")
                    case 404:
                        # Should never happen, report anyway
                        raise OwletAuthenticationError(
                            "IdentityToolkit API failure 404, contact dev"
                        )
                    case _:
                        raise OwletAuthenticationError(
                            f"Generic error contact dev, {response.status}, {response.text}"
                        )
            self._refresh = response_json["refreshToken"]

    async def get_mini_token(self, id_token) -> str:
        """
        Attempts to authenticate against the ayla mini token service with the given ID token
        any response other than a 200 response will throw an error.

        Returns
        --------------------
        (str): String with the returned mini token, for use with final sign in step
        """
        async with self.session.request(
            "GET",
            REGION_INFO[self._region]["url_mini"],
            headers={
                "Authorization": id_token,
            },
        ) as response:
            if response.status != 200:
                match response.status:
                    case 401:
                        raise OwletAuthenticationError("Invalid id token")
                    case _:
                        raise OwletAuthenticationError(
                            "Generic ayla mini error, contact dev"
                        )

            response_json = await response.json()
            return response_json["mini_token"]

    async def token_sign_in(self, mini_token) -> TokenDict:
        """
        Will use the provided mini token to attempt to authenticate against the owlet endpoint, anything other than a 200 response
        will throw an error. If succesful the token dict containing the auth_token, expiry and refresh token will be returned.

        Returns
        ----------------------
        (TokenDict): Dictionary containing the api token, token expiry time and refresh token
        """
        async with self.session.request(
            "POST",
            REGION_INFO[self._region]["url_signin"],
            json={
                "app_id": REGION_INFO[self._region]["app_id"],
                "app_secret": REGION_INFO[self._region]["app_secret"],
                "provider": "owl_id",
                "token": mini_token,
            },
        ) as response:
            response_json = await response.json()

            if response.status != 200:
                match response.status:
                    case 401:
                        raise OwletAuthenticationError("Invalid mini token")
                    case 404:
                        raise OwletAuthenticationError("Ayla 404 error contact dev")
                    case _:
                        raise OwletAuthenticationError(
                            "Generic ayla endpoint error, contact dev"
                        )
            self._auth_token = response_json["access_token"]
            self._expiry = time.time() - 60 + response_json["expires_in"]

            self.headers["Authorization"] = "auth_token " + self._auth_token

            return {
                "api_token": self._auth_token,
                "expiry": self._expiry,
                "refresh": self._refresh,
            }

    async def refresh_authentication(
        self,
    ) -> TokenDict:
        """
        Will attempt to refresh authentication when expired, if no refresh token exists or authentication fails then the relevent
        error will be thrown. On succesful authentication a TokenDict will be returned

        Returns
        ------------------
        (TokenDict): Dictionary containing the new api token, token expiry time and new refresh token
        """
        if self._refresh:
            api_key = REGION_INFO[self._region]["apiKey"]
            async with self.session.request(
                "POST",
                f"https://securetoken.googleapis.com/v1/token?key={api_key}",
                data={"grantType": "refresh_token", "refreshToken": self._refresh},
                headers={
                    "X-Android-Package": "com.owletcare.owletcare",
                    "X-Android-Cert": "2A3BC26DB0B8B0792DBE28E6FFDC2598F9B12B74",
                },
            ) as response:
                response_json = await response.json()

                if response.status != 200:
                    match response.status:
                        case 401:
                            raise OwletAuthenticationError("Refresh token not valid")
                        case _:
                            raise OwletError("Generic refresh error, contact dev")

                self._refresh = response_json["refresh_token"]

                mini_token = await self.get_mini_token(response_json["id_token"])

                return await self.token_sign_in(mini_token)
        raise OwletAuthenticationError("No refresh token supplied")

    async def authenticate(self) -> Union[None, TokenDict]:
        """
        Authentiactes the user against the Owlet api using the provided details

        Sets the values of the headers and expiry time variables on the object

        Returns
        -------
        None: if auth_token and expiry in object are ok then returns none
        dict: If auth token generated then dict with the new token returned
        """
        if self._auth_token is None and self._refresh is None:
            if self._user is None or self._password is None:
                return OwletAuthenticationError("Username or password not supplied")

            await self.password_verification()

        if self._auth_token is None or self._expiry <= time.time():
            return await self.refresh_authentication()

        self.headers["Authorization"] = "auth_token " + self._auth_token

        return await self.validate_authentication()

    async def validate_authentication(self) -> None:
        async with self.session.request(
            "GET", self._api_url + "/devices.json", headers=self.headers
        ) as response:
            if response.status not in (200, 201):
                self._auth_token = None
                return await self.authenticate()

    async def close(self) -> None:
        """
        Closes the aiohttp ClientSession

        Returns
        -------
        None
        """
        if self.session:
            await self.session.close()

    async def check_tokens(self, temp_tokens) -> Union[None, TokenDict]:
        """
        Checks if supplied tokens are different to the current tokens, if they are then return the current tokens as a TokenDict
        otherwise return None
        """
        if temp_tokens != self.tokens:
            return self.tokens

    async def get_devices(self, versions: list[int] = None) -> dict:
        """
        Returns a list of devices from the Owlet API

        Parameters
        ----------
        versions: takes a list of integers representing sock versions, will only return socks where the version is in the supplied list

        Returns
        ------
        dict: Dictionary containing the json response
        """

        temp_tokens = self.tokens

        devices = await self.request("GET", ("/devices.json"))
        if versions:
            for idx, device in enumerate(devices):
                properties = await self.get_properties(device["device"]["dsn"])
                properties = properties["response"]
                version = 0
                if "REAL_TIME_VITALS" in properties:
                    version = 3
                elif "CHARGE_STATUS" in properties:
                    version = 2
                if version not in versions or version == 0:
                    devices.pop(idx)

        if len(devices) < 1:
            raise OwletDevicesError("No devices found")

        return {"response": devices, "tokens": await self.check_tokens(temp_tokens)}

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
        temp_tokens = self.tokens

        properties = {}
        await self.activate(device)
        response = await self.request("GET", f"/dsns/{device}/properties.json")

        for property in response:
            properties[property["property"]["name"]] = property["property"]
        return {"response": properties, "tokens": await self.check_tokens(temp_tokens)}

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

        await self.validate_authentication()

        async with self.session.request(
            method, self._api_url + url, headers=self.headers, json=data
        ) as response:
            if response.status not in (200, 201):
                raise OwletConnectionError("Error sending request")

            return await response.json()
