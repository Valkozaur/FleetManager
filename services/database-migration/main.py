#!/usr/bin/env python3
"""
Database migration runner for FleetManager.
Runs Alembic migrations and exits with appropriate status code.
"""

import sys
import subprocess
import logging
import time
from pathlib import Path

from telemetry import init_telemetry

# Initialize OpenTelemetry
init_telemetry(service_name="database-migration")

logger = logging.getLogger(__name__)


def run_migrations() -> int:
    """
    Run Alembic migrations using upgrade head command.
    
    Returns:
        0 on success, non-zero on failure
    """
    try:
        # Get the path to the database-models package migrations
        migrations_dir = Path(__file__).parent.parent / "database-models"
        alembic_ini = Path(__file__).parent / "alembic.ini"
        
        logger.info("Starting database migrations...")
        logger.info(f"Alembic config: {alembic_ini}")
        logger.info(f"Migrations location: {migrations_dir}")
        
        import time
        from alembic.config import Config
        from alembic import command
        
        start_time = time.time()
        
        # Create Alembic configuration object
        alembic_cfg = Config(str(alembic_ini))
        alembic_cfg.set_main_option("script_location", str(migrations_dir / "migrations"))
        
        # Run alembic upgrade head
        command.upgrade(alembic_cfg, "head")
        
        end_time = time.time()
        logger.info(f"Alembic upgrade took {end_time - start_time:.4f} seconds")
        logger.info("Migrations completed successfully!")
        return 0
            
    except Exception as e:
        logger.error(f"Error running migrations: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(run_migrations())
