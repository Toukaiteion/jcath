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
from jcatch.core.models import MovieMetadata, Actor, ImageUrl


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

    def fetch_metadata(self, number: str) -> MovieMetadata:
        """Fetch metadata from javbus.com using Selenium.

        Args:
            number: Movie number (e.g., "START-534")

        Returns:
            MovieMetadata object with scraped data
        """
        # Use jav_key if provided, otherwise use the original number
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
            year = self._parse_year(releasedate)
            runtime = self._parse_runtime(soup)
            studio = self._parse_studio(soup)
            label = self._parse_label(soup)
            actors = self._parse_actors(soup)
            genres = self._parse_genres(soup)
            fanart_url = self._parse_fanart_url(soup)
            extrafanart_urls = self._parse_extrafanart_urls(soup)

            # Build image headers with referer
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
                runtime=runtime,
                studio=studio,
                maker=studio,
                label=label,
                actors=actors,
                tags=genres,
                genres=genres,
                fanart=ImageUrl(url=fanart_url, headers=headers),
                thumb=ImageUrl(url=fanart_url, headers=headers),
                poster=ImageUrl(url=""),
                extrafanart=[ImageUrl(url=u, headers=headers) for u in extrafanart_urls],
                website=url,
            )

        except Exception as e:
            raise Exception(f"Failed to fetch metadata for {number}: {e}")

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
        # 提取p标签内所有文字，去除首尾空白
        full_text = paragraph.get_text(strip=True)  # 结果：'發行日期:2025-06-27'

        # 关键：按冒号分割，取分割后的第二部分
        if ':' in full_text:
            # split(':') 按冒号分割成列表 → ['發行日期', '2025-06-27']
            # [1] 取第二部分，strip() 去除可能的空格
            date_str = full_text.split(':')[1].strip()
            return date_str
        else:
            print("未找到冒号分隔符")
            return ''

    def _parse_runtime(self, soup: BeautifulSoup) -> int:
        """Parse runtime from "125分鐘" format."""
        paragraph = self._find_paragraph_with_header(soup, "長度:")
        if paragraph and paragraph.select_one("span"):
            text = paragraph.get_text(strip=True)
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
        for span in soup.find_all('span', class_='genre'):
            # 找当前span下的<a>标签
            a_tag = span.find('a')
            if a_tag:  # 只处理有<a>标签的项
                # 提取文字并去除首尾空白
                text = a_tag.get_text(strip=True)
                genres.append(text)
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
                if href.startswith("/"):
                    urls.append(f"{self.BASE_URL}{href}")
                else:
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

    def _parse_year(self, releasedate):

        # 切片取前4个字符
        year = releasedate[:4]
        return int(year)
