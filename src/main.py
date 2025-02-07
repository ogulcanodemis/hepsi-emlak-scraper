from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Union
from datetime import datetime
import uvicorn
from pydantic import BaseModel, HttpUrl
from .models.database import init_db, Property, Feature, PropertyImage, Seller, SearchHistory
from .scrapers.source_scraper import SourceScraper
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
import logging
from sqlalchemy import or_, cast, String, func
from .models.schemas import (
    PropertyStatus, 
    PropertyCategory, 
    ScrapeRequest, 
    LocationResponse, 
    CategoryResponse
)
from .utils.url_builder import create_hepsiemlak_url

load_dotenv()

# Logging ayarlarını güncelle
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="HepsiEmlak Scraper API")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL'i
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./hepsiemlak.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database
init_db()

# Pydantic models for request/response
class PropertyBase(BaseModel):
    url: str
    title: Optional[str] = None
    price: Optional[float] = None
    location: Optional[str] = None
    description: Optional[str] = None

class PropertyCreate(PropertyBase):
    pass

class PropertyResponse(BaseModel):
    id: int
    url: str
    title: Optional[str] = None
    price: Optional[float] = None
    location: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    features: List[str] = []
    images: List[str] = []
    seller_info: Optional[dict] = {}
    details: Optional[dict] = {}
    raw_data: Optional[dict] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class PaginatedResponse(BaseModel):
    items: List[PropertyResponse]
    total: int
    page: int
    total_pages: int
    has_next: bool
    has_previous: bool

    class Config:
        from_attributes = True

async def scrape_and_save_listings(search_url: str, kategori: PropertyCategory, db: Session):
    """Background task to scrape and save listings."""
    logger.info(f"Scraping başlıyor: {search_url}")
    logger.info(f"Seçilen kategori: {kategori.value}")
    
    scraper = None
    try:
        scraper = SourceScraper()
        # Get all listings from search results with pagination
        listings = scraper.search_listings_with_pagination(search_url, use_pagination=True)
        logger.info(f"Bulunan ilan sayısı: {len(listings)}")
        
        # Seçilen kategoriye göre property type belirle
        property_type = kategori.value
        
        logger.info(f"Search URL: {search_url}")
        logger.info(f"Property type: {property_type}")
        
        # Save search history
        search_history = SearchHistory(
            search_url=search_url,
            search_params={
                "property_type": property_type
            },
            results_count=len(listings),
            created_at=datetime.now()
        )
        db.add(search_history)
        
        # Önce tüm özellikleri topla
        all_features = set()
        for listing_data in listings:
            if 'ozellikler' in listing_data:
                all_features.update(listing_data['ozellikler'])
        
        # Özellikleri kaydet veya var olanları bul
        feature_dict = {}
        for feature_name in all_features:
            feature = db.query(Feature).filter_by(name=feature_name).first()
            if not feature:
                feature = Feature(name=feature_name)
                db.add(feature)
        
        # Commit features first
        try:
            db.commit()
        except Exception as e:
            logger.error(f"Feature commit hatası: {str(e)}")
            db.rollback()
            return
            
        # Refresh feature dictionary after commit
        for feature_name in all_features:
            feature = db.query(Feature).filter_by(name=feature_name).first()
            feature_dict[feature_name] = feature
        
        # Save or update listings
        total_new = 0
        total_updated = 0
        total_unchanged = 0
        
        for listing_data in listings:
            try:
                # URL'e göre mevcut ilanı kontrol et
                existing_property = db.query(Property).filter_by(url=listing_data['url']).first()
                
                # Fiyatı parse et
                price_str = listing_data.get('fiyat', '0')
                try:
                    price_str = price_str.replace('TL', '').replace('.', '').replace(',', '.').strip()
                    price = float(price_str)
                except:
                    logger.error(f"Fiyat dönüştürme hatası: {price_str}")
                    price = 0.0

                if existing_property:
                    # İlan varsa, güncelleme gerekiyor mu kontrol et
                    needs_update = False
                    
                    # Fiyat değişmiş mi?
                    if existing_property.price != price:
                        needs_update = True
                        existing_property.price = price
                    
                    # Başlık değişmiş mi?
                    if existing_property.title != listing_data.get('baslik'):
                        needs_update = True
                        existing_property.title = listing_data.get('baslik', '')
                    
                    # Konum değişmiş mi?
                    if existing_property.location != listing_data.get('konum'):
                        needs_update = True
                        existing_property.location = listing_data.get('konum', '')
                    
                    # Property type değişmiş mi?
                    if existing_property.property_type != property_type:
                        needs_update = True
                        existing_property.property_type = property_type
                    
                    # Raw data değişmiş mi?
                    if existing_property.raw_data != listing_data:
                        needs_update = True
                        existing_property.raw_data = listing_data
                    
                    if needs_update:
                        # Özellikleri güncelle
                        existing_property.features.clear()
                        if 'ozellikler' in listing_data:
                            for feature_name in listing_data['ozellikler']:
                                if feature_name in feature_dict:
                                    existing_property.features.append(feature_dict[feature_name])
                        
                        # Resimleri güncelle
                        existing_property.images.clear()
                        if listing_data.get('resim'):
                            image = PropertyImage(
                                url=listing_data['resim'],
                                is_primary=True
                            )
                            existing_property.images.append(image)
                        
                        existing_property.updated_at = datetime.now()
                        db.add(existing_property)
                        total_updated += 1
                        logger.info(f"İlan güncellendi: {listing_data['url']}")
                    else:
                        total_unchanged += 1
                        logger.info(f"İlan değişmemiş: {listing_data['url']}")
                
                else:
                    # Yeni ilan oluştur
                    new_property = Property(
                        url=listing_data['url'],
                        title=listing_data.get('baslik', ''),
                        price=price,
                        location=listing_data.get('konum', ''),
                        property_type=property_type,  # URL'den tespit edilen kategori
                        raw_data=listing_data,
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    
                    logger.info(f"Yeni ilan ekleniyor - URL: {listing_data['url']}, Type: {property_type}")
                    
                    # Özellikleri ekle
                    if 'ozellikler' in listing_data:
                        for feature_name in listing_data['ozellikler']:
                            if feature_name in feature_dict:
                                new_property.features.append(feature_dict[feature_name])
                    
                    # Resmi ekle
                    if listing_data.get('resim'):
                        image = PropertyImage(
                            url=listing_data['resim'],
                            is_primary=True
                        )
                        new_property.images.append(image)
                    
                    db.add(new_property)
                    total_new += 1
                    logger.info(f"Yeni ilan eklendi: {listing_data['url']}")
                
                # Her 50 işlemde bir commit yap
                if (total_new + total_updated) % 50 == 0:
                    db.commit()
                    logger.info(f"Ara commit yapıldı. Yeni: {total_new}, Güncellenen: {total_updated}, Değişmeyen: {total_unchanged}")
                
            except Exception as e:
                logger.error(f"İlan işlenirken hata: {str(e)}")
                continue
        
        # Final commit
        try:
            db.commit()
            logger.info(f"İşlem tamamlandı. Yeni: {total_new}, Güncellenen: {total_updated}, Değişmeyen: {total_unchanged}")
        except Exception as e:
            logger.error(f"Final commit hatası: {str(e)}")
            db.rollback()
        
    except Exception as e:
        logger.error(f"Genel hata: {str(e)}")
        db.rollback()
    finally:
        if scraper and hasattr(scraper, 'driver'):
            try:
                scraper.driver.quit()
                logger.info("WebDriver başarıyla kapatıldı")
            except Exception as e:
                logger.error(f"WebDriver kapatılırken hata: {str(e)}")
        
    logger.info("İşlem tamamlandı")

@app.post("/scrape")
async def start_scraping(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Start a background scraping task with specified parameters."""
    try:
        # URL oluştur
        search_url = create_hepsiemlak_url(
            ilce=request.ilce,
            durum=request.durum,
            kategori=request.kategori,
            mahalleler=request.mahalleler
        )
        
        # Varsayılan kategori
        kategori = request.kategori or PropertyCategory.KONUT
        
        # Search history kaydet
        search_history = SearchHistory(
            search_url=search_url,
            search_params={
                "ilce": request.ilce,
                "durum": request.durum.value,
                "kategori": kategori.value,
                "mahalleler": request.mahalleler
            },
            created_at=datetime.now()
        )
        db.add(search_history)
        db.commit()
        
        # Background task başlat
        background_tasks.add_task(
            scrape_and_save_listings, 
            search_url=search_url,
            kategori=kategori,
            db=db
        )
        
        return {
            "message": "Scraping started",
            "search_url": search_url,
            "search_id": search_history.id
        }
        
    except Exception as e:
        logger.error(f"Scraping başlatılırken hata: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/properties", response_model=PaginatedResponse)
async def get_properties(
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(12, description="Number of records to return"),
    local_kw: str = Query('', description="Local keyword"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    category: str = Query('', description="Property category (konut, arsa, isyeri)"),
    province: str = Query('', description="Province (il)"),
    district: str = Query('', description="District (ilçe)"),
    neighborhood: str = Query('', description="Neighborhood (mahalle)"),
    status: str = Query('', description="Property status (satilik/kiralik)"),
    db: Session = Depends(get_db)
):
    """Get all properties with optional filters."""
    try:
        logger.info(f"Received request with params: skip={skip}, limit={limit}, "
                   f"local_kw={local_kw}, min_price={min_price}, max_price={max_price}, "
                   f"category={category}, province={province}, district={district}, "
                   f"neighborhood={neighborhood}, status={status}")
        
        # Base query with eager loading of relationships
        query = db.query(Property).options(
            joinedload(Property.features),
            joinedload(Property.images),
            joinedload(Property.seller)
        )
        
        # Apply filters
        try:
            if local_kw:
                query = query.filter(Property.title.ilike(f"%{local_kw}%"))
            
            if min_price is not None:
                query = query.filter(Property.price >= min_price)
            
            if max_price is not None:
                if min_price is not None and max_price < min_price:
                    raise HTTPException(status_code=400, detail="Maximum price cannot be less than minimum price")
                query = query.filter(Property.price <= max_price)
            
            # Kategori filtresi
            if category:
                logger.info(f"Filtering by category: {category}")
                # Frontend'den gelen kategori değerini normalize et
                normalized_category = category.replace('-', '')  # 'is-yeri' -> 'isyeri'
                query = query.filter(Property.property_type == normalized_category)
                # Debug için tüm property type'ları logla
                all_types = db.query(Property.property_type).distinct().all()
                logger.info(f"Available property types: {[t[0] for t in all_types]}")
                logger.info(f"Normalized category: {normalized_category}")
            
            # İl filtresi
            if province:
                query = query.filter(Property.location.ilike(f"%{province}%"))
            
            # İlçe filtresi
            if district:
                logger.info(f"Filtering by district: {district}")
                # URL'den gelen ilçe adını temizle (örn: "beykoz-satilik" -> "beykoz")
                clean_district = district.split('-')[0] if '-' in district else district
                query = query.filter(Property.location.ilike(f"%{clean_district}%"))
                logger.info(f"Clean district name: {clean_district}")
            
            # Durum filtresi (satilik/kiralik)
            if status:
                logger.info(f"Filtering by status: {status}")
                # URL'den durum bilgisini al
                query = query.filter(Property.url.ilike(f"%-{status}/%"))
            
            # Mahalle filtresi
            if neighborhood:
                query = query.filter(Property.location.ilike(f"%{neighborhood}%"))
                
        except Exception as filter_error:
            logger.error(f"Error applying filters: {str(filter_error)}")
            raise HTTPException(status_code=400, detail=f"Invalid filter parameters: {str(filter_error)}")
            
        try:
            # Execute query with pagination
            total = query.count()
            properties = query.order_by(Property.created_at.desc()).offset(skip).limit(limit).all()
            logger.info(f"Found {total} properties in total, returning {len(properties)} properties")
        except Exception as query_error:
            logger.error(f"Error executing query: {str(query_error)}")
            raise HTTPException(status_code=500, detail=f"Database query error: {str(query_error)}")
        
        # Convert to response model
        response_items = []
        for prop in properties:
            try:
                raw_data = prop.raw_data or {}
                seller_info = {}
                if prop.seller:
                    seller_info = {
                        'name': prop.seller.name,
                        'company': prop.seller.company,
                        'phone': prop.seller.phone,
                        'membership_status': prop.seller.membership_status,
                        'profile_url': prop.seller.profile_url
                    }
                
                property_response = PropertyResponse(
                    id=prop.id,
                    url=prop.url,
                    title=prop.title or raw_data.get('baslik'),
                    price=prop.price,
                    location=prop.location or raw_data.get('konum'),
                    description=prop.description or raw_data.get('description'),
                    created_at=prop.created_at,
                    features=[f.name for f in prop.features] if prop.features else [],
                    images=[img.url for img in prop.images] if prop.images else [],
                    seller_info=seller_info,
                    raw_data=raw_data
                )
                response_items.append(property_response)
            except Exception as prop_error:
                logger.error(f"Error processing property {prop.id}: {str(prop_error)}")
                continue

        # Calculate pagination info
        current_page = skip // limit + 1
        total_pages = (total + limit - 1) // limit
            
        return PaginatedResponse(
            items=response_items,
            total=total,
            page=current_page,
            total_pages=total_pages,
            has_next=current_page < total_pages,
            has_previous=current_page > 1
        )
        
    except HTTPException as http_error:
        logger.error(f"HTTP error in get_properties: {str(http_error)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_properties: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/properties/{property_id}", response_model=PropertyResponse)
async def get_property(property_id: int, db: Session = Depends(get_db)):
    """Get a specific property by ID."""
    try:
        # Query with eager loading of relationships
        property = db.query(Property).options(
            joinedload(Property.features),
            joinedload(Property.images),
            joinedload(Property.seller)
        ).filter(Property.id == property_id).first()
        
        if property is None:
            raise HTTPException(status_code=404, detail="Property not found")

        # Convert to response model
        try:
            raw_data = property.raw_data or {}
            
            # Seller info
            seller_info = {}
            if property.seller:
                seller_info = {
                    'name': property.seller.name,
                    'company': property.seller.company,
                    'phone': property.seller.phone,
                    'membership_status': property.seller.membership_status,
                    'profile_url': property.seller.profile_url
                }
            
            # Property details
            details = {
                'room_count': property.room_count or raw_data.get('oda_sayisi'),
                'size': property.size or raw_data.get('metrekare'),
                'floor': property.floor or raw_data.get('kat'),
                'building_age': property.building_age or raw_data.get('bina_yasi'),
                'heating_type': property.heating_type or raw_data.get('isitma_tipi'),
                'bathroom_count': property.bathroom_count or raw_data.get('banyo_sayisi'),
                'balcony': property.balcony or raw_data.get('balkon'),
                'furnished': property.furnished or raw_data.get('esyali'),
                'property_type': property.property_type or raw_data.get('ilan_tipi')
            }
            
            property_response = PropertyResponse(
                id=property.id,
                url=property.url,
                title=property.title or raw_data.get('baslik'),
                price=property.price,
                location=property.location or raw_data.get('konum'),
                description=property.description or raw_data.get('description'),
                created_at=property.created_at,
                features=[f.name for f in property.features] if property.features else [],
                images=[img.url for img in property.images] if property.images else [],
                seller_info=seller_info,
                details=details,
                raw_data=raw_data
            )
            return property_response
            
        except Exception as prop_error:
            logger.error(f"Error processing property {property_id}: {str(prop_error)}")
            raise HTTPException(status_code=500, detail=f"Error processing property: {str(prop_error)}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching property {property_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search-history")
async def get_search_history():
    """Get all search history."""
    db = SessionLocal()
    try:
        history = db.query(SearchHistory).order_by(SearchHistory.created_at.desc()).all()
        return history
    finally:
        db.close()

@app.get("/categories", response_model=CategoryResponse)
async def get_categories():
    """Get all available categories and status types."""
    return {
        "categories": list(PropertyCategory),
        "status_types": list(PropertyStatus)
    }

@app.get("/locations/{il}", response_model=LocationResponse)
async def get_locations(il: str, db: Session = Depends(get_db)):
    """Get all locations for a specific province."""
    try:
        # İl bazlı lokasyonları getir
        locations = db.query(Property.location).distinct().all()
        
        iller = set()
        ilceler = {}
        mahalleler = {}
        
        for loc in locations:
            if loc[0]:
                parts = [p.strip() for p in loc[0].split('/')]
                
                if len(parts) >= 1:
                    iller.add(parts[0])
                    if parts[0] not in ilceler:
                        ilceler[parts[0]] = set()
                
                if len(parts) >= 2:
                    ilceler[parts[0]].add(parts[1])
                    if parts[1] not in mahalleler:
                        mahalleler[parts[1]] = set()
                
                if len(parts) >= 3:
                    mahalleler[parts[1]].add(parts[2])
        
        # Set'leri list'e çevir
        return {
            "iller": sorted(list(iller)),
            "ilceler": {k: sorted(list(v)) for k, v in ilceler.items()},
            "mahalleler": {k: sorted(list(v)) for k, v in mahalleler.items()}
        }
        
    except Exception as e:
        logger.error(f"Lokasyonlar getirilirken hata: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/update-property-types")
async def update_property_types(db: Session = Depends(get_db)):
    """Update property types based on URLs."""
    try:
        # Tüm property'leri getir
        properties = db.query(Property).all()
        updated_count = 0
        
        for prop in properties:
            old_type = prop.property_type
            new_type = None
            
            # URL'den kategori bilgisini çıkar
            url_parts = prop.url.lower().split('/')
            
            # URL formatı: .../beykoz-satilik/isyeri gibi veya .../isyeri-bina, .../dukkan-magaza gibi
            if len(url_parts) >= 2:
                last_part = url_parts[-1].split('?')[0]  # Query parametrelerini kaldır
                last_part = last_part.split('-')[0]  # Alt kategorileri kaldır (isyeri-bina -> isyeri)
                
                if last_part == 'arsa':
                    new_type = 'arsa'
                elif last_part in ['isyeri', 'dukkan', 'plaza', 'ofis', 'depo', 'cafe']:
                    new_type = 'isyeri'
                elif last_part == 'devremulk':
                    new_type = 'devremulk'
                elif last_part == 'turistik-isletme':
                    new_type = 'turistik-isletme'
                else:
                    new_type = 'konut'
            else:
                new_type = 'konut'
            
            if old_type != new_type:
                prop.property_type = new_type
                updated_count += 1
                logger.info(f"Property type updated: {old_type} -> {new_type} for URL: {prop.url}")
        
        db.commit()
        return {"message": f"Updated {updated_count} properties"}
        
    except Exception as e:
        logger.error(f"Error updating property types: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/debug/property-types")
async def get_property_types(db: Session = Depends(get_db)):
    """Get all unique property types for debugging."""
    try:
        types = db.query(Property.property_type, func.count(Property.id)).group_by(Property.property_type).all()
        return {
            "property_types": [
                {"type": t[0], "count": t[1]} 
                for t in types
            ]
        }
    finally:
        db.close()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 