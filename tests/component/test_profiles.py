from starlette.testclient import TestClient
from msfwk.utils.conftest import mock_read_config
from msfwk.utils.logging import get_logger

from project_management.models.constants import PROFILE_NOT_FOUND_ERROR
from project_management.models.profiles import ProfileCreationPayload
from tests.common_test_utils import TEST_UUID, assert_response, client
from tests.mock_data.test_data import test_profile

logger = get_logger("tests")

class TestProfiles:
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
        response = client.request("GET", f"/profiles/{TEST_UUID}")
        logger.info(response.content)
        assert_response(response, 404, PROFILE_NOT_FOUND_ERROR)
        
    def test_add_profile(
        self, client: TestClient,
    ) -> None:
        """
        Testing we can create a profile
        """
        response = client.request("POST", f"/profiles", json=test_profile.model_dump())
        logger.info(response.content)
        assert_response(response, 200)
        
    def test_get_profile(
        self, client: TestClient,
    ) -> None:
        """
        Testing we can fetch a profile
        """
        response = client.request("GET", f"/profiles/{TEST_UUID}")
        logger.info(response.content)
        assert_response(response, 200)
        assert response.json()["data"]["username"] == test_profile.model_dump()["username"]
        
    def test_update_profile(
        self, client: TestClient,
    ) -> None:
        """
        Testing we can update a profile
        """
        response = client.request("PATCH", f"/profiles/{TEST_UUID}", json={"username":"changed"})
        logger.info(response.content)
        assert response.status_code == 200
        assert response.json()["data"]["username"] == "changed"
        
    def test_delete_profile(
        self, client: TestClient,
    ) -> None:
        """
        Testing we can remove a profile and that is missing afterwards
        """
        response = client.request("DELETE", f"/profiles/{TEST_UUID}")
        logger.info(response.content)
        assert response.status_code == 200

        # Check the profile is indeed deleted
        response = client.request("GET", f"/profiles/{TEST_UUID}")
        logger.info(response.content)
        assert_response(response, 404, PROFILE_NOT_FOUND_ERROR)
