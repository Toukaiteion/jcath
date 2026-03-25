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

    def fetch_metadata(self, number, jav_key: str | None = None):
        """Fetch metadata (delegated to wrapped by default)."""
        return self.wrapped.fetch_metadata(number)

    def __getattr__(self, name):
        """Delegate any other attributes to wrapped scraper."""
        return getattr(self.wrapped, name)
