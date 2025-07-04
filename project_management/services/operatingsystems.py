import uuid

from despsharedlibrary.schemas.sandbox_schema import OperatingSystems
from msfwk.exceptions import DespGenericError
from msfwk.utils.logging import get_logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from project_management.models.applications import ApplicationInfo
from project_management.models.constants import OPERATING_SYSTEM_NOT_FOUND_ERROR
from project_management.models.expanded_models import OperatingSystemExpanded
from project_management.models.operatingsystems import (
    OperatingSystemCreationPayload,
    OperatingSystemInfo,
    OperatingSystemUpdatePayload,
)
from project_management.services.database_service import update_sqlalchemy_object_from_basemodel

logger = get_logger("operatingsystem")


async def get_operatingsystem_from_database(
    session: AsyncSession, operatingsystem_uuid: uuid.UUID
) -> OperatingSystemExpanded:
    """Fetch operating system from the database
    Args:
        session : database session created in the route method
        operatingsystem_uuid : uuid of the operating system to fetch
    """
    query = (
        select(OperatingSystems)
        .options(joinedload(OperatingSystems.applications))
        .where(OperatingSystems.id == operatingsystem_uuid)
    )
    result = await session.execute(query)
    operatingsystem = result.unique().scalar_one_or_none()

    logger.debug("Found operating system: %s", operatingsystem)

    if operatingsystem is None:
        raise DespGenericError(
            status_code=404, message="Operating system not found", code=OPERATING_SYSTEM_NOT_FOUND_ERROR
        )

    db_application_list = operatingsystem.applications
    model_application_list = [
        ApplicationInfo(id=a.id, name=a.name, description=a.description, icon=a.icon) for a in db_application_list
    ]

    return OperatingSystemExpanded(
        id=operatingsystem.id,
        name=operatingsystem.name,
        applications=model_application_list,
        is_gui=operatingsystem.is_gui,
    )


async def get_all_operatingsystems_from_database(session: AsyncSession) -> list[OperatingSystemExpanded]:
    """Fetch all operatingsystems from the database

    Args:
        session: database session created in the route method

    Returns:
        list[FlavorInfo]: A list of all operatingsystems in the database
    """
    query = select(OperatingSystems).options(joinedload(OperatingSystems.applications))
    result = await session.execute(query)
    operatingsystems = result.unique().scalars().all()

    logger.debug("Found %s operatingsystems", len(operatingsystems))

    return [
        OperatingSystemExpanded(
            id=os.id,
            name=os.name,
            is_gui=os.is_gui,
            applications=[
                ApplicationInfo(id=appli.id, name=appli.name, description=appli.description, icon=appli.icon)
                for appli in os.applications
            ],
        )
        for os in operatingsystems
    ]


async def store_operatingsystem_in_database(
    session: AsyncSession, operatingsystem_payload: OperatingSystemCreationPayload
) -> OperatingSystemExpanded:
    """Store operating system in the database

    Args:
        session : database session created in the route method
        operatingsystem_payload (OperatingSystemCreationPayload): The operating system to store

    Returns:
        OperatingSystemDatabaseClass: The stored operating system object
    """
    # If no ID is provided, generate a new UUID
    operatingsystem_id = operatingsystem_payload.id or uuid.uuid4()

    # Ensure the ID is a UUID object
    if isinstance(operatingsystem_id, str):
        operatingsystem_id = uuid.UUID(operatingsystem_id)

    operatingsystem_to_create = OperatingSystems(
        id=operatingsystem_id,
        name=operatingsystem_payload.name,
        is_gui=operatingsystem_payload.is_gui,
    )

    session.add(operatingsystem_to_create)
    await session.commit()

    return await get_operatingsystem_from_database(session, operatingsystem_to_create.id)


async def update_operatingsystem_in_database(
    session: AsyncSession, operatingsystem_uuid: uuid.UUID, operatingsystem_payload: OperatingSystemUpdatePayload
) -> OperatingSystemInfo:
    """Update an existing operating system in the database

    Args:
        session: database session created in the route method
        operatingsystem_uuid: UUID of the operating system to update
        operatingsystem_payload: Payload containing fields to update

    Returns:
        OperatingSystemDatabaseClass: The updated operating system object
    """
    # First, retrieve the existing operating system
    query = select(OperatingSystems).where(OperatingSystems.id == operatingsystem_uuid)
    result = await session.execute(query)
    operatingsystem = result.scalar_one_or_none()

    if operatingsystem is None:
        raise DespGenericError(
            status_code=404, message="Operating system to update not found", code=OPERATING_SYSTEM_NOT_FOUND_ERROR
        )

    # Update only the non-None fields
    update_sqlalchemy_object_from_basemodel(operatingsystem, operatingsystem_payload)

    session.add(operatingsystem)
    await session.commit()

    # Return the updated operating system
    return await get_operatingsystem_from_database(session, operatingsystem_uuid)


async def delete_operatingsystem_from_database(session: AsyncSession, operatingsystem_uuid: uuid.UUID) -> None:
    """Delete an existing operating system from the database

    Args:
        session: database session created in the route method
        operatingsystem_uuid: UUID of the operating system to delete

    Raises:
        DespGenericError: If the operating system is not found or cannot be deleted
    """
    # First, check if the operating system exists
    query = select(OperatingSystems).where(OperatingSystems.id == operatingsystem_uuid)
    result = await session.execute(query)
    operatingsystem = result.scalar_one_or_none()

    if operatingsystem is None:
        raise DespGenericError(
            status_code=404, message="Operating system to delete not found", code=OPERATING_SYSTEM_NOT_FOUND_ERROR
        )

    await session.delete(operatingsystem)
    await session.commit()
