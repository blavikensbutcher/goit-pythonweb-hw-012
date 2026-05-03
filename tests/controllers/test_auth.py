import pytest
import uuid
from src.models.user import CreateUserModel, AuthCredentials


class TestAuthController:
    def test_sign_up(self, client):
        user_data = {
            "name": "Test User",
            "email": f"test+{uuid.uuid4().hex}@example.com",
            "password": "password123"
        }
        response = client.post("/auth/signup", json=user_data)
        assert response.status_code == 201
        data = response.json()
        assert "accessToken" in data
        assert "refreshToken" in data

    def test_sign_in(self, client):
        # First sign up
        user_email = f"signin+{uuid.uuid4().hex}@example.com"
        user_data = {
            "name": "Test User",
            "email": user_email,
            "password": "password123"
        }
        client.post("/auth/signup", json=user_data)

        signin_data = {
            "email": user_email,
            "password": "password123"
        }
        response = client.post("/auth/signin", json=signin_data)
        assert response.status_code == 200
        data = response.json()
        assert "accessToken" in data
        assert "refreshToken" in data