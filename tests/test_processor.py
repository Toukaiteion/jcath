"""Tests for MediaProcessor."""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock

from jcatch.core import MediaProcessor
from jcatch.core.models import MovieMetadata, Actor


@pytest.fixture
def mock_scraper():
    """Create a mock scraper."""
    scraper = Mock()
    scraper.parse_number.return_value = "FSDSS-549"
    scraper.fetch_metadata.return_value = MovieMetadata(
        num="FSDSS-549",
        title="Test Title",
        fanart_url="https://example.com/fanart.jpg",
        poster_url="https://example.com/poster.jpg",
        thumb_url="https://example.com/thumb.jpg",
        extrafanart_urls=[],
    )
    scraper.download_image = Mock()
    return scraper


@pytest.fixture
def test_video(tmp_path):
    """Create a test video file."""
    video_file = tmp_path / "FSDSS-549.mp4"
    video_file.write_bytes(b"fake video content")
    return video_file


def test_processor_creates_directory_structure(tmp_path, mock_scraper, test_video):
    """Test processor creates correct directory structure."""
    processor = MediaProcessor(mock_scraper)
    output_dir = processor.process(str(test_video), str(tmp_path / "output"))

    # Verify directory structure
    output_path = Path(output_dir)
    assert output_path.exists()
    assert output_path.name == "FSDSS-549"
    assert (output_path / "FSDSS-549.mp4").exists()
    assert (output_path / "FSDSS-549.nfo").exists()


def test_processor_calls_scraper_methods(tmp_path, mock_scraper, test_video):
    """Test processor calls scraper methods correctly."""
    processor = MediaProcessor(mock_scraper)
    processor.process(str(test_video), str(tmp_path / "output"))

    # Verify scraper methods were called
    mock_scraper.parse_number.assert_called_once()
    mock_scraper.fetch_metadata.assert_called_once_with("FSDSS-549")


def test_processor_with_nonexistent_file():
    """Test processor raises error for nonexistent file."""
    processor = MediaProcessor(mock_scraper)
    with pytest.raises(FileNotFoundError):
        processor.process("/nonexistent/file.mp4", "/output")
