"""
Database models package for FleetManager.
Exports ORM models at package root for clean imports.
"""

from .orm import Base, Order

__all__ = ["Base", "Order"]
