from src.pyowletapi.owlet import Owlet

import asyncio


async def run():
    owlet = Owlet('europe', 'username',
                  'password')
    await owlet.authenticate()
    devices = await owlet.devices()
    print(devices)
    for serial, sock in devices.items():
        properties = await sock.update_properties()
        #properties = properties[1]
        print(properties)
        #print(properties['heart_rate'], properties['oxygen_saturation'], properties['battery_percentage'])
    await owlet.close()

if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run())
