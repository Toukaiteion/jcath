"""Plugin-mode media processor with standardized JSON input/output."""

import json
import random
import shutil
import sys
import time
from pathlib import Path
from typing import Any

from PIL import Image
from xml.etree import ElementTree as ET

from jcatch.core.models import MovieMetadata
from jcatch.core.nfo import generate_nfo
from jcatch.scrapers.base import BaseScraper
from jcatch.utils.downloader import ImageDownloader
from jcatch.utils.file import extract_number_from_path


class PluginMediaProcessor:
    """Process video files in plugin mode with standardized JSON I/O.

    Plugin mode communication:
    - Input: JSON via stdin
    - Output: JSON via stdout
    - Progress: JSON lines via stderr
    - Exit codes: 0 for success, non-zero for failure
    """

    def __init__(self, scraper: BaseScraper):
        """Initialize processor with a scraper instance.

        Args:
            scraper: Scraper instance for fetching metadata and images
        """
        self.scraper = scraper
        self.api_requests = 0  # Track API requests for statistics

    def run(self) -> None:
        """Main entry point for plugin mode.

        Reads JSON input from stdin, processes, and writes JSON output to stdout.
        Progress notifications are sent to stderr as JSON lines.
        Returns 0 on success, 1 on failure.
        """
        start_time = time.time()

        try:
            # 1. Read input from stdin
            input_data = self._read_input()

            self._emit_progress("initializing", "Initializing plugin...", 0)

            # 2. Process the request
            result = self._process_request(input_data, start_time)

            # 3. Write output to stdout
            self._write_output(result)

            sys.exit(0)  # Success

        except Exception as e:
            self._write_error(str(e))
            sys.exit(1)  # Failure

    def _read_input(self) -> dict[str, Any]:
        """Read JSON input from stdin.

        Returns:
            Parsed JSON input dictionary

        Raises:
            ValueError: If input is invalid JSON
        """
        try:
            raw_input = sys.stdin.read().strip()
            if not raw_input:
                raise ValueError("No input provided")

            data = json.loads(raw_input)

            # Validate required fields
            if "action" not in data:
                raise ValueError("Missing required field: action")
            if "source_dir" not in data:
                raise ValueError("Missing required field: source_dir")

            return data

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON input: {e}") from e

    def _process_request(self, input_data: dict[str, Any], start_time: float) -> dict[str, Any]:
        """Process a plugin request.

        Args:
            input_data: Parsed JSON input
            start_time: Start time for statistics

        Returns:
            Result dictionary for JSON output
        """
        action = input_data["action"]
        source_dir = Path(input_data["source_dir"])
        config = input_data.get("config", {})
        media_info = input_data.get("media_info", {})

        if action != "scrape":
            raise ValueError(f"Unsupported action: {action}")

        # Find video file in source directory
        video_path = self._find_video_file(source_dir)
        if not video_path:
            raise ValueError(f"No video file found in: {source_dir}")

        self._emit_progress("initializing", f"Found video: {video_path.name}", 5)

        # Extract movie number
        jav_key = media_info.get("num") or media_info.get("title")
        if jav_key:
            number = str(jav_key).upper()
        else:
            number = extract_number_from_path(str(video_path))
            if not number:
                raise ValueError(f"Could not extract movie number from: {video_path}")

        self._emit_progress("searching", f"Identified media number: {number}", 10)

        # Fetch metadata
        self.start_api_request()
        self._emit_progress("searching", "Searching for movie...", 20)
        metadata = self.scraper.fetch_metadata(number)
        self.end_api_request()
        number = metadata.num

        # Create output directory (use source_dir)
        output_path = source_dir
        output_path.mkdir(parents=True, exist_ok=True)

        try:
            # Download images
            self._emit_progress("downloading", "Downloading images...", 30)
            self._download_images(metadata, output_path, number)

            # Generate NFO
            self._emit_progress("parsing", "Parsing data...", 70)
            self._generate_nfo(metadata, output_path, number)

            # Validate output
            self._emit_progress("saving", "Saving metadata...", 85)
            self._validate_output(output_path, number)

            self._emit_progress("completed", "Processing completed successfully", 100)

            # Calculate statistics
            total_time_ms = int((time.time() - start_time) * 1000)

            # Build result
            return {
                "status": "success",
                "message": "Scraping completed",
                "metadata": self._metadata_to_dict(metadata, number, output_path),
                "created_files": self._get_created_files(output_path, number),
                "statistics": {
                    "total_time_ms": total_time_ms,
                    "api_requests": self.api_requests,
                },
            }

        except Exception as e:
            # Clean up on error
            if output_path.exists():
                shutil.rmtree(output_path, ignore_errors=True)
            raise

    def _find_video_file(self, source_dir: Path) -> Path | None:
        """Find the video file in the source directory.

        Args:
            source_dir: Directory to search

        Returns:
            Path to video file, or None if not found
        """
        video_extensions = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv"}

        for ext in video_extensions:
            for path in source_dir.glob(f"*{ext}"):
                return path

        return None

    def _download_images(self, metadata: MovieMetadata, output_dir: Path, number: str) -> None:
        """Download all images and save to output directory."""
        total_steps = 3
        current_step = 0

        if metadata.poster.url:
            self._emit_progress(
                "downloading",
                "Downloading poster...",
                30 + int(40 * current_step / total_steps),
            )
            ImageDownloader.download(metadata.poster, output_dir / f"{number}-poster.jpg")
            current_step += 1
            random.uniform(2, 8)

        if metadata.thumb.url:
            self._emit_progress(
                "downloading",
                "Downloading thumb...",
                30 + int(40 * current_step / total_steps),
            )
            ImageDownloader.download(metadata.thumb, output_dir / f"{number}-thumb.jpg")
            current_step += 1
            random.uniform(2, 8)

        if metadata.fanart.url:
            self._emit_progress(
                "downloading",
                "Downloading fanart...",
                30 + int(40 * current_step / total_steps),
            )
            ImageDownloader.download(metadata.fanart, output_dir / f"{number}-fanart.jpg")
            current_step += 1
            random.uniform(2, 8)

        # Extra fanart
        if metadata.extrafanart:
            extra_dir = output_dir / "extrafanart"
            extra_dir.mkdir(exist_ok=True)

            for i, image in enumerate(metadata.extrafanart, start=1):
                ImageDownloader.download(image, extra_dir / f"extrafanart-{i}.jpg")
                random.uniform(2, 8)

    def _generate_nfo(self, metadata: MovieMetadata, output_dir: Path, number: str) -> None:
        """Generate NFO file."""
        nfo_content = generate_nfo(metadata)
        nfo_path = output_dir / f"{number}.nfo"
        nfo_path.write_text(nfo_content, encoding="utf-8")

    def _validate_output(self, output_dir: Path, number: str) -> None:
        """Validate output directory integrity."""
        missing = []

        extrafanart_dir = output_dir / "extrafanart"
        if not extrafanart_dir.exists():
            missing.append("extrafanart directory")

        fanart_file = output_dir / f"{number}-fanart.jpg"
        if not fanart_file.exists():
            missing.append(f"{number}-fanart.jpg")

        thumb_file = output_dir / f"{number}-thumb.jpg"
        if not thumb_file.exists():
            missing.append(f"{number}-thumb.jpg")

        poster_file = output_dir / f"{number}-poster.jpg"
        if not poster_file.exists():
            if fanart_file.exists():
                try:
                    with Image.open(fanart_file) as img:
                        width, height = img.size
                        if width > 700:
                            max_width = 379
                            crop_width = min(width // 2, max_width)
                            right_half = img.crop((width - crop_width, 0, width, height))
                            right_half.save(poster_file, quality=95)
                        else:
                            missing.append(f"{number}-poster.jpg")
                except Exception:
                    missing.append(f"{number}-poster.jpg")
            else:
                missing.append(f"{number}-poster.jpg")

        nfo_file = output_dir / f"{number}.nfo"
        if not nfo_file.exists():
            missing.append(f"{number}.nfo")

        if nfo_file.exists():
            try:
                tree = ET.parse(nfo_file)
                root = tree.getroot()
                required_tags = ["title", "poster", "thumb", "fanart"]
                for tag in required_tags:
                    elem = root.find(tag)
                    if elem is None or not elem.text or not elem.text.strip():
                        missing.append(f"NFO {tag} tag is empty")
            except ET.ParseError:
                missing.append("NFO file parsing failed")

        if missing:
            raise ValueError(f"Validation failed, missing: {', '.join(missing)}")

    def _metadata_to_dict(self, metadata: MovieMetadata, number: str, output_dir: Path) -> dict[str, Any]:
        """Convert MovieMetadata to dictionary for JSON output."""
        return {
            "title": metadata.title or "",
            "original_title": metadata.original_title or "",
            "year": metadata.year or "",
            "release_date": metadata.release_date or "",
            "summary": metadata.outline or "",
            "runtime": int(metadata.runtime) if metadata.runtime else None,
            "studio": metadata.studio or "",
            "maker": metadata.maker or "",
            "num": metadata.num or "",
            "tags": metadata.genres if metadata.genres else [],
            "actors": metadata.actors if metadata.actors else [],
            "images": {
                "poster": f"{number}-poster.jpg",
                "thumb": f"{number}-thumb.jpg",
                "fanart": f"{number}-fanart.jpg",
            },
        }

    def _get_created_files(self, output_dir: Path, number: str) -> dict[str, Any]:
        """Get list of created files."""
        screenshots = []
        extrafanart_dir = output_dir / "extrafanart"
        if extrafanart_dir.exists():
            for f in sorted(extrafanart_dir.glob("*.jpg")):
                screenshots.append(f.name)

        return {
            "nfo": f"{number}.nfo",
            "poster": f"{number}-poster.jpg",
            "fanart": f"{number}-fanart.jpg",
            "screenshots": screenshots,
        }

    def start_api_request(self) -> None:
        """Mark the start of an API request."""
        self.api_requests += 1

    def end_api_request(self) -> None:
        """Mark the end of an API request."""
        pass

    def _emit_progress(self, step: str, message: str, percent: int) -> None:
        """Emit progress notification to stderr.

        Args:
            step: Current step name (initializing, searching, downloading, parsing, saving, completed)
            message: Progress message
            percent: Progress percentage (0-100)
        """
        progress = {
            "type": "progress",
            "step": step,
            "message": message,
            "percent": percent,
        }
        print(json.dumps(progress), file=sys.stderr, flush=True)

    def _write_output(self, result: dict[str, Any]) -> None:
        """Write JSON output to stdout.

        Args:
            result: Result dictionary to output
        """
        print(json.dumps(result, indent=2), file=sys.stdout, flush=True)

    def _write_error(self, message: str) -> None:
        """Write error to stdout.

        Args:
            message: Error message
        """
        error = {
            "status": "error",
            "message": message,
        }
        print(json.dumps(error, indent=2), file=sys.stdout, flush=True)
