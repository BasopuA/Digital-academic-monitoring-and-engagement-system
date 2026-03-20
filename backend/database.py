"""
Database configuration module.

This module sets up both synchronous and asynchronous connections to a
PostgreSQL database using SQLAlchemy and the `databases` library.
It loads credentials from environment variables and exposes shared
instances such as the SQLAlchemy engine, session factory, async database
connector, and the declarative base for ORM models.

Environment Variables:
    DATABASE_URL

"""

# pylint: disable=unused-import,import-outside-toplevel, cyclic-import,import-error
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

# Load environment variables
load_dotenv()

# Database connection string
DATABASE_URL = os.getenv("DATABASE_URL")
# DATABASE_URL = "postgresql+asyncpg://postgres:1234@localhost:5433/healthDB"

# Create async engine with tuned pool settings
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # enable excessive logging
    pool_size=5,  # number of persistent connections
    max_overflow=20,  # allow temporary extra connections
    pool_timeout=60,  # wait 60s before TimeoutError
    pool_recycle=1800,  # recycle every 30 minutes
    pool_pre_ping=True,  # check connection health status
)

# Async session maker
session_local = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base model class
Base = declarative_base()


async def init_db():
    """
    Initialize database and create all tables.
    Should be called at startup once.
    """

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """
    Dependency for FastAPI endpoints.
    Ensures each request gets its own session,
    and closes it cleanly after use.
    """
    async with session_local() as session:
        try:
            yield session
        finally:
            await session.close()
