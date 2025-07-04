"""Service layer for Project database interactions"""

import base64
import datetime
import uuid

from despsharedlibrary.schemas.sandbox_schema import (
    Applications,
    Applications_x_OperatingSystems,
    Events,
    EventType,
    Projects,
)
from msfwk.exceptions import DespGenericError
from msfwk.utils.logging import get_logger
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from project_management.models.applications import ApplicationInstallInfo
from project_management.models.constants import APPLICATION_NOT_FOUND_ERROR, PROJECT_NOT_FOUND_ERROR
from project_management.models.events import EventFilterPayload, EventInfo
from project_management.models.expanded_models import ProjectExpanded
from project_management.models.projects import BuildStatusPayload, ProjectCreationPayload, ProjectUpdatePayload
from project_management.models.servers import ServerInfo
from project_management.services.database_service import update_sqlalchemy_object_from_basemodel
from project_management.services.flavors import get_flavor_from_database
from project_management.services.operatingsystems import get_operatingsystem_from_database
from project_management.services.other_services import create_repository_with_storage_service
from project_management.services.profiles import get_or_create_current_profile, get_profile_from_database
from project_management.services.repositories import get_repository_from_database

logger = get_logger("project")


async def get_project_from_database(session: AsyncSession, project_uuid: uuid.UUID) -> ProjectExpanded:
    """Retrieve a specific project from the database

    Args:
        session (AsyncSession): Database session
        project_uuid (uuid.UUID): UUID of the project to retrieve

    Returns:
        ProjectExpanded: Project details with expanded related entities
    """
    query = (
        select(Projects)
        .options(joinedload(Projects.applications), joinedload(Projects.server))
        .where(Projects.id == project_uuid)
    )
    result = await session.execute(query)
    project = result.unique().scalar_one_or_none()

    if project is None:
        raise DespGenericError(status_code=404, message="Project not found", code=PROJECT_NOT_FOUND_ERROR)

    # Fetch installation scripts
    model_application_list = []
    for app in project.applications:
        script_query = select(Applications_x_OperatingSystems.c.script).where(
            (Applications_x_OperatingSystems.c.application_id == app.id)
            & (Applications_x_OperatingSystems.c.operatingsystems_id == project.operatingsystem_id)
        )
        script_result = await session.execute(script_query)
        install_script = script_result.scalar_one()

        model_application_list.append(
            ApplicationInstallInfo(
                id=app.id, name=app.name, description=app.description, icon=app.icon, script=install_script
            )
        )

    associated_server = None
    if project.server is not None:
        associated_server = ServerInfo(
            id=project.server.id, public_ip=project.server.public_ip, state=project.server.state
        )

    return ProjectExpanded(
        id=project.id,
        name=project.name,
        ssh_key=project.ssh_key,
        flavor=await get_flavor_from_database(session, project.flavor_id),
        repository=await get_repository_from_database(session, project.repository_id),
        profile=await get_profile_from_database(session, project.profile_id),
        operatingsystem=await get_operatingsystem_from_database(session, project.operatingsystem_id),
        applications=model_application_list,
        server=associated_server,
        status=project.status,
        logs=project.logs,
        docker_image=project.docker_image,
    )


async def get_projects_by_current_profile(session: AsyncSession) -> list[ProjectExpanded]:
    """Retrieves all projects associated with the current profile.

    Args:
        session (AsyncSession): The SQLAlchemy asynchronous session.

    Returns:
        list[ProjectExpanded]: A list of expanded project details associated with the current profile.

    """
    current_profile = await get_or_create_current_profile(session)

    try:
        query = select(Projects).where(Projects.profile_id == current_profile.id)
        result = await session.execute(query)
        projects = result.scalars().all()

    except SQLAlchemyError as sqle:
        message = f"Error retrieving projects: {sqle}"
        logger.exception(message, exc_info=sqle)
        raise DespGenericError(status_code=500, message=message, code=PROJECT_NOT_FOUND_ERROR) from sqle

    return [await get_project_from_database(session, p.id) for p in projects]


async def store_project_in_database(session: AsyncSession, project_payload: ProjectCreationPayload) -> ProjectExpanded:
    """Store a new project in the database

    Args:
        session (AsyncSession): Database session
        project_payload (ProjectCreationPayload): Project creation details

    Returns:
        ProjectExpanded: Created project details
    """
    project_id = project_payload.id or str(uuid.uuid4())
    project_id_uuid = uuid.UUID(project_id)
    flavor_id = uuid.UUID(project_payload.flavor_id)
    operatingsystem_id = uuid.UUID(project_payload.operatingsystem_id)

    # Create repository using storage service
    if project_payload.repository_id is None:
        repository_id = await create_repository_with_storage_service(
            session, repository_name=f"{project_payload.name}_{project_id}"
        )

    current_profile = await get_or_create_current_profile(session)

    # Create project from compiled information
    project_to_create = Projects(
        id=project_id_uuid,
        name=project_payload.name,
        ssh_key=project_payload.ssh_key,
        flavor_id=flavor_id,
        repository_id=repository_id,
        profile_id=current_profile.id,
        operatingsystem_id=operatingsystem_id,
    )

    # Fetch from association relationships

    for a in project_payload.application_ids:
        query = select(Applications).where(Applications.id == a)
        result = await session.execute(query)
        existing_app = result.scalar_one_or_none()

        if existing_app is None:
            raise DespGenericError(
                status_code=404, message="Application not found to create project", code=APPLICATION_NOT_FOUND_ERROR
            )

        project_to_create.applications.append(existing_app)

    session.add(project_to_create)

    await session.commit()

    return await get_project_from_database(session, project_to_create.id)


async def update_project_in_database(
    session: AsyncSession, project_uuid: uuid.UUID, project_payload: ProjectUpdatePayload
) -> ProjectExpanded:
    """Update an existing project in the database

    Args:
        session (AsyncSession): Database session
        project_uuid (uuid.UUID): UUID of the project to update
        project_payload (ProjectUpdatePayload): Project update details

    Returns:
        ProjectExpanded: Updated project details
    """
    # First, retrieve the existing project
    query = select(Projects).where(Projects.id == project_uuid)
    result = await session.execute(query)
    project = result.scalar_one_or_none()

    if project is None:
        raise DespGenericError(status_code=404, message="Project to update not found", code=PROJECT_NOT_FOUND_ERROR)

    # Update only the non-None fields
    update_sqlalchemy_object_from_basemodel(project, project_payload)

    session.add(project)
    await session.commit()

    # Return the updated project
    return await get_project_from_database(session, project_uuid)


async def delete_project_from_database(session: AsyncSession, project_uuid: uuid.UUID) -> None:
    """Delete an existing project from the database

    Args:
        session (AsyncSession): Database session
        project_uuid (uuid.UUID): UUID of the project to delete

    Raises:
        DespGenericError: If the project is not found or cannot be deleted
    """
    # First, check if the project exists
    query = select(Projects).where(Projects.id == project_uuid)
    result = await session.execute(query)
    project = result.scalar_one_or_none()

    if project is None:
        raise DespGenericError(
            status_code=404, message="Project to be deleted was not found", code=PROJECT_NOT_FOUND_ERROR
        )

    # Delete all related events first
    delete_events_query = delete(Events).where(Events.project_id == project_uuid)
    await session.execute(delete_events_query)

    await session.delete(project)
    await session.commit()


async def store_build_status_in_database(
    session: AsyncSession, project_id: uuid.UUID, payload: BuildStatusPayload
) -> None:
    """Stores or updates the build status, Trivy report, and Docker image for a project.

    Args:
        session (AsyncSession): The SQLAlchemy async session.
        project_id (uuid.UUID): The unique identifier of the project.
        payload (BuildStatusPayload): The build status payload containing status, Trivy report, and Docker image.

    Returns:
        None
    """
    query = select(Projects).where(Projects.id == project_id)
    result = await session.execute(query)
    project = result.scalar_one_or_none()

    if not project:
        raise DespGenericError(
            status_code=404, message="Project not found while storing build status", code=PROJECT_NOT_FOUND_ERROR
        )

    # Update project fields with the new build state data
    if payload.step == "pipeline":
        project.status = payload.status
        if payload.status == "STARTED":
            project.logs = None
            project.docker_image = None

    if (payload.logs is not None) and (payload.logs != " "):
        log_header = f"\n<hr/>\nStep: {payload.step} | Time: {datetime.datetime.now().isoformat()}\n"  # noqa: DTZ005
        log_header_base64 = base64.b64encode(log_header.encode()).decode()
        log_entry_combined = f"{log_header_base64},{payload.logs}"

        if project.logs:
            project.logs += f",{log_entry_combined}"
        else:
            project.logs = log_entry_combined

    if (payload.docker_image is not None) and (payload.docker_image != " "):
        if project.docker_image:
            new_image_entry = f",{payload.docker_image}"
            project.docker_image += new_image_entry
        else:
            new_image_entry = f"{payload.docker_image}"
            project.docker_image = new_image_entry
    project.updated_at = datetime.datetime.now()  # noqa: DTZ005

    await session.commit()


async def get_build_status_from_database(session: AsyncSession, project_id: uuid.UUID) -> dict:
    """Retrieves the build status, Trivy report, and Docker image for a given project.

    Args:
        session (AsyncSession): The SQLAlchemy async session.
        project_id (uuid.UUID): The unique identifier of the project.

    Returns:
        dict: Build status information
    """
    query = select(Projects).where(Projects.id == project_id)
    result = await session.execute(query)
    project = result.scalar_one_or_none()

    if not project:
        message = f"Project with ID {project_id} not found"
        raise ValueError(message)

    return {
        "status": project.status,
        "logs": project.logs,
        "docker_image": project.docker_image,
        "updated_at": project.updated_at,
    }


async def store_event_in_database(
    db_session: AsyncSession,
    project_uuid: uuid.UUID,
    payload: BuildStatusPayload,
) -> None:
    """Stores an event in the database.

    Args:
        db_session (AsyncSession): Database session.
        project_uuid (uuid.UUID): The UUID of the project.
        payload (BuildStatusPayload): The build status payload containing status, Trivy report, and Docker image.
    """
    content = f"Step '{payload.step}' has {payload.status.lower()}."
    step = payload.step
    status = payload.status
    pipeline_id = payload.pipeline_id
    event_type = EventType.pipeline
    new_event = Events(
        project_id=project_uuid,
        type=event_type,
        step=step,
        status=status,
        content=content,
        pipeline_id=pipeline_id,
    )

    db_session.add(new_event)
    await db_session.commit()


async def get_events_for_project_from_database(
    session: AsyncSession, project_id: uuid.UUID, event_payload: EventFilterPayload | None = None
) -> list[EventInfo]:
    """Fetch events for a specific project from the database.

    Args:
        session (AsyncSession): The SQLAlchemy async session.
        project_id (uuid.UUID): The unique identifier of the project.
        event_payload (EventFilterPayload, optional): Filter events by event type.

    Returns:
        list[EventInfo]: List of event records.
    """
    query = select(Events).where(Events.project_id == project_id)
    if event_payload and event_payload.event_type:
        query = query.where(Events.type == event_payload.event_type)

    result = await session.execute(query)
    events = result.scalars().all()

    return [
        EventInfo(
            id=event.id,
            project_id=event.project_id,
            type=event.type.value,
            created_at=event.created_at,
            content=event.content,
            pipeline_id=event.pipeline_id,
            step=event.step,
            status=event.status,
        )
        for event in events
    ]
