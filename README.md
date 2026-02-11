# Offline Folium
`offline_folium` is a Python module that makes it possible to use [folium](https://python-visualization.github.io/folium/) without an internet connection.

## Quickstart
- Install offline_folium:

```bash
pip install offline_folium
```

- When you have an internet connection, download the relevant Javascript/CSS by running:
```bash
python -m offline_folium
```
- When you do not have an internet connection, run
```python
from offline_folium import OfflineMap
```
offline_folium does not need to be imported before folium.  

To use, replace folium.Map with OfflineMap:

```python
from offline_folium import offline
import folium

# Create the folium map
m = OfflineMap(
    location=[center_lat, center_lng],
    zoom_start=12,
    tiles="OpenStreetMap",  # change if you want other tiles
    control_scale=True,
)

See offline_folium_test_map.py for another example
```

## Why?
By default, folium loads the required Javascript and CSS from CDNs over the internet. This doesn't work when you need to run folium offline. This project helps with that by allowing you to download the required resources when you have an internet connection (or during the application build/deploy process) and then use folium later on with those downloaded resources. The aim is to package it all up so that it is nice and simple for end-users (who may not be folium or Python specialists) to use.