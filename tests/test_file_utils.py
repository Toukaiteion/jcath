"""Tests for file utility functions."""

import pytest

from jcatch.utils import extract_number_from_path


def test_extract_number_simple():
    """Test extracting number from simple filename."""
    assert extract_number_from_path("/path/to/FSDSS-549.mp4") == "FSDSS-549"


def test_extract_number_with_directory():
    """Test extracting number when directory contains the number."""
    assert extract_number_from_path("/path/to/FSDSS-549/FSDSS-549.mp4") == "FSDSS-549"


def test_extract_number_no_hyphen():
    """Test extracting number from format without hyphen."""
    assert extract_number_from_path("/path/to/FSDSS549.mp4") == "FSDSS-549"


def test_extract_number_complex_filename():
    """Test extracting number from complex filename."""
    assert extract_number_from_path("/path/to/ABC-123_HD.mp4") == "ABC-123"


def test_extract_number_no_match():
    """Test returns empty string when no pattern matches."""
    assert extract_number_from_path("/path/to/random-video.mp4") == ""
    assert extract_number_from_path("/path/to/video.mp4") == ""


def test_extract_number_lowercase():
    """Test that lowercase letters don't match."""
    # Pattern expects uppercase letters
    assert extract_number_from_path("/path/to/fsdss-549.mp4") == ""


def test_extract_number_multiple_numbers():
    """Test extracts first matching pattern."""
    # Should extract from filename, not directory
    result = extract_number_from_path("/ABC-123/FSDSS-456.mp4")
    assert result == "FSDSS-456"
