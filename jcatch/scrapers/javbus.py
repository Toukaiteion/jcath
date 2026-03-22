"""JavBus scraper implementation using Selenium."""

import os
import platform
import re
import time
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
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


class JavBusScraper(BaseScraper):
    """Scraper for javbus.com website using Selenium."""

    BASE_URL = "https://www.javbus.com"

    def __init__(self):
        """Initialize scraper with headless browser."""
        self.current_website = ""
        self.driver = self._init_driver()

    def _init_driver(self):
        """Initialize Chrome WebDriver with headless mode."""
        options = Options()
        # options.add_argument("--headless")  # 无头模式
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
        options.add_argument(f"user-agent={user_agent}")

        # Load .env file
        load_dotenv()

        # Set Chrome binary location
        chrome_path = self._get_chrome_path()
        if chrome_path:
            options.binary_location = chrome_path
            print(f"Chrome 路径: {chrome_path}")

        service = Service(ChromeDriverManager().install())
        print("download driver at: " + ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        # Print Chrome version info
        chrome_version = driver.capabilities.get('browserVersion', 'unknown')
        chromedriver_version = driver.capabilities.get('chrome', {}).get('chromedriverVersion', 'unknown').split(' ')[0]
        print(f"Chrome版本：{chrome_version}")
        print(f"ChromeDriver版本：{chromedriver_version}")
        return driver

    def _get_chrome_path(self) -> str:
        """获取 Chrome 可执行文件路径。

        优先级：
        1. 环境变量 JCATCH_CHROME_PATH
        2. .env 文件中的配置
        3. 平台默认值

        Returns:
            Chrome 可执行文件的绝对路径
        """
        # 读取环境变量（dotenv 已加载）
        if chrome_path := os.getenv("JCATCH_CHROME_PATH"):
            return chrome_path

        # 平台默认值
        if platform.system() == "Windows":
            return r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        else:  # Linux/WSL
            # 尝试常见路径
            candidates = [
                "/usr/bin/google-chrome",
                "/usr/bin/chromium-browser",
                "/usr/bin/chromium",
                "/opt/google/chrome/google-chrome",
            ]
            for path in candidates:
                if Path(path).exists():
                    return path
            return ""  # 返回空字符串，让 webdriver-manager 尝试自动检测

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

            # Save website URL for referer header
            self.current_website = url

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
        """Download and save an image with referer header for JavBus.

        Args:
            url: URL of image
            save_path: File path where image should be saved
        """
        import requests

        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            headers = {}
            if self.current_website:
                headers["referer"] = self.current_website
            headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            save_path.write_bytes(response.content)
        except Exception as e:
            raise Exception(f"Failed to download {url}: {e}")

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
