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
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
import logging

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

async def scrape_and_save_listings(search_url: str, db: Session):
    """Background task to scrape and save listings."""
    logger.info(f"Scraping başlıyor: {search_url}")
    
    scraper = SourceScraper()
    try:
        # Get all listings from search results
        listings = scraper.search_listings(search_url)
        logger.info(f"Bulunan ilan sayısı: {len(listings)}")
        
        # Save search history
        search_history = SearchHistory(
            search_url=search_url,
            search_params={},
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
                db.flush()  # ID'leri almak için flush
            feature_dict[feature_name] = feature
        
        # Save each listing
        for listing_data in listings:
            try:
                # Parse price
                price_str = listing_data.get('fiyat', '0')
                try:
                    price_str = price_str.replace('TL', '').replace('.', '').replace(',', '.').strip()
                    price = float(price_str)
                except:
                    logger.error(f"Fiyat dönüştürme hatası: {price_str}")
                    price = 0.0

                # Create property object
                property_obj = Property(
                    url=listing_data['url'],
                    title=listing_data.get('baslik', ''),
                    price=price,
                    location=listing_data.get('konum', ''),
                    raw_data=listing_data,
                    created_at=datetime.now()
                )
                
                # Add features
                if 'ozellikler' in listing_data:
                    for feature_name in listing_data['ozellikler']:
                        if feature_name in feature_dict:
                            property_obj.features.append(feature_dict[feature_name])
                
                # Add image
                if listing_data.get('resim'):
                    image = PropertyImage(
                        url=listing_data['resim'],
                        is_primary=True
                    )
                    property_obj.images.append(image)
                
                db.add(property_obj)
                logger.info(f"İlan kaydedildi: {listing_data.get('baslik', 'Başlıksız')}")
                
            except Exception as e:
                logger.error(f"İlan kaydedilirken hata: {str(e)}")
                continue
        
        # Commit all changes
        try:
            db.commit()
            logger.info("Tüm değişiklikler kaydedildi")
        except Exception as e:
            logger.error(f"Veritabanı commit hatası: {str(e)}")
            db.rollback()
        
    except Exception as e:
        logger.error(f"Genel hata: {str(e)}")
        db.rollback()
    finally:
        if hasattr(scraper, 'driver'):
            scraper.driver.quit()
        
    logger.info("İşlem tamamlandı")

@app.post("/scrape")
async def start_scraping(
    background_tasks: BackgroundTasks,
    search_url: str = Query(..., description="The HepsiEmlak search URL to scrape")
):
    """Start a background scraping task."""
    db = SessionLocal()
    try:
        # Record search history
        search_history = SearchHistory(search_url=search_url)
        db.add(search_history)
        db.commit()

        # Start background scraping
        background_tasks.add_task(scrape_and_save_listings, search_url, db)
        return {"message": "Scraping started", "search_id": search_history.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/properties", response_model=List[PropertyResponse])
async def get_properties(
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(12, description="Number of records to return"),
    local_kw: str = Query('', description="Local keyword"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    location: str = Query('', description="Location"),
    db: Session = Depends(get_db)
):
    """Get all properties with optional filters."""
    try:
        logger.info(f"Received request with params: skip={skip}, limit={limit}, local_kw={local_kw}, min_price={min_price}, max_price={max_price}, location={location}")
        
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
            if location:
                query = query.filter(Property.location.ilike(f"%{location}%"))
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
        response = []
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
                response.append(property_response)
            except Exception as prop_error:
                logger.error(f"Error processing property {prop.id}: {str(prop_error)}")
                continue
            
        return response
        
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

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 