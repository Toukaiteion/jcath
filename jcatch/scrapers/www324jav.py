"""Www324Jav scraper for poster images."""

from bs4 import BeautifulSoup
import requests

from jcatch.core.models import ImageUrl
from jcatch.scrapers.base import BaseScraper


class Www324JavScraper(BaseScraper):
    """Scraper for www3.24-jav.com to get poster images."""

    BASE_URL = "https://www3.24-jav.com"

    def parse_number(self, filepath: str) -> str:
        """Extract movie number and convert to uppercase.

        Args:
            filepath: Path to video file

        Returns:
            Movie number in uppercase (e.g., "ADN-683")
        """
        from pathlib import Path
        number = Path(filepath).stem
        return number.upper()

    def fetch_metadata(self, number: str):
        """This scraper only provides poster images, not full metadata."""
        raise NotImplementedError("Use _get_poster() method instead of fetch_metadata()")

    def _get_poster(self, number: str) -> ImageUrl:
        """Get poster image URL from www3.24-jav.com.

        Args:
            number: Movie number (e.g., "ADN-683")

        Returns:
            ImageUrl object with URL and empty headers
        """
        url = f"{self.BASE_URL}/{number.lower()}"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")

            # Find image in .limage div
            limage_div = soup.select_one(".limage img")
            if limage_div and limage_div.get("src"):
                img_url = limage_div["src"]
                # Convert relative URL to absolute
                if img_url.startswith("/"):
                    img_url = f"{self.BASE_URL}{img_url}"
                return ImageUrl(url=img_url, headers={})

            return ImageUrl(url="")

        except Exception as e:
            print(f"Failed to get poster from www3.24-jav.com: {e}")
            return ImageUrl(url="")
