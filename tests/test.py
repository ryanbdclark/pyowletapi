import unittest
import json

from src.pyowletapi.api import OwletAPI
from src.pyowletapi.exceptions import (
    OwletAuthenticationError,
    OwletConnectionError,
    OwletDevicesError,
    OwletCredentialsError,
)


# Test to create owlet object
class ValidAuthOwletTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        with open("login.json") as file:
            login_creds = json.load(file)

        self.region = login_creds["region"]
        self.username = login_creds["username"]
        self.password = login_creds["password"]

    async def test_valid_region(self):
        owlet = OwletAPI(self.region, self.username, self.password)
        self.assertGreater(len(owlet._api_url), 0)
        await owlet.close()

    async def test_valid_auth_user_pass_auth_token(self):
        owlet = OwletAPI(self.region, self.username, self.password)
        self.assertEqual(type(await owlet.authenticate()), dict)
        self.assertEqual(await owlet.authenticate(), None)
        await owlet.close()

    async def test_no_devices(self):
        owlet = OwletAPI(self.region, self.username, self.password)
        await owlet.authenticate()
        with self.assertRaises(OwletDevicesError):
            await owlet.get_devices(versions=[10])
        await owlet.close()

    async def test_devices(self):
        owlet = OwletAPI(self.region, self.username, self.password)
        await owlet.authenticate()
        self.assertGreater(
            len((await owlet.get_devices(versions=[3]))["response"]), 0
        )
        await owlet.close()

    async def test_invalid_request(self):
        owlet = OwletAPI(self.region, self.username, self.password)
        with self.assertRaises(OwletConnectionError):
            await owlet.request("GET", "sample")

        await owlet.close()


class InvalidAuthOwletTests(unittest.IsolatedAsyncioTestCase):
    async def test_invalid_region(self):
        self.assertRaises(
            OwletAuthenticationError, OwletAPI, "sample", "sample@gmail.com", "sample"
        )

    async def test_invalid_credentials(self):
        owlet = OwletAPI("europe")
        with self.assertRaises(OwletAuthenticationError):
            await owlet.authenticate()
        await owlet.close()

        owlet = OwletAPI("europe", "sample@gmail.com", "sample")
        with self.assertRaises(OwletCredentialsError):
            await owlet.authenticate()
        await owlet.close()

    async def test_invalid_id_token(self):
        owlet = OwletAPI("europe", "sample@sample.com", "sample")

        with self.assertRaises(OwletAuthenticationError):
            await owlet.get_mini_token("sample")
        await owlet.close()

    async def test_invalid_mini_token(self):
        owlet = OwletAPI("europe", "sample@sample.com", "sample")

        with self.assertRaises(OwletAuthenticationError):
            await owlet.token_sign_in("sample")
        await owlet.close()

    async def test_invalid_refresh_token(self):
        owlet = OwletAPI("europe", refresh="sample")

        with self.assertRaises(OwletAuthenticationError):
            await owlet.refresh_authentication()
        await owlet.close()

    async def test_blank_refresh_token(self):
        owlet = OwletAPI("europe", refresh="")

        with self.assertRaises(OwletAuthenticationError):
            await owlet.refresh_authentication()
        await owlet.close()

    async def test_validate_authentication(self):
        owlet = OwletAPI("europe", token="sample")

        with self.assertRaises(OwletAuthenticationError):
            await owlet.validate_authentication()
        await owlet.close()

