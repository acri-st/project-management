import uuid

from msfwk.models import BaseModelAdjusted


class ProfileInfo(BaseModelAdjusted):
    id: uuid.UUID
    username: str
    password: str
    desp_owner_id: str


class ProfileCreationPayload(BaseModelAdjusted):
    id: str | None = None
    username: str
    password: str | None = None
    desp_owner_id: str


class ProfileUpdatePayload(BaseModelAdjusted):
    username: str | None = None
    password: str | None = None
    desp_owner_id: str | None = None
