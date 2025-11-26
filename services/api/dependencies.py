import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Default to the one in docker-compose if not set
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://fleetmanager:fleetmanager_dev@localhost:5432/fleetmanager")

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
