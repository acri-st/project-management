from starlette.testclient import TestClient
from msfwk.utils.conftest import mock_read_config
from msfwk.utils.logging import get_logger
import uuid

from project_management.models.constants import REPOSITORY_NOT_FOUND_ERROR
from project_management.models.repositories import RepositoryCreationPayload
from tests.common_test_utils import TEST_UUID, assert_response, client
from tests.mock_data.test_data import test_repository

logger = get_logger("tests")

class TestRepositories:
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
        response = client.request("GET", f"/repositories/{TEST_UUID}")
        logger.info(response.content)
        assert_response(response, 404, REPOSITORY_NOT_FOUND_ERROR)
        
    def test_add_repository(
        self, client: TestClient,
    ) -> None:
        """
        Testing we can create a repository
        """
        response = client.request("POST", f"/repositories", json=test_repository.model_dump())
        logger.info(response.content)
        assert_response(response, 200)
        
    def test_get_repository(
        self, client: TestClient,
    ) -> None:
        """
        Testing we can fetch a repository
        """
        response = client.request("GET", f"/repositories/{TEST_UUID}")
        logger.info(response.content)
        assert_response(response, 200)
        assert response.json()["data"]["url"] == test_repository.model_dump()["url"]
        
    def test_update_repository(
        self, client: TestClient,
    ) -> None:
        """
        Testing we can update a repository
        """
        response = client.request("PATCH", f"/repositories/{TEST_UUID}", json={"url":"https://changed.example.com"})
        logger.info(response.content)
        assert response.status_code == 200
        assert response.json()["data"]["url"] == "https://changed.example.com"
        
    def test_delete_repository(
        self, client: TestClient,
    ) -> None:
        """
        Testing we can remove a repository and that is missing afterwards
        """
        response = client.request("DELETE", f"/repositories/{TEST_UUID}")
        logger.info(response.content)
        assert response.status_code == 200

        # Check the repository is indeed deleted
        response = client.request("GET", f"/repositories/{TEST_UUID}")
        logger.info(response.content)
        assert_response(response, 404, REPOSITORY_NOT_FOUND_ERROR)
