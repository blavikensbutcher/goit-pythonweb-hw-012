import pytest


class TestContactsController:
    def test_create_contact(self, auth_client):
        contact_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "123456789",
            "birthday": "1990-01-01",
            "description": "Test contact"
        }
        response = auth_client.post("/contacts", json=contact_data)
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"

    def test_get_contacts(self, auth_client):
        response = auth_client.get("/contacts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)