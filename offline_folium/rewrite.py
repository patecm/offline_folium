"""Asset rewriting - converts remote URLs to local paths in folium elements."""

from typing import Any
from .assets import resolve_url_to_local


def rewrite_asset_list(assets: Any) -> Any:
    """
    Rewrites a folium asset list from [(name, url), ...] format.
    Replaces remote URLs with local paths where available.
    """
    if not isinstance(assets, (list, tuple)):
        return assets
    
    rewritten = []
    for item in assets:
        # Each item should be (name, url) tuple
        if not (isinstance(item, (list, tuple)) and len(item) == 2):
            rewritten.append(item)
            continue
        
        name, url = item
        local_path = resolve_url_to_local(url)
        
        if local_path:
            rewritten.append((name, local_path))
        else:
            rewritten.append((name, url))
    
    return rewritten


def rewrite_element_assets(element: Any) -> None:
    """
    Rewrites default_js and default_css attributes of a folium element in-place.
    """
    if hasattr(element, "default_js"):
        element.default_js = rewrite_asset_list(element.default_js)
    
    if hasattr(element, "default_css"):
        element.default_css = rewrite_asset_list(element.default_css)


def rewrite_tree_assets(root: Any) -> None:
    """
    Recursively walks a folium element tree and rewrites all assets to use local files.
    
    This handles the map itself plus all child elements (markers, plugins, etc.)
    """
    visited = set()
    
    def walk(node: Any) -> None:
        node_id = id(node)
        if node_id in visited:
            return
        visited.add(node_id)
        
        # Rewrite this node's assets
        rewrite_element_assets(node)
        
        # Recursively handle children
        children = getattr(node, "_children", None)
        if isinstance(children, dict):
            for child in children.values():
                walk(child)
    
    walk(root)
