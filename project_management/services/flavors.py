"""Flavors services"""

import uuid

from despsharedlibrary.schemas.sandbox_schema import Flavors
from msfwk.utils.logging import get_logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from project_management.models.constants import ERROR_MSG_FLAVOR_NOT_FOUND, FLAVOR_NOT_FOUND_ERROR
from project_management.models.exceptions import FlavorRetrievalError
from project_management.models.flavors import (
    FlavorCreationPayload,
    FlavorInfo,
    FlavorUpdatePayload,
)
from project_management.services.database_service import update_sqlalchemy_object_from_basemodel

logger = get_logger("flavor")


async def get_flavor_from_database(session: AsyncSession, flavor_uuid: uuid.UUID) -> FlavorInfo:
    """Fetch flavor from the database
    Args:
        session : database session created in the route method
        flavor_uuid : uuid of the flavor to fetch
    """
    query = select(Flavors).where(Flavors.id == flavor_uuid)
    result = await session.execute(query)
    flavor = result.scalar_one_or_none()

    logger.debug("Found flavor: %s", flavor)

    if flavor is None:
        raise FlavorRetrievalError(status_code=404, message=ERROR_MSG_FLAVOR_NOT_FOUND, code=FLAVOR_NOT_FOUND_ERROR)

    return FlavorInfo(
        id=flavor.id,
        name=flavor.name,
        processor=flavor.processor,
        memory=flavor.memory,
        bandwidth=flavor.bandwidth,
        storage=flavor.storage,
        gpu=flavor.gpu,
        price=flavor.price,
        openstack_flavor_id=flavor.openstack_flavor_id,
    )


async def get_all_flavors_from_database(session: AsyncSession) -> list[FlavorInfo]:
    """Fetch all flavors from the database

    Args:
        session: database session created in the route method

    Returns:
        list[FlavorInfo]: A list of all flavors in the database
    """
    query = select(Flavors)
    result = await session.execute(query)
    flavors = result.scalars().all()

    logger.debug("Found %s flavors", len(flavors))

    return [
        FlavorInfo(
            id=flavor.id,
            name=flavor.name,
            processor=flavor.processor,
            memory=flavor.memory,
            bandwidth=flavor.bandwidth,
            storage=flavor.storage,
            gpu=flavor.gpu,
            price=flavor.price,
            openstack_flavor_id=flavor.openstack_flavor_id,
        )
        for flavor in flavors
    ]


async def store_flavor_in_database(session: AsyncSession, flavor_payload: FlavorCreationPayload) -> FlavorInfo:
    """Store flavor in the database

    Args:
        session : database session created in the route method
        flavor_payload (FlavorCreationPayload): The flavor to store

    Returns:
        FlavorDatabaseClass: The stored flavor object
    """
    # If no ID is provided, generate a new UUID
    flavor_id = flavor_payload.id or str(uuid.uuid4())

    # Ensure the ID is a UUID object
    flavor_id_uuid = uuid.UUID(flavor_id)

    # Convert openstack_flavor_id to UUID
    openstack_flavor_id_uuid = uuid.UUID(flavor_payload.openstack_flavor_id)

    flavor_to_create = Flavors(
        id=flavor_id_uuid,
        name=flavor_payload.name,
        processor=flavor_payload.processor,
        memory=flavor_payload.memory,
        bandwidth=flavor_payload.bandwidth,
        storage=flavor_payload.storage,
        gpu=flavor_payload.gpu or "None",
        price=flavor_payload.price or "Free",
        openstack_flavor_id=openstack_flavor_id_uuid,
    )

    session.add(flavor_to_create)
    await session.commit()

    return await get_flavor_from_database(session, flavor_to_create.id)


async def update_flavor_in_database(
    session: AsyncSession, flavor_uuid: uuid.UUID, flavor_payload: FlavorUpdatePayload
) -> FlavorInfo:
    """Update an existing flavor in the database

    Args:
        session: database session created in the route method
        flavor_uuid: UUID of the flavor to update
        flavor_payload: Payload containing fields to update

    Returns:
        FlavorDatabaseClass: The updated flavor object
    """
    # First, retrieve the existing flavor
    query = select(Flavors).where(Flavors.id == flavor_uuid)
    result = await session.execute(query)
    flavor = result.scalar_one_or_none()

    if flavor is None:
        raise FlavorRetrievalError(status_code=404, message=ERROR_MSG_FLAVOR_NOT_FOUND, code=FLAVOR_NOT_FOUND_ERROR)

    # Update only the non-None fields
    update_sqlalchemy_object_from_basemodel(flavor, flavor_payload)

    session.add(flavor)
    await session.commit()

    # Return the updated flavor
    return await get_flavor_from_database(session, flavor_uuid)


async def delete_flavor_from_database(session: AsyncSession, flavor_uuid: uuid.UUID) -> None:
    """Delete an existing flavor from the database

    Args:
        session: database session created in the route method
        flavor_uuid: UUID of the flavor to delete

    Raises:
        FlavorRetrievalError: If the flavor is not found
    """
    # First, check if the flavor exists
    query = select(Flavors).where(Flavors.id == flavor_uuid)
    result = await session.execute(query)
    flavor = result.scalar_one_or_none()

    if flavor is None:
        raise FlavorRetrievalError(status_code=404, message=ERROR_MSG_FLAVOR_NOT_FOUND, code=FLAVOR_NOT_FOUND_ERROR)

    await session.delete(flavor)
    await session.commit()
