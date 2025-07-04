import uuid

from despsharedlibrary.schemas.sandbox_schema import Repositories
from msfwk.exceptions import DespGenericError
from msfwk.utils.logging import get_logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from project_management.models.constants import REPOSITORY_NOT_FOUND_ERROR
from project_management.models.repositories import (
    RepositoryCreationPayload,
    RepositoryInfo,
    RepositoryUpdatePayload,
)
from project_management.services.database_service import update_sqlalchemy_object_from_basemodel

logger = get_logger("repository")


async def get_repository_from_database(session: AsyncSession, repository_uuid: uuid.UUID) -> RepositoryInfo:
    """Fetch repository from the database
    Args:
        session : database session created in the route method
        repository_uuid : uuid of the repository to fetch
    """
    query = select(Repositories).where(Repositories.id == repository_uuid)
    result = await session.execute(query)
    repository = result.scalar_one_or_none()

    logger.debug("Found repository: %s", repository)

    if repository is None:
        raise DespGenericError(status_code=404, message="Repository not found", code=REPOSITORY_NOT_FOUND_ERROR)

    return RepositoryInfo(id=repository.id, url=repository.url, username=repository.username, token=repository.token)


async def store_repository_in_database(
    session: AsyncSession, repository_payload: RepositoryCreationPayload
) -> RepositoryInfo:
    """Store repository in the database

    Args:
        session : database session created in the route method
        repository_payload (RepositoryCreationPayload): The repository to store

    Returns:
        RepositoryDatabaseClass: The stored repository object
    """
    # If no ID is provided, generate a new UUID
    repository_id = repository_payload.id or str(uuid.uuid4())

    # Ensure the ID is a UUID object
    repository_id_uuid = uuid.UUID(repository_id)

    repository_to_create = Repositories(
        id=repository_id_uuid,
        url=repository_payload.url,
        username=repository_payload.username,
        token=repository_payload.token,
    )

    session.add(repository_to_create)
    await session.commit()

    return await get_repository_from_database(session, repository_to_create.id)


async def update_repository_in_database(
    session: AsyncSession, repository_uuid: uuid.UUID, repository_payload: RepositoryUpdatePayload
) -> RepositoryInfo:
    """Update an existing repository in the database

    Args:
        session: database session created in the route method
        repository_uuid: UUID of the repository to update
        repository_payload: Payload containing fields to update

    Returns:
        RepositoryDatabaseClass: The updated repository object
    """
    # First, retrieve the existing repository
    query = select(Repositories).where(Repositories.id == repository_uuid)
    result = await session.execute(query)
    repository = result.scalar_one_or_none()

    if repository is None:
        raise DespGenericError(
            status_code=404, message="Repository to update not found", code=REPOSITORY_NOT_FOUND_ERROR
        )

    # Update only the non-None fields
    update_sqlalchemy_object_from_basemodel(repository, repository_payload)

    session.add(repository)
    await session.commit()

    # Return the updated repository
    return await get_repository_from_database(session, repository_uuid)


async def delete_repository_from_database(session: AsyncSession, repository_uuid: uuid.UUID) -> None:
    """Delete an existing repository from the database

    Args:
        session: database session created in the route method
        repository_uuid: UUID of the repository to delete

    Raises:
        DespGenericError: If the repository is not found or cannot be deleted
    """
    # First, check if the repository exists
    query = select(Repositories).where(Repositories.id == repository_uuid)
    result = await session.execute(query)
    repository = result.scalar_one_or_none()

    if repository is None:
        raise DespGenericError(
            status_code=404, message="Repository to delete not found", code=REPOSITORY_NOT_FOUND_ERROR
        )

    await session.delete(repository)
    await session.commit()
