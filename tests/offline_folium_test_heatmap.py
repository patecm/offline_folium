#!/usr/bin/env python3
"""
Offline HeatMap smoke test for offline_folium.

What it does:
- Builds a folium map
- Adds a HeatMap layer
- Saves to HTML
- Verifies the saved HTML does NOT reference http/https (basic offline check)

Usage:
  python test_offline_heatmap.py

Notes:
- For true offline HeatMap, you must have the Leaflet.heat JS vendored locally
  (commonly named "leaflet-heat.js" or similar), AND your offline_folium rewrite
  logic must rewrite the HeatMap asset URL to that local file.
"""

from __future__ import annotations

import random
from pathlib import Path

import folium
from folium.plugins import HeatMap

# If your package exposes OfflineMap, prefer it:
try:
    from offline_folium import OfflineMap  # type: ignore
except Exception:
    OfflineMap = None  # fallback to folium.Map


def make_points(center_lat: float, center_lng: float, n: int = 400, spread: float = 0.03):
    rng = random.Random(42)
    pts = []
    for _ in range(n):
        lat = center_lat + rng.uniform(-spread, spread)
        lng = center_lng + rng.uniform(-spread, spread)
        # weight (optional) - keep between 0 and 1
        w = rng.random()
        pts.append([lat, lng, w])
    return pts


def assert_no_remote_refs(html_text: str) -> None:
    # Basic (but effective) offline check
    bad = []
    for token in ("http://", "https://", "//"):
        if token in html_text:
            bad.append(token)
    if bad:
        # Show a small snippet around the first occurrence to help debug
        first = min((html_text.find(t), t) for t in bad if html_text.find(t) != -1)
        idx, tok = first
        lo = max(idx - 120, 0)
        hi = min(idx + 200, len(html_text))
        snippet = html_text[lo:hi].replace("\n", " ")
        raise AssertionError(
            f"Found remote reference token {tok!r} in output HTML. "
            f"This likely means the HeatMap plugin JS/CSS wasn't rewritten to local.\n"
            f"Snippet: ...{snippet}..."
        )


def main() -> None:
    # Choose a center (Denver-ish). Change freely.
    center_lat, center_lng = 39.7392, -104.9903

    MapCls = OfflineMap if OfflineMap is not None else folium.Map

    m = MapCls(
        location=[center_lat, center_lng],
        zoom_start=12,
        tiles="OpenStreetMap",
        control_scale=True,
    )

    # Generate data
    data = make_points(center_lat, center_lng, n=600, spread=0.04)

    # Add HeatMap
    HeatMap(
        data,
        name="HeatMap",
        radius=18,
        blur=14,
        min_opacity=0.25,
        max_zoom=14,
    ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    out = Path("offline_heatmap_test.html").resolve()
    m.save(str(out))

    html = out.read_text(encoding="utf-8")

    # 1) Sanity check the HeatMap layer actually made it into the HTML
    # (this string can vary by folium version, but usually includes "HeatLayer" or "heatLayer")
    if "heatLayer" not in html and "HeatLayer" not in html:
        raise AssertionError(
            "Did not find expected HeatMap marker strings in HTML. "
            "HeatMap may not have rendered as expected."
        )

    # 2) Offline check: ensure no remote URLs remain
    assert_no_remote_refs(html)

    print(f"✅ Offline HeatMap HTML generated with no remote refs: {out}")
    print("Open it in a browser with Wi-Fi off to confirm visually.")


if __name__ == "__main__":
    main()
