"""Manage the API entrypoints"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from msfwk.application import openapi_extra
from msfwk.models import BaseDespResponse, DespResponse
from msfwk.utils.logging import get_logger
from sqlalchemy.ext.asyncio import AsyncSession

from project_management.models.applications import (
    ApplicationCreationPayload,
    ApplicationInfo,
    ApplicationInstallPayload,
    ApplicationUpdatePayload,
)
from project_management.models.expanded_models import ApplicationExpanded
from project_management.routes.api_metadata import TAG_APPLICATIONS
from project_management.services.applications import (
    delete_application_from_database,
    get_all_applications_from_database,
    get_application_from_database,
    store_application_in_database,
    update_application_in_database,
    update_or_create_application_install,
)
from project_management.services.database_service import get_database_session

router = APIRouter()

logger = get_logger("application")


@router.get(
    "/applications/{application_id}",
    summary="Get a specific application by ID",
    response_description="Details of the requested application",
    response_model=BaseDespResponse[ApplicationExpanded],
    tags=[TAG_APPLICATIONS],
    openapi_extra=openapi_extra(secured=True, roles=["user"]),
)
async def get_application_by_id(
    application_id: str, db_session: Annotated[AsyncSession, Depends(get_database_session)]
) -> DespResponse:
    """API route to get a specific application from the database by its ID

    Args:
        application_id (str): The UUID of the application to retrieve
        db_session (AsyncSession): Database session dependency

    Returns:
        DespResponse: Response containing the requested application
    """
    logger.debug("Getting application with ID: %s", application_id)

    application_uuid = uuid.UUID(application_id)

    application: ApplicationExpanded = await get_application_from_database(db_session, application_uuid)

    return DespResponse(data=application.model_dump())


@router.get(
    "/applications",
    summary="Get all applications",
    response_description="List of all applications",
    response_model=BaseDespResponse[list[ApplicationExpanded]],
    tags=[TAG_APPLICATIONS],
    openapi_extra=openapi_extra(secured=True, roles=["user"]),
)
async def get_all_applications(db_session: Annotated[AsyncSession, Depends(get_database_session)]) -> DespResponse:
    """API route to retrieve all applications from the database

    Args:
        db_session (AsyncSession): Database session dependency

    Returns:
        DespResponse: Response containing a list of all expanded applications
    """
    logger.debug("Retrieving all applications")

    applications = await get_all_applications_from_database(db_session)

    return DespResponse(data=[app.model_dump() for app in applications])


@router.post(
    "/applications",
    summary="Create a new application",
    response_description="Details of the created application",
    response_model=BaseDespResponse[ApplicationInfo],
    tags=[TAG_APPLICATIONS],
    openapi_extra=openapi_extra(secured=True, roles=["admin"]),
)
async def create_application(
    application_payload: ApplicationCreationPayload,
    db_session: Annotated[AsyncSession, Depends(get_database_session)],
) -> DespResponse:
    """API route to create a new application in the database

    Args:
        application_payload (ApplicationCreationPayload): The application details to create
        db_session (AsyncSession): Database session dependency

    Returns:
        DespResponse: Response containing the created application
    """
    logger.debug("Creating new application: %s", application_payload)

    created_application = await store_application_in_database(db_session, application_payload)

    return DespResponse(data=created_application.model_dump(), http_status=200)


@router.patch(
    "/applications/{application_id}",
    summary="Update an existing application",
    response_description="Details of the updated application",
    response_model=BaseDespResponse[ApplicationInfo],
    tags=[TAG_APPLICATIONS],
    openapi_extra=openapi_extra(secured=True, roles=["admin"]),
)
async def update_application(
    application_id: str,
    application_payload: ApplicationUpdatePayload,
    db_session: Annotated[AsyncSession, Depends(get_database_session)],
) -> DespResponse:
    """API route to update an existing application in the database

    Args:
        application_id (str): The UUID of the application to update
        application_payload (ApplicationUpdatePayload): The application details to update
        db_session (AsyncSession): Database session dependency

    Returns:
        DespResponse: Response containing the updated application
    """
    logger.debug("Updating application with ID: %s", application_id)

    application_uuid = uuid.UUID(application_id)

    updated_application = await update_application_in_database(db_session, application_uuid, application_payload)

    return DespResponse(data=updated_application.model_dump())


@router.delete(
    "/applications/{application_id}",
    summary="Delete an existing application",
    response_description="Confirmation of application deletion",
    tags=[TAG_APPLICATIONS],
    openapi_extra=openapi_extra(secured=True, roles=["admin"]),
)
async def delete_application(
    application_id: str, db_session: Annotated[AsyncSession, Depends(get_database_session)]
) -> DespResponse:
    """API route to delete an existing application from the database

    Args:
        application_id (str): The UUID of the application to delete
        db_session (AsyncSession): Database session dependency

    Returns:
        DespResponse: Confirmation of deletion
    """
    logger.debug("Deleting application with ID: %s", application_id)

    application_uuid = uuid.UUID(application_id)

    await delete_application_from_database(db_session, application_uuid)

    return DespResponse(
        data={},
        http_status=200,  # No Content, successful deletion
    )


@router.put(
    "/applications/{application_id}/installation",
    summary="Create or update an application installation for a given OS",
    response_description="Details of updated application",
    tags=[TAG_APPLICATIONS],
    openapi_extra=openapi_extra(secured=True, roles=["admin"]),
)
async def overwrite_application_installation(
    application_id: str,
    installation_payload: ApplicationInstallPayload,
    db_session: Annotated[AsyncSession, Depends(get_database_session)],
) -> DespResponse:
    """API route to create or update an application installation in database

    Args:
        application_id (str): The UUID of the application to update
        installation_payload: the installation information
        db_session (AsyncSession): Database session dependency
    """
    logger.debug("Adding/Updating installation for application : %s", application_id)

    updated_application: ApplicationExpanded = await update_or_create_application_install(
        db_session, installation_payload, uuid.UUID(application_id)
    )

    return DespResponse(
        data=updated_application,
        http_status=200,
    )
