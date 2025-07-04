from datetime import datetime  # noqa: D100
from uuid import UUID

from msfwk.models import BaseModelAdjusted

###############
#  Resources
###############


class ResourceDatabaseBase(BaseModelAdjusted):
    """Class describing a resource class used in the database"""

    name: str
    processor: str
    memory: str
    bandwidth: str
    storage: str
    system: str
    price: int
    pool_name: str


class ResourceCreationPayload(ResourceDatabaseBase):
    """Class describing a resource that will be registered"""


class ResourceDatabaseClass(ResourceDatabaseBase):
    """Class describing a resource that has been updated."""

    id: UUID


class ResourceDatabaseReturnStruct(ResourceDatabaseBase):
    """Class describing an existing resource."""

    id: UUID
    created_at: datetime
    updated_at: datetime


###############
#  Repository
###############


class RepositoryDatabaseBase(BaseModelAdjusted):
    """Class describing a repository class used in the database"""

    url: str
    username: str
    token: str


class RepositoryCreationPayload(RepositoryDatabaseBase):
    """Class describing a repository that will be registered"""


class RepositoryDatabaseClass(RepositoryDatabaseBase):
    """Class describing a project that has been updated."""

    id: UUID


class RepositoryResponseStorage(BaseModelAdjusted):
    """Class describing a repository that will be send as a return"""

    id: UUID
    url: str
    token: str

    @staticmethod
    def from_record(record: dict) -> "RepositoryResponseStorage":
        """Return RepositoryResponseStorage from a business object"""
        return RepositoryResponseStorage(
            id=record["resource_id"],
            url=record["url"],
            token=record["token"],
        )


###############
#   Storage
###############


class GitServer(BaseModelAdjusted):
    """Class used to store git information to give to the storgae"""

    url: str
    token: str


class StoragePayload(BaseModelAdjusted):
    """Class used as a payload for storage requests"""

    repositoryName: str  # noqa: N815
    repositoryGroupe: str  # noqa: N815
    gitServer: GitServer | None  # noqa: N815


###############
#  Project
###############


class ProjectCreationPayload(BaseModelAdjusted):
    """Class describing a project that will be registered"""

    name: str
    repository: RepositoryCreationPayload | None = None
    resourceId: UUID  # noqa: N815
    applications: list


class ProjectDatabaseClass(BaseModelAdjusted):
    """Class describing a project that has been updated."""

    id: UUID
    name: str
    despOwner: str  # noqa: N815
    repositoryId: UUID  # noqa: N815
    resourceId: UUID  # noqa: N815


class ProjectDatabaseReturnStruct(BaseModelAdjusted):
    """Class describing an existing project."""

    id: UUID
    name: str
    despOwner: str  # noqa: N815
    repository: RepositoryDatabaseClass | None = None
    resource: ResourceDatabaseClass | None = None
    applications: list | None = None
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def from_record(record: dict) -> "ProjectDatabaseReturnStruct":
        """Reformat the project database response

        Args:
            record (dict): result of an sql query

        Returns:
            ProjectDatabaseReturnStruct: project ojbect as it should be return to the user
        """
        # Aggregate data
        project_details = None
        repository_details = None
        resource_details = None
        applications = []

        if not project_details:
            project_details = {
                key[len("project_") :]: value for key, value in record.items() if key.startswith("project_")
            }

        if not repository_details:
            repository_details = {
                key[len("repository_") :]: value for key, value in record.items() if key.startswith("repository_")
            }

        if not resource_details:
            resource_details = {
                key[len("resource_") :]: value for key, value in record.items() if key.startswith("resource_")
            }

        # Add application details if present
        application_record = {
            key[len("application_") :]: value for key, value in record.items() if key.startswith("application_")
        }
        if application_record and application_record.get("id"):
            applications.append(application_record)

        # Return structured data
        project = {
            **project_details,
            "repository": repository_details,
            "resource": resource_details,
            "applications": applications,
        }
        return ProjectDatabaseReturnStruct(**project)


class ProjectStatus(BaseModelAdjusted):
    """Class describing an existing project."""

    name: str
    status: str
    last_modified: datetime


class ProjectDeletionPayload(BaseModelAdjusted):
    """Class used for the paylaod to give informations about a project to delete"""

    pool_name: str
    project_id: str


###############
#   Profiles
###############


class ProfileDatabaseClass(BaseModelAdjusted):
    """Class describing an existing profile."""

    despUserId: str  # noqa: N815
    username: str
    password: str


###############
# Application
###############


class ApplicationXProjectDatabaseClass(BaseModelAdjusted):
    """Class describing an existing aplpication x project row in database."""

    applicationId: str  # noqa: N815
    projectId: str  # noqa: N815
