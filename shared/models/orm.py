"""
SQLAlchemy ORM models for FleetManager database
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Order(Base):
    """
    Order table schema matching LogisticsDataExtract model
    """
    __tablename__ = 'orders'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Email metadata fields
    email_id = Column(String(255), nullable=False, unique=True, index=True)
    email_subject = Column(String(500), nullable=True)
    email_sender = Column(String(255), nullable=True)
    email_date = Column(DateTime, nullable=True)
    polled_at = Column(DateTime, nullable=True)

    # Logistics fields
    loading_address = Column(Text, nullable=False)
    unloading_address = Column(Text, nullable=False)
    loading_date = Column(DateTime, nullable=False)
    unloading_date = Column(DateTime, nullable=False)
    loading_coordinates = Column(String(100), nullable=True)
    unloading_coordinates = Column(String(100), nullable=True)
    cargo_description = Column(Text, nullable=False)
    weight = Column(String(100), nullable=False)
    vehicle_type = Column(String(100), nullable=False)
    special_requirements = Column(Text, nullable=True)
    reference_number = Column(String(100), nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Order(id={self.id}, email_id={self.email_id}, reference_number={self.reference_number})>"
