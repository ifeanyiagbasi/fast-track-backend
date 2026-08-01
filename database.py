import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# 1. Fallback to local postgres if DATABASE_URL isn't set in production env
DEFAULT_LOCAL_DB = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_LOCAL_DB)

# Fix Render URL prefix if needed
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# 2. Create the Async Engine
engine = create_async_engine(DATABASE_URL, echo=True)

# 3. Create Session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session