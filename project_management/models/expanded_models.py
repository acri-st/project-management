import uuid

from msfwk.models import BaseModelAdjusted

from project_management.models.applications import ApplicationInfo, ApplicationInstallInfo
from project_management.models.flavors import FlavorInfo
from project_management.models.operatingsystems import OperatingSystemInfo
from project_management.models.profiles import ProfileInfo
from project_management.models.repositories import RepositoryInfo
from project_management.models.servers import ServerInfo

"""
All models which include expanded submodels
They are in a separate file to avoid circular imports
"""


class AvailableOperatingSystem(BaseModelAdjusted):
    """Class describing 1 application's possible installation"""

    name: str
    id: uuid.UUID
    script: str


class ApplicationExpanded(ApplicationInfo):
    """Class describing an application with expanded attributes"""

    available_operatingsystems: list[AvailableOperatingSystem]


class OperatingSystemExpanded(OperatingSystemInfo):
    applications: list[ApplicationInfo]


class ProjectExpanded(BaseModelAdjusted):
    id: uuid.UUID
    name: str
    ssh_key: str
    flavor: FlavorInfo
    repository: RepositoryInfo
    profile: ProfileInfo
    operatingsystem: OperatingSystemExpanded
    applications: list[ApplicationInstallInfo]
    server: ServerInfo | None
    logs: str | None
    status: str | None
    docker_image: str | None
