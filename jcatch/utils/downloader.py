"""Unified image downloader with header support."""

from pathlib import Path
from typing import Union

import requests

from jcatch.core.models import ImageUrl


class ImageDownloader:
    """Unified image downloader that handles headers."""

    @staticmethod
    def download(image: ImageUrl, save_path: Union[str, Path]) -> None:
        """Download an image with headers.

        Args:
            image: ImageUrl object with URL and headers
            save_path: Path where image should be saved

        Raises:
            Exception: If download fails
        """
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            response = requests.get(image.url, headers=image.headers, timeout=30)
            response.raise_for_status()
            save_path.write_bytes(response.content)
        except Exception as e:
            raise Exception(f"Failed to download {image.url}: {e}")
