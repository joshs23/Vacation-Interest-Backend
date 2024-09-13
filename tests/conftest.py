from .test_database import client
import pytest
from .test_database import create_all, drop_all


@pytest.fixture
def test_client():
    drop_all()
    create_all()
    yield client

@pytest.fixture
def test_user(test_client):
    user_info = {"Username": "test_1", 
                 "Email": "test_1@gmail.com", 
                 "Password": "password123"}
    response = test_client.post("/users/", json = user_info)
    assert response.status_code == 201
    new_user = response.json()
    new_user["Password"] = user_info["Password"]
    return new_user