"""Poster decorator - override poster image from another scraper."""

from jcatch.core.models import MovieMetadata
from jcatch.scrapers.decorator import ScraperDecorator


class PosterDecorator(ScraperDecorator):
    """Decorator that replaces poster URL from a different scraper.

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
        poster_url = self._get_poster_url(number)
        if poster_url:
            metadata.poster_url = poster_url

        return metadata

    def _get_poster_url(self, number: str) -> str:
        """Get poster URL from the poster scraper.

        Args:
            number: Movie number

        Returns:
            Poster image URL or empty string if not available
        """
        # Try to call _get_poster_url on the poster_scraper
        if hasattr(self.poster_scraper, '_get_poster_url'):
            return self.poster_scraper._get_poster_url(number)

        # Alternative: fetch full metadata and extract poster
        if hasattr(self.poster_scraper, 'fetch_metadata'):
            metadata = self.poster_scraper.fetch_metadata(number)
            return metadata.poster_url

        return ""
