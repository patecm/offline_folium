from importlib import resources
from pathlib import Path


def get_dest_path() -> Path:
    """
    Robust replacement for pkg_resources.resource_filename().
    Works for editable installs and normal installs.
    """
    # Primary: correct modern way
    pkg_path = Path(resources.files("offline_folium") / "local")
    if pkg_path.exists():
        return pkg_path

    # Fallback: repo-layout editable install edge case
    repo_fallback = Path(__file__).resolve().parent / "local"
    if repo_fallback.exists():
        return repo_fallback

    raise FileNotFoundError(
        "Could not locate 'offline_folium/local' directory in package or repo."
    )

#dest_path = resources.files("offline_folium").joinpath("local")

dest_path = get_dest_path()

