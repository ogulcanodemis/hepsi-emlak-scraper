import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import json
import time
import random
from datetime import datetime

class HTMLScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.hepsiemlak.com'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get_page_source(self, url: str) -> Optional[str]:
        """Sayfanın kaynak kodunu al"""
        try:
            # URL'den view-source: kısmını kaldır
            url = url.replace('view-source:', '')
            
            print(f"İstek atılıyor: {url}")
            
            # Önce ana sayfaya istek at
            self.session.get('https://www.hepsiemlak.com')
            
            # Cookies'i güncelle
            cookies = {
                'userType': 'desktop',
                'userLang': 'tr',
                'country': 'tr',
                'isSearchVisited': 'true',
            }
            self.session.cookies.update(cookies)
            
            # Asıl isteği yap
            response = self.session.get(
                url,
                timeout=30,
                allow_redirects=True,
                verify=True
            )
            
            response.raise_for_status()
            
            # Response bilgilerini yazdır
            print(f"Status Code: {response.status_code}")
            print(f"Content Length: {len(response.text)} bytes")
            print(f"Headers: {dict(response.headers)}")
            
            # İçeriği kontrol et
            if len(response.text) < 1000:
                print("Uyarı: Sayfa içeriği çok kısa!")
                print(f"İçerik: {response.text[:500]}")
                return None
            
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Sayfa kaynağı alınırken hata: {str(e)}")
            print(f"Response detayları: {getattr(e.response, 'text', 'No response text')}")
            return None
        except Exception as e:
            print(f"Beklenmeyen hata: {str(e)}")
            return None

    def parse_listings(self, html: str) -> List[Dict]:
        """HTML içeriğinden ilanları parse et"""
        listings = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Debug için HTML'i kaydet
        with open('debug_page.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("Debug için sayfa kaynağı 'debug_page.html' dosyasına kaydedildi")
        
        # İlan listesi container'ını bul
        listing_container = soup.find('ul', class_='list-items-container')
        if not listing_container:
            print("İlan listesi container'ı bulunamadı")
            print("Sayfadaki tüm ul elementleri:")
            for ul in soup.find_all('ul'):
                print(f"Class: {ul.get('class', 'No class')}")
            return listings

        # Tüm ilanları bul
        listing_items = listing_container.find_all('li', class_='listing-item')
        print(f"Bulunan ilan sayısı: {len(listing_items)}")
        
        if not listing_items:
            print("İlanlar bulunamadı. Tüm li elementleri kontrol ediliyor...")
            for li in soup.find_all('li'):
                print(f"Li element class: {li.get('class', 'No class')}")

        for item in listing_items:
            try:
                listing = {}
                
                # Debug için item HTML'ini yazdır
                print(f"\nİlan HTML:\n{item.prettify()[:500]}")
                
                # Başlık
                title_elem = item.find('h3')  # class kontrolünü kaldırdık
                if title_elem:
                    listing['baslik'] = title_elem.text.strip()
                    print(f"Başlık bulundu: {listing['baslik']}")
                else:
                    print("Başlık bulunamadı")
                    continue

                # Fiyat
                price_elem = item.find('span', class_='list-view-price')
                if price_elem:
                    price = price_elem.text.strip()
                    currency = price_elem.find('span', class_='currency')
                    currency_text = currency.text.strip() if currency else 'TL'
                    listing['fiyat'] = f"{price} {currency_text}"
                    print(f"Fiyat bulundu: {listing['fiyat']}")
                else:
                    print("Fiyat bulunamadı")
                    continue

                # İlan tarihi
                date_elem = item.find('span', class_='list-view-date')
                listing['ilan_tarihi'] = date_elem.text.strip() if date_elem else ''
                print(f"İlan tarihi: {listing['ilan_tarihi']}")

                # Özellikler
                specs = item.find('span', class_='right celly')
                if specs:
                    # Oda sayısı
                    room_elem = specs.find('span', class_='houseRoomCount')
                    listing['oda_sayisi'] = room_elem.text.strip() if room_elem else ''
                    
                    # Metrekare
                    size_elem = specs.find('span', class_='squareMeter')
                    listing['metrekare'] = size_elem.text.strip() if size_elem else ''
                    
                    # Bina yaşı
                    age_elem = specs.find('span', class_='buildingAge')
                    listing['bina_yasi'] = age_elem.text.strip() if age_elem else ''
                    
                    # Kat
                    floor_elem = specs.find('span', class_='floortype')
                    listing['kat'] = floor_elem.text.strip() if floor_elem else ''
                    
                    print(f"Özellikler: {listing['oda_sayisi']}, {listing['metrekare']}, {listing['bina_yasi']}, {listing['kat']}")

                # Konum
                location_elem = item.find('span', class_='list-view-location')
                listing['konum'] = location_elem.text.strip() if location_elem else ''
                print(f"Konum: {listing['konum']}")

                # Satan firma
                company_elem = item.find('p', class_='listing-card--owner-info__firm-name')
                listing['satan_firma'] = company_elem.text.strip() if company_elem else ''
                print(f"Satan firma: {listing['satan_firma']}")

                # İlan linki
                link_elem = item.find('a', class_='card-link')
                if link_elem and link_elem.get('href'):
                    listing['url'] = f"https://www.hepsiemlak.com{link_elem['href']}"
                    print(f"URL: {listing['url']}")

                # Resim URL'i
                img_elem = item.find('img', class_='list-view-image')
                listing['resim'] = img_elem['src'] if img_elem and img_elem.get('src') else ''
                print(f"Resim URL: {listing['resim']}")

                # Listeye ekle
                if listing['baslik'] and listing['fiyat']:
                    listings.append(listing)
                    print(f"İlan eklendi: {listing['baslik']}")
                else:
                    print("İlan eklenemedi: Başlık veya fiyat eksik")

            except Exception as e:
                print(f"İlan parse edilirken hata: {str(e)}")
                continue

        return listings

    def search_listings(self, search_url: str, max_pages: Optional[int] = None) -> List[Dict]:
        """Arama URL'inden ilanları topla"""
        all_listings = []
        current_page = 1

        while True:
            if max_pages and current_page > max_pages:
                break

            # Sayfa URL'ini oluştur
            page_url = f"{search_url}{'&' if '?' in search_url else '?'}page={current_page}" if current_page > 1 else search_url
            print(f"\nSayfa {current_page} yükleniyor: {page_url}")

            # Sayfa kaynağını al
            html = self.get_page_source(page_url)
            if not html:
                print("Sayfa kaynağı alınamadı")
                break

            # İlanları parse et
            page_listings = self.parse_listings(html)
            if not page_listings:
                print("Sayfada ilan bulunamadı")
                break

            # İlanları listeye ekle
            all_listings.extend(page_listings)
            print(f"Sayfa {current_page}: {len(page_listings)} ilan eklendi")

            # Sonraki sayfa kontrolü
            soup = BeautifulSoup(html, 'html.parser')
            next_button = soup.find('a', class_='he-pagination__button--next')
            if not next_button or 'disabled' in next_button.get('class', []):
                print("Son sayfaya ulaşıldı")
                break

            current_page += 1
            # Anti-bot önlemi için rastgele bekleme
            time.sleep(random.uniform(2, 4))

        print(f"\nToplam {len(all_listings)} ilan toplandı")
        return all_listings 