"""Metadata decorator - merge metadata from backup scraper when fields are empty."""

from jcatch.core.models import MovieMetadata
from jcatch.scrapers.decorators.base_decorator import ScraperDecorator


class MetadataDecorator(ScraperDecorator):
    """Decorator that merges metadata from backup scraper when fields are empty.

    Checks title, studio, year, outline, genres, actors for empty values.
    If any are empty, fetches from backup_scraper and fills in the missing fields.

    Example:
        # Use JavBus as primary, MissAvWs as backup for empty fields
        base = JavBusScraper()
        scraper = MetadataDecorator(base, MissAvWsScraper())
    """

    def __init__(self, wrapped, backup_scraper):
        """Initialize with wrapped scraper and backup scraper.

        Args:
            wrapped: Primary scraper for metadata
            backup_scraper: Backup scraper to fill empty fields
        """
        super().__init__(wrapped)
        self.backup_scraper = backup_scraper

    def fetch_metadata(self, number: str) -> MovieMetadata:
        """Fetch metadata and merge from backup if fields are empty."""
        metadata = self.wrapped.fetch_metadata(number)

        # Check if any key fields are empty
        if self._needs_backup(metadata):
            print(f"[{self.__class__.__name__}] Some fields empty, fetching from backup")
            backup_metadata = self._fetch_backup(number)
            metadata = self._merge_metadata(metadata, backup_metadata)

        return metadata

    def _needs_backup(self, metadata: MovieMetadata) -> bool:
        """Check if any key fields are empty.

        Returns:
            True if title, studio, year, outline, genres, or actors is empty
        """
        return (
            not metadata.title
            or not metadata.studio
            or metadata.year == 0
            or not metadata.outline
            or len(metadata.genres) == 0
            or len(metadata.actors) == 0
        )

    def _fetch_backup(self, number: str) -> MovieMetadata:
        """Fetch metadata from backup scraper.

        Returns empty metadata if fetch fails.
        """
        try:
            return self.backup_scraper.fetch_metadata(number)
        except Exception as e:
            print(f"[{self.__class__.__name__}] Backup scraper error: {e}")
            return MovieMetadata()

    def _merge_metadata(
        self, primary: MovieMetadata, backup: MovieMetadata
    ) -> MovieMetadata:
        """Merge backup metadata into primary, filling empty fields.

        Args:
            primary: Primary metadata (keep existing values)
            backup: Backup metadata (use for empty fields)

        Returns:
            Merged metadata with empty fields filled from backup
        """
        # Use pydantic's model_copy with update to merge
        return primary.model_copy(
            update={
                # Only fill if primary is empty
                "title": backup.title if not primary.title else primary.title,
                "originaltitle": (
                    backup.originaltitle if not primary.originaltitle else primary.originaltitle
                ),
                "sorttitle": (
                    backup.sorttitle if not primary.sorttitle else primary.sorttitle
                ),
                "studio": backup.studio if not primary.studio else primary.studio,
                "maker": backup.maker if not primary.maker else primary.maker,
                "year": backup.year if primary.year == 0 else primary.year,
                "outline": backup.outline if not primary.outline else primary.outline,
                "plot": backup.plot if not primary.plot else primary.plot,
                "director": (
                    backup.director if not primary.director else primary.director
                ),
                "label": backup.label if not primary.label else primary.label,
                "release": backup.release if not primary.release else primary.release,
                "releasedate": (
                    backup.releasedate if not primary.releasedate else primary.releasedate
                ),
                "premiered": (
                    backup.premiered if not primary.premiered else primary.premiered
                ),
                # Merge lists: keep primary if non-empty, use backup otherwise
                "actors": backup.actors if len(primary.actors) == 0 else primary.actors,
                "genres": backup.genres if len(primary.genres) == 0 else primary.genres,
                "tags": backup.tags if len(primary.tags) == 0 else primary.tags,
            }
        )
