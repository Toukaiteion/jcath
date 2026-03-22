"""Scraper modules for fetching metadata from various sources."""

from jcatch.scrapers.base import BaseScraper
from jcatch.scrapers.jav321 import Jav321Scraper
from jcatch.scrapers.javbus import JavBusScraper
from jcatch.scrapers.javwine import JavWineScraper
from jcatch.scrapers.missavws import MissAvWsScraper
from jcatch.scrapers.www324jav import Www324JavScraper
from jcatch.scrapers.decorators import (
    MetadataDecorator,
    ScraperDecorator,
    FanartDecorator,
    PosterDecorator,
)

__all__ = [
    "BaseScraper",
    "Jav321Scraper",
    "JavBusScraper",
    "JavWineScraper",
    "MissAvWsScraper",
    "Www324JavScraper",
    "ScraperDecorator",
    "FanartDecorator",
    "MetadataDecorator",
    "PosterDecorator",
]
