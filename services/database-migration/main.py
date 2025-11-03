#!/usr/bin/env python3
"""
Database migration runner for FleetManager.
Runs Alembic migrations and exits with appropriate status code.
"""

import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
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
        
        # Run alembic upgrade head
        result = subprocess.run(
            ["alembic", "-c", str(alembic_ini), "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=str(migrations_dir)
        )
        
        # Log output
        if result.stdout:
            logger.info(f"Alembic output:\n{result.stdout}")
        if result.stderr:
            logger.error(f"Alembic errors:\n{result.stderr}")
        
        if result.returncode == 0:
            logger.info("Migrations completed successfully!")
            return 0
        else:
            logger.error(f"Migrations failed with exit code {result.returncode}")
            return result.returncode
            
    except Exception as e:
        logger.error(f"Error running migrations: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(run_migrations())
