from msfwk.application import app
from msfwk.context import current_config, register_init
from msfwk.mqclient import load_default_rabbitmq_config
from msfwk.utils.logging import get_logger

from project_management.routes.applications import router as application_router
from project_management.routes.flavors import router as flavors_router
from project_management.routes.operatingsystems import router as operatingsystems_router
from project_management.routes.profiles import router as profiles_router
from project_management.routes.projects import router as project_router
from project_management.routes.repositories import router as repositories_router

logger = get_logger("application")

# Add middleware or subtasks here


async def init(config: dict) -> bool:
    """Init"""
    logger.info("Initialising project management ...")
    load_succeded = load_default_rabbitmq_config()
    current_config.set(config)
    if load_succeded:
        logger.info("RabbitMQ config loaded")
    else:
        logger.error("Failed to load rabbitmq config")
    return load_succeded


# Register the init function
register_init(init)

app.include_router(application_router)
app.include_router(operatingsystems_router)
app.include_router(flavors_router)
app.include_router(repositories_router)
app.include_router(profiles_router)
app.include_router(project_router)
