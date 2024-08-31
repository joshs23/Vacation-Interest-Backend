from .test_database import client
from app.main import app
from app import schemas
import pytest
from .test_database import create_all, drop_all

@pytest.fixture
def test_client():
    drop_all()
    create_all()
    yield client

def test_add_user(test_client):
    response = client.post("/users/", json={"Username": "test_1", "Email": "test_1@gmail.com", "Password": "password123"})
    new_user = schemas.UserResponse(**response.json())
    assert new_user.Email == "test_1@gmail.com"
    assert response.status_code == 201