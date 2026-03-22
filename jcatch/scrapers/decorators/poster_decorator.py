"""Poster decorator - override poster image from another scraper."""

from jcatch.core.models import ImageUrl, MovieMetadata
from jcatch.scrapers.decorators.base_decorator import ScraperDecorator


class PosterDecorator(ScraperDecorator):
    """Decorator that replaces poster URL from a different scraper.

    With chain retry: if poster_scraper returns empty (or previous
    decorator returned empty), retry with own scraper.

    Example:
        # Get metadata from JavBus, but poster from Jav321
        base = JavBusScraper()
        scraper = PosterDecorator(base, Jav321Scraper())
    """

    def __init__(self, wrapped, poster_scraper):
        """Initialize with wrapped scraper and poster scraper.

        Args:
            wrapped: Base scraper for metadata
            poster_scraper: Scraper that provides poster URLs
        """
        super().__init__(wrapped)
        self.poster_scraper = poster_scraper

    def fetch_metadata(self, number: str) -> MovieMetadata:
        """Fetch metadata and replace poster URL."""
        metadata = self.wrapped.fetch_metadata(number)

        # Replace poster URL from poster_scraper
        poster = self._get_poster(number, metadata)
        if poster.url:
            metadata.poster = poster

        return metadata

    def _get_poster(self, number: str, wrapper_metadata: MovieMetadata) -> ImageUrl:
        """Get poster URL from poster scraper.

        Args:
            number: Movie number

        Returns:
            ImageUrl object with URL and headers
        """

        # If wrapped poster is empty or invalid, retry with own scraper
        if not wrapper_metadata.poster or not wrapper_metadata.poster.url:
            print(f"[{self.__class__.__name__}] Poster empty, retrying with own scraper")
            return self._call_poster_scraper(number)

        return wrapper_metadata.poster

    def _call_poster_scraper(self, number: str) -> ImageUrl:
        """Call poster scraper and return result.

        Allows catching and logging of any errors.
        """
        try:
            # Try to call _get_poster on poster_scraper
            if hasattr(self.poster_scraper, '_get_poster'):
                return self.poster_scraper._get_poster(number)

            # Alternative: fetch full metadata and extract poster
            if hasattr(self.poster_scraper, 'fetch_metadata'):
                metadata = self.poster_scraper.fetch_metadata(number)
                return metadata.poster
        except Exception as e:
            print(f"[{self.__class__.__name__}] Poster scraper error: {e}")
            return ImageUrl(url="")
