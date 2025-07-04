import uuid  # noqa: D100, INP001

from aiohttp.client_exceptions import ClientConnectorError
from msfwk.context import current_config, current_user
from msfwk.exceptions import DespGenericError
from msfwk.request import HttpClient
from msfwk.utils.logging import get_logger
from sqlalchemy.ext.asyncio import AsyncSession

from project_management.models.constants import REPOSITORY_CREATION_ERROR, VM_MGMT_ERROR
from project_management.models.exceptions import RepositoryCreationError
from project_management.models.expanded_models import ProjectExpanded
from project_management.models.repositories import (
    RepositoryCreationPayload,
)
from project_management.services.repositories import store_repository_in_database

logger = get_logger("other_services")

"""
Functions that call upon other DESP services
"""


async def create_vm_with_vm_mgmt(project: ProjectExpanded) -> None:
    """Creata a new vm

    Args:
        project (ProjectExpanded): object coanting information about a projects
    """
    try:
        http_client = HttpClient()
        vm_creation_payload = {
            "username": project.profile.username,
            "password": project.profile.password,
            "image_name": project.operatingsystem.name,
            "flavor_name": project.flavor.name,
            "ssh_public_key": project.ssh_key,
            "project_id": str(project.id),
        }
        # Call the vm mgmt service to handle ovh creation etc
        async with (
            http_client.get_service_session("vm-management") as http_session,
            http_session.post("/servers", json=vm_creation_payload) as response,
        ):
            if response.status != 200:  # noqa: PLR2004
                logger.error(await response.json())
            else:
                logger.info("VM creation launched !")

            response_content = await response.json()
            logger.info("Reponse from the service: %s", response_content)

    except Exception as E:
        msg = f"Exception while contacting vm mgmt during project creation : {E}"
        logger.exception(msg)
        raise DespGenericError(
            status_code=500,
            message=f"Could not call vm mgmt during project creation : {E}",
            code=VM_MGMT_ERROR,
        ) from None


async def create_repository_in_storage(repository_name: str) -> RepositoryCreationPayload:
    """Create a new repository in storage

    Args:
        repository_name (str): name of the repository

    Returns:
        RepositoryCreationPayload: object containing infot necessary to create a new repository
    """
    http_client = HttpClient()
    repository_creation_payload = {
        "repositoryName": repository_name,
        "repositoryGroupe": current_config.get()
        .get("services", {})
        .get("project-management", {})
        .get("repository_group", "desp-aas-projects"),
        "gitServer": None,
    }

    try:
        async with (
            http_client.get_service_session("storage") as http_session,
            http_session.post("/repository", json=repository_creation_payload) as response,
        ):
            if response.status not in (200, 201):
                error = await response.json()
                logger.error("Failed to create repository %s, %s", response.status, error)
                raise RepositoryCreationError(error["error"]["message"])
            logger.info("Repository registered in GitLab")

            response_content = await response.json()
            logger.info("Response from the storage: %s", response_content)

            return RepositoryCreationPayload(
                id=response_content["data"]["resource_id"],
                username=current_user.get().username,
                url=response_content["data"]["url"],
                token=response_content["data"]["token"],
            )

    except ClientConnectorError as cce:
        message = "Failed to create repository due to service unavailability"
        logger.exception(message, exc_info=cce)
        raise RepositoryCreationError(message) from cce


async def create_repository_with_storage_service(session: AsyncSession, repository_name: str) -> uuid.UUID:
    """Creata a new repository using the module storage

    Args:
        session (AsyncSession): session used to connect to the database
        repository_name (str): name of the new repository

    Returns:
        uuid.UUID: id of the new repository
    """
    try:
        new_repo = await create_repository_in_storage(repository_name)
        created_repo = await store_repository_in_database(session, new_repo)
        return created_repo.id  # noqa: TRY300

    except RepositoryCreationError as rce:
        message = "Failed to create repository in storage service"
        logger.exception(message, exc_info=rce)
        raise DespGenericError(
            status_code=400,
            message=str(rce),
            code=REPOSITORY_CREATION_ERROR,
        ) from rce

    except Exception as e:
        logger.exception("Exception while creating repository during project creation: %s", e)  # noqa: TRY401
        raise DespGenericError(
            status_code=500,
            message=f"Could not initialize repository during project creation: {e}",
            code=REPOSITORY_CREATION_ERROR,
        ) from e
