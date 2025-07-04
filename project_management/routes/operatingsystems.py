"""Manage the API entrypoints for Operating Systems"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from msfwk.application import openapi_extra
from msfwk.models import BaseDespResponse, DespResponse
from msfwk.utils.logging import get_logger
from sqlalchemy.ext.asyncio import AsyncSession

from project_management.models.expanded_models import OperatingSystemExpanded
from project_management.models.operatingsystems import (
    OperatingSystemCreationPayload,
    OperatingSystemInfo,
    OperatingSystemUpdatePayload,
)
from project_management.routes.api_metadata import TAG_OPERATINGSYSTEMS
from project_management.services.database_service import get_database_session
from project_management.services.operatingsystems import (
    delete_operatingsystem_from_database,
    get_all_operatingsystems_from_database,
    get_operatingsystem_from_database,
    store_operatingsystem_in_database,
    update_operatingsystem_in_database,
)

router = APIRouter()

logger = get_logger("operatingsystem")


@router.get(
    "/operatingsystems/{operatingsystem_id}",
    summary="Get a specific operating system by ID",
    response_description="Details of the requested operating system",
    response_model=BaseDespResponse[OperatingSystemInfo],
    tags=[TAG_OPERATINGSYSTEMS],
    openapi_extra=openapi_extra(secured=True, roles=["user"]),
)
async def get_operatingsystem_by_id(
    operatingsystem_id: str, db_session: Annotated[AsyncSession, Depends(get_database_session)]
) -> DespResponse:
    """API route to get a specific operating system from the database by its ID

    Args:
        operatingsystem_id (str): The UUID of the operating system to retrieve
        db_session (AsyncSession): Database session dependency

    Returns:
        DespResponse: Response containing the requested operating system
    """
    logger.debug("Getting operating system with ID: %s", operatingsystem_id)

    operatingsystem_uuid = uuid.UUID(operatingsystem_id)

    operatingsystem: OperatingSystemExpanded = await get_operatingsystem_from_database(db_session, operatingsystem_uuid)

    return DespResponse(data=operatingsystem.model_dump())


@router.get(
    "/operatingsystems",
    summary="Get all operating systems",
    response_description="List of all operating systems",
    response_model=BaseDespResponse[list[OperatingSystemExpanded]],
    tags=[TAG_OPERATINGSYSTEMS],
    openapi_extra=openapi_extra(secured=True, roles=["user"]),
)
async def get_all_operatingsystems(db_session: Annotated[AsyncSession, Depends(get_database_session)]) -> DespResponse:
    """API route to retrieve all operatingsystems from the database

    Args:
        db_session (AsyncSession): Database session dependency

    Returns:
        DespResponse: Response containing a list of all operatingsystems
    """
    logger.debug("Retrieving all operatingsystems")

    operatingsystems = await get_all_operatingsystems_from_database(db_session)

    return DespResponse(data=[os.model_dump() for os in operatingsystems])


@router.post(
    "/operatingsystems",
    summary="Create a new operating system",
    response_description="Details of the created operating system",
    response_model=BaseDespResponse[OperatingSystemInfo],
    tags=[TAG_OPERATINGSYSTEMS],
    openapi_extra=openapi_extra(secured=True, roles=["admin"]),
)
async def create_operatingsystem(
    operatingsystem_payload: OperatingSystemCreationPayload,
    db_session: Annotated[AsyncSession, Depends(get_database_session)],
) -> DespResponse:
    """API route to create a new operating system in the database

    Args:
        operatingsystem_payload (OperatingSystemCreationPayload): The operating system details to create
        db_session (AsyncSession): Database session dependency

    Returns:
        DespResponse: Response containing the created operating system
    """
    logger.debug("Creating new operating system: %s", operatingsystem_payload)

    created_operatingsystem = await store_operatingsystem_in_database(db_session, operatingsystem_payload)

    return DespResponse(data=created_operatingsystem.model_dump(), http_status=200)


@router.patch(
    "/operatingsystems/{operatingsystem_id}",
    summary="Update an existing operating system",
    response_description="Details of the updated operating system",
    response_model=BaseDespResponse[OperatingSystemInfo],
    tags=[TAG_OPERATINGSYSTEMS],
    openapi_extra=openapi_extra(secured=True, roles=["admin"]),
)
async def update_operatingsystem(
    operatingsystem_id: str,
    operatingsystem_payload: OperatingSystemUpdatePayload,
    db_session: Annotated[AsyncSession, Depends(get_database_session)],
) -> DespResponse:
    """API route to update an existing operating system in the database

    Args:
        operatingsystem_id (str): The UUID of the operating system to update
        operatingsystem_payload (OperatingSystemUpdatePayload): The operating system details to update
        db_session (AsyncSession): Database session dependency

    Returns:
        DespResponse: Response containing the updated operating system
    """
    logger.debug("Updating operating system with ID: %s", operatingsystem_id)

    operatingsystem_uuid = uuid.UUID(operatingsystem_id)

    updated_operatingsystem = await update_operatingsystem_in_database(
        db_session, operatingsystem_uuid, operatingsystem_payload
    )

    return DespResponse(data=updated_operatingsystem.model_dump())


@router.delete(
    "/operatingsystems/{operatingsystem_id}",
    summary="Delete an existing operating system",
    response_description="Confirmation of operating system deletion",
    tags=[TAG_OPERATINGSYSTEMS],
    openapi_extra=openapi_extra(secured=True, roles=["admin"]),
)
async def delete_operatingsystem(
    operatingsystem_id: str, db_session: Annotated[AsyncSession, Depends(get_database_session)]
) -> DespResponse:
    """API route to delete an existing operating system from the database

    Args:
        operatingsystem_id (str): The UUID of the operating system to delete
        db_session (AsyncSession): Database session dependency

    Returns:
        DespResponse: Confirmation of deletion
    """
    logger.debug("Deleting operating system with ID: %s", operatingsystem_id)

    operatingsystem_uuid = uuid.UUID(operatingsystem_id)

    await delete_operatingsystem_from_database(db_session, operatingsystem_uuid)

    return DespResponse(
        data={},
        http_status=200,  # No Content, successful deletion
    )
