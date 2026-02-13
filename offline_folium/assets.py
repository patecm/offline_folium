"""Asset URL resolution - maps remote URLs to local files."""

from pathlib import Path
from typing import Optional
from .paths import LOCAL_DIR


def resolve_url_to_local(url: str) -> Optional[str]:
    """
    Given a remote URL, return the local file path if we have it downloaded.
    
    Args:
        url: Remote URL (e.g., https://cdn.../leaflet.js)
        
    Returns:
        Local file path if it exists, None otherwise
    """
    if not url.startswith(("http://", "https://")):
        # Already a local path or data URI
        return None
    
    # Extract filename from URL (handles query strings)
    filename = url.split("?")[0].rsplit("/", 1)[-1]
    
    if not filename:
        return None
    
    local_file = LOCAL_DIR / filename
    
    # Only return if file actually exists
    if local_file.exists():
        return str(local_file)
    
    return None
