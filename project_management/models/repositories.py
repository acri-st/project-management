import uuid

from msfwk.models import BaseModelAdjusted


class RepositoryInfo(BaseModelAdjusted):
    id: uuid.UUID
    username: str
    url: str
    token: str


class RepositoryCreationPayload(BaseModelAdjusted):
    id: str | None = None
    username: str
    url: str
    token: str


class RepositoryUpdatePayload(BaseModelAdjusted):
    username: str | None = None
    url: str | None = None
    token: str | None = None
