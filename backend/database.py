from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from sqlalchemy.pool import NullPool
from contextlib import asynccontextmanager
import chromadb
from chromadb.config import Settings as ChromaSettings
import logging

from config import settings

# Determine engine arguments based on database type
is_sqlite = settings.database_url.startswith("sqlite")
engine_kwargs = {
    "pool_pre_ping": True,
    "echo": settings.debug,
}
if not is_sqlite:
    engine_kwargs.update({
        "pool_size": settings.database_pool_size,
        "max_overflow": settings.database_max_overflow,
    })
else:
    engine_kwargs["poolclass"] = NullPool

# SQLAlchemy async engine
engine = create_async_engine(
    settings.database_url,
    **engine_kwargs
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    """Dependency for FastAPI to get DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context():
    """Context manager for getting DB session outside of FastAPI."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# ChromaDB client
chroma_client = chromadb.PersistentClient(
    path=settings.chroma_path,
    settings=ChromaSettings(
        anonymized_telemetry=False,
        allow_reset=True,
    )
)


def get_chroma_collection(name: str = None):
    """Get or create a ChromaDB collection."""
    collection_name = name or settings.chroma_collection
    return chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )


async def init_db():
    """Initialize database - create tables if they don't exist."""
    from models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections."""
    await engine.dispose()


# Health check
async def check_db_health() -> bool:
    """Check database connectivity."""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def check_chroma_health() -> bool:
    """Check ChromaDB connectivity."""
    try:
        chroma_client.heartbeat()
        return True
    except Exception:
        return False


async def init_chroma():
    """Initialize ChromaDB collections."""
    collections = [
        "industrial_safety",
        "incidents",
        "regulations",
        "permits",
        "audits",
        "near_misses",
        "procedures",
    ]
    for coll_name in collections:
        chroma_client.get_or_create_collection(
            name=coll_name,
            metadata={"hnsw:space": "cosine"}
        )