import asyncio
import logging
import uuid

from despsharedlibrary.schemas.sandbox_schema import KeycloakRealms
from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakAuthenticationError, KeycloakConnectionError, KeycloakError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from project_management.models.constants import KEYCLOAK_SETUP_ERROR
from project_management.models.exceptions import KeycloakSetupError
from project_management.utils.keycloak_config import CLIENT_REPRESENTATION_TEMPLATE, KEYCLOAK_CONFIG

logger = logging.getLogger(__name__)

async def create_realm(keycloak_admin: KeycloakAdmin, realm_name: str) -> None:
    """Create a new Keycloak realm.

    Args:
        keycloak_admin: KeycloakAdmin instance
        realm_name: Name of the realm to create

    Raises:
        KeycloakSetupError: If realm creation fails
    """
    realm_representation = {
        "realm": realm_name,
        "enabled": True,
        "displayName": f"{realm_name.capitalize()} Realm",
    }
    try:
        keycloak_admin.connection.get_token()
        keycloak_admin.create_realm(payload=realm_representation, skip_exists=True)
        logger.info("Realm '%s' created or already exists", realm_name)
    except KeycloakError as ke:
        error_msg = "Failed to create realm '%s': %s"
        logger.exception(error_msg, exc_info=ke)
        raise KeycloakSetupError(
            status_code=500,
            code=KEYCLOAK_SETUP_ERROR,
            message=error_msg % (realm_name, str(ke))
        ) from ke

async def create_client(
    keycloak_admin: KeycloakAdmin,
) -> str:
    """Create a new client in the specified realm.

    Args:
        keycloak_admin: KeycloakAdmin instance
        client_id: ID of the client to create
        redirect_uris: List of redirect URIs for the client
        web_origins: List of web origins for the client

    Returns:
        str: ID of the created client

    Raises:
        KeycloakSetupError: If client creation fails
    """
    client_representation = CLIENT_REPRESENTATION_TEMPLATE

    try:
        client_id = keycloak_admin.create_client(payload=client_representation)
        logger.info("Client '%s' created successfully", client_id)
        return client_id
    except KeycloakError as e:
        error_msg = "Failed to create client '%s': %s"
        logger.exception(error_msg, client_id, str(e))
        raise KeycloakSetupError(
            status_code=500,
            code=KEYCLOAK_SETUP_ERROR,
            message=error_msg % (client_id, str(e))
        ) from e


async def initialize_keycloak_admin() -> KeycloakAdmin:
    """Initialize and return a KeycloakAdmin instance.

    Returns
        KeycloakAdmin: Initialized KeycloakAdmin instance

    Raises
        KeycloakSetupError: If initialization fails
    """
    try:
        logger.debug("Initializing Keycloak admin")
        return KeycloakAdmin(
            server_url=KEYCLOAK_CONFIG["server_url"],
            username=KEYCLOAK_CONFIG["admin_username"],
            password=KEYCLOAK_CONFIG["admin_password"],
            realm_name=KEYCLOAK_CONFIG["master_realm"],
            verify=KEYCLOAK_CONFIG["verify_ssl"]
        )
    except (KeycloakConnectionError, KeycloakAuthenticationError) as e:
        error_msg = "Failed to initialize Keycloak admin: %s"
        logger.exception(error_msg, str(e))
        raise KeycloakSetupError(
            status_code=500,
            code=KEYCLOAK_SETUP_ERROR,
            message=error_msg % str(e)
        ) from e

async def create_default_user(keycloak_admin: KeycloakAdmin, username: str, email: str, realm_name: str) -> None:
    """Create a default user in the specified realm.

    Args:
        keycloak_admin: KeycloakAdmin instance
        username: Username for the default user
        email: Email for the default user
        realm_name: Name of the realm

    Raises:
        KeycloakSetupError: If user creation fails
    """
    try:
        user_data = {
            "username": username,
            "enabled": True,
            "credentials": [{
                "type": "password",
                "value": "initial123",  # Initial password that should be changed on first login
                "temporary": True
            }],
            "firstName": "Default",
            "lastName": "User",
            "email": email,
            "emailVerified": True
        }
        await asyncio.to_thread(keycloak_admin.create_user, user_data)
        logger.info("Created default user for realm %s", realm_name)
    except Exception as e:
        error_msg = f"Failed to create default user in realm {realm_name}: {str(e)}"
        logger.error(error_msg)
        raise KeycloakSetupError(
            status_code=500,
            code=KEYCLOAK_SETUP_ERROR,
            message=error_msg
        ) from e

async def setup_keycloak_realm_and_client(
    project_id: uuid.UUID,
    username: str,
    email: str,
    db_session: AsyncSession,
) -> str:
    """Main function to set up a Keycloak realm and client.

    Args:
        username: Username for the default user
        email: Email for the default user
        db_session: Database session for storing realm data
        project_id: UUID of the project
    Returns:
        str: Client ID if successful

    Raises:
        KeycloakSetupError: If setup fails
    """
    try:
        logger.debug("Initializing Keycloak admin")
        # Initialize Keycloak admin
        keycloak_admin = await initialize_keycloak_admin()

        # Create realm
        realm_name = str(project_id)
        logger.debug("Creating realm %s", realm_name)
        await create_realm(keycloak_admin, realm_name)

        # Switch to the new realm
        logger.debug("Switching to realm %s", realm_name)
        keycloak_admin.connection.realm_name = realm_name

        # Create client
        logger.debug("Creating client")
        client_id = await create_client(keycloak_admin)
        # Create default user
        logger.debug("Creating default user in realm %s", realm_name)
        await create_default_user(keycloak_admin, username, email, realm_name)

        # Store realm data in database
        logger.debug("Storing Keycloak realm data in database")
        await store_keycloak_realm_data(db_session, project_id, realm_name, client_id, username)

        return client_id

    except KeycloakSetupError as e:
        logger.exception("Keycloak setup failed: %s", str(e))
        raise
    except Exception as e:
        error_msg = "Unexpected error during Keycloak setup: %s"
        logger.exception(error_msg, str(e))
        raise KeycloakSetupError(
            status_code=500,
            code=KEYCLOAK_SETUP_ERROR,
            message=error_msg % str(e)
        ) from e

async def store_keycloak_realm_data(
    db_session: AsyncSession,
    project_id: uuid.UUID,
    realm_name: str,
    client_id: str,
    username: str
) -> None:
    """Store Keycloak realm data in the database.

    Args:
        db_session: Database session
        project_id: UUID of the project
        realm_name: Name of the realm
        client_id: ID of the created client
        username: Username of the default user

    Raises:
        KeycloakSetupError: If storing data fails
    """
    try:

        keycloak_realm = KeycloakRealms(
            project_id=project_id,
            realm_name=realm_name,
            client_id=client_id,
            user=username
        )

        db_session.add(keycloak_realm)
        await db_session.commit()

        logger.info("Stored Keycloak realm data for project %s", project_id)

    except Exception as e:
        error_msg = f"Failed to store Keycloak realm data for project {project_id}: {str(e)}"
        logger.exception(error_msg)
        raise KeycloakSetupError(
            status_code=500,
            code=KEYCLOAK_SETUP_ERROR,
            message=error_msg
        ) from e

async def get_keycloak_realm_data(db_session: AsyncSession, project_id: uuid.UUID) -> KeycloakRealms | None:
    """Retrieve Keycloak realm data from the database for a project.

    Args:
        db_session: Database session
        project_id: UUID of the project

    Returns:
        KeycloakRealms | None: Keycloak realm data if found, None otherwise
    """
    try:
        query = select(KeycloakRealms).where(KeycloakRealms.project_id == project_id)
        result = await db_session.execute(query)
        return result.scalar_one_or_none()
    except Exception as e:
        logger.exception("Failed to retrieve Keycloak realm data for project %s: %s", project_id, str(e))
        return None



async def delete_keycloak_realm(keycloak_admin: KeycloakAdmin, realm_name: str) -> None:
    """Delete a Keycloak realm.

    Args:
        keycloak_admin: KeycloakAdmin instance
        realm_name: Name of the realm to delete

    Raises:
        KeycloakSetupError: If realm deletion fails
    """
    try:
        await asyncio.to_thread(keycloak_admin.delete_realm, realm_name=realm_name)
        logger.info("Deleted realm %s", realm_name)
    except Exception as e:
        error_msg = f"Failed to delete realm {realm_name}: {str(e)}"
        logger.exception(error_msg)
        raise KeycloakSetupError(
            status_code=500,
            code=KEYCLOAK_SETUP_ERROR,
            message=error_msg
        ) from e

async def delete_keycloak_realm_data(db_session: AsyncSession, project_id: uuid.UUID) -> None:
    """Delete Keycloak realm data from the database.

    Args:
        db_session: Database session
        project_id: UUID of the project

    Raises:
        KeycloakSetupError: If deleting data fails
    """
    try:
        query = select(KeycloakRealms).where(KeycloakRealms.project_id == project_id)
        result = await db_session.execute(query)
        keycloak_realm = result.scalar_one_or_none()

        if keycloak_realm:
            await db_session.delete(keycloak_realm)
            await db_session.commit()
            logger.info("Deleted Keycloak realm data for project %s", project_id)
        else:
            logger.warning("No Keycloak realm data found for project %s", project_id)
    except Exception as e:
        error_msg = f"Failed to delete Keycloak realm data for project {project_id}: {str(e)}"
        logger.exception(error_msg)
        raise KeycloakSetupError(
            status_code=500,
            code=KEYCLOAK_SETUP_ERROR,
            message=error_msg
        ) from e

async def cleanup_keycloak_for_project(
    db_session: AsyncSession,
    project_id: uuid.UUID,
) -> None:
    """Clean up Keycloak resources for a project by deleting the realm (which automatically deletes clients and users) and database data.

    Args:
        db_session: Database session
        project_id: UUID of the project

    Raises:
        KeycloakSetupError: If cleanup fails
    """
    try:
        # Get Keycloak realm data from database
        keycloak_realm_data = await get_keycloak_realm_data(db_session, project_id)
        if not keycloak_realm_data:
            logger.info("No Keycloak realm data found for project %s, skipping cleanup", project_id)
            return

        # Initialize Keycloak admin
        keycloak_admin = await initialize_keycloak_admin()

        # Switch back to master realm to delete the realm
        keycloak_admin.connection.realm_name = KEYCLOAK_CONFIG["master_realm"]

        # Delete realm (this will automatically delete all clients and users in the realm)
        try:
            await delete_keycloak_realm(keycloak_admin, keycloak_realm_data.realm_name)
        except Exception as e:
            logger.warning("Failed to delete realm %s: %s", keycloak_realm_data.realm_name, str(e))

        # Delete database data
        await delete_keycloak_realm_data(db_session, project_id)

        logger.info("Successfully cleaned up Keycloak resources for project %s", project_id)

    except Exception as e:
        error_msg = f"Failed to cleanup Keycloak resources for project {project_id}: {str(e)}"
        logger.exception(error_msg)
        raise KeycloakSetupError(
            status_code=500,
            code=KEYCLOAK_SETUP_ERROR,
            message=error_msg
        ) from e

