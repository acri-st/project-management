import datetime
import uuid

from despsharedlibrary.schemas.sandbox_schema import EventType
from msfwk.models import BaseModelAdjusted


class EventInfo(BaseModelAdjusted):
    """Event information"""

    id: int
    project_id: uuid.UUID
    type: EventType
    content: str
    created_at: datetime.datetime
    pipeline_id: str
    step: str
    status: str


class EventFilterPayload(BaseModelAdjusted):
    """Event filter payload"""

    event_type: str | None = None  # Optional filter by event type
    sort_by_date: bool = True  # Optional sorting by date (True by default)
