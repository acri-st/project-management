import uuid

from msfwk.models import BaseModelAdjusted


class OperatingSystemInfo(BaseModelAdjusted):
    id: uuid.UUID
    name: str
    is_gui: bool


class OperatingSystemCreationPayload(BaseModelAdjusted):
    id: str | None = None
    name: str
    is_gui: bool = False


class OperatingSystemUpdatePayload(BaseModelAdjusted):
    name: str | None = None
    is_gui: bool | None = None
