import uuid

from msfwk.models import BaseModelAdjusted


class FlavorInfo(BaseModelAdjusted):
    id: uuid.UUID
    name: str
    processor: str
    memory: str
    bandwidth: str
    storage: str
    gpu: str = "None"
    price: str = "Free"
    openstack_flavor_id: uuid.UUID


class FlavorCreationPayload(BaseModelAdjusted):
    id: str | None = None
    name: str
    processor: str
    memory: str
    bandwidth: str
    storage: str
    gpu: str | None = "None"
    price: str | None = "Free"
    openstack_flavor_id: str


class FlavorUpdatePayload(BaseModelAdjusted):
    name: str | None = None
    processor: str | None = None
    memory: str | None = None
    bandwidth: str | None = None
    storage: str | None = None
    gpu: str | None = None
    price: str | None = None
    openstack_flavor_id: uuid.UUID | None = None
