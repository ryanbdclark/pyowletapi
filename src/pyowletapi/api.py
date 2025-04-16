import aiohttp
import time
import logging
from logging import Logger
import asyncio
from typing import TypedDict, Optional, Any, NotRequired

from .exceptions import (
    OwletCredentialsError,
    OwletAuthenticationError,
    OwletConnectionError,
    OwletDevicesError,
    OwletError,
)
from .const import REGION_INFO

logger: Logger = logging.getLogger(__package__)


class SockData(TypedDict):
    product_name: str
    model: str
    dsn: str
    oem_model: str
    sw_version: str
    mac: str
    lan_ip: str
    connection_status: str
    device_type: str
    manuf_model: str


class TokenDict(TypedDict):
    api_token: Optional[str]
    expiry: Optional[float]
    refresh: Optional[str]


class DevicesResponse(TypedDict):
    response: list[dict[str, SockData]]
    tokens: NotRequired[TokenDict]


class PropertiesResponse(TypedDict):
    response: dict[str, dict[str, Any]]
    tokens: NotRequired[TokenDict]


class OwletAPI:
    """A class that creates an API object, to be used to call against the Owlet baby Monitor API.

    Attributes
    ----------
    region : str
        region of user account, either world or europe
    user : str
        username (email) of user logging in
    password : str
        password of user logging in
    auth_token : str
        once authentiacted the auth token will be stored in the object to be used for future api calls
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
        user: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
        expiry: Optional[float] = None,
        refresh: Optional[str] = None,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> None:
        """Sets all the necessary variables for the API caller based on the passed in information, if a session is not passed in then one is created.

        Parameters
        ----------
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
        self._auth_token: Optional[str] = token
        self._expiry: Optional[float] = expiry
        self._refresh: Optional[str] = refresh
        self._tokens_changed: bool = False
        self.session: aiohttp.ClientSession = session or aiohttp.ClientSession()
        self.headers: dict[str, str] = {}

        if self._auth_token:
            self.headers["Authorization"] = "auth_token " + self._auth_token

        if self._region not in ["europe", "world"]:
            raise OwletAuthenticationError("Supplied region not valid")

        self._api_url = REGION_INFO[self._region]["url_base"]

    @property
    def tokens(self) -> TokenDict:
        """Returns a TokenDict object with current auth token, expiry and refresh token"""
        return {
            "api_token": self._auth_token,
            "expiry": self._expiry,
            "refresh": self._refresh,
        }

    async def password_verification(self) -> None:
        """Will attempt to use the users username and password to login to the identitytoolkit api if authentication fails
        for any reason the relevant error is thrown, otherwise the returned refresh token will be stored.
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
                            case "INVALID_LOGIN_CREDENTIALS":
                                raise OwletCredentialsError(
                                    "Invalid login credentials",
                                )
                            case "TOO_MANY_ATTEMPTS_TRY_LATER":
                                raise OwletAuthenticationError(
                                    "Too many incorrect attempts",
                                )
                            case [
                                "API key not valid. Please pass a valid API key.",
                                "MISSING_EMAIL",
                                "MISSING_PASSWORD",
                            ]:
                                # Should never happen, report anyway
                                raise OwletAuthenticationError(
                                    "Identitytoolkit API failure 400, contact dev",
                                )
                            case _:
                                raise OwletAuthenticationError(
                                    "Generic identitytoolkit error, contact dev",
                                )
                    case 403:
                        # Should never happen, report anyway
                        raise OwletAuthenticationError(
                            "API failure 403, contact dev",
                        )
                    case 404:
                        # Should never happen, report anyway
                        raise OwletAuthenticationError(
                            "IdentityToolkit API failure 404, contact dev",
                        )
                    case _:
                        raise OwletAuthenticationError(
                            f"Generic error contact dev, {response.status}, {response.text}",
                        )

            self._update_tokens(
                new_token=self._auth_token,
                new_expiry=self._expiry,
                new_refresh=response_json["refreshToken"],
            )

    async def get_mini_token(self, id_token: str) -> str:
        """Attempts to authenticate against the ayla mini token service with the given ID token
        any response other than a 200 response will throw an error.

        Returns
        -------
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
                            "Generic ayla mini error, contact dev",
                        )

            response_json: dict[str, str] = await response.json()
            return response_json["mini_token"]

    async def token_sign_in(self, mini_token: str) -> Optional[TokenDict]:
        """Will use the provided mini token to attempt to authenticate against the owlet endpoint, anything other than a 200 response
        will throw an error. If successful the token dict containing the auth_token, expiry and refresh token will be returned.

        Returns
        -------
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
                        raise OwletAuthenticationError(
                            "Ayla 404 error contact dev",
                        )
                    case _:
                        raise OwletAuthenticationError(
                            "Generic ayla endpoint error, contact dev",
                        )

            self._update_tokens(
                new_token=response_json["access_token"],
                new_expiry=time.time() - 60 + response_json["expires_in"],
                new_refresh=self._refresh,
            )

            if self._tokens_changed:
                self._tokens_changed = False
                return self.tokens
            else:
                return None

    async def refresh_authentication(
        self,
    ) -> Optional[TokenDict]:
        """Will attempt to refresh authentication when expired, if no refresh token exists or authentication fails then the relevant
        error will be thrown. On successful authentication a TokenDict will be returned.

        Returns
        -------
        (TokenDict): Dictionary containing the new api token, token expiry time and new refresh token

        """
        if self._refresh:
            api_key = REGION_INFO[self._region]["apiKey"]
            async with self.session.request(
                "POST",
                f"https://securetoken.googleapis.com/v1/token?key={api_key}",
                data={
                    "grantType": "refresh_token",
                    "refreshToken": self._refresh,
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
                            raise OwletAuthenticationError(
                                "Refresh token not valid",
                            )
                        case _:
                            raise OwletError(
                                "Generic refresh error, contact dev",
                            )

                self._update_tokens(
                    new_token=self._auth_token,
                    new_expiry=self._expiry,
                    new_refresh=response_json["refresh_token"],
                )

                mini_token: str = await self.get_mini_token(
                    response_json["id_token"],
                )

                return await self.token_sign_in(mini_token)
        raise OwletAuthenticationError("No refresh token supplied")

    async def authenticate(self) -> Optional[TokenDict]:
        """Authentiactes the user against the Owlet api using the provided details.

        Sets the values of the headers and expiry time variables on the object.

        Returns
        -------
        None: if auth_token and expiry in object are ok then returns none
        dict: If auth token generated then dict with the new token returned

        """
        if self._auth_token is None and self._refresh is None:
            if self._user is None or self._password is None:
                raise OwletAuthenticationError(
                    "Username or password not supplied",
                )

            await self.password_verification()

        if (
            self._auth_token is None
            or self._expiry is None
            or self._expiry <= time.time()
        ):
            return await self.refresh_authentication()

        return None

    async def validate_authentication(self) -> Optional[TokenDict]:
        async with self.session.request(
            "GET",
            self._api_url + "/devices.json",
            headers=self.headers,
        ) as response:
            if response.status not in (200, 201):
                self._auth_token = None
                return await self.authenticate()
            return None

    async def close(self) -> None:
        """Closes the aiohttp ClientSession."""
        if self.session:
            await self.session.close()

    def _update_tokens(
        self,
        new_token: Optional[str],
        new_expiry: Optional[float],
        new_refresh: Optional[str],
    ) -> None:
        if (
            self._auth_token != new_token
            or self._expiry != new_expiry
            or self._refresh != new_refresh
        ):
            self._auth_token = new_token
            if self._auth_token:
                self.headers["Authorization"] = "auth_token " + self._auth_token
            self._expiry = new_expiry
            self._refresh = new_refresh
            self._tokens_changed = True

    async def _is_valid_version(self, dsn: str, versions: list[int]) -> bool:
        properties = await self.get_properties(dsn)
        properties_item = properties["response"]
        if "REAL_TIME_VITALS" in properties_item:
            return 3 in versions
        if "CHARGE_STATUS" in properties_item:
            return 2 in versions
        return False

    async def get_devices(
        self,
        versions: list[int] = [3, 2],
    ) -> DevicesResponse:
        """Returns a list of devices from the Owlet API.

        Parameters
        ----------
        versions: takes a list of integers representing sock versions, will only return socks where the version is in the supplied list

        Returns
        -------
        dict: Dictionary containing the json response

        """
        api_response = await self._request(
            "GET",
            "/devices.json",
        )

        if isinstance(api_response, list):
            devices = api_response

            checks = [
                self._is_valid_version(d["device"]["dsn"], versions) for d in devices
            ]
            results = await asyncio.gather(*checks)

            valid_devices = [d for d, valid in zip(devices, results) if valid]

            if not valid_devices:
                raise OwletDevicesError("No devices found")
            response: DevicesResponse = {"response": valid_devices}
            if self._tokens_changed:
                response["tokens"] = self.tokens
                self._tokens_changed = False
            return response
        else:
            raise OwletError("Unexpected response type from request.")

    async def activate(self, device_serial: str) -> None:
        """Sets APP_ACTIVE on the Owlet API to 1 to return properties.

        Parameters
        ----------
        device_serial (str):The serial number of the device being activated

        """
        data = {"datapoint": {"metadata": {}, "value": 1}}
        await self._request(
            "POST",
            f"/dsns/{device_serial}/properties/APP_ACTIVE/datapoints.json",
            data=data,
        )

    async def get_properties(
        self,
        device: str,
    ) -> PropertiesResponse:
        """Gets the properties from the Owlet API for a given device.

        Parameters
        ----------
        device (str):The serial number of the device to get the properties of

        Returns
        -------
        (dict):A dictionary containing all the current properties for the request device

        """
        properties = {}
        await self.activate(device)
        api_response = await self._request(
            "GET",
            f"/dsns/{device}/properties.json",
        )
        for property in api_response:
            properties[property["property"]["name"]] = property["property"]

            response: PropertiesResponse = {
                "response": properties,
            }

        if self._tokens_changed:
            response["tokens"] = self.tokens
        return response

    async def post_command(
        self,
        device: str,
        command: str,
        data: dict[str, Any],
    ) -> Any:
        """Send a command to the Owlet API and return the response."""
        await self.activate(device)
        response = await self._request(
            "POST",
            f"/dsns/{device}/properties/{command}/datapoints.json",
            data,
        )

        return response

    async def _request(
        self,
        method: str,
        url: str,
        data: Optional[dict[str, Any]] = None,
    ) -> Any:
        """Send a request to the Owlet API and return the response.

        Parameters
        ----------
        method (str):The method to call, either 'GET' or 'POST'
        url (str):The API url to call against
        data (dict):A dictionary with the data to send to the API.

        Returns
        -------
        dict: Dictionary containing the response

        """
        await self.validate_authentication()

        async with self.session.request(
            method,
            self._api_url + url,
            headers=self.headers,
            json=data,
        ) as response:
            if response.status not in (200, 201):
                raise OwletConnectionError("Error sending request")

            return await response.json()
