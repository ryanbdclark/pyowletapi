from src.pyowletapi.api import OwletAPI
from src.pyowletapi.sock import Sock
from src.pyowletapi.exceptions import OwletError

import asyncio
import json


async def run():
    with open("login.json") as file:
        data = json.load(file)
    region = data["region"]
    username = data["username"]
    password = data["password"]

    api = OwletAPI(region, username, password)

    try:
        await api.authenticate()

        devices = await api.get_devices()
        socks = {
            device["device"]["dsn"]: Sock(api, device["device"])
            for device in devices["response"]
        }
        for sock in socks.values():
            # print(await sock._api.get_properties(sock.serial))
            properties = await sock.update_properties()
            properties = properties["properties"]
            print(properties)

    except OwletError as err:
        print(err)
        await api.close()
        exit()

    await api.close()


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run())
