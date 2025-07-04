import uuid

from despsharedlibrary.schemas.sandbox_schema import Applications, Applications_x_OperatingSystems
from msfwk.utils.logging import get_logger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from project_management.models.applications import (
    ApplicationCreationPayload,
    ApplicationInfo,
    ApplicationInstallPayload,
    ApplicationUpdatePayload,
)
from project_management.models.constants import APPLICATION_NOT_FOUND_ERROR
from project_management.models.exceptions import ApplicationRetrievalError
from project_management.models.expanded_models import ApplicationExpanded, AvailableOperatingSystem
from project_management.services.database_service import update_sqlalchemy_object_from_basemodel

logger = get_logger("application")


async def get_application_from_database(session: AsyncSession, application_uuid: uuid.UUID) -> ApplicationExpanded:
    """Fetch application from the database
    Args:
        session : database session created in the route method
        application_uuid : uuid of the app to fetch
    """
    query = (
        select(Applications)
        .options(joinedload(Applications.operatingsystems))
        .where(Applications.id == application_uuid)
    )
    result = await session.execute(query)
    application = result.unique().scalar_one_or_none()

    logger.debug("Found application: %s", application)

    if application is None:
        raise ApplicationRetrievalError(
            status_code=404, message="Application not found", code=APPLICATION_NOT_FOUND_ERROR
        )

    available_operatingsystems = []
    # Fetch associated installation script
    for aos in application.operatingsystems:
        script_query = select(Applications_x_OperatingSystems.c.script).where(
            (Applications_x_OperatingSystems.c.application_id == application.id)
            & (Applications_x_OperatingSystems.c.operatingsystems_id == aos.id)
        )
        script_result = await session.execute(script_query)
        install_script = script_result.scalar_one()

        available_operatingsystems.append(AvailableOperatingSystem(name=aos.name, script=install_script, id=aos.id))

    return ApplicationExpanded(
        id=application.id,
        name=application.name,
        description=application.description,
        icon=application.icon,
        available_operatingsystems=available_operatingsystems,
    )


async def get_all_applications_from_database(session: AsyncSession) -> list[ApplicationExpanded]:
    """Fetch all applications from the database

    Args:
        session: database session created in the route method

    Returns:
        list[FlavorInfo]: A list of all applications in the database
    """
    query = select(Applications).options(joinedload(Applications.operatingsystems))
    result = await session.execute(query)
    applications = result.unique().scalars().all()

    logger.debug("Found %s applications", len(applications))

    return [await get_application_from_database(session, app.id) for app in applications]


async def store_application_in_database(
    session: AsyncSession, application_payload: ApplicationCreationPayload
) -> ApplicationInfo:
    """Store application in the database

    Args:
        session : database session created in the route method
        application_payload (ApplicationDatabaseClass): The application to store

    Returns:
        ApplicationDatabaseClass: The stored application object
    """
    if application_payload.id is None:
        application_payload.id = str(uuid.uuid4())

    application_to_create = Applications(
        id=uuid.UUID(application_payload.id),
        name=application_payload.name,
        description=application_payload.description,
        icon=application_payload.icon,
    )

    session.add(application_to_create)
    await session.commit()

    return await get_application_from_database(session, application_to_create.id)


async def update_application_in_database(
    session: AsyncSession, application_uuid: uuid.UUID, application_payload: ApplicationUpdatePayload
) -> ApplicationInfo:
    """Update an existing application in the database

    Args:
        session: database session created in the route method
        application_uuid: UUID of the application to update
        application_payload: Payload containing fields to update

    Returns:
        ApplicationDatabaseClass: The updated application object
    """
    # First, retrieve the existing application
    query = select(Applications).where(Applications.id == application_uuid)
    result = await session.execute(query)
    application = result.scalar_one_or_none()

    if application is None:
        raise ApplicationRetrievalError(
            status_code=404, message="Application to update not found", code=APPLICATION_NOT_FOUND_ERROR
        )

    # Update only the non-None fields
    update_sqlalchemy_object_from_basemodel(application, application_payload)

    session.add(application)
    await session.commit()

    # Return the updated application
    return await get_application_from_database(session, application_uuid)


async def delete_application_from_database(session: AsyncSession, application_uuid: uuid.UUID) -> None:
    """Delete an existing application from the database

    Args:
        session: database session created in the route method
        application_uuid: UUID of the application to delete

    Raises:
        DespGenericError: If the application is not found or cannot be deleted
    """
    # First, check if the application exists
    query = select(Applications).where(Applications.id == application_uuid)
    result = await session.execute(query)
    application = result.scalar_one_or_none()

    if application is None:
        raise ApplicationRetrievalError(
            status_code=404, message="Application to delete not found", code=APPLICATION_NOT_FOUND_ERROR
        )

    await session.delete(application)
    await session.commit()


async def update_or_create_application_install(
    session: AsyncSession,
    payload: ApplicationInstallPayload,
    application_id: uuid.UUID,
) -> ApplicationExpanded:
    """Update or create an application installation script

    Args:
        session: database session created in the route method
        payload: ApplicationInstallPayload
        application_id: UUID of the application to update or create
    """
    base_application = await get_application_from_database(session, application_id)

    os_id = uuid.UUID(payload.operatingsystem_id)
    existing_os_ids = [aos.id for aos in base_application.available_operatingsystems]

    if os_id in existing_os_ids:
        logger.debug(f"Updating installation script for OS {os_id}...")
        update_stmt = (
            update(Applications_x_OperatingSystems)
            .where(
                (Applications_x_OperatingSystems.c.application_id == application_id)
                & (Applications_x_OperatingSystems.c.operatingsystems_id == os_id)
            )
            .values(script=payload.script)
        )
        await session.execute(update_stmt)
        logger.debug("Updated installation script for OS %s", os_id)
    else:
        logger.debug("Adding new installation script for OS %s...", os_id)
        insert_stmt = Applications_x_OperatingSystems.insert().values(
            application_id=application_id, operatingsystems_id=os_id, script=payload.script
        )
        await session.execute(insert_stmt)
        logger.debug("Added new installation script for OS %s", os_id)

    # Commit the changes
    await session.commit()

    # Return the updated application details
    return await get_application_from_database(session, application_id)
