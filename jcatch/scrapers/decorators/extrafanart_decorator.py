"""ExtraFanart decorator - override extrafanart/screenshot images from another scraper."""

from jcatch.core.models import ImageUrl, MovieMetadata
from jcatch.scrapers.decorators.base_decorator import ScraperDecorator
from jcatch.utils.logger import setup_logger

logger = setup_logger(__name__)


class ExtraFanartDecorator(ScraperDecorator):
    """Decorator that replaces extrafanart/screenshot images from a different scraper.

    With chain retry: if extrafanart_scraper returns empty list, print log
    and the next decorator will retry with its own scraper.

    Example:
        # Get metadata from JavBus, but screenshots from JavTrailers
        base = JavBusScraper()
        scraper = ExtraFanartDecorator(base, JavTrailersScraper())
    """

    def __init__(self, wrapped, extrafanart_scraper):
        """Initialize with wrapped scraper and extrafanart scraper.

        Args:
            wrapped: Base scraper for metadata
            extrafanart_scraper: Scraper that provides extrafanart URLs
        """
        super().__init__(wrapped)
        self.extrafanart_scraper = extrafanart_scraper

    def fetch_metadata(self, number: str) -> MovieMetadata:
        """Fetch metadata and replace extrafanart URLs."""
        metadata = self.wrapped.fetch_metadata(number)

        # Replace extrafanart URLs from extrafanart_scraper
        extrafanart = self._get_extrafanart(number)
        if extrafanart:
            metadata.extrafanart = extrafanart

        return metadata

    def _get_extrafanart(self, number: str) -> list[ImageUrl]:
        """Get extrafanart URLs from extrafanart scraper.

        Args:
            number: Movie number

        Returns:
            List of ImageUrl objects with URLs and headers
        """
        # First try: call extrafanart_scraper
        result = self._call_extrafanart_scraper(number)

        # Chain retry: if empty, log and note for retry
        if not result:
            logger.debug(f"{self.__class__.__name__} ExtraFanart 为空, 下一个装饰器重试")

        return result

    def _call_extrafanart_scraper(self, number: str) -> list[ImageUrl]:
        """Call extrafanart scraper and return result.

        Allows catching and logging of any errors.
        """
        try:
            # Try to call fetch_metadata on extrafanart_scraper
            if hasattr(self.extrafanart_scraper, 'fetch_metadata'):
                metadata = self.extrafanart_scraper.fetch_metadata(number)
                return metadata.extrafanart
        except Exception as e:
            logger.error(f"{self.__class__.__name__} ExtraFanart 搜刮器错误: {e}")
            return []