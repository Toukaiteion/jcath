"""Fanart decorator - override fanart/thumb images from another scraper."""

from jcatch.core.models import MovieMetadata
from jcatch.scrapers.decorator import ScraperDecorator


class FanartDecorator(ScraperDecorator):
    """Decorator that replaces fanart/thumb URLs from a different scraper.

    Example:
        # Get metadata from JavBus, but fanart from DMM
        base = JavBusScraper()
        scraper = FanartDecorator(base, DMMScraper())
    """

    def __init__(self, wrapped, fanart_scraper):
        """Initialize with wrapped scraper and fanart scraper.

        Args:
            wrapped: Base scraper for metadata
            fanart_scraper: Scraper that provides fanart URLs
        """
        super().__init__(wrapped)
        self.fanart_scraper = fanart_scraper

    def fetch_metadata(self, number: str) -> MovieMetadata:
        """Fetch metadata and replace fanart URLs."""
        metadata = self.wrapped.fetch_metadata(number)

        # Replace fanart URLs from fanart_scraper
        # Fanart scraper should have _get_fanart_url(number) method
        fanart_url = self._get_fanart_url(number)
        if fanart_url:
            metadata.fanart_url = fanart_url
            metadata.thumb_url = fanart_url  # thumb usually same as fanart

        return metadata

    def _get_fanart_url(self, number: str) -> str:
        """Get fanart URL from the fanart scraper.

        Args:
            number: Movie number

        Returns:
            Fanart image URL or empty string if not available
        """
        # Try to call _get_fanart_url on the fanart_scraper
        # If it doesn't exist, return empty string
        if hasattr(self.fanart_scraper, '_get_fanart_url'):
            return self.fanart_scraper._get_fanart_url(number)

        # Alternative: fetch full metadata and extract fanart
        if hasattr(self.fanart_scraper, 'fetch_metadata'):
            metadata = self.fanart_scraper.fetch_metadata(number)
            return metadata.fanart_url

        return ""
