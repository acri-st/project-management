import uuid
from project_management.models.applications import ApplicationCreationPayload
from project_management.models.operatingsystems import OperatingSystemCreationPayload
from project_management.models.flavors import FlavorCreationPayload
from project_management.models.profiles import ProfileCreationPayload
from project_management.models.projects import ProjectCreationPayload
from project_management.models.repositories import RepositoryCreationPayload
from tests.common_test_utils import TEST_UUID

test_profile = ProfileCreationPayload(
    id=TEST_UUID,
    username="test-user",
    password="test-password",
    desp_owner_id="some-id"
)

test_application = ApplicationCreationPayload(
    id=TEST_UUID,
    name="test application", 
    description="this is a test application",
    icon=b""
)

test_operatingsystem = OperatingSystemCreationPayload(
    id=TEST_UUID,
    name="Test Operating System"
)

test_flavor = FlavorCreationPayload(
    id=TEST_UUID,
    name="Test Flavor",
    processor="Test Processor",
    memory="8GB",
    bandwidth="1Gbps",
    storage="256GB SSD",
    gpu="None",
    price="Free",
    openstack_flavor_id=str(uuid.uuid4())
)

test_repository = RepositoryCreationPayload(
    id=TEST_UUID,
    url="https://gitlab.example.com/test-repo",
    username="test_user",
    token="test_token"
)

test_project = ProjectCreationPayload(
    id=TEST_UUID,
    name="test project",
    ssh_key="ssh key",
    flavor_id=TEST_UUID,
    repository_id=TEST_UUID,
    operatingsystem_id=TEST_UUID,
    application_ids=[]
)