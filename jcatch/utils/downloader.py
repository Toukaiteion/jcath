"""Unified image downloader with header support."""

from pathlib import Path
from typing import Union
import time

import requests

from jcatch.core.models import ImageUrl


class ImageDownloader:
    """Unified image downloader with retry and cache support."""

    # Class-level cache: {url: bytes}
    _cache: dict[str, bytes] = {}

    @staticmethod
    def download(image: ImageUrl, save_path: Union[str, Path], max_retries: int = 3) -> None:
        """Download an image with retry and cache.

        Args:
            image: ImageUrl object with URL and headers
            save_path: Path where image should be saved
            max_retries: Maximum retry attempts (default: 3)

        Raises:
            Exception: If download fails after all retries
        """
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # Check cache first
        if image.url in ImageDownloader._cache:
            print(f"[缓存命中] {save_path.name}")
            save_path.write_bytes(ImageDownloader._cache[image.url])
            return

        # Download with retry
        last_error = None
        for attempt in range(max_retries):
            try:
                response = requests.get(image.url, headers=image.headers, timeout=30)
                response.raise_for_status()
                content = response.content

                # Save to cache
                ImageDownloader._cache[image.url] = content

                # Write to file
                save_path.write_bytes(content)
                print(f"[下载成功] {save_path.name}")
                return
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    delay = 2 ** attempt
                    print(f"[重试 {attempt + 1}/{max_retries}] {save_path.name}, 延迟 {delay}s")
                    time.sleep(delay)

        # All retries failed
        raise Exception(f"Failed to download {image.url} after {max_retries} attempts: {last_error}")

    @classmethod
    def clear_cache(cls) -> None:
        """Clear in-memory cache."""
        cls._cache.clear()
        print("[缓存已清空]")
