"""Download assets for offline use."""

import sys
from pathlib import Path
from urllib.request import urlopen, Request
from typing import Dict, List, Set

import folium
import folium.plugins
from .paths import LOCAL_DIR


# Available plugins that can be downloaded
AVAILABLE_PLUGINS = {
    "heatmap": folium.plugins.HeatMap,
    "markercluster": folium.plugins.MarkerCluster,
    "draw": folium.plugins.Draw,
    "minimap": folium.plugins.MiniMap,
    "mouseposition": folium.plugins.MousePosition,
    "fullscreen": folium.plugins.Fullscreen,
    "beautifyicon": folium.plugins.BeautifyIcon,
}


def download_file(url: str, dest: Path) -> bool:
    """Download a single file from URL to destination."""
    try:
        # Use Request with headers to avoid 403 errors
        req = Request(url, headers={"User-Agent": "offline-folium/0.1.0"})
        
        print(f"  Downloading {dest.name}...")
        content = urlopen(req, timeout=30).read()
        
        dest.write_bytes(content)
        print(f"    ✓ Saved ({len(content)} bytes)")
        return True
        
    except Exception as e:
        print(f"    ✗ Failed: {e}")
        return False


def collect_urls_from_object(obj, label: str) -> Set[str]:
    """Collect remote URLs from a folium object's default_js and default_css."""
    urls = set()
    
    for _, url in getattr(obj, "default_js", []):
        if url.startswith(("http://", "https://")):
            urls.add(url)
    
    for _, url in getattr(obj, "default_css", []):
        if url.startswith(("http://", "https://")):
            urls.add(url)
    
    return urls


def collect_urls(plugins: List[str]) -> Dict[str, Set[str]]:
    """
    Collect all asset URLs organized by component.
    
    Args:
        plugins: List of plugin names to include (e.g., ["heatmap", "markercluster"])
    
    Returns:
        Dictionary mapping component name to set of URLs
    """
    collections = {}
    
    # Always include core Map assets
    collections["Map"] = collect_urls_from_object(folium.Map, "Map")
    
    # Add requested plugins
    for plugin_name in plugins:
        plugin_name_lower = plugin_name.lower()
        if plugin_name_lower not in AVAILABLE_PLUGINS:
            print(f"Warning: Unknown plugin '{plugin_name}'. Available: {', '.join(AVAILABLE_PLUGINS.keys())}")
            continue
        
        plugin_class = AVAILABLE_PLUGINS[plugin_name_lower]
        urls = collect_urls_from_object(plugin_class, plugin_name)
        if urls:
            collections[plugin_name] = urls
    
    return collections


def download_assets(plugins: List[str], force: bool = False) -> None:
    """
    Download all required assets for offline use.
    
    Args:
        plugins: List of plugin names to download (e.g., ["heatmap"])
        force: Overwrite existing files (default: False)
    """
    print("=" * 60)
    print("Offline Folium Asset Downloader")
    print("=" * 60)
    print(f"Download location: {LOCAL_DIR}")
    print()
    
    # Ensure directory exists
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    
    # Collect URLs by component
    collections = collect_urls(plugins)
    
    if not collections:
        print("No components selected. Nothing to download.")
        return
    
    # Show what we're downloading
    total_urls = sum(len(urls) for urls in collections.values())
    print(f"Components to download:")
    for component, urls in collections.items():
        print(f"  • {component}: {len(urls)} asset{'s' if len(urls) != 1 else ''}")
    print(f"\nTotal: {total_urls} unique assets")
    print()
    
    # Track results
    success = 0
    skipped = 0
    failed = 0
    failed_urls = []
    
    # Download each component's assets
    for component, urls in collections.items():
        if urls:
            print(f"Downloading {component} assets:")
            for url in sorted(urls):
                filename = url.split("?")[0].rsplit("/", 1)[-1]
                dest = LOCAL_DIR / filename
                
                # Skip if exists and not forcing
                if dest.exists() and not force:
                    print(f"  ✓ {filename} (already exists)")
                    skipped += 1
                    continue
                
                if download_file(url, dest):
                    success += 1
                else:
                    failed += 1
                    failed_urls.append(url)
            print()
    
    # Summary
    print("=" * 60)
    print("Summary:")
    print(f"  ✓ Downloaded: {success}")
    print(f"  → Skipped:    {skipped}")
    print(f"  ✗ Failed:     {failed}")
    print("=" * 60)
    
    if failed > 0:
        print("\n⚠️  Some downloads failed:")
        for url in failed_urls:
            print(f"  • {url}")
        print("\nTry running again or check your internet connection.")
        sys.exit(1)
    
    if success > 0 or skipped > 0:
        print("\n✅ Ready for offline use!")
        print("   You can now use OfflineMap without internet connection.")


def main():
    """CLI entry point for python -m offline_folium"""
    args = sys.argv[1:]
    
    if "--help" in args or "-h" in args:
        print("Usage: python -m offline_folium [PLUGINS...] [OPTIONS]")
        print()
        print("Download folium assets for offline use.")
        print()
        print("Plugins:")
        for name in sorted(AVAILABLE_PLUGINS.keys()):
            print(f"  {name}")
        print()
        print("Options:")
        print("  --force, -f    Overwrite existing files")
        print("  --all          Download all available plugins")
        print("  --help, -h     Show this help")
        print()
        print("Examples:")
        print("  python -m offline_folium heatmap")
        print("  python -m offline_folium heatmap markercluster")
        print("  python -m offline_folium --all")
        print("  python -m offline_folium heatmap --force")
        return
    
    # Parse arguments
    force = "--force" in args or "-f" in args
    download_all = "--all" in args
    
    # Get plugin list
    if download_all:
        plugins = list(AVAILABLE_PLUGINS.keys())
    else:
        plugins = [arg for arg in args if not arg.startswith("-")]
    
    # Default to heatmap if nothing specified
    if not plugins:
        plugins = ["heatmap"]
        print("No plugins specified, defaulting to: heatmap")
        print("(Use --help to see all available plugins)\n")
    
    download_assets(plugins=plugins, force=force)


if __name__ == "__main__":
    main()
