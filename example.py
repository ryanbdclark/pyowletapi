from pyowletapi.owlet import Owlet

import asyncio
import json


async def run():
    with open("login.json") as file:
        data = json.load(file)
    username = data['username']
    password = data['password']

    owlet = Owlet('europe', username,
                  password)
    await owlet.authenticate()
    devices = await owlet.devices()
    print(devices)
    for i in range(10):
        for serial, sock in devices.items():
            properties = await sock.update_properties()
            #properties = properties[1]
            print(properties[1])
            #print(properties['heart_rate'], properties['oxygen_saturation'], properties['battery_percentage'])   
        await asyncio.sleep(60)
    await owlet.close()

if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run())
