"""JavTrailers scraper for screenshots and metadata."""

import os
import platform
import re
import time
from pathlib import Path

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
from jcatch.core.models import MovieMetadata, Actor, ImageUrl


class JavTrailersScraper(BaseScraper):
    """Scraper for javtrailers.com website using Selenium."""

    BASE_URL = "https://javtrailers.com/ja"

    def __init__(self, headless: bool = True, chromedriver_path: str | None = None):
        """Initialize scraper with headless browser.

        Args:
            headless: Whether to run Chrome in headless mode (default: True)
            chromedriver_path: Path to ChromeDriver executable. If None, use webdriver-manager to install.
        """
        self.headless = headless
        self.chromedriver_path = chromedriver_path
        self.driver = self._init_driver()

    def _init_driver(self):
        """Initialize Chrome WebDriver with headless mode."""
        options = Options()
        if self.headless:
            options.add_argument("--headless")
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

        # Use provided chromedriver_path or install via webdriver-manager
        if self.chromedriver_path:
            service = Service(self.chromedriver_path)
            print(f"使用指定 ChromeDriver: {self.chromedriver_path}")
        else:
            driver_path = ChromeDriverManager().install()
            print("download driver at: " + driver_path)
            service = Service(driver_path)

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

    def fetch_metadata(self, number: str) -> MovieMetadata:
        """Fetch metadata from javtrailers.com using Selenium.

        Args:
            number: Movie number (e.g., "SQTE-633")

        Returns:
            MovieMetadata object with scraped data
        """
        try:
            # Normalize number: uppercase
            number = number.upper()

            print(f"从 JavTrailers 获取 {number} 的信息...")

            # Navigate to homepage
            self.driver.get(self.BASE_URL)
            time.sleep(2)

            # Find and interact with search input
            search_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".autocomplete-input"))
            )
            search_input.clear()
            search_input.send_keys(number)
            time.sleep(1)

            # Click search button
            search_button = self.driver.find_element(By.CSS_SELECTOR, ".search-button")
            search_button.click()

            # Wait for results to load
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".videos-list"))
            )
            time.sleep(2)

            # Click first result
            first_card = self.driver.find_element(By.CSS_SELECTOR, ".card-container:first-child a")
            first_card.click()

            # Wait for detail page to load
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".video-card"))
            )
            time.sleep(2)

            # Get page source for parsing
            html = self.driver.page_source
            soup = BeautifulSoup(html, "lxml")

            # Try to click gallery button
            try:
                gallery_button = self.driver.find_element(By.XPATH, "//button[contains(text(), '画廊')]")
                if gallery_button and "active" not in gallery_button.get_attribute("class"):
                    gallery_button.click()
                    time.sleep(2)
                    # Re-parse after clicking gallery
                    html = self.driver.page_source
                    soup = BeautifulSoup(html, "lxml")
            except Exception as e:
                print(f"Gallery button not found or already active: {e}")

            # Parse metadata
            num = self._parse_num(soup, number)
            title = self._parse_title(soup)
            releasedate = self._parse_releasedate(soup)
            year = self._parse_year(releasedate)
            studio = self._parse_studio(soup)
            label = self._parse_label(soup)
            actors = self._parse_actors(soup)
            genres = self._parse_genres(soup)
            poster_url = self._parse_poster(soup)
            extrafanart_urls = self._parse_extrafanart_urls(soup)
            outline = self._parse_outline(soup)

            # Build image headers with referer
            headers = {
                "referer": self.driver.current_url,
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
                actors=actors,
                tags=genres,
                genres=genres,
                fanart=ImageUrl(url=poster_url, headers=headers),
                thumb=ImageUrl(url=poster_url, headers=headers),
                poster=ImageUrl(url=poster_url, headers=headers),
                extrafanart=[ImageUrl(url=u, headers=headers) for u in extrafanart_urls],
                outline=outline,
                plot=outline,
                website=self.driver.current_url,
            )

        except Exception as e:
            raise Exception(f"Failed to fetch metadata for {number}: {e}")

    # Parsing methods

    def _parse_num(self, soup: BeautifulSoup, default: str) -> str:
        """Parse movie number from page or use default."""
        # Try to find number in title or breadcrumb
        # Look for pattern like "SQTE-633" in text
        for elem in soup.find_all(text=re.compile(r'[A-Z]+-\d+', re.IGNORECASE)):
            match = re.search(r'([A-Z]+-\d+)', elem.upper())
            if match:
                return match.group(1)
        return default

    def _parse_title(self, soup: BeautifulSoup) -> str:
        """Parse title from page."""
        # Try to find title in h1, h2, or .vid-title
        selectors = [".vid-title", "h1", "h2", ".video-title"]
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                if text:
                    return text
        return ""

    def _parse_releasedate(self, soup: BeautifulSoup) -> str:
        """Parse release date."""
        # Look for date in various formats
        # Try to find date in .text-muted or similar
        for elem in soup.find_all(text=re.compile(r'\d{1,2} \w+ \d{4}')):
            # Try to parse various date formats
            match = re.search(r'(\d{1,2} \w+ \d{4})', elem)
            if match:
                # Could try to convert to YYYY-MM-DD, but return raw for now
                date_str = match.group(1)
                # Try to convert to standard format
                try:
                    # Simple conversion for common formats
                    return self._convert_date_format(date_str)
                except:
                    return date_str
        return ""

    def _convert_date_format(self, date_str: str) -> str:
        """Convert various date formats to YYYY-MM-DD."""
        # This is a simplified conversion - could be expanded
        # For now, return as-is and let the user verify
        return date_str

    def _parse_year(self, releasedate: str) -> int:
        """Parse year from release date string."""
        if releasedate and len(releasedate) >= 4:
            try:
                # Extract 4-digit year
                match = re.search(r'(\d{4})', releasedate)
                if match:
                    return int(match.group(1))
            except ValueError:
                pass
        return 0

    def _parse_studio(self, soup: BeautifulSoup) -> str:
        """Parse studio (manufacturer)."""
        # Look for studio/manufacturer label
        for div in soup.find_all("div", class_=lambda c: c and "text-secondary" in c):
            label_span = div.find("span")
            if label_span and "メーカー" in label_span.text or "製作商" in label_span.text:
                link = div.find("a")
                if link:
                    return link.text.strip()
        return ""

    def _parse_label(self, soup: BeautifulSoup) -> str:
        """Parse label."""
        for div in soup.find_all("div", class_=lambda c: c and "text-secondary" in c):
            label_span = div.find("span")
            if label_span and "レーベル" in label_span.text or "シリーズ" in label_span.text:
                link = div.find("a")
                if link:
                    return link.text.strip()
        return ""

    def _parse_actors(self, soup: BeautifulSoup) -> list[Actor]:
        """Parse actors list."""
        actors = []
        # Look for actor links
        for link in soup.select("a[href*='/star/']"):
            name = link.get_text(strip=True)
            if name and name not in [a.name for a in actors]:
                actors.append(Actor(name=name))
        return actors

    def _parse_genres(self, soup: BeautifulSoup) -> list[str]:
        """Parse genres list."""
        genres = []
        # Look for genre tags/links
        for link in soup.select("a[href*='/category/']"):
            genre = link.get_text(strip=True)
            if genre and genre not in genres:
                genres.append(genre)
        return genres

    def _parse_poster(self, soup: BeautifulSoup) -> str:
        """Parse poster image URL."""
        # Look for the main poster image
        img = soup.select_one(".video-card img, .card-img-top, .poster img")
        if img and img.get("src"):
            return img["src"]
        return ""

    def _parse_extrafanart_urls(self, soup: BeautifulSoup) -> list[str]:
        """Parse extrafanart/screenshot URLs from gallery."""
        urls = []
        # Find gallery slides
        for img in soup.select(".swiper-slide img, .gallery img, .screenshot img"):
            # Prefer src, fallback to data-loading or data-src
            url = img.get("src") or img.get("data-loading") or img.get("data-src")
            if url:
                urls.append(url)
        return urls

    def _parse_outline(self, soup: BeautifulSoup) -> str:
        """Parse outline/description."""
        # Look for description text
        desc_elem = soup.select_one(".description, .outline, .plot, .video-description")
        if desc_elem:
            return desc_elem.get_text(strip=True)
        return ""
