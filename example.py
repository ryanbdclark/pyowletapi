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
    region = data["region"]
    username = data["username"]
    password = data["password"]

    api = OwletAPI(
        region, username, password)

    try:
        await api.authenticate()

        devices = await api.get_devices()
        #print(devices)
        socks = {
            device["device"]["dsn"]: Sock(api, device["device"]) for device in devices['response']
        }
        for sock in socks.values():
            #print(await sock._api.get_properties(sock.serial))
            properties = await sock.update_properties()
            print(sock.revision)
            properties = properties["properties"]
            print(properties)

            print(await sock.control_base_station(True))
            # print(properties['heart_rate'], properties['oxygen_saturation'], properties['battery_percentage'])
    except (OwletEmailError, OwletPasswordError, OwletError) as err:
        print(err)
        await api.close()
        exit()

    await api.close()


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run())
