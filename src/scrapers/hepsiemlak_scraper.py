from typing import Dict, List, Optional
from .base_scraper import BaseScraper
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

class HepsiEmlakScraper(BaseScraper):
    def __init__(self):
        super().__init__(base_url="https://www.hepsiemlak.com")
        
    def _has_next_page(self, soup: BeautifulSoup) -> bool:
        """Check if there's a next page in HepsiEmlak listing."""
        next_button = soup.select_one('a[rel="next"]') or soup.select_one('a.he-pagination__button--next')
        return bool(next_button)

    async def get_listing_details(self, listing_url: str) -> Optional[Dict]:
        """Extract details from a single listing page."""
        soup = await self.get_page_content(listing_url)
        if not soup:
            return None

        try:
            # Try to extract data from script tag first
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if '@type' in data and data['@type'] == 'Product':
                        return {
                            'url': listing_url,
                            'title': data.get('name', ''),
                            'price': data.get('offers', {}).get('price', ''),
                            'location': data.get('address', {}).get('addressLocality', ''),
                            'description': data.get('description', ''),
                            'features': self._extract_features(soup),
                            'details': self._extract_property_details(soup),
                            'images': [img.get('contentUrl', '') for img in data.get('image', [])],
                            'seller_info': self._extract_seller_info(soup),
                            'scraped_at': datetime.now().isoformat()
                        }
                except:
                    continue

            # Fallback to HTML parsing if script data is not available
            return {
                'url': listing_url,
                'title': self.extract_text(soup, 'h1.detail-title'),
                'price': self.extract_text(soup, 'p.price'),
                'location': self.extract_text(soup, 'div.detail-location'),
                'description': self.extract_text(soup, 'div.description'),
                'features': self._extract_features(soup),
                'details': self._extract_property_details(soup),
                'images': self._extract_images(soup),
                'seller_info': self._extract_seller_info(soup),
                'scraped_at': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error extracting listing details from {listing_url}: {str(e)}")
            return None

    def _extract_features(self, soup: BeautifulSoup) -> List[str]:
        """Extract property features."""
        features = []
        feature_elements = soup.select('ul.adv-info-list li') or soup.select('div.spec-item')
        for element in feature_elements:
            feature_text = element.get_text(strip=True)
            if feature_text:
                features.append(feature_text)
        return features

    def _extract_property_details(self, soup: BeautifulSoup) -> Dict:
        """Extract detailed property information."""
        details = {}
        detail_items = soup.select('ul.adv-info-list li') or soup.select('div.spec-item')
        
        for item in detail_items:
            label = self.extract_text(item, 'span.spec-item-name') or self.extract_text(item, 'span.left')
            value = self.extract_text(item, 'span.spec-item-value') or self.extract_text(item, 'span.right')
            if label and value:
                details[label.lower().replace(' ', '_')] = value
                
        return details

    def _extract_images(self, soup: BeautifulSoup) -> List[str]:
        """Extract all property images."""
        images = []
        
        # Try to find image URLs in script tags
        scripts = soup.find_all('script', type='text/javascript')
        for script in scripts:
            if script.string and ('imageGallery' in script.string or 'contentUrl' in script.string):
                urls = re.findall(r'https?://[^\s<>"]+?(?:jpg|jpeg|png|webp)', script.string)
                images.extend(urls)
        
        # Fallback to direct img tags
        if not images:
            img_elements = soup.select('div.image-gallery img') or soup.select('div.gallery-img img')
            for img in img_elements:
                src = img.get('src') or img.get('data-src')
                if src:
                    images.append(src)
            
        return list(set(images))  # Remove duplicates

    def _extract_seller_info(self, soup: BeautifulSoup) -> Dict:
        """Extract information about the seller/agent."""
        seller_info = {}
        seller_section = soup.select_one('div.owner-info') or soup.select_one('div.broker-info')
        
        if seller_section:
            seller_info['name'] = self.extract_text(seller_section, 'span.name') or self.extract_text(seller_section, 'div.broker-name')
            seller_info['company'] = self.extract_text(seller_section, 'span.company') or self.extract_text(seller_section, 'div.broker-company')
            seller_info['phone'] = self.extract_text(seller_section, 'span.phone') or self.extract_text(seller_section, 'div.broker-phone')
            
        return seller_info

    async def search_listings(self, search_url: str, max_pages: Optional[int] = None) -> List[Dict]:
        """Search and extract listings from search results pages."""
        listings = []
        pages = await self.process_pagination(search_url, max_pages)
        
        for page_soup in pages:
            page_listings = self._extract_listings_from_page(page_soup)
            listings.extend(page_listings)
            
        return listings

    def _extract_listings_from_page(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract all listings from a single search results page."""
        listings = []
        listing_elements = soup.select('div.listing-item') or soup.select('div.list-item-wrapper')
        
        for element in listing_elements:
            try:
                listing = {
                    'title': self.extract_text(element, 'span.title') or self.extract_text(element, 'h3.list-item-title'),
                    'price': self.extract_text(element, 'span.price') or self.extract_text(element, 'div.list-item-price'),
                    'location': self.extract_text(element, 'span.location') or self.extract_text(element, 'div.list-item-location'),
                    'url': self._build_full_url(self.extract_attribute(element, 'a.listing-link', 'href') or self.extract_attribute(element, 'a.list-item-link', 'href')),
                    'thumbnail': self.extract_attribute(element, 'img.listing-image', 'src') or self.extract_attribute(element, 'img.list-item-image', 'src'),
                    'features': [
                        feature.get_text(strip=True)
                        for feature in (element.select('ul.features li') or element.select('div.list-item-features span'))
                    ]
                }
                listings.append(listing)
            except Exception as e:
                self.logger.error(f"Error extracting listing: {str(e)}")
                continue
                
        return listings 