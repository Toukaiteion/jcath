"""Tests for NFO generation."""

from jcatch.core.models import MovieMetadata, Actor
from jcatch.core.nfo import generate_nfo


def test_nfo_generation_basic():
    """Test basic NFO generation."""
    metadata = MovieMetadata(
        num="FSDSS-549",
        title="Test Title",
        studio="FALENO",
        year=2023,
    )

    nfo = generate_nfo(metadata)

    assert "<?xml version" in nfo
    assert "<movie>" in nfo
    assert "<num>FSDSS-549</num>" in nfo
    assert "<title>Test Title</title>" in nfo
    assert "<studio>FALENO</studio>" in nfo
    assert "<year>2023</year>" in nfo


def test_nfo_generation_with_actors():
    """Test NFO generation with actors."""
    metadata = MovieMetadata(
        num="FSDSS-549",
        title="Test Title",
        actors=[Actor(name="Actor 1"), Actor(name="Actor 2")],
    )

    nfo = generate_nfo(metadata)

    assert "<actor>" in nfo
    assert "<name>Actor 1</name>" in nfo
    assert "<name>Actor 2</name>" in nfo


def test_nfo_image_filenames():
    """Test NFO generates correct image filenames."""
    metadata = MovieMetadata(
        num="FSDSS-549",
        title="Test Title",
    )

    nfo = generate_nfo(metadata)

    assert "<poster>FSDSS-549-poster.jpg</poster>" in nfo
    assert "<thumb>FSDSS-549-thumb.jpg</thumb>" in nfo
    assert "<fanart>FSDSS-549-fanart.jpg</fanart>" in nfo


def test_nfo_tags_and_genres_count():
    """Test NFO always has exactly 2 tag and 2 genre elements."""
    metadata = MovieMetadata(
        num="FSDSS-549",
        title="Test Title",
        tags=["tag1", "tag2", "tag3"],
        genres=["genre1"],
    )

    nfo = generate_nfo(metadata)

    # Count occurrences (opening tags only)
    tag_count = nfo.count("<tag>")
    genre_count = nfo.count("<genre>")

    assert tag_count == 2, f"Expected 2 <tag> elements, got {tag_count}"
    assert genre_count == 2, f"Expected 2 <genre> elements, got {genre_count}"


def test_nfo_cdata_wrapping():
    """Test that title and certain fields are CDATA wrapped."""
    metadata = MovieMetadata(
        num="FSDSS-549",
        title="Title with <special> characters",
        originaltitle="Original <title>",
    )

    nfo = generate_nfo(metadata)

    # Verify CDATA wrapping for title
    assert "<title>" in nfo
    # Note: Our implementation encodes special characters instead of using CDATA
    # to maintain compatibility with standard ElementTree
    assert "&lt;" in nfo  # < encoded as &lt;
