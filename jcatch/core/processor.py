"""Main media processor that orchestrates the workflow."""

from pathlib import Path
import shutil

from jcatch.scrapers.base import BaseScraper
from jcatch.core.models import MovieMetadata
from jcatch.core.nfo import generate_nfo
from jcatch.utils.downloader import ImageDownloader


class MediaProcessor:
    """Process video files and generate complete media directory structure."""

    def __init__(self, scraper: BaseScraper):
        """Initialize processor with a scraper instance.

        Args:
            scraper: Scraper instance for fetching metadata and images
        """
        self.scraper = scraper

    def process(self, video_path: str, output_dir: str = "output") -> str:
        """Process a video file and generate complete directory structure.

        Args:
            video_path: Path to the input video file
            output_dir: Base directory for output (default: "output")

        Returns:
            Path to the generated output directory

        Raises:
            FileNotFoundError: If video file doesn't exist
            Exception: If processing fails
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # 1. Extract movie number from file path
        number = self.scraper.parse_number(str(video_path))
        if not number:
            raise ValueError(f"Could not extract movie number from: {video_path}")

        # 2. Fetch metadata from scraper
        metadata = self.scraper.fetch_metadata(number)

        # 3. Create output directory
        output_path = Path(output_dir) / number
        output_path.mkdir(parents=True, exist_ok=True)

        # 4. Copy video file
        self._copy_video(video_path, output_path, number)

        # 5. Download and save images
        self._download_images(metadata, output_path, number)

        # 6. Generate NFO file
        self._generate_nfo(metadata, output_path, number)

        return str(output_path)

    def _copy_video(self, video_path: Path, output_dir: Path, number: str) -> None:
        """Copy video file to output directory.

        Args:
            video_path: Source video file path
            output_dir: Target directory
            number: Movie number for filename
        """
        output_file = output_dir / f"{number}.mp4"
        shutil.copy2(video_path, output_file)

    def _download_images(self, metadata: MovieMetadata, output_dir: Path, number: str) -> None:
        """Download all images and save to output directory.

        Args:
            metadata: Movie metadata containing image URLs
            output_dir: Target directory
            number: Movie number for filenames
        """
        # Main images
        if metadata.poster.url:
            ImageDownloader.download(metadata.poster, output_dir / f"{number}-poster.jpg")

        if metadata.thumb.url:
            ImageDownloader.download(metadata.thumb, output_dir / f"{number}-thumb.jpg")

        if metadata.fanart.url:
            ImageDownloader.download(metadata.fanart, output_dir / f"{number}-fanart.jpg")

        # Extra fanart screenshots
        if metadata.extrafanart:
            extra_dir = output_dir / "extrafanart"
            extra_dir.mkdir(exist_ok=True)

            for i, image in enumerate(metadata.extrafanart, start=1):
                ImageDownloader.download(image, extra_dir / f"extrafanart-{i}.jpg")

    def _generate_nfo(self, metadata: MovieMetadata, output_dir: Path, number: str) -> None:
        """Generate NFO file.

        Args:
            metadata: Movie metadata
            output_dir: Target directory
            number: Movie number for filename
        """
        nfo_content = generate_nfo(metadata)
        nfo_path = output_dir / f"{number}.nfo"
        nfo_path.write_text(nfo_content, encoding="utf-8")
