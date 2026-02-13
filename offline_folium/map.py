"""OfflineMap - A folium.Map that works without internet connection."""

from __future__ import annotations
import folium
from .rewrite import rewrite_tree_assets


class OfflineMap(folium.Map):
    """
    A drop-in replacement for folium.Map that uses locally downloaded assets.
    
    Usage:
        from offline_folium import OfflineMap
        
        m = OfflineMap(location=[45.5, -122.5], zoom_start=13)
        m.save("map.html")
    
    The map will automatically use local JS/CSS files if available,
    falling back to CDN URLs if files haven't been downloaded yet.
    """
    
    def render(self, **kwargs):
        """
        Render the map, rewriting all asset URLs to use local files.
        """
        # Rewrite this map and all its children/plugins to use local assets
        rewrite_tree_assets(self)
        
        # Call parent render
        return super().render(**kwargs)
