"""Base scraper abstract class - all scrapers must implement this interface."""

from abc import ABC, abstractmethod

from jcatch.core.models import MovieMetadata


class BaseScraper(ABC):
    """Abstract base class for metadata scrapers.

    Implement this class to add support for different data sources.
    """

    @abstractmethod
    def parse_number(self, filepath: str) -> str:
        """Extract movie number from file path.

        Args:
            filepath: Path to the video file

        Returns:
            Movie number (e.g., "FSDSS-549")

        Example:
            >>> scraper.parse_number("/path/to/FSDSS-549.mp4")
            "FSDSS-549"
        """
        pass

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

    @abstractmethod
    def download_image(self, url: str, save_path: str) -> None:
        """Download and save an image.

        Args:
            url: URL of the image
            save_path: File path where the image should be saved

        Raises:
            Exception: If download fails

        Example:
            >>> scraper.download_image(
            ...     "https://example.com/image.jpg",
            ...     "/output/FSDSS-549-poster.jpg"
            ... )
        """
        pass
