from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# 1. PostgreSQL Connection URL (Default PostgresApp local connection)
# Format: postgresql+asyncpg://username:password@localhost:5432/dbname
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"


# 2. Create the Async Engine (The pipe between Python and Postgres)
engine = create_async_engine(DATABASE_URL, echo=True)

# 3. Create a Session factory (How we open/close database connections)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 4. Base class for defining our database models
class Base(DeclarativeBase):
    pass

# 5. Dependency helper to get a database session for each request
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session