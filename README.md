# Introduction

Inspiration and API reverse engineering taken from various projects:

https://github.com/BastianPoe/owlet_api

https://github.com/mbevand/owlet_monitor

## Install

To install via pip run command

```
pip install pyowletapi
```

## To do

Tidy up exception logging

Create test routines

## Use

import the api and sock objects

```python
from pyowletapi.api import OwletAPI
from pyowlet.sock import Sock
```

create an api object passing your region, username and password, the OwletAPI will also take a aiohttp session as a keyword argument

```python
api = OwletAPI('europe', username, password)
```

you can then authenticate against the Owlet servers using this object and create a list of sock objects

```python
await api.authenticate()
socks = {device['device']['dsn']: Sock(api, device['device']) for device in devices}
```

to get current reading from sock call the update_properties function on each sock object

```python
device.update_properties()
```

This will return a dictionary, the key 'raw_properties' contains the raw response as a dict and the 'properties' key is a more cut down dict version of the response showing only the most relevant data and the 'tokens' key will return a dictionary if the api tokens have changed since the last call
