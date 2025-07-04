"""Manage the API entrypoints for Repositories"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from msfwk.application import openapi_extra
from msfwk.models import BaseDespResponse, DespResponse
from msfwk.utils.logging import get_logger
from sqlalchemy.ext.asyncio import AsyncSession

from project_management.models.repositories import (
    RepositoryCreationPayload,
    RepositoryInfo,
    RepositoryUpdatePayload,
)
from project_management.routes.api_metadata import TAG_REPOSITORIES
from project_management.services.database_service import get_database_session
from project_management.services.repositories import (
    delete_repository_from_database,
    get_repository_from_database,
    store_repository_in_database,
    update_repository_in_database,
)

router = APIRouter()

logger = get_logger("repository")


@router.get(
    "/repositories/{repository_id}",
    summary="Get a specific repository by ID",
    response_description="Details of the requested repository",
    response_model=BaseDespResponse[RepositoryInfo],
    tags=[TAG_REPOSITORIES],
    openapi_extra=openapi_extra(secured=True, roles=["admin"], internal=True),
)
async def get_repository_by_id(
    repository_id: str, db_session: Annotated[AsyncSession, Depends(get_database_session)]
) -> DespResponse:
    """API route to get a specific repository from the database by its ID

    Args:
        repository_id (str): The UUID of the repository to retrieve
        db_session (AsyncSession): Database session dependency

    Returns:
        DespResponse: Response containing the requested repository
    """
    logger.debug("Getting repository with ID: %s", repository_id)

    repository_uuid = uuid.UUID(repository_id)

    repository: RepositoryInfo = await get_repository_from_database(db_session, repository_uuid)

    return DespResponse(data=repository.model_dump())


@router.post(
    "/repositories",
    summary="Create a new repository",
    response_description="Details of the created repository",
    response_model=BaseDespResponse[RepositoryInfo],
    tags=[TAG_REPOSITORIES],
    openapi_extra=openapi_extra(secured=True, roles=["admin"], internal=True),
)
async def create_repository(
    repository_payload: RepositoryCreationPayload,
    db_session: Annotated[AsyncSession, Depends(get_database_session)],
) -> DespResponse:
    """API route to create a new repository in the database

    Args:
        repository_payload (RepositoryCreationPayload): The repository details to create
        db_session (AsyncSession): Database session dependency

    Returns:
        DespResponse: Response containing the created repository
    """
    logger.debug("Creating new repository: %s", repository_payload)

    created_repository = await store_repository_in_database(db_session, repository_payload)

    return DespResponse(data=created_repository.model_dump(), http_status=200)


@router.patch(
    "/repositories/{repository_id}",
    summary="Update an existing repository",
    response_description="Details of the updated repository",
    response_model=BaseDespResponse[RepositoryInfo],
    tags=[TAG_REPOSITORIES],
    openapi_extra=openapi_extra(secured=True, roles=["admin"], internal=True),
)
async def update_repository(
    repository_id: str,
    repository_payload: RepositoryUpdatePayload,
    db_session: Annotated[AsyncSession, Depends(get_database_session)],
) -> DespResponse:
    """API route to update an existing repository in the database

    Args:
        repository_id (str): The UUID of the repository to update
        repository_payload (RepositoryUpdatePayload): The repository details to update
        db_session (AsyncSession): Database session dependency

    Returns:
        DespResponse: Response containing the updated repository
    """
    logger.debug("Updating repository with ID: %s", repository_id)

    repository_uuid = uuid.UUID(repository_id)

    updated_repository = await update_repository_in_database(db_session, repository_uuid, repository_payload)

    return DespResponse(data=updated_repository.model_dump())


@router.delete(
    "/repositories/{repository_id}",
    summary="Delete an existing repository",
    response_description="Confirmation of repository deletion",
    tags=[TAG_REPOSITORIES],
    openapi_extra=openapi_extra(secured=True, roles=["admin"], internal=True),
)
async def delete_repository(
    repository_id: str, db_session: Annotated[AsyncSession, Depends(get_database_session)]
) -> DespResponse:
    """API route to delete an existing repository from the database

    Args:
        repository_id (str): The UUID of the repository to delete
        db_session (AsyncSession): Database session dependency

    Returns:
        DespResponse: Confirmation of deletion
    """
    logger.debug("Deleting repository with ID: %s", repository_id)

    repository_uuid = uuid.UUID(repository_id)

    await delete_repository_from_database(db_session, repository_uuid)

    return DespResponse(
        data={},
        http_status=200,  # No Content, successful deletion
    )
