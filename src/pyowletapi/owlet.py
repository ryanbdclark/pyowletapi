import logging

from logging import Logger

from .api import OwletAPI
from .sock import Sock

from .exceptions import OwletDevicesError

logger: Logger = logging.getLogger(__package__)


class Owlet:
    def __init__(self, region, username, password, session=None):
        self._session = session
        self.username = username
        self.region = region

        logger.info(f"Creating API object for {username}, region: {region}")
        self._api = OwletAPI(region, username, password, self._session)

    async def authenticate(self):
        logger.info(
            f"attempting login for {self.username}, region {self.region}")
        await self._api.authenticate()
        logger.info("Authentication succesful")

    async def devices(self):
        try:
            logger.info("retrieving devices")
            devices = await self._api.get_devices()

            if len(devices) < 1:
                raise OwletDevicesError

            return {device['device']['dsn']: Sock(self._api, device['device']) for device in devices}
        except OwletDevicesError:
            logger.degug(
                f"No devices exist for user {self.username}, region: {self.region}")

    async def close(self):
        await self._api.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self):
        await self.close()
