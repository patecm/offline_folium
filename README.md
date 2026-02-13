# Offline Folium

Use [folium](https://python-visualization.github.io/folium/) maps without an internet connection.

## Installation

```bash
pip install offline-folium
```

Or for development:
```bash
pip install -e .
```

## Quick Start

### 1. Download Assets (when you have internet)

Download the plugins you need:

```bash
# Download Map + HeatMap
python -m offline_folium heatmap

# Download multiple plugins
python -m offline_folium heatmap markercluster draw

# Download everything
python -m offline_folium --all

# See all available plugins
python -m offline_folium --help
```

This downloads all required JavaScript and CSS files to `offline_folium/local/`.

### 2. Create Maps Offline

```python
from offline_folium import OfflineMap
import folium.plugins

# Use exactly like folium.Map
m = OfflineMap(
    location=[45.5, -122.5],
    zoom_start=13,
    tiles="OpenStreetMap"
)
```
  
Available maps: 
- "OpenStreetMap"  
- "CartoDB positron"  
- "CartoDB dark_matter"  
- "Stamen Toner"  
- "Stamen Watercolor"  

```python
m = OfflineMap(location=[39.7, -104.9], zoom_start=12, tiles="CartoDB positron")
```

# Add a heatmap
heat_data = [[45.52, -122.68], [45.53, -122.67]]
folium.plugins.HeatMap(heat_data).add_to(m)

# Save - works completely offline!
m.save("my_map.html")
```

## Available Plugins

Download any combination of:
- `heatmap` - HeatMap plugin
- `markercluster` - MarkerCluster plugin
- `draw` - Draw plugin
- `minimap` - MiniMap plugin
- `mouseposition` - MousePosition plugin
- `fullscreen` - Fullscreen plugin
- `timestampedgeojson` - TimestampedGeoJson (animate data over time)
- `floatimage` - FloatImage (add images/logos to map)
- `groupedlayercontrol` - GroupedLayerControl (advanced layer management)
- `heatmapwithtime` - HeatMapWithTime (animated heatmaps)
- `fastmarkercluster` - FastMarkerCluster (performance version)

## Download Options

```bash
# Download specific plugins
python -m offline_folium heatmap markercluster

# Download all available plugins
python -m offline_folium --all

# Force re-download existing files
python -m offline_folium heatmap --force

# See help
python -m offline_folium --help
```

## How It Works

When you call `m.render()` or `m.save()`, OfflineMap automatically:
1. Walks through the map and all child elements (markers, plugins, etc.)
2. Finds any remote URLs for JS/CSS files
3. Replaces them with local file paths if the files were downloaded
4. Falls back to CDN URLs if local files are missing (requires internet)

**For true offline use:** Make sure to download all plugins you'll need before going offline!

## Example Workflow

```bash
# 1. While online, download what you need
python -m offline_folium heatmap markercluster

# 2. Disconnect from internet

# 3. Create maps offline
python my_script.py
```

## License

MIT
