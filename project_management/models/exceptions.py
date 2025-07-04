from msfwk.exceptions import DespGenericError

###############
#   Project
###############


class ProjectCreationError(DespGenericError):
    """Raised when something wrong happens during the creation of the project"""


class ProjectRetrievalError(DespGenericError):
    """Raised when something wrong happens during the retrieval of the project"""


###############
#  Repository
###############


class RepositoryRetrievalError(DespGenericError):
    """Raised when something wrong happens during the retrieval of the repository"""


class RepositoryCreationError(Exception):
    """Raised when we recieve an error from the storage service"""


###############
#  Flavor
###############


class FlavorRetrievalError(DespGenericError):
    """Raised when something wrong happens during the retrieval of the flavor"""


###############
# Application
###############


class ApplicationRetrievalError(DespGenericError):
    """Raised when something wrong happens during the retrieval of an application"""

class KeycloakSetupError(DespGenericError):
    """Custom exception for general Keycloak setup errors."""

class KeycloakRealmCreationError(KeycloakSetupError):
    """Raised when there is an error creating a Keycloak realm."""

class KeycloakClientCreationError(KeycloakSetupError):
    """Raised when there is an error creating a Keycloak client."""

class KeycloakUserCreationError(KeycloakSetupError):
    """Raised when there is an error creating a Keycloak user."""

