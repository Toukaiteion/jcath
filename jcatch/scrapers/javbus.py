"""JavBus scraper implementation using Selenium."""

import re
import time
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

from jcatch.scrapers.base import BaseScraper
from jcatch.core.models import MovieMetadata, Actor
from jcatch.utils import download_image


class JavBusScraper(BaseScraper):
    """Scraper for javbus.com website using Selenium."""

    BASE_URL = "https://www.javbus.com"

    def __init__(self):
        """Initialize scraper with headless browser."""
        self.driver = self._init_driver()

    def _init_driver(self):
        """Initialize Chrome WebDriver with headless mode."""
        options = Options()
        # options.add_argument("--headless")  # 无头模式
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

        service = Service(ChromeDriverManager().install())
        print("download driver at: " + ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)

    def __del__(self):
        """Cleanup: close browser when scraper is destroyed."""
        if hasattr(self, "driver") and self.driver:
            self.driver.quit()

    def parse_number(self, filepath: str) -> str:
        """Extract movie number and convert to uppercase.

        Args:
            filepath: Path to video file

        Returns:
            Movie number in uppercase (e.g., "START-534")
        """
        from pathlib import Path
        number = Path(filepath).stem
        return number.upper()

    def fetch_metadata(self, number: str) -> MovieMetadata:
        """Fetch metadata from javbus.com using Selenium.

        Args:
            number: Movie number (e.g., "START-534")

        Returns:
            MovieMetadata object with scraped data
        """
        url = f"{self.BASE_URL}/{number}"

        try:
            # Navigate to page
            self.driver.get(url)

            # Wait for page to load - wait for movie info section
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "movie"))
            )

            # Additional wait for dynamic content
            time.sleep(2)

            # Get page source after JS execution
            html = self.driver.page_source
            soup = BeautifulSoup(html, "lxml")

            # Parse fields
            num = self._parse_num(soup)
            title = self._parse_title(soup)
            releasedate = self._parse_releasedate(soup)
            runtime = self._parse_runtime(soup)
            studio = self._parse_studio(soup)
            label = self._parse_label(soup)
            actors = self._parse_actors(soup)
            genres = self._parse_genres(soup)
            fanart_url = self._parse_fanart_url(soup)
            extrafanart_urls = self._parse_extrafanart_urls(soup)

            return MovieMetadata(
                num=num,
                title=title,
                releasedate=releasedate,
                runtime=runtime,
                studio=studio,
                label=label,
                actors=actors,
                genres=genres,
                fanart_url=fanart_url,
                thumb_url=fanart_url,  # Same as fanart_url
                poster_url="",  # Not available from javbus
                extrafanart_urls=extrafanart_urls,
                website=url,
            )

        except Exception as e:
            raise Exception(f"Failed to fetch metadata for {number}: {e}")

    def download_image(self, url: str, save_path: str) -> None:
        """Download and save an image.

        Args:
            url: URL of image
            save_path: File path where image should be saved
        """
        download_image(url, save_path)

    # Parsing methods

    def _parse_num(self, soup: BeautifulSoup) -> str:
        """Parse movie number from span with red color."""
        elem = soup.find("span", style=lambda s: s and "#CC0000" in s)
        return elem.text.strip() if elem else ""

    def _parse_title(self, soup: BeautifulSoup) -> str:
        """Parse title from h3 element."""
        h3 = soup.find("h3")
        return h3.text.strip() if h3 else ""

    def _parse_releasedate(self, soup: BeautifulSoup) -> str:
        """Parse release date."""
        paragraph = self._find_paragraph_with_header(soup, "發行日期:")
        if paragraph and paragraph.select_one("span"):
            return paragraph.select_one("span:last-child").text.strip()
        return ""

    def _parse_runtime(self, soup: BeautifulSoup) -> int:
        """Parse runtime from "125分鐘" format."""
        paragraph = self._find_paragraph_with_header(soup, "長度:")
        if paragraph and paragraph.select_one("span"):
            text = paragraph.select_one("span:last-child").text
            match = re.search(r"(\d+)", text)
            return int(match.group(1)) if match else 0
        return 0

    def _parse_studio(self, soup: BeautifulSoup) -> str:
        """Parse studio (製作商)."""
        paragraph = self._find_paragraph_with_header(soup, "製作商:")
        if paragraph:
            link = paragraph.select_one("a")
            return link.text.strip() if link else ""
        return ""

    def _parse_label(self, soup: BeautifulSoup) -> str:
        """Parse label (發行商)."""
        paragraph = self._find_paragraph_with_header(soup, "發行商:")
        if paragraph:
            link = paragraph.select_one("a")
            return link.text.strip() if link else ""
        return ""

    def _parse_actors(self, soup: BeautifulSoup) -> list[Actor]:
        """Parse actors list.

        Priority: .star-name a > #avatar-waterfall span
        """
        actors = []

        # Try star-name elements first
        for link in soup.select(".star-name a"):
            name = link.text.strip()
            if name:
                actors.append(Actor(name=name))

        # Fallback to avatar-waterfall
        if not actors:
            for span in soup.select("#avatar-waterfall span"):
                name = span.text.strip()
                if name:
                    actors.append(Actor(name=name))

        return actors

    def _parse_genres(self, soup: BeautifulSoup) -> list[str]:
        """Parse genres from .genre a elements."""
        genres = []
        for link in soup.select(".genre a"):
            name = link.text.strip()
            if name:
                genres.append(name)
        return genres

    def _parse_fanart_url(self, soup: BeautifulSoup) -> str:
        """Parse fanart/cover image URL."""
        img = soup.select_one(".bigImage img")
        if img and img.get("src"):
            src = img["src"]
            # Convert relative URL to absolute
            if src.startswith("/"):
                return f"{self.BASE_URL}{src}"
            return src
        return ""

    def _parse_extrafanart_urls(self, soup: BeautifulSoup) -> list[str]:
        """Parse extrafanart/screenshot URLs."""
        urls = []
        for link in soup.select("#sample-waterfall .sample-box"):
            href = link.get("href")
            if href:
                urls.append(href)
        return urls

    @staticmethod
    def _find_paragraph_with_header(soup: BeautifulSoup, header_text: str) -> Optional:
        """Find a paragraph containing specified header text."""
        for p in soup.find_all("p"):
            header = p.find("span", class_="header")
            if header and header.text.strip() == header_text:
                return p
        return None
