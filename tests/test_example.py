"""Example usage of offline_folium"""

from offline_folium import OfflineMap
import folium.plugins

# Create an offline map
m = OfflineMap(
    location=[45.5236, -122.6750],  # Portland, OR
    zoom_start=12,
    tiles="OpenStreetMap"
)

# Add Options for different tile layers
folium.TileLayer(
    tiles="CartoDB positron",
    name="CartoDB Positron",
    overlay=False,  # This makes it a basemap, not an overlay
    control=True,
).add_to(m)

folium.TileLayer(
    tiles="CartoDB dark_matter",
    name="CartoDB Dark",
    overlay=False,
    control=True,
).add_to(m)

# Add a marker
# folium.Marker(
#     location=[45.5236, -122.6750],
#     popup="Portland!",
#     icon=folium.Icon(color="red")
# ).add_to(m)

# Add a heatmap
heat_data = [
    [45.52, -122.68],
    [45.53, -122.67],
    [45.51, -122.69],
]
folium.plugins.HeatMap(heat_data).add_to(m)

# Save the map
m.save("test_example_map.html")
print("Map saved to test_map.html")
