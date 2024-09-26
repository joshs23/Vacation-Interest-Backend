from .test_database import client
import pytest
from .test_database import create_all, drop_all
from app.oauth2 import createAccessToken


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

@pytest.fixture
def token(test_user):
    return createAccessToken({"user_id": test_user["User_id"]})

@pytest.fixture
def authorized_client(test_client, token):
    test_client.headers = {
        **test_client.headers,
        "Authorization": f"Bearer {token}"
    }
    return test_client