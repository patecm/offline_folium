

import os

def _local_first(url: str, dest_path: str) -> str:
    local = os.path.join(dest_path, os.path.basename(url))
    return local if os.path.exists(local) else url

def patch_assets(obj, dest_path: str):
    # obj can be folium.folium (for _default_js/_default_css) or a plugin class
    if hasattr(obj, "default_js"):
        obj.default_js = [(name, _local_first(url, dest_path)) for name, url in obj.default_js]
    if hasattr(obj, "default_css"):
        obj.default_css = [(name, _local_first(url, dest_path)) for name, url in obj.default_css]

# ##For specific plugins## #
# import folium
# from folium.plugins import HeatMap, Draw, MarkerCluster

# # patch core map assets if you want:
# patch_assets(folium.Map, dest_path)

# # patch plugin classes (affects all instances):
# patch_assets(HeatMap, dest_path)
# patch_assets(Draw, dest_path)
# patch_assets(MarkerCluster, dest_path)

#!/usr/bin/env python3
"""
vendor_folium_assets.py

Vendoring script for Folium 0.20.0 to make offline_folium truly offline.

It will:
- Import folium + selected plugins
- Read their default_js/default_css (and Map defaults if requested)
- Download each remote asset URL
- Save it into your offline_folium/local/ directory using the *URL basename*
  (matching your current os.path.basename(url) rewriting approach)
- Skip files that already exist (unless --force)
- Print a summary of what it did

Usage:
  python vendor_folium_assets.py --out offline_folium/local --plugins heatmap draw markercluster --include-map
  python vendor_folium_assets.py --out offline_folium/local --all

Notes:
- This script intentionally saves as URL basename, e.g. leaflet_heat.min.js, leaflet.draw.js, etc.
- It ignores assets that are already local (non-http(s)).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, List, Tuple
from urllib.parse import urlparse

import requests


def is_remote(url: str) -> bool:
    return url.startswith("http://") or url.startswith("https://")


def basename_from_url(url: str) -> str:
    # Handles query strings safely
    parsed = urlparse(url)
    name = Path(parsed.path).name
    if not name:
        raise ValueError(f"Could not determine basename from URL: {url}")
    return name


def iter_assets_from_obj(obj) -> Iterable[Tuple[str, str]]:
    """
    Yield (name, url) pairs from obj.default_js and obj.default_css when present.
    """
    for attr in ("default_js", "default_css"):
        assets = getattr(obj, attr, None)
        if not assets:
            continue
        for item in assets:
            if isinstance(item, (tuple, list)) and len(item) == 2:
                yield str(item[0]), str(item[1])


def download(url: str, dest: Path, force: bool, timeout: int = 30) -> str:
    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists() and not force:
        return "skipped (exists)"

    headers = {
        "User-Agent": "offline_folium vendoring script (requests)",
        "Accept": "*/*",
    }
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()
    dest.write_bytes(r.content)
    return f"downloaded ({len(r.content)} bytes)"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="Output directory (e.g. offline_folium/local)")
    ap.add_argument(
        "--plugins",
        nargs="*",
        default=[],
        help="Which plugins to vendor: heatmap draw markercluster (default: none)",
    )
    ap.add_argument("--include-map", action="store_true", help="Also vendor folium.Map defaults")
    ap.add_argument("--all", action="store_true", help="Vendor Map + heatmap + draw + markercluster")
    ap.add_argument("--force", action="store_true", help="Overwrite existing files")
    ap.add_argument("--timeout", type=int, default=30, help="HTTP timeout seconds (default 30)")
    args = ap.parse_args()

    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Import folium lazily so script errors are clear
    import folium
    from folium.plugins import Draw, HeatMap, MarkerCluster

    print(f"Folium version: {getattr(folium, '__version__', 'unknown')}")
    print(f"Vendoring into: {out_dir}")

    # Determine what to vendor
    want_map = args.include_map or args.all
    selected = set(p.lower() for p in (args.plugins or []))
    if args.all:
        selected |= {"heatmap", "draw", "markercluster"}

    targets: List[Tuple[str, object]] = []
    if want_map:
        targets.append(("folium.Map", folium.Map))
    if "heatmap" in selected:
        targets.append(("folium.plugins.HeatMap", HeatMap))
    if "draw" in selected:
        targets.append(("folium.plugins.Draw", Draw))
    if "markercluster" in selected:
        targets.append(("folium.plugins.MarkerCluster", MarkerCluster))

    if not targets:
        print("Nothing selected. Use --all or specify --plugins and/or --include-map.", file=sys.stderr)
        return 2

    # Collect remote assets
    remote: List[Tuple[str, str, str]] = []  # (owner, name, url)
    for owner, obj in targets:
        for name, url in iter_assets_from_obj(obj):
            if is_remote(url):
                remote.append((owner, name, url))

    # De-dup by URL (same URL may appear multiple times)
    seen = set()
    remote_dedup: List[Tuple[str, str, str]] = []
    for owner, name, url in remote:
        if url in seen:
            continue
        seen.add(url)
        remote_dedup.append((owner, name, url))

    if not remote_dedup:
        print("No remote assets found to vendor (already local or none present).")
        return 0

    print(f"Found {len(remote_dedup)} unique remote assets to vendor:")
    for owner, name, url in remote_dedup:
        print(f"  - {owner}: {name} -> {url}")

    print("\nDownloading...")
    ok = 0
    fail = 0
    for owner, name, url in remote_dedup:
        try:
            filename = basename_from_url(url)
            dest = out_dir / filename
            status = download(url, dest, force=args.force, timeout=args.timeout)
            print(f"  ✅ {filename}: {status}")
            ok += 1
        except Exception as e:
            print(f"  ❌ {owner} / {name}: {url}\n     {type(e).__name__}: {e}")
            fail += 1

    print("\nDone.")
    print(f"Successful: {ok}")
    print(f"Failed:     {fail}")

    # Helpful reminder about your current local folder
    if (out_dir / "leafelet.awesome.rotate.min.css").exists() and not (out_dir / "leaflet.awesome.rotate.min.css").exists():
        print(
            "\n⚠️  Note: you have 'leafelet.awesome.rotate.min.css' (typo). "
            "If folium expects 'leaflet.awesome.rotate.min.css', rename it."
        )

    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())

