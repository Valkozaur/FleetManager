"""
SQLAlchemy ORM models for the FleetManager application.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base declarative class for email processor ORM models."""
    pass


class Order(Base):
    """Order table schema aligned with LogisticsDataExtract."""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email_id = Column(String(255), nullable=False, unique=True, index=True)
    email_subject = Column(String(500), nullable=True)
    email_sender = Column(String(255), nullable=True)
    email_date = Column(DateTime, nullable=True)
    polled_at = Column(DateTime, nullable=True)
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
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:  # pragma: no cover - repr formatting
        return f"<Order(id={self.id}, email_id={self.email_id}, reference_number={self.reference_number})>"
