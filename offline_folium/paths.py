"""Path utilities for locating the local assets directory."""

from importlib import resources
from pathlib import Path


def get_local_dir() -> Path:
    """
    Returns the path to offline_folium/local directory.
    Works for both normal and editable installs.
    """
    # Modern approach using importlib.resources
    try:
        pkg_files = resources.files("offline_folium")
        local_path = Path(str(pkg_files / "local"))
        
        # For editable installs, this will be the actual repo path
        if local_path.exists():
            return local_path
            
        # Create it if it doesn't exist (first time use)
        local_path.mkdir(parents=True, exist_ok=True)
        return local_path
        
    except Exception:
        # Fallback for edge cases
        fallback = Path(__file__).resolve().parent / "local"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


LOCAL_DIR = get_local_dir()
