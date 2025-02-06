from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, JSON, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./hepsiemlak.db")

engine = create_engine(DATABASE_URL)
Base = declarative_base()

# Many-to-many relationship table for property features
property_features = Table(
    'property_features',
    Base.metadata,
    Column('property_id', Integer, ForeignKey('properties.id'), primary_key=True),
    Column('feature_id', Integer, ForeignKey('features.id'), primary_key=True)
)

class Property(Base):
    __tablename__ = 'properties'

    id = Column(Integer, primary_key=True)
    external_id = Column(String, unique=True, index=True)
    title = Column(String, index=True)
    price = Column(Float, index=True)
    currency = Column(String)
    location = Column(String, index=True)
    description = Column(String)
    property_type = Column(String)
    size = Column(Float)
    room_count = Column(String)
    floor = Column(String)
    building_age = Column(String)
    heating_type = Column(String)
    bathroom_count = Column(String)
    balcony = Column(String)
    furnished = Column(String)
    url = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    raw_data = Column(JSON)  # Store the complete raw data

    # Relationships
    features = relationship('Feature', secondary=property_features, back_populates='properties')
    images = relationship('PropertyImage', back_populates='property')
    seller = relationship('Seller', back_populates='properties')
    seller_id = Column(Integer, ForeignKey('sellers.id'))

class Feature(Base):
    __tablename__ = 'features'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    properties = relationship('Property', secondary=property_features, back_populates='features')

class PropertyImage(Base):
    __tablename__ = 'property_images'

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('properties.id'))
    url = Column(String)
    is_primary = Column(String, default=False)
    
    property = relationship('Property', back_populates='images')

class Seller(Base):
    __tablename__ = 'sellers'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    company = Column(String)
    phone = Column(String)
    email = Column(String)
    membership_status = Column(String)  # Gold, Silver veya Standart üye
    profile_url = Column(String)
    total_listings = Column(String)
    properties = relationship('Property', back_populates='seller')

class SearchHistory(Base):
    __tablename__ = 'search_history'

    id = Column(Integer, primary_key=True)
    search_url = Column(String)
    search_params = Column(JSON)
    results_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(engine) 