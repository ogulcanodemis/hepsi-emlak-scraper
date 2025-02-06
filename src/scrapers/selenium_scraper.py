import json
import time
import random
import logging
from typing import Dict, List, Optional, Tuple

import undetected_chromedriver as uc
from fake_useragent import UserAgent
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime

class SeleniumScraper:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_driver()

    def setup_driver(self):
        """WebDriver'ı yapılandır"""
        options = uc.ChromeOptions()
        
        # Proxy ayarları
        PROXY = "http://proxy.example.com:8080"  # Buraya çalışan bir proxy adresi gelecek
        uc.DesiredCapabilities.CHROME['proxy'] = {
            "httpProxy": PROXY,
            "sslProxy": PROXY,
            "proxyType": "MANUAL",
        }
        
        # Gerçek bir tarayıcı user agent'ı kullan
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Temel ayarlar
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Stealth mode için ek ayarlar
        options.add_argument('--disable-features=IsolateOrigins,site-per-process,SitePerProcess')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-extensions')
        
        # Çerezleri ve resimleri etkinleştir
        prefs = {
            'profile.default_content_settings': {
                'images': 1,
                'javascript': 1,
                'cookies': 1,
                'plugins': 1,
                'popups': 2,
                'geolocation': 2,
                'notifications': 2,
                'auto_select_certificate': 2,
                'fullscreen': 2,
                'mouselock': 2,
                'mixed_script': 2,
                'media_stream': 2,
                'media_stream_mic': 2,
                'media_stream_camera': 2,
                'protocol_handlers': 2,
                'ppapi_broker': 2,
                'automatic_downloads': 2,
                'midi_sysex': 2,
                'push_messaging': 2,
                'ssl_cert_decisions': 2,
                'metro_switch_to_desktop': 2,
                'protected_media_identifier': 2,
                'app_banner': 2,
                'site_engagement': 2,
                'durable_storage': 2
            }
        }
        options.add_experimental_option('prefs', prefs)
        
        # Otomasyon belirtilerini gizle
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        try:
            # Driver'ı başlat
            self.driver = uc.Chrome(
                options=options,
                driver_executable_path=None,
                version_main=None,
                use_subprocess=True
            )
            
            # Timeoutları ayarla
            self.driver.set_page_load_timeout(60)  # Timeout süresini artır
            self.wait = WebDriverWait(self.driver, 30)  # Wait süresini artır
            
            # JavaScript'i etkinleştir ve otomasyon belirtilerini gizle
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['tr-TR', 'tr', 'en-US', 'en']
                    });
                    window.chrome = {
                        runtime: {}
                    };
                '''
            })
            
        except Exception as e:
            self.logger.error(f"Driver başlatılamadı: {str(e)}")
            raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, 'driver'):
            self.driver.quit()

    def random_sleep(self, min_seconds=2, max_seconds=5):
        time.sleep(random.uniform(min_seconds, max_seconds))

    def scroll_page(self):
        """Sayfayı aşağı kaydır ve dinamik içeriğin yüklenmesini bekle"""
        try:
            print("Sayfa kaydırma ve ilan toplama başlıyor...")
            processed_items = set()  # İşlenen ilanların ID'lerini tutacak set
            
            last_height = self.driver.execute_script("return document.documentElement.scrollHeight")
            scroll_pause_time = 1.5
            scroll_attempts = 0
            max_attempts = 20  # Maksimum deneme sayısı
            
            while scroll_attempts < max_attempts:
                # Mevcut ilanları bul ve işle
                print("\nMevcut ilanlar kontrol ediliyor...")
                listing_items = self.driver.find_elements(By.CSS_SELECTOR, "li.listing-item")
                
                for item in listing_items:
                    try:
                        # İlanın ID'sini al
                        item_id = item.get_attribute('id')
                        if item_id not in processed_items:
                            print(f"Yeni ilan bulundu: {item_id}")
                            # İlanı işle
                            listing = self._process_listing_item(item)
                            if listing:
                                processed_items.add(item_id)
                    except Exception as e:
                        print(f"İlan işlenirken hata: {str(e)}")
                        continue
                
                print(f"Toplam işlenen ilan sayısı: {len(processed_items)}")
                
                # Sayfayı parça parça kaydır
                current_height = self.driver.execute_script("return window.pageYOffset")
                scroll_step = 800  # Her seferinde 800px kaydır
                new_height = min(current_height + scroll_step, last_height)
                
                # Smooth scroll
                self.driver.execute_script(f"window.scrollTo({{top: {new_height}, behavior: 'smooth'}})")
                
                # Yeni içeriğin yüklenmesi için bekle
                time.sleep(scroll_pause_time)
                
                # Yeni yüksekliği hesapla
                new_total_height = self.driver.execute_script("return document.documentElement.scrollHeight")
                
                # Eğer sayfa sonuna geldiysek ve yeni içerik yüklenmediyse
                if new_total_height == last_height and new_height >= last_height:
                    scroll_attempts += 1
                    print(f"Sayfa sonu kontrol ediliyor... ({scroll_attempts}/3)")
                    if scroll_attempts >= 3:  # 3 kez aynı yüksekliği görürsek bitir
                        break
                else:
                    scroll_attempts = 0  # Yeni içerik yüklendiyse sayacı sıfırla
                    last_height = new_total_height
                
                # Rastgele bekleme süresi ekle (anti-bot önlemi)
                time.sleep(random.uniform(0.5, 1.0))
            
            print("Sayfa kaydırma ve ilan toplama tamamlandı")
            return list(processed_items)
            
        except Exception as e:
            print(f"Sayfa kaydırma hatası: {str(e)}")
            return []

    def _process_listing_item(self, item) -> Optional[Dict]:
        """Tek bir ilan öğesini işle"""
        try:
            listing = {}
            
            # Başlık
            try:
                listing['baslik'] = item.find_element(By.CSS_SELECTOR, "div.list-view-title h3").text.strip()
                print(f"İşleniyor: {listing['baslik']}")
            except:
                listing['baslik'] = ""
                return None  # Başlık bulunamazsa bu ilanı atla
            
            # Fiyat
            try:
                price = item.find_element(By.CSS_SELECTOR, "span.list-view-price").text.strip()
                currency = item.find_element(By.CSS_SELECTOR, "span.currency").text.strip()
                listing['fiyat'] = f"{price} {currency}"
            except:
                listing['fiyat'] = ""
                return None  # Fiyat bulunamazsa bu ilanı atla
            
            # İlan tarihi
            try:
                listing['ilan_tarihi'] = item.find_element(By.CSS_SELECTOR, "span.list-view-date").text.strip()
            except:
                listing['ilan_tarihi'] = ""
            
            # Özellikler (oda sayısı, metrekare, yaş, kat)
            try:
                specs = item.find_element(By.CSS_SELECTOR, "span.right.celly")
                listing['oda_sayisi'] = specs.find_element(By.CSS_SELECTOR, "span.houseRoomCount").text.strip()
                listing['metrekare'] = specs.find_element(By.CSS_SELECTOR, "span.squareMeter").text.strip()
                listing['bina_yasi'] = specs.find_element(By.CSS_SELECTOR, "span.buildingAge").text.strip()
                listing['kat'] = specs.find_element(By.CSS_SELECTOR, "span.floortype").text.strip()
            except:
                listing['oda_sayisi'] = ""
                listing['metrekare'] = ""
                listing['bina_yasi'] = ""
                listing['kat'] = ""
            
            # Konum
            try:
                listing['konum'] = item.find_element(By.CSS_SELECTOR, "span.list-view-location").text.strip()
            except:
                listing['konum'] = ""
            
            # Satan firma
            try:
                listing['satan_firma'] = item.find_element(By.CSS_SELECTOR, "p.listing-card--owner-info__firm-name").text.strip()
            except:
                listing['satan_firma'] = ""
            
            # İlan linki
            try:
                listing['url'] = item.find_element(By.CSS_SELECTOR, "a.card-link").get_attribute('href')
            except:
                listing['url'] = ""
            
            # Resim URL'i
            try:
                listing['resim'] = item.find_element(By.CSS_SELECTOR, "img.list-view-image").get_attribute('src')
            except:
                listing['resim'] = ""
            
            print(f"İlan başarıyla işlendi: {listing['baslik']}")
            return listing
            
        except Exception as e:
            print(f"İlan işlenirken hata: {str(e)}")
            return None

    def safe_find_element_text(self, selector: str, parent_element=None) -> str:
        """Güvenli bir şekilde element metnini bul"""
        try:
            element = (parent_element or self.driver).find_element(By.CSS_SELECTOR, selector)
            return element.text.strip()
        except:
            return ""

    def analyze_page_structure(self, url: str):
        """Sayfa yapısını analiz et ve debug bilgisi yazdır"""
        try:
            self.driver.get(url)
            self.random_sleep(5, 7)
            
            print("\n=== SAYFA ANALİZİ BAŞLIYOR ===")
            print(f"URL: {url}")
            
            # İlan kartları analizi
            print("\nİlan kartları analizi:")
            listing_cards = self.driver.find_elements(By.CSS_SELECTOR, '[class*="listing-item"], [class*="list-item"], [class*="card"]')
            print(f"Bulunan kart sayısı: {len(listing_cards)}")
            
            if listing_cards:
                print("\nİlk kartın detaylı analizi:")
                first_card = listing_cards[0]
                print(f"Kart class: {first_card.get_attribute('class')}")
                print(f"Kart HTML:\n{first_card.get_attribute('outerHTML')[:500]}")
                
                # Link analizi
                links = first_card.find_elements(By.TAG_NAME, 'a')
                print("\nLinkler:")
                for link in links:
                    print(f"- href: {link.get_attribute('href')}")
                    print(f"- class: {link.get_attribute('class')}")
                    print(f"- text: {link.text[:100]}")
                
                # Başlık analizi
                titles = first_card.find_elements(By.CSS_SELECTOR, 'h1, h2, h3, h4, h5, h6, [class*="title"]')
                print("\nBaşlıklar:")
                for title in titles:
                    print(f"- tag: {title.tag_name}")
                    print(f"- class: {title.get_attribute('class')}")
                    print(f"- text: {title.text}")
                
                # Fiyat analizi
                prices = first_card.find_elements(By.CSS_SELECTOR, '[class*="price"], [class*="fee"]')
                print("\nFiyatlar:")
                for price in prices:
                    print(f"- class: {price.get_attribute('class')}")
                    print(f"- text: {price.text}")
                
                # Özellikler analizi
                features = first_card.find_elements(By.CSS_SELECTOR, '[class*="feature"], [class*="property"], [class*="detail"]')
                print("\nÖzellikler:")
                for feature in features:
                    print(f"- class: {feature.get_attribute('class')}")
                    print(f"- text: {feature.text[:100]}")
            
            # Sayfa kaynağını kaydet
            with open('search_page_source.html', 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            print("\nSayfa kaynağı 'search_page_source.html' dosyasına kaydedildi")
            
            print("\n=== SAYFA ANALİZİ TAMAMLANDI ===\n")
            
        except Exception as e:
            print(f"Analiz sırasında hata: {str(e)}")

    def search_listings(self, search_url: str, max_pages: Optional[int] = None) -> List[Dict]:
        """Arama sonuçlarından ilanları çek"""
        listings = []
        
        try:
            print(f"Sayfa yükleniyor: {search_url}")
            
            # Önce ana sayfaya git
            # Önce ana sayfaya git ve çerezleri kabul et
            self.driver.get("https://www.hepsiemlak.com")
            time.sleep(5)
            
            try:
                cookie_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[id*='onetrust-accept']")))
                cookie_button.click()
                print("Çerezler kabul edildi")
                time.sleep(2)
            except:
                print("Çerez butonu bulunamadı")
            
            # Şimdi arama sayfasına git
            print("Arama sayfasına yönlendiriliyor...")
            self.driver.get(search_url)
            
            # Cloudflare korumasını geçmek için bekle
            print("Cloudflare koruması bekleniyor...")
            time.sleep(15)
            
            # Sayfanın tamamen yüklenmesini bekle
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "li[class*='listing-item']")))
                print("Sayfa yüklendi, ilanlar bulundu")
            except:
                print("İlanlar yüklenemedi! Sayfa kaynağı kontrol ediliyor...")
                with open('debug_page.html', 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                return []

            # Sayfayı aşağı kaydır
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            while True:
                # Sayfayı aşağı kaydır
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

                # Yeni yüksekliği hesapla
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            # İlanları topla
            listing_items = self.driver.find_elements(By.CSS_SELECTOR, "li[class*='listing-item']")
            print(f"Bulunan ilan sayısı: {len(listing_items)}")

            for item in listing_items:
                try:
                    # İlanın görünür olmasını bekle
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", item)
                    time.sleep(0.5)

                    listing = {}
                    
                    # Başlık
                    try:
                        title = item.find_element(By.CSS_SELECTOR, "h3").text.strip()
                        listing['baslik'] = title
                        print(f"Başlık: {title}")
                    except:
                        continue

                    # Fiyat
                    try:
                        price = item.find_element(By.CSS_SELECTOR, "span.list-view-price").text.strip()
                        listing['fiyat'] = price
                        print(f"Fiyat: {price}")
                    except:
                        continue

                    # Özellikler
                    try:
                        specs = item.find_element(By.CSS_SELECTOR, "span.right.celly")
                        listing['oda_sayisi'] = specs.find_element(By.CSS_SELECTOR, "span.houseRoomCount").text.strip()
                        listing['metrekare'] = specs.find_element(By.CSS_SELECTOR, "span.squareMeter").text.strip()
                        listing['bina_yasi'] = specs.find_element(By.CSS_SELECTOR, "span.buildingAge").text.strip()
                        listing['kat'] = specs.find_element(By.CSS_SELECTOR, "span.floortype").text.strip()
                    except:
                        listing['oda_sayisi'] = ""
                        listing['metrekare'] = ""
                        listing['bina_yasi'] = ""
                        listing['kat'] = ""

                    # Konum
                    try:
                        listing['konum'] = item.find_element(By.CSS_SELECTOR, "span.list-view-location").text.strip()
                    except:
                        listing['konum'] = ""

                    # İlan linki
                    try:
                        link = item.find_element(By.CSS_SELECTOR, "a.card-link").get_attribute('href')
                        listing['url'] = link
                    except:
                        continue

                    # Resim
                    try:
                        listing['resim'] = item.find_element(By.CSS_SELECTOR, "img.list-view-image").get_attribute('src')
                    except:
                        listing['resim'] = ""

                    # Satan firma
                    try:
                        listing['satan_firma'] = item.find_element(By.CSS_SELECTOR, "p.listing-card--owner-info__firm-name").text.strip()
                    except:
                        listing['satan_firma'] = ""

                    # İlan tarihi
                    try:
                        listing['ilan_tarihi'] = item.find_element(By.CSS_SELECTOR, "span.list-view-date").text.strip()
                    except:
                        listing['ilan_tarihi'] = ""

                    if listing.get('baslik') and listing.get('fiyat'):
                        listings.append(listing)
                        print(f"İlan eklendi: {listing['baslik']}")

                except Exception as e:
                    print(f"İlan işlenirken hata: {str(e)}")
                    continue

            print(f"Toplam {len(listings)} ilan başarıyla toplandı")
            return listings

        except Exception as e:
            print(f"Genel hata: {str(e)}")
            return listings

    def extract_listing_details(self, url: str) -> Optional[Dict]:
        """Tek bir ilan detayını çek"""
        def _extract():
            try:
                # Sayfayı yükle ve daha uzun bekle
                self.driver.get(url)
                self.random_sleep(8, 12)  # Bekleme süresini artır
                
                # Sayfanın yüklenmesini bekle - birden fazla selector dene
                try:
                    # Farklı elementleri kontrol et
                    selectors = [
                        '.realty-name',
                        '.detail-title',
                        '.detail-price-wrap',
                        'h1.fontRB'
                    ]
                    
                    for selector in selectors:
                        try:
                            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                            print(f"Sayfa yüklendi, bulunan element: {selector}")
                            break
                        except:
                            continue
                            
                    # Sayfanın tam yüklenmesi için ekstra bekle
                    self.random_sleep(2, 4)
                    
                except TimeoutException:
                    self.logger.error(f"Sayfa yüklenemedi (timeout): {url}")
                    return None
                
                # Sayfayı yavaşça kaydır
                self.scroll_page()
                self.random_sleep(2, 3)

                # Sayfa kaynağını kontrol et
                page_source = self.driver.page_source
                if len(page_source) < 1000:  # Sayfa çok kısaysa muhtemelen hata sayfası
                    self.logger.error(f"Sayfa içeriği çok kısa, muhtemelen hata sayfası: {url}")
                    return None

                # Temel bilgileri topla
                details = {
                    'url': url,
                    'title': (
                        self.safe_find_element_text('.realty-name h1.fontRB') or 
                        self.safe_find_element_text('h1.fontRB') or
                        self.safe_find_element_text('h1.detail-title')
                    ),
                    'price': (
                        self.safe_find_element_text('.detail-price-wrap .price') or
                        self.safe_find_element_text('.price') or
                        self.safe_find_element_text('.fz24-text.price')
                    ),
                    'location': self._extract_location(),
                    'description': (
                        self.safe_find_element_text('.description-content') or
                        self.safe_find_element_text('.description')
                    ),
                    'features': self.extract_features(),
                    'details': self.extract_property_details(),
                    'images': self.extract_images(),
                    'seller_info': self.extract_seller_info(),
                    'scraped_at': datetime.now().isoformat()
                }

                # Temel alanların kontrolü
                if not details['title'] or not details['price']:
                    self.logger.error(f"Temel bilgiler eksik: {url}")
                    print(f"Sayfa kaynağı önizlemesi: {self.driver.page_source[:500]}")
                    return None

                return details

            except Exception as e:
                self.logger.error(f"İlan detayı çekilirken hata: {str(e)}")
                return None

        return self._retry_with_new_driver(_extract)

    def _extract_location(self) -> str:
        """Konum bilgisini çıkar"""
        try:
            # Yeni konum yapısından bilgiyi al
            location_items = self.driver.find_elements(By.CSS_SELECTOR, '.detail-info-location li')
            if location_items:
                # Tüm konum öğelerini birleştir (İstanbul, Beşiktaş, Ortaköy Mah.)
                location_parts = [item.text.strip() for item in location_items]
                return ' '.join(location_parts)
            
            return ""
        except Exception as e:
            self.logger.error(f"Konum bilgisi çıkarılırken hata: {str(e)}")
            return ""

    def extract_features(self) -> List[str]:
        """İlan özelliklerini çek"""
        features = []
        
        try:
            # Ana özellikler listesini bul
            feature_items = self.driver.find_elements(By.CSS_SELECTOR, '.adv-info-list .spec-item')
            
            for item in feature_items:
                try:
                    # Özellik adı ve değerini al
                    label = item.find_element(By.CSS_SELECTOR, '.txt').text.strip()
                    value = item.find_element(By.CSS_SELECTOR, '.value-txt').text.strip()
                    if label and value:
                        features.append(f"{label}: {value}")
                except:
                    continue

            return features
        except Exception as e:
            self.logger.error(f"Özellikler çekilirken hata: {str(e)}")
            return features

    def extract_property_details(self) -> Dict:
        """Detaylı özellik bilgilerini çek"""
        details = {}
        try:
            elements = self.driver.find_elements(By.CSS_SELECTOR, '.adv-info-list .spec-item')
            for element in elements:
                try:
                    label = element.find_element(By.CSS_SELECTOR, '.txt').text.strip()
                    value = element.find_element(By.CSS_SELECTOR, '.value-txt').text.strip()
                    if label and value:
                        # Özel karakterleri temizle ve küçük harfe çevir
                        key = label.lower().replace(' ', '_').replace('ı', 'i').replace('ğ', 'g').replace('ü', 'u').replace('ş', 's').replace('ö', 'o').replace('ç', 'c')
                        details[key] = value
                except:
                    continue
        except Exception as e:
            self.logger.error(f"Detaylar çekilirken hata: {str(e)}")
        return details

    def extract_images(self) -> List[str]:
        """Tüm ilan fotoğraflarını çek"""
        images = []
        try:
            # Ana resim elementlerini bul
            img_elements = self.driver.find_elements(By.CSS_SELECTOR, '.img-wrapper img')
            for img in img_elements:
                try:
                    # Önce src attribute'unu kontrol et, yoksa data-src'yi dene
                    src = img.get_attribute('src') or img.get_attribute('data-src')
                    if src and src not in images:  # Tekrar eden resimleri önle
                        images.append(src)
                except:
                    continue
                
            return list(set(images))  # Tekrar eden resimleri temizle
        except Exception as e:
            self.logger.error(f"Resimler çekilirken hata: {str(e)}")
            return images

    def extract_seller_info(self) -> Dict:
        """Satıcı bilgilerini çek"""
        seller_info = {}
        try:
            # Satıcı bilgileri bölümünün yüklenmesini bekle
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.owner-header')))
                self.random_sleep(1, 2)
            except TimeoutException:
                print("Satıcı bilgileri bölümü yüklenemedi")
                return {
                    'name': '',
                    'membership_status': '',
                    'phones': [],
                    'profile_url': ''
                }
            
            # İsim
            seller_info['name'] = self.safe_find_element_text('.firm-card-detail .firm-link')
            
            # Üyelik durumu
            member_type = self.safe_find_element_text('.member-type')
            member_badge = self.safe_find_element_text('.member-badge')
            member_year = self.safe_find_element_text('.member-badge-year')
            
            if member_type and member_badge:
                seller_info['membership_status'] = f"{member_type} ({member_badge}{member_year})"
            elif member_type:
                seller_info['membership_status'] = member_type
            else:
                seller_info['membership_status'] = ''
            
            # Telefon numaraları
            phones = []
            try:
                # Telefon göster butonuna tıkla
                show_phone_button = self.wait.until(EC.element_to_be_clickable((
                    By.CSS_SELECTOR, '.owner-phone-numbers-button'
                )))
                show_phone_button.click()
                self.random_sleep(2, 3)
                
                # Telefon numaralarını topla
                phone_elements = self.driver.find_elements(By.CSS_SELECTOR, '.owner-phone-numbers-list li')
                for phone_elem in phone_elements:
                    phone_text = phone_elem.text.strip()
                    if phone_text:
                        phones.append(phone_text)
            except TimeoutException:
                self.logger.warning("Telefon numaraları gösterilemiyor")
            except Exception as e:
                self.logger.error(f"Telefon numaraları alınırken hata: {str(e)}")
            
            seller_info['phones'] = phones
            
            # Profil linki
            try:
                profile_link = self.driver.find_element(By.CSS_SELECTOR, '.firm-card-detail .card-link')
                seller_info['profile_url'] = profile_link.get_attribute('href')
            except:
                seller_info['profile_url'] = ''
            
        except Exception as e:
            self.logger.error(f"Satıcı bilgileri çekilirken hata: {str(e)}")
            seller_info = {
                'name': '',
                'membership_status': '',
                'phones': [],
                'profile_url': ''
            }
            
        return seller_info

    def _extract_price(self, price_str: str) -> str:
        """Fiyat bilgisini temizle ve formatla"""
        if not price_str:
            return "0 TL"
        try:
            # Sayısal değeri al
            price = float(str(price_str).replace('.', '').replace(',', '.').strip())
            # Formatlı string olarak döndür
            return f"{price:,.0f} TL".replace(',', '.')
        except:
            return "0 TL"

    def _retry_with_new_driver(self, func, *args, max_retries=3):
        """Başarısız işlemleri yeni driver ile tekrar dene"""
        for attempt in range(max_retries):
            try:
                return func(*args)
            except Exception as e:
                self.logger.error(f"Hata (Deneme {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    self.logger.info("Driver yeniden başlatılıyor...")
                    try:
                        self.driver.quit()
                    except:
                        pass
                    self.setup_driver()
                    time.sleep(2)  # Driver'ın başlaması için bekle
                else:
                    raise 