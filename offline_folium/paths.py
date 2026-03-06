"""Path utilities for locating the local assets directory."""

from importlib import resources
from pathlib import Path

def get_local_dir() -> Path:
    """
    Returns the path to offline_folium/local directory.
    Works for both normal and editable installs.
    """
    # Always use the source directory approach
    # This file is in offline_folium/paths.py
    # So local directory is offline_folium/local
    local_path = Path(__file__).resolve().parent / "local"
    
    # Create it if it doesn't exist
    local_path.mkdir(parents=True, exist_ok=True)
    
    return local_path

LOCAL_DIR = get_local_dir()
