"""Fanart decorator - override fanart/thumb images from another scraper."""

from jcatch.core.models import ImageUrl, MovieMetadata
from jcatch.scrapers.decorators.base_decorator import ScraperDecorator


class FanartDecorator(ScraperDecorator):
    """Decorator that replaces fanart/thumb from a different scraper.

    With chain retry: if fanart_scraper returns empty, print log
    and the next decorator will retry with its own scraper.

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
        """Get fanart URL from fanart scraper.

        Args:
            number: Movie number

        Returns:
            ImageUrl object with URL and headers
        """
        # First try: call fanart_scraper
        result = self._call_fanart_scraper(number)

        # Chain retry: if empty, print log and note for retry
        if not result.url:
            print(f"[{self.__class__.__name__}] Fanart empty, next decorator should retry")

        return result

    def _call_fanart_scraper(self, number: str) -> ImageUrl:
        """Call fanart scraper and return result.

        Allows catching and logging of any errors.
        """
        try:
            # Try to call _get_fanart on fanart_scraper
            if hasattr(self.fanart_scraper, '_get_fanart'):
                return self.fanart_scraper._get_fanart(number)

            # Alternative: fetch full metadata and extract fanart
            if hasattr(self.fanart_scraper, 'fetch_metadata'):
                metadata = self.fanart_scraper.fetch_metadata(number)
                return metadata.fanart
        except Exception as e:
            print(f"[{self.__class__.__name__}] Fanart scraper error: {e}")
            return ImageUrl(url="")
