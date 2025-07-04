"""Manage the API entrypoints"""

from collections.abc import AsyncGenerator

from fastapi import APIRouter
from msfwk.models import BaseModelAdjusted
from msfwk.utils.config import read_config
from msfwk.utils.logging import get_logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

router = APIRouter()

logger = get_logger("application")


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides an async database session.

    Returns
        AsyncGenerator[AsyncSession, Any]: Database session for dependency injection
    """
    config = read_config()
    database_uri = config.get(
        "database_sandbox", "postgresql+asyncpg://postgres:postgres@postgres-db-service:5432/csdb"
    )
    engine = create_async_engine(
        database_uri,
        echo=False,  # Set to False to disable SQL logging
    )
    async_session_local = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    """Dependency to get a database session"""
    async with async_session_local() as session:
        try:
            yield session  # yield to allow usage with "with xxx as Session:"
        finally:
            await session.close()


def update_sqlalchemy_object_from_basemodel(
    sqlalchemy_obj: DeclarativeBase, basemodel_obj: BaseModelAdjusted
) -> DeclarativeBase:
    """Update a SQLAlchemy Declarative Base object with fields from a Pydantic BaseModelAdjusted.

    This function allows for a generic way to update SQLAlchemy database objects
    using Pydantic models, handling only non-None fields from the input model.

    Args:
        sqlalchemy_obj (DeclarativeBase): The SQLAlchemy object to update
        basemodel_obj (BaseModelAdjusted): The Pydantic BaseModelAdjusted containing update values

    Returns:
        DeclarativeBase: The updated SQLAlchemy object
    """
    update_fields = {k: v for k, v in basemodel_obj.model_dump(exclude_unset=True).items() if v is not None}

    for field, value in update_fields.items():
        if hasattr(sqlalchemy_obj, field):
            setattr(sqlalchemy_obj, field, value)
        else:
            logger.warning("Field %s not found in SQLAlchemy object", field)

    return sqlalchemy_obj
