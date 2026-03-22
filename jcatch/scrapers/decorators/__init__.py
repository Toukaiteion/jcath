"""Scraper decorators for composing different scrapers."""

from jcatch.scrapers.decorators.base_decorator import ScraperDecorator
from jcatch.scrapers.decorators.fanart_decorator import FanartDecorator
from jcatch.scrapers.decorators.metadata_decorator import MetadataDecorator
from jcatch.scrapers.decorators.poster_decorator import PosterDecorator

__all__ = ["ScraperDecorator", "FanartDecorator", "MetadataDecorator", "PosterDecorator"]
