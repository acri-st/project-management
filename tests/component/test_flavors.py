from starlette.testclient import TestClient
from msfwk.utils.conftest import mock_read_config
from msfwk.utils.logging import get_logger
import uuid

from project_management.models.constants import FLAVOR_NOT_FOUND_ERROR
from project_management.models.flavors import FlavorCreationPayload
from tests.common_test_utils import TEST_UUID, assert_response, client
from tests.mock_data.test_data import test_flavor

logger = get_logger("tests")

class TestFlavors:
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
        response = client.request("GET", f"/flavors/{TEST_UUID}")
        logger.info(response.content)
        assert_response(response, 404, FLAVOR_NOT_FOUND_ERROR)
        
    def test_add_flavor(
        self, client: TestClient,
    ) -> None:
        """
        Testing we can create a flavor
        """
        response = client.request("POST", f"/flavors", json=test_flavor.model_dump())
        logger.info(response.content)
        assert_response(response, 200)
        
    def test_get_flavor(
        self, client: TestClient,
    ) -> None:
        """
        Testing we can fetch a flavor
        """
        response = client.request("GET", f"/flavors/{TEST_UUID}")
        logger.info(response.content)
        assert_response(response, 200)
        assert response.json()["data"]["name"] == test_flavor.model_dump()["name"]
        
    def test_get_flavors(
        self, client: TestClient,
    ) -> None:
        """
        Testing we can fetch a flavor
        """
        response = client.request("GET", f"/flavors")
        logger.info(response.content)
        assert_response(response, 200)
        assert len(response.json()["data"]) == 1
        
    def test_update_flavor(
        self, client: TestClient,
    ) -> None:
        """
        Testing we can update a flavor
        """
        response = client.request("PATCH", f"/flavors/{TEST_UUID}", json={"name":"changed"})
        logger.info(response.content)
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "changed"
        
    def test_delete_flavor(
        self, client: TestClient,
    ) -> None:
        """
        Testing we can remove a flavor and that is missing afterwards
        """
        response = client.request("DELETE", f"/flavors/{TEST_UUID}")
        logger.info(response.content)
        assert response.status_code == 200

        # Check the flavor is indeed deleted
        response = client.request("GET", f"/flavors/{TEST_UUID}")
        logger.info(response.content)
        assert_response(response, 404, FLAVOR_NOT_FOUND_ERROR)
