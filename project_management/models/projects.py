from msfwk.models import BaseModelAdjusted

class ProjectCreationPayload(BaseModelAdjusted):
    id: str | None = None
    name: str
    ssh_key: str
    flavor_id: str
    repository_id: str | None = None
    operatingsystem_id: str
    application_ids: list[str] = []


class ProjectUpdatePayload(BaseModelAdjusted):
    name: str | None = None
    ssh_key: str | None = None
    flavor_id: str | None = None
    repository_id: str | None = None
    profile_id: str | None = None
    operatingsystem_id: str | None = None


class BuildStatusPayload(BaseModelAdjusted):
    status: str
    step: str
    message: str | None = None
    logs: str | None = None
    docker_image: str | None = None
    pipeline_id: str | None = None
    profile_id : str
