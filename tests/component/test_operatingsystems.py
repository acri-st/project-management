from starlette.testclient import TestClient
from msfwk.utils.conftest import mock_read_config
from msfwk.utils.logging import get_logger
import uuid

from project_management.models.constants import OPERATING_SYSTEM_NOT_FOUND_ERROR
from project_management.models.operatingsystems import OperatingSystemCreationPayload
from tests.common_test_utils import TEST_UUID, assert_response, client
from tests.mock_data.test_data import test_operatingsystem

logger = get_logger("tests")

class TestOperatingSystems:
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
        response = client.request("GET", f"/operatingsystems/{TEST_UUID}")
        logger.info(response.content)
        assert_response(response, 404, OPERATING_SYSTEM_NOT_FOUND_ERROR)
        
    def test_add_operatingsystem(
        self, client: TestClient,
    ) -> None:
        """
        Testing we can create an operating system
        """
        response = client.request("POST", f"/operatingsystems", json=test_operatingsystem.model_dump())
        logger.info(response.content)
        assert_response(response, 200)
        
    def test_get_operatingsystem(
        self, client: TestClient,
    ) -> None:
        """
        Testing we can fetch an operating system
        """
        response = client.request("GET", f"/operatingsystems/{TEST_UUID}")
        logger.info(response.content)
        assert_response(response, 200)
        assert response.json()["data"]["name"] == test_operatingsystem.model_dump()["name"]
        
    def test_update_operatingsystem(
        self, client: TestClient,
    ) -> None:
        """
        Testing we can update an operating system
        """
        response = client.request("PATCH", f"/operatingsystems/{TEST_UUID}", json={"name":"changed"})
        logger.info(response.content)
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "changed"
        
    def test_delete_operatingsystem(
        self, client: TestClient,
    ) -> None:
        """
        Testing we can remove an operating system and that is missing afterwards
        """
        response = client.request("DELETE", f"/operatingsystems/{TEST_UUID}")
        logger.info(response.content)
        assert response.status_code == 200

        # Check the operating system is indeed deleted
        response = client.request("GET", f"/operatingsystems/{TEST_UUID}")
        logger.info(response.content)
        assert_response(response, 404, OPERATING_SYSTEM_NOT_FOUND_ERROR)
