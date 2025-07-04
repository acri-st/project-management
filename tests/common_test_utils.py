import os
from typing import Generator, AsyncGenerator

import pytest
from fastapi import FastAPI
from httpx import Response
from fastapi.testclient import TestClient
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from project_management.main import app
from despsharedlibrary.schemas.sandbox_schema import Base

TEST_UUID = "c3ac5979-f07a-4f6e-bdaa-7502938e2df4"
TEST_DATABASE_URL = "sqlite+aiosqlite:///tests/test_database.db"


########################################
###### UTILITY FUNCTIONS
########################################

def assert_response(response: Response, expected_status_code: int = 200, expected_error_code: int | None = None):
    if response.status_code != expected_status_code:
        raise Exception(f"Received status code : {response.status_code}, Expected : {expected_status_code}, Content : {response.content}")
    if expected_error_code is None:
        return # code check is correct, and no error code is expected
    if response.json().get("error", None) is None:
        raise Exception(f"Missing functional code, expected : {expected_error_code}")
    if response.json()["error"]["code"] != expected_error_code:
        raise Exception(f"Received functional error code : {response.status_code}, Expected : {expected_status_code}, Content : {response.content}")
    return # both checks are correct
    

########################################
###### FIXTURES FOR TESTS
########################################

# Create async engine
engine = create_async_engine(
    TEST_DATABASE_URL, 
    echo=True,  # Set to False in production
    connect_args={"check_same_thread": False}  # Only for SQLite
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine, 
    expire_on_commit=False, 
    class_=AsyncSession
)

@pytest.fixture(scope="class")
def client() -> Generator:
    """
    Test client fixture that sets up an in-memory database for each test class
    """
    # Create tables before tests
    async def create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    asyncio.run(create_tables())
    
    # Overwrite the config path
    os.environ["APP_CONFIG_FILE"] = "tests/mock_data/desp-aas-config.yaml"

    # Create test client
    with TestClient(app) as c:
        yield c

    # Drop tables after tests
    async def drop_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    # Run the async function to drop tables
    asyncio.run(drop_tables())

@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Database session fixture for individual test functions
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()