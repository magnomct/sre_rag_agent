"""
SRE RAG Agent — Asynchronous Database Engine & Session Factory
Provides SQLAlchemy 2.0 AsyncEngine, scoped sessions, and database lifecycle helpers.
"""

from typing import AsyncGenerator
import structlog
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase
from config import settings

logger = structlog.get_logger()


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 declarative base for all relational models."""
    pass


# Global AsyncEngine with connection pooling and health pre-ping
engine: AsyncEngine = create_async_engine(
    settings.async_postgres_url,
    pool_size=settings.postgres_pool_size,
    max_overflow=settings.postgres_max_overflow,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.debug,
)

# Async session factory
AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an isolated async database session."""
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> bool:
    """
    Verify database connectivity during startup and ensure relational schema exists.
    Returns True if database is reachable, False otherwise.
    """
    try:
        from models import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("database_connection_initialized", host=settings.postgres_host, db=settings.postgres_db)
        return True
    except Exception as exc:
        try:
            async with engine.connect() as conn:
                from sqlalchemy import text
                await conn.execute(text("SELECT 1"))
            logger.info("database_connection_initialized", host=settings.postgres_host, db=settings.postgres_db)
            return True
        except Exception:
            logger.warning(
                "database_initialization_offline_fallback",
                error=str(exc),
                detail="Application will run with in-memory fallback until DB is reachable."
            )
            return False


async def close_db() -> None:
    """Gracefully dispose connection pool upon application shutdown."""
    await engine.dispose()
    logger.info("database_connection_closed")
