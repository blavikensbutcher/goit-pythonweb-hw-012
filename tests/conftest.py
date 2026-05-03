import os
import uuid
import pytest
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from src.controllers.auth import router as auth_router
from src.controllers.contacts import router as contacts_router
from src.database import Base, get_db

from src.models.user import UserModel
from src.models.contacts import ContactModel

test_app = FastAPI()
test_app.include_router(auth_router)
test_app.include_router(contacts_router)

TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:mysecretpassword@127.0.0.1:5999/postgres",
)

# Використовуємо NullPool, щоб уникнути помилки "another operation is in progress"
engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

# Перевизначаємо залежність get_db для контролерів
async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

test_app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
async def test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield

@pytest.fixture
async def db_session(test_db):
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()

@pytest.fixture
def client():
    with TestClient(test_app) as c:
        yield c

@pytest.fixture
def auth_client(client):
    user_data = {
        "name": "Test User",
        "email": f"auth+{uuid.uuid4().hex}@example.com",
        "password": "password123"
    }

    with patch('src.utils.mailer.Mailer.send_simple_message', new_callable=AsyncMock):
        client.post("/auth/signup", json=user_data)

    signin_data = {"email": user_data["email"], "password": "password123"}
    response = client.post("/auth/signin", json=signin_data)
    
    if response.status_code == 200:
        token = response.json()["accessToken"]
        client.headers.update({"Authorization": f"Bearer {token}"})
        
    yield client