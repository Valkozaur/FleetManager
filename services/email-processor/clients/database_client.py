"""
PostgreSQL Database Client for FleetManager
Handles database connections and order persistence
"""

import logging
from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from database_models import Base, Order
from models.logistics import LogisticsDataExtract


class DatabaseClient:
    """
    Client for managing PostgreSQL database connections and operations
    """

    def __init__(self, database_url: str):
        """
        Initialize the database client

        Args:
            database_url: PostgreSQL connection string (e.g., postgresql://user:pass@host:port/db)
        """
        self.logger = logging.getLogger(__name__)
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None

        try:
            # Create database engine
            self.engine = create_engine(
                database_url,
                pool_pre_ping=True,  # Verify connections before using
                pool_size=5,
                max_overflow=10,
                echo=False  # Set to True for SQL query logging
            )

            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )

            self.logger.info("Database client initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize database client: {e}")
            raise

    def initialize_database(self) -> bool:
        """
        Create all tables if they don't exist

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create all tables
            Base.metadata.create_all(bind=self.engine)
            self.logger.info("Database tables initialized successfully")

            # Verify orders table exists
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            if 'orders' in tables:
                self.logger.info("Orders table verified")
                return True
            else:
                self.logger.error("Orders table not found after initialization")
                return False

        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            return False

    def get_session(self) -> Session:
        """
        Create a new database session

        Returns:
            SQLAlchemy Session object
        """
        if not self.SessionLocal:
            raise RuntimeError("Database client not initialized")

        return self.SessionLocal()

    def save_order(self, logistics_data: LogisticsDataExtract) -> Optional[int]:
        """
        Save a new order to the database

        Args:
            logistics_data: LogisticsDataExtract Pydantic model

        Returns:
            The ID of the saved order, or None if save failed
        """
        session = None
        try:
            session = self.get_session()

            # Check if order with this email_id already exists
            existing_order = session.query(Order).filter_by(
                email_id=logistics_data.email_id
            ).first()

            if existing_order:
                self.logger.warning(
                    f"Order with email_id {logistics_data.email_id} already exists. Skipping."
                )
                return existing_order.id

            # Create Order ORM model from Pydantic model
            try:
                email_date_dt = logistics_data.email_date if isinstance(logistics_data.email_date, datetime) else (datetime.fromisoformat(logistics_data.email_date) if logistics_data.email_date else None)
                polled_at_dt = datetime.fromisoformat(logistics_data.polled_at) if logistics_data.polled_at else None
                loading_date_dt = datetime.strptime(logistics_data.loading_date, "%d.%m.%Y") if logistics_data.loading_date else None
                unloading_date_dt = datetime.strptime(logistics_data.unloading_date, "%d.%m.%Y") if logistics_data.unloading_date else None
            except ValueError as ve:
                self.logger.error(f"Date parsing error for email_id {logistics_data.email_id}: {ve}")
                print(f"ERROR: Date parsing error for email_id {logistics_data.email_id}: {ve}") # Debug print
                return None

            order = Order(
                email_id=logistics_data.email_id,
                email_subject=logistics_data.email_subject,
                email_sender=logistics_data.email_sender,
                email_date=email_date_dt,
                polled_at=polled_at_dt,
                loading_address=logistics_data.loading_address,
                unloading_address=logistics_data.unloading_address,
                loading_date=loading_date_dt,
                unloading_date=unloading_date_dt,
                loading_coordinates=logistics_data.loading_coordinates,
                unloading_coordinates=logistics_data.unloading_coordinates,
                cargo_description=logistics_data.cargo_description,
                weight=logistics_data.weight,
                vehicle_type=logistics_data.vehicle_type,
                special_requirements=logistics_data.special_requirements,
                reference_number=logistics_data.reference_number
            )

            # Add and commit
            session.add(order)
            session.commit()
            session.refresh(order)

            self.logger.info(f"Successfully saved order with ID {order.id} (email_id: {logistics_data.email_id})")
            return order.id

        except IntegrityError as e:
            if session:
                session.rollback()
            self.logger.error(f"Integrity error saving order (email_id: {logistics_data.email_id}): {e}")
            print(f"ERROR: Integrity error saving order (email_id: {logistics_data.email_id}): {e}") # Debug print
            return None

        except SQLAlchemyError as e:
            if session:
                session.rollback()
            self.logger.error(f"Database error saving order (email_id: {logistics_data.email_id}): {e}")
            print(f"ERROR: Database error saving order (email_id: {logistics_data.email_id}): {e}") # Debug print
            return None

        except Exception as e:
            if session:
                session.rollback()
            self.logger.error(f"Unexpected error saving order (email_id: {logistics_data.email_id}): {e}")
            print(f"ERROR: Unexpected error saving order (email_id: {logistics_data.email_id}): {e}") # Debug print
            return None

        finally:
            if session:
                session.close()

    def test_connection(self) -> bool:
        """
        Test database connection

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                self.logger.info("Database connection test successful")
                return True
        except Exception as e:
            self.logger.error(f"Database connection test failed: {e}")
            return False

    def close(self):
        """
        Close database connections and cleanup resources
        """
        try:
            if self.engine:
                self.engine.dispose()
                self.logger.info("Database connections closed")
        except Exception as e:
            self.logger.error(f"Error closing database connections: {e}")
