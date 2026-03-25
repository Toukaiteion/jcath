"""MissAvWs scraper for metadata."""

import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from jcatch.scrapers.base import BaseScraper
from jcatch.core.models import MovieMetadata, Actor, ImageUrl


class MissAvWsScraper(BaseScraper):
    """Scraper for missav.ws website."""

    BASE_URL = "https://missav.ws"

    def fetch_metadata(self, number: str) -> MovieMetadata:
        """Fetch metadata from missav.ws.

        Args:
            number: Movie number (e.g., "ADN-638")

        Returns:
            MovieMetadata object with scraped data
        """
        url = f"{self.BASE_URL}/cn/{number.lower()}"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")

            # Parse fields
            num = self._parse_num(soup, number)
            title = self._parse_title(soup)
            releasedate = self._parse_releasedate(soup)
            year = self._parse_year(releasedate)
            studio = self._parse_studio(soup)
            label = self._parse_label(soup)
            director = self._parse_director(soup)
            actors = self._parse_actors(soup)
            genres = self._parse_genres(soup)
            series = self._parse_series(soup)
            outline = self._parse_outline(soup)
            poster = self._parse_poster(soup)

            # Build image headers
            headers = {
                "referer": url,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
            }

            return MovieMetadata(
                num=num,
                title=title,
                originaltitle=title,
                sorttitle=title,
                release=releasedate,
                releasedate=releasedate,
                premiered=releasedate,
                year=year,
                studio=studio,
                maker=studio,
                label=label,
                director=director,
                actors=actors,
                tags=genres,
                genres=genres,
                poster=ImageUrl(url=poster, headers=headers),
                fanart=ImageUrl(url=poster, headers=headers),
                thumb=ImageUrl(url=poster, headers=headers),
                outline=outline,
                plot=outline,
                website=url,
            )

        except Exception as e:
            raise Exception(f"Failed to fetch metadata for {number}: {e}")

    # Parsing methods

    def _parse_num(self, soup: BeautifulSoup, number: str) -> str:
        """Parse movie number from page or use provided number."""
        # Try to find number in page
        for div in soup.find_all("div", class_="text-secondary"):
            label_span = div.find("span")
            if label_span and label_span.text.strip() == "番号:":
                value_span = div.find("span", class_="font-medium")
                if value_span:
                    return value_span.text.strip()
        return number.upper()

    def _parse_title(self, soup: BeautifulSoup) -> str:
        """Parse title from page."""
        for div in soup.find_all("div", class_="text-secondary"):
            label_span = div.find("span")
            if label_span and label_span.text.strip() == "标题:":
                value_span = div.find("span", class_="font-medium")
                if value_span:
                    return value_span.text.strip()
        return ""

    def _parse_releasedate(self, soup: BeautifulSoup) -> str:
        """Parse release date from datetime attribute."""
        for div in soup.find_all("div", class_="text-secondary"):
            label_span = div.find("span")
            if label_span and label_span.text.strip() == "发行日期:":
                time_elem = div.find("time")
                if time_elem and time_elem.get("datetime"):
                    # Extract YYYY-MM-DD from datetime attribute
                    datetime_str = time_elem["datetime"]
                    match = re.match(r"(\d{4}-\d{2}-\d{2})", datetime_str)
                    return match.group(1) if match else ""
        return ""

    def _parse_studio(self, soup: BeautifulSoup) -> str:
        """Parse studio (发行商)."""
        for div in soup.find_all("div", class_="text-secondary"):
            label_span = div.find("span")
            if label_span and label_span.text.strip() == "发行商:":
                link = div.find("a")
                if link:
                    return link.text.strip()
        return ""

    def _parse_label(self, soup: BeautifulSoup) -> str:
        """Parse label (标籤)."""
        for div in soup.find_all("div", class_="text-secondary"):
            label_span = div.find("span")
            if label_span and label_span.text.strip() == "标籤:":
                link = div.find("a")
                if link:
                    return link.text.strip()
        return ""

    def _parse_director(self, soup: BeautifulSoup) -> str:
        """Parse director."""
        for div in soup.find_all("div", class_="text-secondary"):
            label_span = div.find("span")
            if label_span and label_span.text.strip() == "导演:":
                link = div.find("a")
                if link:
                    return link.text.strip()
        return ""

    def _parse_actors(self, soup: BeautifulSoup) -> list[Actor]:
        """Parse actors list."""
        actors = []
        for div in soup.find_all("div", class_="text-secondary"):
            label_span = div.find("span")
            if label_span and label_span.text.strip() == "女优:":
                for link in div.find_all("a"):
                    name = link.text.strip()
                    if name:
                        actors.append(Actor(name=name))
        return actors

    def _parse_genres(self, soup: BeautifulSoup) -> list[str]:
        """Parse genres list."""
        genres = []
        for div in soup.find_all("div", class_="text-secondary"):
            label_span = div.find("span")
            if label_span and label_span.text.strip() == "类型:":
                for link in div.find_all("a"):
                    genre = link.text.strip()
                    if genre:
                        genres.append(genre)
        return genres

    def _parse_series(self, soup: BeautifulSoup) -> str:
        """Parse series."""
        for div in soup.find_all("div", class_="text-secondary"):
            label_span = div.find("span")
            if label_span and label_span.text.strip() == "系列:":
                link = div.find("a")
                if link:
                    return link.text.strip()
        return ""

    def _parse_outline(self, soup: BeautifulSoup) -> str:
        """Parse outline/description."""
        # Find the div with line-clamp-2 class (description)
        outline_div = soup.find("div", class_=lambda c: c and "line-clamp-2" in c.split())
        if outline_div:
            return outline_div.text.strip()
        return ""

    def _parse_poster(self, soup: BeautifulSoup) -> str:
        """Parse poster image URL."""
        # Look for images in the page - try common selectors
        img = soup.select_one("img[src*='missav']")
        if img and img.get("src"):
            src = img["src"]
            # Convert relative URL to absolute
            if src.startswith("/"):
                return f"{self.BASE_URL}{src}"
            return src
        return ""

    def _parse_year(self, releasedate: str) -> int:
        """Parse year from release date string."""
        if releasedate and len(releasedate) >= 4:
            try:
                return int(releasedate[:4])
            except ValueError:
                pass
        return 0
