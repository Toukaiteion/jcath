"""Example scraper implementation - placeholder for actual implementation.

This is a placeholder showing how to implement a concrete scraper.
You will need to implement the actual scraping logic based on the target website.
"""

from jcatch.scrapers.base import BaseScraper
from jcatch.core.models import MovieMetadata
from jcatch.utils import extract_number_from_path, download_image


class Jav321Scraper(BaseScraper):
    """Example scraper for jav321.com.

    NOTE: This is a placeholder. Actual implementation needs to be added
    based on the website's structure and your specific requirements.
    """

    def parse_number(self, filepath: str) -> str:
        """Extract movie number from file path."""
        return extract_number_from_path(filepath)

    def fetch_metadata(self, number: str) -> MovieMetadata:
        """Fetch metadata for a given movie number.

        TODO: Implement actual scraping logic here.
        You may need to:
        1. Construct the URL (e.g., https://www.jav321.com/video/{number})
        2. Fetch and parse the HTML
        3. Extract all metadata fields
        4. Return MovieMetadata object
        """
        # Placeholder - return minimal metadata
        return MovieMetadata(
            num=number,
            title=f"Placeholder title for {number}",
            customrating="JP-18+",
            mpaa="JP-18+",
        )

    def download_image(self, url: str, save_path: str) -> None:
        """Download and save an image."""
        download_image(url, save_path)
