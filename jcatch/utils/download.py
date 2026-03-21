"""Image download utility."""

from pathlib import Path
import requests


def download_image(url: str, save_path: str | Path) -> None:
    """Download an image from URL and save to file.

    Args:
        url: URL of the image to download
        save_path: Path where the image should be saved

    Raises:
        Exception: If download fails
    """
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        save_path.write_bytes(response.content)
    except Exception as e:
        raise Exception(f"Failed to download {url}: {e}")
