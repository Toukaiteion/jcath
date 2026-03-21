"""Scraper modules for fetching metadata from various sources."""

from jcatch.scrapers.base import BaseScraper
from jcatch.scrapers.jav321 import Jav321Scraper
from jcatch.scrapers.javbus import JavBusScraper

__all__ = ["BaseScraper", "Jav321Scraper", "JavBusScraper"]
