import aiohttp
import time
import logging
from logging import Logger
from aiohttp.client_exceptions import ClientResponseError

from .exceptions import OwletAuthenticationError, OwletConnectionError, OwletDevicesError, OwletError

logger: Logger = logging.getLogger(__package__)


class OwletAPI:
    def __init__(self, region: str, user: str, password: str, session=None):
        self._region = region
        self._user = user
        self._password = password
        self._auth_token = None
        self._expiry = None
        self.session = session
        self.headers = {}
        self.devices = {}

        self._region_info = {
            'world': {
                'url_mini': 'https://ayla-sso.owletdata.com/mini/',
                'url_signin': 'https://user-field-1a2039d9.aylanetworks.com/api/v1/token_sign_in',
                'url_base': 'https://ads-field-1a2039d9.aylanetworks.com/apiv1',
                'apiKey': 'AIzaSyCsDZ8kWxQuLJAMVnmEhEkayH1TSxKXfGA',
                'app_id': 'sso-prod-3g-id',
                'app_secret': 'sso-prod-UEjtnPCtFfjdwIwxqnC0OipxRFU',
            },
            'europe': {
                'url_mini': 'https://ayla-sso.eu.owletdata.com/mini/',
                'url_signin': 'https://user-field-eu-1a2039d9.aylanetworks.com/api/v1/token_sign_in',
                'url_base': 'https://ads-field-eu-1a2039d9.aylanetworks.com/apiv1',
                'apiKey': 'AIzaSyDm6EhV70wudwN3iOSq3vTjtsdGjdFLuuM',
                'app_id': 'OwletCare-Android-EU-fw-id',
                'app_secret': 'OwletCare-Android-EU-JKupMPBoj_Npce_9a95Pc8Qo0Mw',
            }
        }

        self._api_url = self._region_info[self._region]['url_base']

        if self.session is None:
            self.session = aiohttp.ClientSession(raise_for_status=True)

    async def authenticate(self) -> None:
        try:
            if self._auth_token is not None:
                raise OwletError

            api_key = self._region_info[self._region]['apiKey']
            async with self.session.request("POST", f'https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={api_key}', data={'email': self._user, 'password': self._password, 'returnSecureToken': True}, headers={
                    'X-Android-Package': 'com.owletcare.owletcare', 'X-Android-Cert': '2A3BC26DB0B8B0792DBE28E6FFDC2598F9B12B74'}) as response:

                id_token = await response.json()
                id_token = id_token['idToken']

                async with self.session.request("GET", self._region_info[self._region]['url_mini'], headers={
                        'Authorization': id_token}) as response:

                    mini_token = await response.json()
                    mini_token = mini_token['mini_token']

                    async with self.session.request("POST", self._region_info[self._region]['url_signin'], json={
                        "app_id": self._region_info[self._region]['app_id'],
                        "app_secret": self._region_info[self._region]['app_secret'],
                        "provider": "owl_id",
                        "token": mini_token,
                    }) as response:

                        response = await response.json()
                        access_token = response['access_token']

                        self.headers['Authorization'] = 'auth_token ' + \
                            access_token
                        self._expiry = time.time() + response['expires_in']

        except ClientResponseError as error:
            raise OwletError from error
        except Exception as error:
            raise OwletError from error

    async def close(self) -> None:
        if self.session:
            await self.session.close()

    async def get_devices(self) -> dict:
        if self._expiry <= time.time():
            self.authenticate()

        return await self.request("GET", ('/devices.json'))

    async def activate(self, device_serial):
        data = {"datapoint": {"metadata": {}, "value": 1}}
        await self.request("POST",
                           f'/dsns/{device_serial}/properties/APP_ACTIVE/datapoints.json', data=data)

    async def get_properties(self, device):
        properties = {}
        await self.activate(device)
        response = await self.request("GET", f'/dsns/{device}/properties.json')
        # print(response)

        for property in response:
            properties[property['property']
                       ['name']] = property['property']

        return properties

    async def request(self, method, url, data=None):
        try:
            async with self.session.request(method, self._api_url+url, headers=self.headers, json=data) as response:
                return await response.json()
        except ClientResponseError as error:
            raise OwletError from error
        except Exception as error:
            raise OwletError from error
