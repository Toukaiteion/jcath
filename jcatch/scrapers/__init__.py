"""Scraper modules for fetching metadata from various sources."""

from jcatch.scrapers.base import BaseScraper
from jcatch.scrapers.jav321 import Jav321Scraper
from jcatch.scrapers.javbus import JavBusScraper
from jcatch.scrapers.decorator import ScraperDecorator
from jcatch.scrapers.fanart_decorator import FanartDecorator
from jcatch.scrapers.poster_decorator import PosterDecorator

__all__ = [
    "BaseScraper",
    "Jav321Scraper",
    "JavBusScraper",
    "ScraperDecorator",
    "FanartDecorator",
    "PosterDecorator",
]
