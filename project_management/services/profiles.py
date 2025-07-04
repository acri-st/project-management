import secrets
import string
import uuid

from despsharedlibrary.schemas.sandbox_schema import Profiles
from msfwk.context import current_user
from msfwk.exceptions import DbConnectionError, DespGenericError
from msfwk.models import DespUser
from msfwk.utils.logging import get_logger
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from project_management.models.constants import (
    CURRENT_USER_FETCH_ERROR,
    PROFILE_NOT_FOUND_ERROR,
)
from project_management.models.profiles import (
    ProfileCreationPayload,
    ProfileInfo,
    ProfileUpdatePayload,
)
from project_management.services.database_service import update_sqlalchemy_object_from_basemodel

logger = get_logger("profile")


async def get_or_create_current_profile(session: AsyncSession) -> ProfileInfo:
    """Fetch current user using the context (token in header)
    If it does not exist yet, it is created
    """
    user: DespUser | None = current_user.get()
    if user is None:
        raise DespGenericError(
            status_code=404,
            message="Could not fetch current user for the transaction during project creation",
            code=CURRENT_USER_FETCH_ERROR,
        )
    try:
        query = select(Profiles).where(Profiles.desp_owner_id == user.id)
        result = await session.execute(query)
        profile = result.scalar_one_or_none()

    except SQLAlchemyError as sqle:
        message = f"Error retrieving profile: {sqle}"
        logger.exception(message, exc_info=sqle)
        if isinstance(sqle, ConnectionError):
            raise DbConnectionError(code=PROFILE_NOT_FOUND_ERROR) from sqle
        raise DespGenericError(status_code=500, message=message, code=PROFILE_NOT_FOUND_ERROR) from sqle

    if profile is not None:
        # Profile found
        return await get_profile_from_database(session, profile.id)

    # Profile not found, create new profile
    return await store_profile_in_database(
        session, ProfileCreationPayload(username=user.username, desp_owner_id=user.id)
    )


async def get_profile_from_database(session: AsyncSession, profile_uuid: uuid.UUID) -> ProfileInfo:
    """Fetch profile from the database
    Args:
        session : database session created in the route method
        profile_uuid : uuid of the profile to fetch
    """
    query = select(Profiles).where(Profiles.id == profile_uuid)
    result = await session.execute(query)
    profile = result.scalar_one_or_none()

    logger.debug("Found profile: %s", profile)

    if profile is None:
        raise DespGenericError(status_code=404, message="Profile not found", code=PROFILE_NOT_FOUND_ERROR)

    return ProfileInfo(
        id=profile.id, username=profile.username, password=profile.password, desp_owner_id=profile.desp_owner_id
    )


async def store_profile_in_database(session: AsyncSession, profile_payload: ProfileCreationPayload) -> ProfileInfo:
    """Store profile in the database

    Args:
        session : database session created in the route method
        profile_payload (ProfileCreationPayload): The profile to store

    Returns:
        ProfileDatabaseClass: The stored profile object
    """
    # If no ID is provided, generate a new UUID
    profile_id = profile_payload.id or str(uuid.uuid4())

    # Ensure the ID is a UUID object
    profile_id_uuid = uuid.UUID(profile_id)

    if profile_payload.password is None:
        profile_payload.password = _generate_user_credentials()

    profile_to_create = Profiles(
        id=profile_id_uuid,
        username=profile_payload.username,
        password=profile_payload.password,
        desp_owner_id=profile_payload.desp_owner_id,
    )

    session.add(profile_to_create)
    await session.commit()

    return await get_profile_from_database(session, profile_to_create.id)


async def update_profile_in_database(
    session: AsyncSession, profile_uuid: uuid.UUID, profile_payload: ProfileUpdatePayload
) -> ProfileInfo:
    """Update an existing profile in the database

    Args:
        session: database session created in the route method
        profile_uuid: UUID of the profile to update
        profile_payload: Payload containing fields to update

    Returns:
        ProfileDatabaseClass: The updated profile object
    """
    # First, retrieve the existing profile
    query = select(Profiles).where(Profiles.id == profile_uuid)
    result = await session.execute(query)
    profile = result.scalar_one_or_none()

    if profile is None:
        raise DespGenericError(status_code=404, message="Profile to update not found", code=PROFILE_NOT_FOUND_ERROR)

    # Update only the non-None fields
    update_sqlalchemy_object_from_basemodel(profile, profile_payload)

    session.add(profile)
    await session.commit()

    # Return the updated profile
    return await get_profile_from_database(session, profile_uuid)


async def delete_profile_from_database(session: AsyncSession, profile_uuid: uuid.UUID) -> None:
    """Delete an existing profile from the database

    Args:
        session: database session created in the route method
        profile_uuid: UUID of the profile to delete

    Raises:
        DespGenericError: If the profile is not found or cannot be deleted
    """
    # First, check if the profile exists
    query = select(Profiles).where(Profiles.id == profile_uuid)
    result = await session.execute(query)
    profile = result.scalar_one_or_none()

    if profile is None:
        raise DespGenericError(status_code=404, message="Profile to delete not found", code=PROFILE_NOT_FOUND_ERROR)

    await session.delete(profile)
    await session.commit()


def _generate_user_credentials(length: int = 12) -> str:
    """Generate a secure password.

    Args:
        length (int, optional): Length of the password. Defaults to 12.

    Returns:
        str: Password generated.
    """
    if length < 4:  # noqa: PLR2004
        msg = "Password length must be at least 4 to include all character types."
        raise ValueError(msg)

    # Define the character pools
    digits = string.digits
    lower_case = string.ascii_lowercase
    upper_case = string.ascii_uppercase
    special_chars = "&#@$%?!"

    password = [
        secrets.choice(digits),
        secrets.choice(lower_case),
        secrets.choice(upper_case),
        secrets.choice(special_chars),
    ]

    # Fill the rest of the password length with random characters from all pools
    all_chars = digits + lower_case + upper_case + special_chars
    password += [secrets.choice(all_chars) for _ in range(length - 4)]

    # Shuffle the password to avoid predictable patterns
    secrets.SystemRandom().shuffle(password)

    # Convert the list to a string
    return "".join(password)
