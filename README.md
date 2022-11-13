# Introduction

First pass at creating a wrapper for the Owlet baby monitor api, this currently only supports the sock v3 as I do not have a v2 to test with

inspiration and API reverse engineering taken from various projects:

https://github.com/BastianPoe/owlet_api
https://github.com/mbevand/owlet_monitor


End goal is to create a homeassistant integration using this API.


## To do
Tidy up exception logging
Create test routines

## Use
import the base Olwet object 

from pyowletapi.owlet import Owlet

create an Owlet object passing your region, username and password

owlet = Owlet('europe', username, password)

you can then authenticate against the Owlet servers using this object and get a list of devices (as sock objects)

await owlet.authenticate()
devices = await owlet.devices()

for each object call device.update_properties() to get the current readings from the sock, this will return a tuple, the first element being the raw response as a dict and the second element is a more cut down dict version of the response showing only the most relevant data.