"""Manage the API entrypoints for Projects"""

import asyncio
import time
import uuid
from typing import TYPE_CHECKING, Annotated

import fastapi
from fastapi import APIRouter, BackgroundTasks, Depends
from msfwk.application import openapi_extra
from msfwk.models import BaseDespResponse, DespResponse
from msfwk.notification import NotificationTemplate, send_email_to_mq
from msfwk.request import HttpClient
from msfwk.utils.logging import get_logger
from msfwk.utils.user import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession

from project_management.models.events import EventFilterPayload, EventInfo
from project_management.models.exceptions import KeycloakSetupError
from project_management.models.expanded_models import ProjectExpanded
from project_management.models.projects import BuildStatusPayload, ProjectCreationPayload, ProjectUpdatePayload
from project_management.routes.api_metadata import TAG_PROJECTS
from project_management.services.database_service import get_database_session
from project_management.services.other_services import create_vm_with_vm_mgmt
from project_management.services.projects import (
    delete_project_from_database,
    get_build_status_from_database,
    get_events_for_project_from_database,
    get_project_from_database,
    get_projects_by_current_profile,
    store_build_status_in_database,
    store_event_in_database,
    store_project_in_database,
    update_project_in_database,
)
from project_management.utils.keycloak_utils import cleanup_keycloak_for_project, setup_keycloak_realm_and_client

if TYPE_CHECKING:
    from msfwk.models import DespUser

router = APIRouter()

logger = get_logger("project")

ERROR_PROJECT_NOT_FOUND = "Project not found"


@router.get(
    "/projects_by_profile",
    summary="Get all projects associated to the current user",
    response_description="Details of the requested projects",
    response_model=BaseDespResponse[list[ProjectExpanded]],
    tags=[TAG_PROJECTS],
    openapi_extra=openapi_extra(secured=True, roles=["user"]),
)
async def get_project_by_profile(db_session: Annotated[AsyncSession, Depends(get_database_session)]) -> DespResponse:
    """API route to get all projects associated with the current user's profile.

    Args:
        db_session (AsyncSession): Database session dependency

    Returns:
        DespResponse: Response containing list of projects
    """
    projects: list[ProjectExpanded] = await get_projects_by_current_profile(db_session)

    return DespResponse(data=[p.model_dump() for p in projects])


@router.get(
    "/projects/{project_id}",
    summary="Get a specific project by ID",
    response_description="Details of the requested project",
    response_model=BaseDespResponse[ProjectExpanded],
    tags=[TAG_PROJECTS],
    openapi_extra=openapi_extra(secured=True, roles=["user"]),
)
async def get_project_by_id(
    project_id: str, db_session: Annotated[AsyncSession, Depends(get_database_session)]
) -> DespResponse:
    """API route to get a specific project from the database by its ID

    Args:
        project_id (str): The UUID of the project to retrieve
        db_session (AsyncSession): Database session dependency

    Returns:
        DespResponse: Response containing the requested project
    """
    logger.debug("Getting project with ID: %s", project_id)

    project_uuid = uuid.UUID(project_id)

    project: ProjectExpanded = await get_project_from_database(db_session, project_uuid)

    if not project:
        return DespResponse(
            data={"error": ERROR_PROJECT_NOT_FOUND},
            http_status=404,
        )

    return DespResponse(data=project.model_dump())


@router.post(
    "/projects",
    summary="Create a new project",
    response_description="Details of the created project",
    response_model=BaseDespResponse[ProjectExpanded],
    tags=[TAG_PROJECTS],
    openapi_extra=openapi_extra(secured=True, roles=["user"]),
)
async def create_project(
    project_payload: ProjectCreationPayload,
    db_session: Annotated[AsyncSession, Depends(get_database_session)],
) -> DespResponse:
    """API route to create a new project in the database

    Args:
        project_payload (ProjectCreationPayload): The project details to create
        db_session (AsyncSession): Database session dependency

    Returns:
        DespResponse: Response containing the created project
    """
    logger.debug("Creating new project: %s", project_payload)
    user: DespUser = get_current_user()

    created_project = await store_project_in_database(db_session, project_payload)

    await send_email_to_mq(
        notification_type=NotificationTemplate.GENERIC,
        user_email=user.profile.email,
        subject="Vm creation started",
        message=f"Vm creation started for project {created_project.name}",
        user_id=user.id,
    )

    # Once all is created, call vm mgmt
    await create_vm_with_vm_mgmt(created_project)
    # Create Keycloak realm and client for the project
    try:
        logger.info("Creating Keycloak realm and client for project %s", created_project.id)
        client_id = await setup_keycloak_realm_and_client(
            created_project.id,
            user.username,
            user.profile.email,
            db_session,
        )
        logger.info("Created Keycloak realm and client for project %s. Client ID: %s",
                created_project.id, client_id)
    except KeycloakSetupError as e:
        logger.exception("Failed to create Keycloak realm and client for project %s: %s",
                    created_project.id, str(e))
        # Continue execution even if Keycloak setup fails

    return DespResponse(data=created_project.model_dump(), http_status=200)


@router.patch(
    "/projects/{project_id}",
    summary="Update an existing project",
    response_description="Details of the updated project",
    response_model=BaseDespResponse[ProjectExpanded],
    tags=[TAG_PROJECTS],
    openapi_extra=openapi_extra(secured=True, roles=["user"]),
)
async def update_project(
    project_id: str,
    project_payload: ProjectUpdatePayload,
    db_session: Annotated[AsyncSession, Depends(get_database_session)],
) -> DespResponse:
    """API route to update an existing project in the database

    Args:
        project_id (str): The UUID of the project to update
        project_payload (ProjectUpdatePayload): The project details to update
        db_session (AsyncSession): Database session dependency

    Returns:
        DespResponse: Response containing the updated project
    """
    logger.debug("Updating project with ID: %s", project_id)

    project_uuid = uuid.UUID(project_id)

    updated_project = await update_project_in_database(db_session, project_uuid, project_payload)

    return DespResponse(data=updated_project.model_dump())


# 10 minutes timeout in seconds
SERVER_DELETION_TIMEOUT = 600


async def _delete_server_and_project(
    db_session: AsyncSession, project_uuid: uuid.UUID, project_id: str, server_id: uuid.UUID
) -> None:
    """Background task to delete a server and then the associated project.

    Args:
        db_session (AsyncSession): Database session
        project_uuid (uuid.UUID): UUID of the project to delete
        project_id (str): String representation of project UUID (for logging)
        server_id (uuid.UUID): UUID of the server to delete
    """
    try:
        http_client = HttpClient()
        # Call VM management to delete the server
        async with http_client.get_service_session("vm-management") as session:
            server_response = await session.delete(f"/servers/{server_id}")
            if server_response.status != fastapi.status.HTTP_202_ACCEPTED:
                logger.error("Failed to delete server: %s", await server_response.text())
                return

            # Track time for timeout
            start_time = time.time()

            # Wait for server to be deleted with timeout
            while (time.time() - start_time) < SERVER_DELETION_TIMEOUT:
                await asyncio.sleep(5)  # Check every 5 seconds

                try:
                    status_response = await session.get(f"/servers/{server_id}")

                    if status_response.status == fastapi.status.HTTP_404_NOT_FOUND:
                        # Server is deleted, now delete the project with Keycloak cleanup
                        await _delete_project_with_keycloak_cleanup(db_session, project_uuid, project_id)
                        logger.info("Successfully deleted project %s and its server", project_id)
                        return

                    server_data = await status_response.json()
                    if server_data.get("data", {}).get("state") == "DELETED":
                        # Server is deleted, now delete the project with Keycloak cleanup
                        await _delete_project_with_keycloak_cleanup(db_session, project_uuid, project_id)
                        logger.info("Successfully deleted project %s and its server", project_id)
                        return
                except Exception:
                    logger.exception("Error checking server status")
                    # Continue the loop even if a status check fails

            # If we reach here, we've timed out
            logger.warning(
                "Server deletion timed out after %ss for project %s, server %s",
                SERVER_DELETION_TIMEOUT,
                project_id,
                server_id,
            )
            # Still attempt to delete the project with Keycloak cleanup
            await _delete_project_with_keycloak_cleanup(db_session, project_uuid, project_id)
            logger.info("Deleted project %s after server deletion timeout", project_id)

    except Exception:
        logger.exception("Error in background deletion task")


async def _delete_project_with_keycloak_cleanup(
    db_session: AsyncSession, project_uuid: uuid.UUID, project_id: str
) -> None:
    """Background task to delete a project and clean up its Keycloak resources.

    Args:
        db_session (AsyncSession): Database session
        project_uuid (uuid.UUID): UUID of the project to delete
        project_id (str): String representation of project UUID (for logging)
    """
    try:
        # Clean up Keycloak resources first
        try:
            await cleanup_keycloak_for_project(db_session, project_uuid)
            logger.info("Successfully cleaned up Keycloak resources for project %s", project_id)
        except KeycloakSetupError as e:
            logger.warning("Failed to cleanup Keycloak resources for project %s: %s", project_id, str(e))
            # Continue with project deletion even if Keycloak cleanup fails

        # Delete the project from database
        await delete_project_from_database(db_session, project_uuid)
        logger.info("Successfully deleted project %s", project_id)

    except Exception:
        logger.exception("Error in project deletion with Keycloak cleanup task")


@router.delete(
    "/projects/{project_id}",
    summary="Delete an existing project",
    response_description="Confirmation of project deletion",
    tags=[TAG_PROJECTS],
    openapi_extra=openapi_extra(secured=True, roles=[]),
)
async def delete_project(
    project_id: str,
    background_tasks: BackgroundTasks,
    db_session: Annotated[AsyncSession, Depends(get_database_session)],
) -> DespResponse:
    """API route to delete an existing project from the database

    Args:
        project_id (str): The UUID of the project to delete
        background_tasks (BackgroundTasks): FastAPI background tasks handler
        db_session (AsyncSession): Database session dependency

    Returns:
        DespResponse: Confirmation of deletion
    """
    logger.debug("Deleting project with ID: %s", project_id)

    project_uuid = uuid.UUID(project_id)
    project = await get_project_from_database(db_session, project_uuid)

    if not project:
        return DespResponse(
            data={"error": ERROR_PROJECT_NOT_FOUND},
            http_status=404,
        )

    # If project has an associated server, check its status
    if project.server:
        logger.info("Project has associated server %s, checking server status", project.server.id)

        # Check if server is already in DELETED state
        if project.server.state and project.server.state == "DELETED":
            logger.info("Server %s is already in DELETED state, proceeding with project deletion", project.server.id)
            # Add the deletion task to background tasks to include Keycloak cleanup
            background_tasks.add_task(_delete_project_with_keycloak_cleanup, db_session, project_uuid, project_id)
            return DespResponse(
                data={"status": "accepted", "message": "Project deletion initiated"},
                http_status=200,
            )

        logger.info("Server %s needs to be deleted, initiating server deletion", project.server.id)
        # Add the deletion task to background tasks
        background_tasks.add_task(_delete_server_and_project, db_session, project_uuid, project_id, project.server.id)

        return DespResponse(
            data={"status": "accepted", "message": "Project and server deletion initiated"},
            http_status=202,
        )
    # No server associated, delete project directly with Keycloak cleanup
    background_tasks.add_task(_delete_project_with_keycloak_cleanup, db_session, project_uuid, project_id)
    return DespResponse(
        data={"status": "accepted", "message": "Project deletion initiated"},
        http_status=200,
    )


@router.patch(
    "/projects/{project_id}/build-status",
    summary="Store or update a project's build status",
    response_description="Confirmation of stored build status",
    tags=[TAG_PROJECTS],
    openapi_extra=openapi_extra(secured=False, roles=["user"], internal=True),
)
async def store_project_build_state(
    project_id: str,
    payload: BuildStatusPayload,
    db_session: Annotated[AsyncSession, Depends(get_database_session)],
) -> DespResponse:
    """Stores or updates a project's build status, and logs the event.

    Args:
        project_id (str): Project UUID
        payload (BuildStatusPayload): Build status data
        db_session (AsyncSession): Database session

    Returns:
        DespResponse: Confirmation of storage
    """
    message = f"Updating build status for project ID: {project_id}"
    logger.debug(message)

    project_uuid = uuid.UUID(project_id)
    profile_id = uuid.UUID(payload.profile_id)

    # Fetch the project to ensure it exists
    project = await get_project_from_database(db_session, project_uuid)

    if not project:
        return DespResponse(
            data={"error": ERROR_PROJECT_NOT_FOUND},
            http_status=404,
        )

    # Ensure the profile_id in the request matches the project's profile_id
    if project.profile.id != profile_id:
        return DespResponse(
            data={"error": "Unauthorized: Profile ID mismatch"},
            http_status=401,  # Unauthorized
        )

    # Store pipeline status in the database
    await store_build_status_in_database(db_session, project_uuid, payload)

    # Log the event using the new method
    await store_event_in_database(db_session, project_uuid, payload)

    return DespResponse(
        data={"message": "Build status updated successfully and event logged"},
        http_status=200,
    )


@router.get(
    "/projects/{project_id}/build-status",
    summary="Get the build step status of a project",
    response_description="Details of the build step status",
    tags=[TAG_PROJECTS],
    openapi_extra=openapi_extra(secured=False, roles=["user"], internal=False),
)
async def get_project_build_state(
    project_id: str,
    db_session: Annotated[AsyncSession, Depends(get_database_session)],
) -> DespResponse:
    """API route to get the build step status of a project

    Args:
        project_id (str): The UUID of the project
        db_session (AsyncSession): Database session dependency

    Returns:
        DespResponse: Response containing the build step status
    """
    message = f"Fetching build status for project ID: {project_id}"
    logger.debug(message)

    project_uuid = uuid.UUID(project_id)

    # Fetch the project to ensure it exists
    project = await get_project_from_database(db_session, project_uuid)

    if not project:
        return DespResponse(
            data={"error": ERROR_PROJECT_NOT_FOUND},
            http_status=404,
        )

    build_status = await get_build_status_from_database(db_session, project_uuid)

    return DespResponse(
        data={"project_id": project_id, "build_status": build_status},
        http_status=200,
    )


@router.get(
    "/projects/{project_id}/events",
    summary="Get the events of a specific project",
    response_description="List of events for the project, optionally sorted and filtered",
    response_model=BaseDespResponse[list[EventInfo]],
    tags=[TAG_PROJECTS],
    openapi_extra=openapi_extra(secured=False, roles=["user"]),
)
async def get_project_events(
    project_id: str,
    event_filter: EventFilterPayload | None = None,  # it's optional
    db_session: AsyncSession = Depends(get_database_session),
) -> DespResponse[list[EventInfo]]:
    """API route to get the events for a project, optionally sorted by date and filtered by event type

    Args:
        project_id (str): The UUID of the project
        event_filter (EventFilterPayload): The payload containing the filter parameters
        db_session (AsyncSession): Database session dependency

    Returns:
        DespResponse: Response containing the list of events
    """
    message = f"Fetching events for project ID: {project_id}"
    logger.debug(message)

    project_uuid = uuid.UUID(project_id)

    # Fetch the project to ensure it exists
    project = await get_project_from_database(db_session, project_uuid)

    if not project:
        return DespResponse(
            data={"error": ERROR_PROJECT_NOT_FOUND},
            http_status=404,
        )

    # Fetch the events for the project, possibly filtered by event type
    events = await get_events_for_project_from_database(db_session, project_uuid, event_filter)

    # Sort the events by created_at if requested
    if event_filter and event_filter.sort_by_date:
        events = sorted(events, key=lambda event: event.created_at, reverse=True)

    return DespResponse(data=[event.dict() for event in events])
