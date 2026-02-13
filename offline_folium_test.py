"""
Quick smoke-test for: folium + h3
** Test the OLD functionality from original forked repo **
- Builds a folium map
- Generates a small H3 disk around a center point
- Draws each hexagon polygon on the map
- Colors hexes by a fake "value" (random)
- Saves to an HTML file you can open in a browser

Install (one-time):
  pip install folium h3 numpy

Run:
  python test_folium_h3.py
"""

from __future__ import annotations

import random
from pathlib import Path

from offline_folium import offline #MUST import BEFORE folium
import folium
import numpy as np
import h3


def h3_cell_to_geojson_polygon(cell: str) -> dict:
    """
    Convert an H3 cell id to a GeoJSON polygon (lon/lat order).
    """
    # h3.cell_to_boundary returns list of (lat, lng)
    boundary_latlng = h3.cell_to_boundary(cell)
    coords_lnglat = [(lng, lat) for (lat, lng) in boundary_latlng]
    # GeoJSON polygons must be closed (first == last)
    if coords_lnglat[0] != coords_lnglat[-1]:
        coords_lnglat.append(coords_lnglat[0])
    return {
        "type": "Feature",
        "properties": {"h3": cell},
        "geometry": {"type": "Polygon", "coordinates": [coords_lnglat]},
    }


def color_for_value(v: float, vmin: float, vmax: float) -> str:
    """
    Map value to a simple red-ish ramp (no extra deps).
    Returns an HTML hex color string like '#RRGGBB'.
    """
    if vmax <= vmin:
        t = 0.5
    else:
        t = (v - vmin) / (vmax - vmin)
    t = float(np.clip(t, 0.0, 1.0))

    # interpolate between light yellow and red
    r1, g1, b1 = (255, 245, 200)
    r2, g2, b2 = (200, 0, 0)
    r = int(r1 + t * (r2 - r1))
    g = int(g1 + t * (g2 - g1))
    b = int(b1 + t * (b2 - b1))
    return f"#{r:02x}{g:02x}{b:02x}"


def main() -> None:
    # Pick a center (Denver-ish). Change to wherever you like.
    center_lat, center_lng = 39.7392, -104.9903

    # H3 resolution: 7 ~ neighborhood-scale; 8/9 more detailed; 6 bigger
    res = 7

    center_cell = h3.latlng_to_cell(center_lat, center_lng, res)

    # "Disk" radius in hex steps around the center cell
    k = 3
    cells = list(h3.grid_disk(center_cell, k))

    # Fake data per cell (to test coloring/choropleth)
    rng = random.Random(42)
    values = {c: rng.random() for c in cells}
    vmin, vmax = min(values.values()), max(values.values())

    # Create the folium map
    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=12,
        tiles="OpenStreetMap",  # change if you want other tiles
        control_scale=True,
    )

    # Add center marker
    folium.Marker(
        location=[center_lat, center_lng],
        tooltip=f"Center (H3 res={res})",
        icon=folium.Icon(color="blue", icon="info-sign"),
    ).add_to(m)

    # Draw each hex polygon
    hex_layer = folium.FeatureGroup(name=f"H3 hexes (res={res}, k={k})", show=True)

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
                "fillOpacity": 0.55,
            },
            tooltip=folium.Tooltip(f"h3={cell}<br>value={val:.3f}"),
        ).add_to(hex_layer)

    hex_layer.add_to(m)

    # Add a few random points and show which H3 cell they land in
    pts_layer = folium.FeatureGroup(name="Random points", show=True)
    for i in range(10):
        # roughly within a few km around center
        lat = center_lat + rng.uniform(-0.03, 0.03)
        lng = center_lng + rng.uniform(-0.03, 0.03)
        cell = h3.latlng_to_cell(lat, lng, res)
        folium.CircleMarker(
            location=[lat, lng],
            radius=4,
            fill=True,
            fill_opacity=0.9,
            tooltip=f"pt#{i} → {cell}",
        ).add_to(pts_layer)

    pts_layer.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    out = Path("folium_h3_test_offline.html").resolve()
    m.save(str(out))
    print(f"Saved map to: {out}")
    print("Open that HTML file in your browser.")


if __name__ == "__main__":
    main()
