from sqlalchemy import create_engine, Engine
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from config import settings

if settings.DEBUG:
    SQLALCHEMY_DATABASE_URL = 'sqlite:///db.sqlite'
    SQLALCHEMY_ASYNC_DATABASE_URL = "sqlite+aiosqlite:///./db.sqlite"
else:
    SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.DB_USER}:{settings.DB_PASS}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    SQLALCHEMY_ASYNC_DATABASE_URL = f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASS}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

engine_async: AsyncEngine = create_async_engine(SQLALCHEMY_ASYNC_DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(
    bind=engine_async,
    expire_on_commit=False,
    class_=AsyncSession,
)

engine: Engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

