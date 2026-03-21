"""Tests for data models."""

import pytest

from jcatch.core.models import Actor, MovieMetadata


def test_actor_creation():
    """Test creating an Actor."""
    actor = Actor(name="Test Actor")
    assert actor.name == "Test Actor"


def test_movie_metadata_defaults():
    """Test MovieMetadata has correct defaults."""
    metadata = MovieMetadata(num="FSDSS-549", title="Test Title")

    assert metadata.num == "FSDSS-549"
    assert metadata.title == "Test Title"
    assert metadata.customrating == "JP-18+"
    assert metadata.mpaa == "JP-18+"
    assert metadata.year == 0
    assert metadata.actors == []
    assert metadata.tags == []
    assert metadata.genres == []


def test_movie_metadata_with_actors():
    """Test MovieMetadata with actors."""
    metadata = MovieMetadata(
        num="FSDSS-549",
        title="Test Title",
        actors=[Actor(name="Actor 1"), Actor(name="Actor 2")],
    )

    assert len(metadata.actors) == 2
    assert metadata.actors[0].name == "Actor 1"
    assert metadata.actors[1].name == "Actor 2"


def test_movie_metadata_with_urls():
    """Test MovieMetadata with image URLs."""
    metadata = MovieMetadata(
        num="FSDSS-549",
        title="Test Title",
        fanart_url="https://example.com/fanart.jpg",
        poster_url="https://example.com/poster.jpg",
        thumb_url="https://example.com/thumb.jpg",
        extrafanart_urls=[
            "https://example.com/screenshot1.jpg",
            "https://example.com/screenshot2.jpg",
        ],
    )

    assert metadata.fanart_url == "https://example.com/fanart.jpg"
    assert metadata.poster_url == "https://example.com/poster.jpg"
    assert metadata.thumb_url == "https://example.com/thumb.jpg"
    assert len(metadata.extrafanart_urls) == 2
