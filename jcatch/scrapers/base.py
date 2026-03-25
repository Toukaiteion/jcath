"""Base scraper abstract class - all scrapers must implement this interface."""

from abc import ABC, abstractmethod

from jcatch.core.models import MovieMetadata


class BaseScraper(ABC):
    """Abstract base class for metadata scrapers.

    Implement this class to add support for different data sources.
    """

    @abstractmethod
    def fetch_metadata(self, number: str) -> MovieMetadata:
        """Fetch metadata for a given movie number.

        Args:
            number: Movie number (e.g., "FSDSS-549")

        Returns:
            Complete MovieMetadata object with all available information

        Raises:
            Exception: If metadata cannot be fetched

        Example:
            >>> metadata = scraper.fetch_metadata("FSDSS-549")
            >>> metadata.title
            "FSDSS-549-「上司からここに来るように言われました」..."
        """
        pass
