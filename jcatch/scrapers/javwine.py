"""JavWine scraper for poster images."""

from bs4 import BeautifulSoup
import requests

from jcatch.core.models import ImageUrl
from jcatch.scrapers.base import BaseScraper


class JavWineScraper(BaseScraper):
    """Scraper for jav.wine website to get poster images."""

    BASE_URL = "https://jav.wine"

    def parse_number(self, filepath: str) -> str:
        """Extract movie number and convert to uppercase.

        Args:
            filepath: Path to video file

        Returns:
            Movie number in uppercase (e.g., "FSDSS-549")
        """
        from pathlib import Path
        number = Path(filepath).stem
        return number.upper()

    def fetch_metadata(self, number: str):
        """This scraper only provides poster images, not full metadata."""
        raise NotImplementedError("Use _get_poster() method instead of fetch_metadata()")

    def _get_poster(self, number: str) -> ImageUrl:
        """Get poster image URL from jav.wine.

        Args:
            number: Movie number (e.g., "FSDSS-549")

        Returns:
            ImageUrl object with URL and empty headers
        """
        url = f"{self.BASE_URL}/{number.lower()}"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")

            # Find image in .likes div
            likes_div = soup.select_one(".likes img")
            if likes_div and likes_div.get("src"):
                img_url = likes_div["src"]
                # Convert relative URL to absolute
                if img_url.startswith("/"):
                    img_url = f"{self.BASE_URL}{img_url}"
                return ImageUrl(url=img_url, headers={})

            return ImageUrl(url="")

        except Exception as e:
            print(f"Failed to get poster from jav.wine: {e}")
            return ImageUrl(url="")
