from starlette.testclient import TestClient
from msfwk.utils.conftest import mock_read_config
from msfwk.utils.logging import get_logger
from project_management.models.applications import ApplicationCreationPayload
from tests.common_test_utils import TEST_UUID, assert_response, client
from tests.mock_data.test_data import test_application

logger = get_logger("tests")

class TestValidation:
    """
    The context for the client fixture is "class", 
    so tests from the same class will be executed successively without clearing the db
    """
    def test_validation_application(
        self, client: TestClient,
    ) -> None:
        """
        Testing we can create an application
        """
        response = client.request("POST", f"/applications", json={})
        logger.info(response.content)
        assert_response(response, 422)