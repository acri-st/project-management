import pytest
from starlette.testclient import TestClient
from msfwk.utils.conftest import mock_read_config
from msfwk.utils.logging import get_logger
from project_management.models.applications import ApplicationCreationPayload
from tests.common_test_utils import TEST_UUID, assert_response, client
from tests.mock_data.test_data import test_application

from msfwk.utils.config import read_config


@pytest.mark.unit
def test_placeholder():
    assert True
    
logger = get_logger("tests")

class TestBaseServiceThings:
    """
    send help
    """
    def test_validation_application(
        self, client: TestClient,
    ) -> None:
        # Up an api to test out things
        response = client.request("GET", f"/health")
        
        config = read_config()
        assert config.get("database_sandbox") is not None