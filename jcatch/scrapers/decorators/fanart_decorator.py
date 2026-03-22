"""Fanart decorator - override fanart/thumb images from another scraper."""

from jcatch.core.models import ImageUrl, MovieMetadata
from jcatch.scrapers.decorators.base_decorator import ScraperDecorator


class FanartDecorator(ScraperDecorator):
    """Decorator that replaces fanart/thumb from a different scraper.

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
        fanart = self._get_fanart(number)
        if fanart.url:
            metadata.fanart = fanart
            metadata.thumb = fanart

        return metadata

    def _get_fanart(self, number: str) -> ImageUrl:
        """Get fanart URL from the fanart scraper.

        Args:
            number: Movie number

        Returns:
            ImageUrl object with URL and headers
        """
        # Try to call _get_fanart on the fanart_scraper
        if hasattr(self.fanart_scraper, '_get_fanart'):
            return self.fanart_scraper._get_fanart(number)

        # Alternative: fetch full metadata and extract fanart
        if hasattr(self.fanart_scraper, 'fetch_metadata'):
            metadata = self.fanart_scraper.fetch_metadata(number)
            return metadata.fanart

        return ImageUrl(url="")
