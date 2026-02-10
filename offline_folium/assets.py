from __future__ import annotations

from importlib import resources
from pathlib import Path
from typing import Dict, Optional


def local_dir() -> Path:
    """
    Returns a real filesystem path to offline_folium/local.

    Works for normal installs and editable installs when files are present.
    If you later need true zip-safety, we can add resources.as_file() wrapping,
    but for local-repo installs this is enough.
    """
    p = resources.files("offline_folium").joinpath("local")
    # p can be Traversable; cast through Path if it's already a filesystem path-like
    return Path(str(p))


def local_file(filename: str) -> str:
    return str(local_dir() / filename)


# Canonical mapping: CDN/remote URLs -> local filenames
# Keep keys as "basename" OR full URL; support both.
URL_MAP: Dict[str, str] = {
    # Leaflet (examples; match whatever folium ships in your version)
    "leaflet.js": "leaflet.js",
    "leaflet.css": "leaflet.css",

    # Common plugin assets you bundle:
    "leaflet.awesome-markers.js": "leaflet.awesome-markers.js",
    "leaflet.awesome-markers.css": "leaflet.awesome-markers.css",
    # Add others as needed...
}


def resolve_url_to_local(url: str) -> Optional[str]:
    """
    Given a URL from folium/plugin default_js/default_css, return the local path
    if we have it, else None.
    """
    basename = url.rsplit("/", 1)[-1]
    if url in URL_MAP:
        return local_file(URL_MAP[url])
    if basename in URL_MAP:
        return local_file(URL_MAP[basename])
    return None
