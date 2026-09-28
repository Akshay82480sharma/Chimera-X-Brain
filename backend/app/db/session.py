"""Async database session and Base for Chimera-X.

This is the SINGLE source of truth for the SQLAlchemy Base and async engine.
All models inherit from this Base. All routes use get_db() for sessions.
"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


# Ensure data directory exists
DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "chimera.db")

# Check for Postgres URL, fallback to SQLite
POSTGRES_URL = os.environ.get("POSTGRES_URL")
if POSTGRES_URL:
    DATABASE_URL = POSTGRES_URL
    # Standard connection args for Postgres
    connect_args = {}
else:
    DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"
    # Timeout needed for SQLite
    connect_args = {"timeout": 15.0}

engine = create_async_engine(
    DATABASE_URL, 
    echo=False, 
    connect_args=connect_args
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def init_db():
    """Create all tables on startup."""
    # Import models to ensure they register with Base.metadata
    import app.db.models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """Async dependency that yields an AsyncSession."""
    async with AsyncSessionLocal() as session:
        yield session
