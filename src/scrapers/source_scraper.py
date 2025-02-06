import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import random
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SourceScraper:
    def __init__(self):
        self.setup_driver()

    def setup_driver(self):
        """WebDriver'ı yapılandır"""
        try:
            options = uc.ChromeOptions()
            
            # Temel ayarlar
            options.add_argument('--start-maximized')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--lang=tr-TR')
            options.add_argument('--disable-blink-features=AutomationControlled')
            
            # User agent
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.6834.160 Safari/537.36')
            
            # Çerezleri ve resimleri etkinleştir
            prefs = {
                'profile.default_content_settings': {
                    'images': 1,
                    'javascript': 1,
                    'cookies': 1,
                    'plugins': 1,
                    'popups': 2,
                    'geolocation': 2,
                    'notifications': 2
                },
                'intl.accept_languages': 'tr-TR,tr,en-US,en'
            }
            options.add_experimental_option('prefs', prefs)
            
            try:
                # Önce Chrome 132 ile dene
                self.driver = uc.Chrome(
                    options=options,
                    use_subprocess=True,
                    version_main=132  # Mevcut Chrome sürümü
                )
            except Exception as e:
                logger.warning(f"Chrome 132 ile bağlantı hatası: {str(e)}")
                # Sürüm belirtmeden tekrar dene
                self.driver = uc.Chrome(
                    options=options,
                    use_subprocess=True,
                    version_main=None
                )
            
            # JavaScript ile otomasyon belirtilerini gizle
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            # Bekleme süresini ayarla
            self.wait = WebDriverWait(self.driver, 30)
            logger.info("WebDriver başarıyla başlatıldı")
            
        except Exception as e:
            logger.error(f"Driver başlatılamadı: {str(e)}")
            raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, 'driver'):
            self.driver.quit()
            logger.info("WebDriver kapatıldı")

    def get_page_source(self, url: str) -> Optional[str]:
        """Web sayfasının kaynak kodunu al"""
        try:
            logger.info(f"Sayfa yükleniyor: {url}")
            
            # Sayfayı yükle
            self.driver.get(url)
            time.sleep(5)
            
            # Çerezleri kabul et
            try:
                cookie_button = self.wait.until(EC.element_to_be_clickable((
                    By.CSS_SELECTOR, "button#onetrust-accept-btn-handler"
                )))
                cookie_button.click()
                logger.info("Çerezler kabul edildi")
                time.sleep(2)
            except Exception as e:
                logger.warning(f"Çerez butonu bulunamadı: {str(e)}")
            
            # İlan listesinin yüklenmesini bekle
            try:
                self.wait.until(EC.presence_of_element_located((
                    By.CSS_SELECTOR, 'ul.list-items-container'
                )))
                logger.info("İlan listesi container'ı yüklendi")
                
                # İlanların yüklenmesini bekle
                items = self.wait.until(EC.presence_of_all_elements_located((
                    By.CSS_SELECTOR, 'li.listing-item'
                )))
                logger.info(f"İlanlar yüklendi: {len(items)} adet")
                
            except Exception as e:
                logger.error(f"İlanlar yüklenemedi: {str(e)}")
                return None
            
            # Sayfayı yavaşça kaydır
            try:
                # Scroll işlemi için JavaScript
                self.driver.execute_script("""
                    window.scrollTo({
                        top: document.body.scrollHeight,
                        behavior: 'smooth'
                    });
                """)
                time.sleep(3)  # Scroll'un tamamlanmasını bekle
                
                # Son ilan sayısını kontrol et
                final_items = self.driver.find_elements(By.CSS_SELECTOR, 'li.listing-item')
                logger.info(f"Toplam ilan sayısı: {len(final_items)}")
                
            except Exception as e:
                logger.error(f"Scroll hatası: {str(e)}")
            
            # Kaynak kodunu al
            page_source = self.driver.page_source
            
            # Debug için kaydet
            with open('page_source.html', 'w', encoding='utf-8') as f:
                f.write(page_source)
            logger.info("Sayfa kaynağı kaydedildi")
            
            return page_source
            
        except Exception as e:
            logger.error(f"Sayfa kaynağı alınırken hata: {str(e)}")
            return None

    def parse_listings(self, html: str) -> List[Dict]:
        """HTML içeriğinden ilanları parse et"""
        listings = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Ana ul container'ını bul
        container = soup.select_one('ul.list-items-container')
        if not container:
            logger.error("İlan listesi container'ı bulunamadı")
            return []
        
        # İlanları bul
        listing_items = container.select('li.listing-item')
        logger.info(f"Bulunan ilan sayısı: {len(listing_items)}")
        
        for item in listing_items:
            try:
                listing = {}
                
                # Başlık
                title = item.select_one('h3')
                if title:
                    listing['baslik'] = title.text.strip()
                    logger.info(f"Başlık: {listing['baslik']}")
                
                # Fiyat
                price_elem = item.select_one('span.list-view-price')
                if price_elem:
                    price = price_elem.text.strip()
                    currency = price_elem.select_one('span.currency')
                    currency_text = currency.text.strip() if currency else 'TL'
                    listing['fiyat'] = f"{price} {currency_text}"
                    logger.info(f"Fiyat: {listing['fiyat']}")
                
                # İlan tarihi
                date_elem = item.select_one('span.list-view-date')
                if date_elem:
                    listing['ilan_tarihi'] = date_elem.text.strip()
                    logger.info(f"İlan tarihi: {listing['ilan_tarihi']}")
                
                # Konum
                location = item.select_one('span.list-view-location')
                if location:
                    listing['konum'] = location.text.strip()
                    logger.info(f"Konum: {listing['konum']}")
                
                # İlan linki
                link = item.select_one('a[href*="/istanbul-"]')
                if link and link.get('href'):
                    listing['url'] = f"https://www.hepsiemlak.com{link['href']}"
                    logger.info(f"URL: {listing['url']}")
                
                # Resim
                img = item.select_one('img.list-view-image')
                if img and img.get('src'):
                    listing['resim'] = img['src']
                    logger.info(f"Resim: {listing['resim']}")
                
                # Özellikler
                features = []
                
                # İlan tipi
                prop_type = item.select_one('span.left')
                if prop_type:
                    listing['ilan_tipi'] = prop_type.text.strip()
                    features.append(prop_type.text.strip())
                
                # Detaylı özellikler
                specs = item.select_one('span.right.celly')
                if specs:
                    # Oda sayısı
                    room_count = specs.select_one('span.houseRoomCount')
                    if room_count:
                        listing['oda_sayisi'] = room_count.text.strip()
                        features.append(room_count.text.strip())
                    
                    # Metrekare
                    square_meter = specs.select_one('span.squareMeter')
                    if square_meter:
                        listing['metrekare'] = square_meter.text.strip()
                        features.append(square_meter.text.strip())
                    
                    # Bina yaşı
                    building_age = specs.select_one('span.buildingAge')
                    if building_age:
                        listing['bina_yasi'] = building_age.text.strip()
                        features.append(building_age.text.strip())
                    
                    # Kat
                    floor = specs.select_one('span.floortype')
                    if floor:
                        listing['kat'] = floor.text.strip()
                        features.append(floor.text.strip())
                
                listing['ozellikler'] = features
                
                # Emlak ofisi bilgileri
                office = item.select_one('p.listing-card--owner-info__firm-name')
                if office:
                    listing['emlak_ofisi'] = office.text.strip()
                    logger.info(f"Emlak ofisi: {listing['emlak_ofisi']}")
                
                # Emlak ofisi logosu
                office_logo = item.select_one('img.branded-image')
                if office_logo and office_logo.get('src'):
                    listing['emlak_ofisi_logo'] = office_logo['src']
                
                # Emlak ofisi linki
                office_link = item.select_one('a[href*="/emlak-ofisi/"]')
                if office_link and office_link.get('href'):
                    listing['emlak_ofisi_url'] = f"https://www.hepsiemlak.com{office_link['href']}"
                
                # Fotoğraf sayısı
                photo_count = item.select_one('span.photo-count')
                if photo_count:
                    listing['fotograf_sayisi'] = photo_count.text.strip()

                # Telefon numaralarını al
                try:
                    # Telefon göster butonunu bul ve tıkla
                    phone_button = self.driver.find_element(By.CSS_SELECTOR, f"li#{item.get('id')} button.action-telephone")
                    self.driver.execute_script("arguments[0].click();", phone_button)
                    time.sleep(1)  # Numaraların yüklenmesini bekle

                    # Telefon numaralarını topla
                    phone_numbers = []
                    phone_elements = self.driver.find_elements(By.CSS_SELECTOR, f"li#{item.get('id')} ul.list-phone-numbers li a")
                    for phone_elem in phone_elements:
                        phone_number = phone_elem.text.strip()
                        if phone_number:
                            phone_numbers.append(phone_number)

                    # Danışman adını al
                    consultant_name = self.driver.find_element(By.CSS_SELECTOR, f"li#{item.get('id')} span.phone-consultant-name").text.strip()
                    
                    listing['telefon_numaralari'] = phone_numbers
                    listing['danısman_adi'] = consultant_name
                    logger.info(f"Telefon numaraları: {phone_numbers}")
                    logger.info(f"Danışman adı: {consultant_name}")

                except Exception as e:
                    logger.error(f"Telefon numaraları alınırken hata: {str(e)}")
                    listing['telefon_numaralari'] = []
                    listing['danısman_adi'] = ""
                
                if listing:  # Eğer en az bir bilgi varsa listeye ekle
                    listings.append(listing)
                    logger.info(f"İlan başarıyla eklendi")
                
            except Exception as e:
                logger.error(f"İlan parse edilirken hata: {str(e)}")
                continue
        
        return listings

    def search_listings(self, search_url: str) -> List[Dict]:
        """Arama URL'inden ilanları topla"""
        try:
            # Sayfa kaynağını al
            html = self.get_page_source(search_url)
            if not html:
                logger.error("Sayfa kaynağı alınamadı")
                return []
            
            # İlanları parse et
            listings = self.parse_listings(html)
            logger.info(f"Toplam {len(listings)} ilan başarıyla toplandı")
            
            return listings
            
        except Exception as e:
            logger.error(f"İlan toplama hatası: {str(e)}")
            return []
        finally:
            if hasattr(self, 'driver'):
                self.driver.quit()
                logger.info("WebDriver kapatıldı") 