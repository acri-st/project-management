from starlette.testclient import TestClient
from msfwk.utils.conftest import mock_read_config
from msfwk.utils.logging import get_logger
from project_management.models.constants import APPLICATION_NOT_FOUND_ERROR
from project_management.models.applications import ApplicationCreationPayload
from tests.common_test_utils import TEST_UUID, assert_response, client
from tests.mock_data.test_data import test_application

logger = get_logger("tests")

class TestApplications:
    """
    The context for the client fixture is "class", 
    so tests from the same class will be executed successively without clearing the db
    """
    def test_empty(
        self, client: TestClient,
    ) -> None:
        """
        Testing we correctly receive 404 because none have been added yet
        """
        response = client.request("GET", f"/applications/{TEST_UUID}")
        logger.info(response.content)
        assert_response(response, 404, APPLICATION_NOT_FOUND_ERROR)
        
    def test_add_application(
        self, client: TestClient,
    ) -> None:
        """
        Testing we can create an application
        """
        response = client.request("POST", f"/applications", json=test_application.model_dump())
        logger.info(response.content)
        assert_response(response, 200)
        
    def test_get_application(
        self, client: TestClient,
    ) -> None:
        """
        Testing we can fetch an application
        """
        response = client.request("GET", f"/applications/{TEST_UUID}")
        logger.info(response.content)
        assert_response(response, 200)
        dump = test_application.model_dump()
        assert response.json()["data"]["name"] == test_application.model_dump()["name"]
        
    def test_update_application(
        self, client: TestClient,
    ) -> None:
        """
        Testing we can update an application
        """
        response = client.request("PATCH", f"/applications/{TEST_UUID}", json={"name":"changed"})
        logger.info(response.content)
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "changed"
        
    def test_delete_application(
        self, client: TestClient,
    ) -> None:
        """
        Testing we can remove an application and that is missing afterwards
        """
        response = client.request("DELETE", f"/applications/{TEST_UUID}")
        logger.info(response.content)
        assert response.status_code == 200

        # Check the application is indeed deleted
        response = client.request("GET", f"/applications/{TEST_UUID}")
        logger.info(response.content)
        assert_response(response, 404, APPLICATION_NOT_FOUND_ERROR)