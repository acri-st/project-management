"""Manage the API entrypoints for Flavors"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from msfwk.application import openapi_extra
from msfwk.models import BaseDespResponse, DespResponse
from msfwk.utils.logging import get_logger
from sqlalchemy.ext.asyncio import AsyncSession

from project_management.models.flavors import (
    FlavorCreationPayload,
    FlavorInfo,
    FlavorUpdatePayload,
)
from project_management.routes.api_metadata import TAG_FLAVORS
from project_management.services.database_service import get_database_session
from project_management.services.flavors import (
    delete_flavor_from_database,
    get_all_flavors_from_database,
    get_flavor_from_database,
    store_flavor_in_database,
    update_flavor_in_database,
)

router = APIRouter()

logger = get_logger("flavor")


@router.get(
    "/flavors/{flavor_id}",
    summary="Get a specific flavor by ID",
    response_description="Details of the requested flavor",
    response_model=BaseDespResponse[FlavorInfo],
    tags=[TAG_FLAVORS],
    openapi_extra=openapi_extra(secured=True, roles=["user"]),
)
async def get_flavor_by_id(
    flavor_id: str, db_session: Annotated[AsyncSession, Depends(get_database_session)]
) -> DespResponse:
    """API route to get a specific flavor from the database by its ID

    Args:
        flavor_id (str): The UUID of the flavor to retrieve
        db_session (AsyncSession): Database session dependency

    Returns:
        DespResponse: Response containing the requested flavor
    """
    logger.debug("Getting flavor with ID: %s", flavor_id)

    flavor_uuid = uuid.UUID(flavor_id)

    flavor: FlavorInfo = await get_flavor_from_database(db_session, flavor_uuid)

    return DespResponse(data=flavor.model_dump())


@router.get(
    "/flavors",
    summary="Get all flavors",
    response_description="List of all flavors",
    response_model=BaseDespResponse[list[FlavorInfo]],
    tags=[TAG_FLAVORS],
    openapi_extra=openapi_extra(secured=True, roles=["user"]),
)
async def get_all_flavors(db_session: Annotated[AsyncSession, Depends(get_database_session)]) -> DespResponse:
    """API route to retrieve all flavors from the database

    Args:
        db_session (AsyncSession): Database session dependency

    Returns:
        DespResponse: Response containing a list of all flavors
    """
    logger.debug("Retrieving all flavors")

    flavors = await get_all_flavors_from_database(db_session)

    return DespResponse(data=[flavor.model_dump() for flavor in flavors])


@router.post(
    "/flavors",
    summary="Create a new flavor",
    response_description="Details of the created flavor",
    response_model=BaseDespResponse[FlavorInfo],
    tags=[TAG_FLAVORS],
    openapi_extra=openapi_extra(secured=True, roles=["admin"]),
)
async def create_flavor(
    flavor_payload: FlavorCreationPayload,
    db_session: Annotated[AsyncSession, Depends(get_database_session)],
) -> DespResponse:
    """API route to create a new flavor in the database

    Args:
        flavor_payload (FlavorCreationPayload): The flavor details to create
        db_session (AsyncSession): Database session dependency

    Returns:
        DespResponse: Response containing the created flavor
    """
    logger.debug("Creating new flavor: %s", flavor_payload)

    created_flavor = await store_flavor_in_database(db_session, flavor_payload)

    return DespResponse(data=created_flavor.model_dump(), http_status=200)


@router.patch(
    "/flavors/{flavor_id}",
    summary="Update an existing flavor",
    response_description="Details of the updated flavor",
    response_model=BaseDespResponse[FlavorInfo],
    tags=[TAG_FLAVORS],
    openapi_extra=openapi_extra(secured=True, roles=["admin"]),
)
async def update_flavor(
    flavor_id: str,
    flavor_payload: FlavorUpdatePayload,
    db_session: Annotated[AsyncSession, Depends(get_database_session)],
) -> DespResponse:
    """API route to update an existing flavor in the database

    Args:
        flavor_id (str): The UUID of the flavor to update
        flavor_payload (FlavorUpdatePayload): The flavor details to update
        db_session (AsyncSession): Database session dependency

    Returns:
        DespResponse: Response containing the updated flavor
    """
    logger.debug("Updating flavor with ID: %s", flavor_id)

    flavor_uuid = uuid.UUID(flavor_id)

    updated_flavor = await update_flavor_in_database(db_session, flavor_uuid, flavor_payload)

    return DespResponse(data=updated_flavor.model_dump())


@router.delete(
    "/flavors/{flavor_id}",
    summary="Delete an existing flavor",
    response_description="Confirmation of flavor deletion",
    tags=[TAG_FLAVORS],
    openapi_extra=openapi_extra(secured=True, roles=["admin"], internal=False),
)
async def delete_flavor(
    flavor_id: str, db_session: Annotated[AsyncSession, Depends(get_database_session)]
) -> DespResponse:
    """API route to delete an existing flavor from the database

    Args:
        flavor_id (str): The UUID of the flavor to delete
        db_session (AsyncSession): Database session dependency

    Returns:
        DespResponse: Confirmation of deletion
    """
    logger.debug("Deleting flavor with ID: %s", flavor_id)

    flavor_uuid = uuid.UUID(flavor_id)

    await delete_flavor_from_database(db_session, flavor_uuid)

    return DespResponse(
        data={},
        http_status=200,  # No Content, successful deletion
    )
