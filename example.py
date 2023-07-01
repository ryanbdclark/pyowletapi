from src.pyowletapi.api import OwletAPI
from src.pyowletapi.sock import Sock
from src.pyowletapi.exceptions import (
    OwletAuthenticationError,
    OwletConnectionError,
    OwletError,
    OwletPasswordError,
    OwletEmailError,
)

import asyncio
import json


async def run():
    with open("login.json") as file:
        data = json.load(file)
    username = data["region"]
    password = data["password"]
    password = data["password"]

    #region = "world"
    #username = "email@domain.com"
    #password = "password"

    api = OwletAPI(
        region, username, password)

    try:
        await api.authenticate()

        devices = await api.get_devices()
        print(devices)
        socks = {
            device["device"]["dsn"]: Sock(api, device["device"]) for device in devices['response']
        }

        # for sock in socks.values():
        # print(sock._api.tokens)
        # for i in range(10):
        for sock in socks.values():
            properties = await sock.update_properties()
            # properties = properties[1]
            #print(properties)
            # print(sock._api.tokens_changed)
            # print(sock._api.tokens)

            # print(properties['heart_rate'], properties['oxygen_saturation'], properties['battery_percentage'])
    except (OwletEmailError, OwletPasswordError, OwletError) as err:
        print(err)
        await api.close()
        exit()

    await asyncio.sleep(60)
    await api.close()


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run())
