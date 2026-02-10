from __future__ import annotations

import folium

from .rewrite import rewrite_tree_assets


class OfflineMap(folium.Map):
    """
    A folium.Map that rewrites JS/CSS asset URLs to local package files
    at render time. No global monkey patching.
    """

    def render(self, **kwargs):
        # Ensure *this map and all children/plugins* use local assets
        rewrite_tree_assets(self)
        return super().render(**kwargs)
