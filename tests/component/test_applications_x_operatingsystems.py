from starlette.testclient import TestClient
from msfwk.utils.conftest import mock_read_config
from msfwk.utils.logging import get_logger
from project_management.models.constants import APPLICATION_NOT_FOUND_ERROR
from project_management.models.applications import ApplicationCreationPayload, ApplicationInstallPayload
from tests.common_test_utils import TEST_UUID, assert_response, client
from tests.mock_data.test_data import test_application, test_operatingsystem

logger = get_logger("tests")

class TestApplications_x_OperatingSystems:
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
    
    def test_add_operatingsystem(
        self, client: TestClient,
    ) -> None:
        """
        Testing we can create an operating system
        """
        response = client.request("POST", f"/operatingsystems", json=test_operatingsystem.model_dump())
        logger.info(response.content)
        assert_response(response, 200)
        
    def test_add_install_script(
        self, client: TestClient,
    ) -> None:
        """
        Testing we can add an installation script
        """
        response = client.request(
            "PUT", 
            f"/applications/{TEST_UUID}/installation", 
            json=ApplicationInstallPayload(operatingsystem_id=TEST_UUID, script="initial").model_dump(),
        )
        logger.info(response.content)
        assert_response(response, 200)
        assert len(response.json()["data"]["available_operatingsystems"]) == 1
        assert response.json()["data"]["available_operatingsystems"][0]["script"] == "initial"
        
    def test_update_install_script(
        self, client: TestClient,
    ) -> None:
        """
        Testing we can add an installation script
        """
        response = client.request(
            "PUT", 
            f"/applications/{TEST_UUID}/installation", 
            json=ApplicationInstallPayload(operatingsystem_id=TEST_UUID, script="updated").model_dump(),
        )
        logger.info(response.content)
        assert_response(response, 200)
        assert len(response.json()["data"]["available_operatingsystems"]) == 1
        assert response.json()["data"]["available_operatingsystems"][0]["script"] == "updated"
        
    def test_get_all_applications_with_os(
        self, client: TestClient,
    ) -> None:
        """
        Testing we can fetch all of them
        """
        response = client.request(
            "GET", 
            f"/applications"
        )
        logger.info(response.content)
        assert_response(response, 200)
        assert len(response.json()["data"]) == 1
        assert len(response.json()["data"][0]["available_operatingsystems"]) == 1
        assert response.json()["data"][0]["available_operatingsystems"][0]["script"] == "updated"