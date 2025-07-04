"""Manage the API entrypoints for Profiles"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from msfwk.application import openapi_extra
from msfwk.models import BaseDespResponse, DespResponse
from msfwk.utils.logging import get_logger
from sqlalchemy.ext.asyncio import AsyncSession

from project_management.models.profiles import (
    ProfileCreationPayload,
    ProfileInfo,
    ProfileUpdatePayload,
)
from project_management.routes.api_metadata import TAG_PROFILES
from project_management.services.database_service import get_database_session
from project_management.services.profiles import (
    delete_profile_from_database,
    get_profile_from_database,
    store_profile_in_database,
    update_profile_in_database,
)

router = APIRouter()

logger = get_logger("profile")


@router.get(
    "/profiles/{profile_id}",
    summary="Get a specific profile by ID",
    response_description="Details of the requested profile",
    response_model=BaseDespResponse[ProfileInfo],
    tags=[TAG_PROFILES],
    openapi_extra=openapi_extra(secured=True, roles=["admin"], internal=True),
)
async def get_profile_by_id(
    profile_id: str, db_session: Annotated[AsyncSession, Depends(get_database_session)]
) -> DespResponse:
    """API route to get a specific profile from the database by its ID

    Args:
        profile_id (str): The UUID of the profile to retrieve
        db_session (AsyncSession): Database session dependency

    Returns:
        DespResponse: Response containing the requested profile
    """
    logger.debug("Getting profile with ID: %s", profile_id)

    profile_uuid = uuid.UUID(profile_id)

    profile: ProfileInfo = await get_profile_from_database(db_session, profile_uuid)

    return DespResponse(data=profile.model_dump())


@router.post(
    "/profiles",
    summary="Create a new profile",
    response_description="Details of the created profile",
    response_model=BaseDespResponse[ProfileInfo],
    tags=[TAG_PROFILES],
    openapi_extra=openapi_extra(secured=True, roles=["admin"], internal=True),
)
async def create_profile(
    profile_payload: ProfileCreationPayload,
    db_session: Annotated[AsyncSession, Depends(get_database_session)],
) -> DespResponse:
    """API route to create a new profile in the database

    Args:
        profile_payload (ProfileCreationPayload): The profile details to create
        db_session (AsyncSession): Database session dependency

    Returns:
        DespResponse: Response containing the created profile
    """
    logger.debug("Creating new profile: %s", profile_payload)

    created_profile = await store_profile_in_database(db_session, profile_payload)

    return DespResponse(data=created_profile.model_dump(), http_status=200)


@router.patch(
    "/profiles/{profile_id}",
    summary="Update an existing profile",
    response_description="Details of the updated profile",
    response_model=BaseDespResponse[ProfileInfo],
    tags=[TAG_PROFILES],
    openapi_extra=openapi_extra(secured=True, roles=["admin"], internal=True),
)
async def update_profile(
    profile_id: str,
    profile_payload: ProfileUpdatePayload,
    db_session: Annotated[AsyncSession, Depends(get_database_session)],
) -> DespResponse:
    """API route to update an existing profile in the database

    Args:
        profile_id (str): The UUID of the profile to update
        profile_payload (ProfileUpdatePayload): The profile details to update
        db_session (AsyncSession): Database session dependency

    Returns:
        DespResponse: Response containing the updated profile
    """
    logger.debug("Updating profile with ID: %s", profile_id)

    profile_uuid = uuid.UUID(profile_id)

    updated_profile = await update_profile_in_database(db_session, profile_uuid, profile_payload)

    return DespResponse(data=updated_profile.model_dump())


@router.delete(
    "/profiles/{profile_id}",
    summary="Delete an existing profile",
    response_description="Confirmation of profile deletion",
    tags=[TAG_PROFILES],
    openapi_extra=openapi_extra(secured=True, roles=["admin"], internal=True),
)
async def delete_profile(
    profile_id: str, db_session: Annotated[AsyncSession, Depends(get_database_session)]
) -> DespResponse:
    """API route to delete an existing profile from the database

    Args:
        profile_id (str): The UUID of the profile to delete
        db_session (AsyncSession): Database session dependency

    Returns:
        DespResponse: Confirmation of deletion
    """
    logger.debug("Deleting profile with ID: %s", profile_id)

    profile_uuid = uuid.UUID(profile_id)

    await delete_profile_from_database(db_session, profile_uuid)

    return DespResponse(
        data={},
        http_status=200,  # No Content, successful deletion
    )
