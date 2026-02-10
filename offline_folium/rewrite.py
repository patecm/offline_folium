from __future__ import annotations

from typing import Any, Iterable, Tuple

from .assets import resolve_url_to_local


AssetList = Iterable[Tuple[str, str]]


def _rewrite_asset_list(assets: Any) -> Any:
    """
    Rewrites a folium-style asset list: [(name, url), ...]
    Returns the same type (usually list).
    """
    if not isinstance(assets, (list, tuple)):
        return assets

    out = []
    changed = False
    for item in assets:
        if not (isinstance(item, (list, tuple)) and len(item) == 2):
            out.append(item)
            continue
        name, url = item
        local = resolve_url_to_local(url)
        if local:
            out.append((name, local))
            changed = True
        else:
            out.append((name, url))
    return out if changed else assets


def rewrite_element_assets(elem: Any) -> None:
    """
    In-place rewrite of an element's default_js/default_css if present.
    """
    if hasattr(elem, "default_js"):
        elem.default_js = _rewrite_asset_list(elem.default_js)
    if hasattr(elem, "default_css"):
        elem.default_css = _rewrite_asset_list(elem.default_css)


def rewrite_tree_assets(root: Any) -> None:
    """
    Walk folium element tree starting at root and rewrite assets everywhere.
    """
    seen = set()

    def walk(node: Any) -> None:
        node_id = id(node)
        if node_id in seen:
            return
        seen.add(node_id)

        rewrite_element_assets(node)

        children = getattr(node, "_children", None)
        if isinstance(children, dict):
            for child in children.values():
                walk(child)

    walk(root)
