import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any, List
import logging
import time
from urllib.parse import urljoin
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseScraper:
    def __init__(self, base_url: str, headers: Optional[Dict[str, str]] = None):
        self.base_url = base_url
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit = random.uniform(2, 4)  # Random delay between requests

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _make_request(self, url: str) -> Optional[str]:
        """Make an HTTP request with rate limiting and error handling."""
        if not self.session:
            raise RuntimeError("Session not initialized. Use 'async with' context manager.")
        
        try:
            await asyncio.sleep(self.rate_limit)
            async with self.session.get(url, ssl=False) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.error(f"Error fetching {url}: Status code {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None

    def _parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML content using BeautifulSoup."""
        return BeautifulSoup(html, 'html.parser')

    def _build_full_url(self, path: str) -> str:
        """Build full URL from relative path."""
        return urljoin(self.base_url, path)

    async def get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """Get and parse page content."""
        html = await self._make_request(url)
        if html:
            return self._parse_html(html)
        return None

    def extract_text(self, element: Any, selector: str, default: str = "") -> str:
        """Safely extract text from a BS4 element."""
        found = element.select_one(selector)
        return found.get_text(strip=True) if found else default

    def extract_attribute(self, element: Any, selector: str, attribute: str, default: str = "") -> str:
        """Safely extract attribute from a BS4 element."""
        found = element.select_one(selector)
        return found.get(attribute, default) if found else default

    async def process_pagination(self, url: str, max_pages: int = None) -> List[BeautifulSoup]:
        """Process multiple pages of content."""
        pages = []
        current_page = 1
        
        while True:
            if max_pages and current_page > max_pages:
                break
                
            page_url = f"{url}?page={current_page}" if current_page > 1 else url
            soup = await self.get_page_content(page_url)
            
            if not soup:
                break
                
            pages.append(soup)
            current_page += 1
            
            # Random delay between pages
            await asyncio.sleep(random.uniform(1, 3))
            
            # Check if there's a next page
            if not self._has_next_page(soup):
                break
                
        return pages

    def _has_next_page(self, soup: BeautifulSoup) -> bool:
        """Check if there's a next page. Override this in child classes."""
        raise NotImplementedError("This method should be implemented in child classes") 