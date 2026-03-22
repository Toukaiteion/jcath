"""Scraper decorator base class for composing scrapers."""

from jcatch.scrapers.base import BaseScraper


class ScraperDecorator(BaseScraper):
    """Base class for scraper decorators.

    Wraps a BaseScraper and allows composition of different scrapers
    for different purposes (e.g., metadata from one, images from another).

    Subclasses should override specific methods to add or modify behavior.
    """

    def __init__(self, wrapped: BaseScraper):
        """Initialize decorator with wrapped scraper.

        Args:
            wrapped: The scraper to wrap/decorate
        """
        self.wrapped = wrapped

    def parse_number(self, filepath: str) -> str:
        """Parse movie number from file path (delegated to wrapped)."""
        return self.wrapped.parse_number(filepath)

    def fetch_metadata(self, number: str):
        """Fetch metadata (delegated to wrapped by default)."""
        return self.wrapped.fetch_metadata(number)

    def download_image(self, url: str, save_path: str) -> None:
        """Download image (delegated to wrapped by default)."""
        return self.wrapped.download_image(url, save_path)

    def __getattr__(self, name):
        """Delegate any other attributes to wrapped scraper."""
        return getattr(self.wrapped, name)
