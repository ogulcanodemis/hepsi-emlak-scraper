from enum import Enum
from typing import Optional, List
from pydantic import BaseModel

class PropertyStatus(str, Enum):
    SATILIK = "satilik"
    KIRALIK = "kiralik"

class PropertyCategory(str, Enum):
    KONUT = "konut"
    ARSA = "arsa"
    ISYERI = "isyeri"
    DEVREMULK = "devremulk"
    TURISTIK = "turistik-isletme"

class ScrapeRequest(BaseModel):
    ilce: str
    durum: PropertyStatus
    kategori: Optional[PropertyCategory] = PropertyCategory.KONUT
    mahalleler: Optional[List[str]] = None

class LocationResponse(BaseModel):
    iller: List[str]
    ilceler: dict[str, List[str]]  # il -> ilçeler
    mahalleler: dict[str, List[str]]  # ilçe -> mahalleler

class CategoryResponse(BaseModel):
    categories: List[PropertyCategory]
    status_types: List[PropertyStatus] 