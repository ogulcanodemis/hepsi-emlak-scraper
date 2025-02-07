from typing import List, Optional
from ..models.schemas import PropertyStatus, PropertyCategory
import re
from urllib.parse import quote
import logging

logger = logging.getLogger(__name__)

def format_location_name(name: str) -> str:
    """Lokasyon ismini URL'ye uygun formata çevirir"""
    # Türkçe karakterleri değiştir
    replacements = {
        'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c',
        'İ': 'i', 'Ğ': 'g', 'Ü': 'u', 'Ş': 's', 'Ö': 'o', 'Ç': 'c',
        'â': 'a', 'î': 'i', 'û': 'u', 'ê': 'e', 'ô': 'o',
        'Â': 'a', 'Î': 'i', 'Û': 'u', 'Ê': 'e', 'Ô': 'o'
    }
    
    formatted = name.lower()
    for old, new in replacements.items():
        formatted = formatted.replace(old, new)
    
    # Sadece alfanumerik karakterler ve tire kalacak şekilde temizle
    formatted = re.sub(r'[^a-z0-9\s-]', '', formatted)
    # Boşlukları tire ile değiştir
    formatted = re.sub(r'\s+', '-', formatted.strip())
    # Birden fazla tireyi tekli tireye çevir
    formatted = re.sub(r'-+', '-', formatted)
    
    return formatted

def create_hepsiemlak_url(
    ilce: str,
    durum: PropertyStatus,
    kategori: Optional[PropertyCategory] = None,
    mahalleler: Optional[List[str]] = None
) -> str:
    """HepsiEmlak URL'i oluşturur"""
    # Base URL
    base_url = "https://www.hepsiemlak.com"
    
    # İlçe adını formatla
    ilce = format_location_name(ilce)
    
    # Ana URL yapısını oluştur
    url = f"{base_url}/{ilce}-{durum.value}"
    
    # Eğer kategori varsa ve konut değilse ekle
    if kategori and kategori != PropertyCategory.KONUT:
        # Kategori değerini URL formatına çevir
        kategori_value = kategori.value
        if kategori == PropertyCategory.ISYERI:
            kategori_value = 'isyeri'
        url += f"/{kategori_value}"
    
    # Mahalleler varsa ekle
    if mahalleler and len(mahalleler) > 0:
        # Mahalleleri formatla ve encode et
        formatted_districts = [
            quote(f"{ilce}-{format_location_name(m)}", safe='')
            for m in mahalleler
        ]
        districts_param = ",".join(formatted_districts)
        url += f"?districts={districts_param}"
    
    logger.info(f"Created URL: {url} for category: {kategori.value if kategori else 'None'}")
    return url 