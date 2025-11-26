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


# Route Management Models

import uuid
import enum
from sqlalchemy import ForeignKey, Float, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID, ENUM, JSONB

class RouteStatus(str, enum.Enum):
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"

class DriverStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    ON_ROUTE = "ON_ROUTE"

class StopActivityType(str, enum.Enum):
    PICKUP = "PICKUP"
    DROP = "DROP"

class StopStatus(str, enum.Enum):
    PENDING = "PENDING"
    ARRIVED = "ARRIVED"
    COMPLETED = "COMPLETED"

class Truck(Base):
    __tablename__ = "trucks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plate_number = Column(String(50), unique=True, nullable=False)
    capacity_weight = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Truck(id={self.id}, plate_number={self.plate_number})>"

class Driver(Base):
    __tablename__ = "drivers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=False)
    status = Column(ENUM(DriverStatus, name="driver_status_enum", create_type=False), default=DriverStatus.AVAILABLE, nullable=False)

    def __repr__(self) -> str:
        return f"<Driver(id={self.id}, name={self.name})>"

class Route(Base):
    __tablename__ = "routes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("drivers.id"), nullable=False)
    truck_id = Column(UUID(as_uuid=True), ForeignKey("trucks.id"), nullable=False)
    status = Column(ENUM(RouteStatus, name="route_status_enum", create_type=False), default=RouteStatus.PLANNED, nullable=False)
    scheduled_start_at = Column(DateTime, nullable=False)

    def __repr__(self) -> str:
        return f"<Route(id={self.id}, status={self.status})>"

class RouteStop(Base):
    __tablename__ = "route_stops"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id = Column(UUID(as_uuid=True), ForeignKey("routes.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    sequence_number = Column(Integer, nullable=False)
    activity_type = Column(ENUM(StopActivityType, name="stop_activity_type_enum", create_type=False), nullable=False)
    status = Column(ENUM(StopStatus, name="stop_status_enum", create_type=False), default=StopStatus.PENDING, nullable=False)
    location = Column(JSONB, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<RouteStop(id={self.id}, sequence={self.sequence_number}, status={self.status})>"
