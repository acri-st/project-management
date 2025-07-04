from uuid import UUID

from msfwk.models import BaseModelAdjusted


class ApplicationInfo(BaseModelAdjusted):
    """Class describing an existing application in database"""

    id: UUID
    name: str
    description: str
    icon: bytes


class ApplicationInstallInfo(ApplicationInfo):
    """Class describing an existing application in database + the script"""

    script: str


class ApplicationCreationPayload(BaseModelAdjusted):
    """_Class describing an application that will be registered"""

    id: str | None = None
    name: str
    description: str
    icon: bytes = b""


class ApplicationUpdatePayload(BaseModelAdjusted):
    """_Class describing an application change"""

    name: str | None = None
    description: str | None = None
    icon: bytes | None = None


class ApplicationInstallPayload(BaseModelAdjusted):
    """_Class describing an installation of an app on a specific OS"""

    operatingsystem_id: str
    script: str
