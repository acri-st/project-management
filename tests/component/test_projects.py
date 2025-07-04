from starlette.testclient import TestClient
from msfwk.utils.conftest import mock_read_config
from msfwk.utils.logging import get_logger

from project_management.models.constants import PROJECT_NOT_FOUND_ERROR
from project_management.models.projects import ProjectCreationPayload
from tests.common_test_utils import TEST_UUID, assert_response, client
from tests.mock_data.test_data import test_project, test_flavor, test_operatingsystem, test_profile, test_repository

logger = get_logger("tests")

class TestProjects:
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
        response = client.request("GET", f"/projects/{TEST_UUID}")
        assert_response(response, 404, PROJECT_NOT_FOUND_ERROR)

    def test_add_project_dependencies(
        self, client: TestClient,
    ) -> None:
        response = client.request("POST", f"/repositories", json=test_repository.model_dump())
        assert_response(response, 200)
        response = client.request("POST", f"/flavors", json=test_flavor.model_dump())
        assert_response(response, 200)
        response = client.request("POST", f"/operatingsystems", json=test_operatingsystem.model_dump())
        assert_response(response, 200)

    # Require the DESP specific header/cookie whatever to fetch current_user
    # def test_add_project(
    #     self, client: TestClient,
    # ) -> None:
    #     """
    #     Testing we can create a project
    #     """
    #     response = client.request("POST", f"/projects", json=test_project.model_dump())
    #     assert_response(response, 200)
        
    # def test_get_project(
    #     self, client: TestClient,
    # ) -> None:
    #     """
    #     Testing we can fetch a project
    #     """
    #     response = client.request("GET", f"/projects/{TEST_UUID}")
    #     assert_response(response, 200)
    #     assert response.json()["data"]["name"] == test_project.model_dump()["name"]
        
    # def test_update_project(
    #     self, client: TestClient,
    # ) -> None:
    #     """
    #     Testing we can update a project
    #     """
    #     response = client.request("PATCH", f"/projects/{TEST_UUID}", json={"name":"changed"})
    #     assert response.status_code == 200
    #     assert response.json()["data"]["name"] == "changed"
        
    # def test_delete_project(
    #     self, client: TestClient,
    # ) -> None:
    #     """
    #     Testing we can remove a project and that is missing afterwards
    #     """
    #     response = client.request("DELETE", f"/projects/{TEST_UUID}")
    #     assert response.status_code == 200

    #     # Check the project is indeed deleted
    #     response = client.request("GET", f"/projects/{TEST_UUID}")
    #     assert_response(response, 404, PROJECT_NOT_FOUND_ERROR)
