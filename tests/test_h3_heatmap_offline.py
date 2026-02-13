"""
Test for: offline_folium + h3 + HeatMap
- Creates H3 hexagons around Denver
- Adds a heatmap layer using the same H3 cell centers
- Everything works offline after downloading assets

Install (one-time):
  pip install offline-folium h3 numpy

Setup (one-time, requires internet):
  python -m offline_folium heatmap  # Downloads Map + HeatMap assets

Run (works offline):
  python test_h3_heatmap_offline.py
"""

from __future__ import annotations

import random
from pathlib import Path

from offline_folium import OfflineMap
import folium
import folium.plugins
import numpy as np
import h3


def h3_cell_to_geojson_polygon(cell: str) -> dict:
    """Convert an H3 cell id to a GeoJSON polygon (lon/lat order)."""
    boundary_latlng = h3.cell_to_boundary(cell)
    coords_lnglat = [(lng, lat) for (lat, lng) in boundary_latlng]
    # GeoJSON polygons must be closed
    if coords_lnglat[0] != coords_lnglat[-1]:
        coords_lnglat.append(coords_lnglat[0])
    return {
        "type": "Feature",
        "properties": {"h3": cell},
        "geometry": {"type": "Polygon", "coordinates": [coords_lnglat]},
    }


def h3_cell_center(cell: str) -> tuple[float, float]:
    """Get the center lat/lng of an H3 cell."""
    lat, lng = h3.cell_to_latlng(cell)
    return lat, lng


def color_for_value(v: float, vmin: float, vmax: float) -> str:
    """Map value to a color (yellow to red)."""
    if vmax <= vmin:
        t = 0.5
    else:
        t = (v - vmin) / (vmax - vmin)
    t = float(np.clip(t, 0.0, 1.0))

    r1, g1, b1 = (255, 245, 200)  # light yellow
    r2, g2, b2 = (200, 0, 0)      # red
    r = int(r1 + t * (r2 - r1))
    g = int(g1 + t * (g2 - g1))
    b = int(b1 + t * (b2 - b1))
    return f"#{r:02x}{g:02x}{b:02x}"


def main() -> None:
    # Center on Denver
    center_lat, center_lng = 39.7392, -104.9903

    # H3 resolution and radius
    res = 7
    k = 4  # disk radius

    center_cell = h3.latlng_to_cell(center_lat, center_lng, res)
    cells = list(h3.grid_disk(center_cell, k))

    # Generate fake values for each cell
    rng = random.Random(42)
    values = {c: rng.random() for c in cells}
    vmin, vmax = min(values.values()), max(values.values())

    # Create OFFLINE map
    m = OfflineMap(
        location=[center_lat, center_lng],
        zoom_start=11,
        control_scale=True,
        tiles="OpenStreetMap",
        name="OpenStreetMap"
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

    # Layer 1: H3 hexagons with choropleth coloring
    hex_layer = folium.FeatureGroup(name="H3 Hexagons", show=True)
    
    for cell in cells:
        feature = h3_cell_to_geojson_polygon(cell)
        val = values[cell]
        fill = color_for_value(val, vmin, vmax)

        folium.GeoJson(
            feature,
            style_function=lambda _feat, fill=fill: {
                "color": "#333333",
                "weight": 1,
                "fillColor": fill,
                "fillOpacity": 0.5,
            },
            tooltip=folium.Tooltip(f"h3={cell}<br>value={val:.3f}"),
        ).add_to(hex_layer)

    hex_layer.add_to(m)

    # Layer 2: HeatMap using cell centers weighted by values
    heat_data = []
    for cell in cells:
        lat, lng = h3_cell_center(cell)
        weight = values[cell]
        heat_data.append([lat, lng, weight])

    heatmap_layer = folium.plugins.HeatMap(
        heat_data,
        name="HeatMap (weighted by value)",
        min_opacity=0.3,
        radius=25,
        blur=35,
        gradient={0.4: 'blue', 0.6: 'lime', 0.8: 'yellow', 1.0: 'red'},
        show=False,  # Start hidden so you can toggle it
    )
    heatmap_layer.add_to(m)

    # Add center marker
    # folium.Marker(
    #     location=[center_lat, center_lng],
    #     tooltip=f"Center<br>H3 res={res}, k={k}<br>{len(cells)} hexes",
    #     icon=folium.Icon(color="blue", icon="info-sign"),
    # ).add_to(m)

    # Layer control to toggle layers
    folium.LayerControl(collapsed=False).add_to(m)

    out = Path("test_h3_heatmap_offline.html").resolve()
    m.save(str(out))
    print(f"✓ Saved offline map with H3 + HeatMap to: {out}")
    print("  Features:")
    print(f"    - {len(cells)} H3 hexagons (colored by value)")
    print("    - HeatMap layer (toggle on/off)")
    print("  Open in browser - works without internet!")


if __name__ == "__main__":
    main()
