import pydantic_settings


class Settings(pydantic_settings.BaseSettings):
    # Database default values for local test (overriden in CI and environment)
    database_url: str = "sqlite+aiosqlite:///tests/test_database.db"  # test value
    db_host: str = "127.0.0.1"
    db_user: str = "test"
    db_password: str = "test"
    db_name: str = "test"
    db_schema: str = "test"
    db_port: str = "5432"
    db_connection_name: str = "database_connection"


settings = Settings()
