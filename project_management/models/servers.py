import uuid

from despsharedlibrary.schemas.sandbox_schema import ServerStatus
from msfwk.models import BaseModelAdjusted


class ServerInfo(BaseModelAdjusted):
    """Server information"""

    id: uuid.UUID
    public_ip: str | None
    state: ServerStatus | None
