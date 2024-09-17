import pytest
from app import schemas
from jose import jwt
from app.config import settings

def test_add_user(test_client):
    response = test_client.post("/users/", json={"Username": "test_1", "Email": "test_1@gmail.com", "Password": "password123"})
    new_user = schemas.UserResponse(**response.json())
    assert new_user.Email == "test_1@gmail.com"
    assert response.status_code == 201

def test_email_login(test_client, test_user):
    response = test_client.post("/login", data={"username": test_user["Email"], "password": test_user["Password"]})
    login_response = schemas.Token(**response.json())
    payload = jwt.decode(login_response.Access_token, settings.SECRET_KEY, settings.ALGORITHM)
    id = payload.get("user_id")
    assert id == test_user["User_id"]
    assert login_response.Token_type == "bearer"
    assert response.status_code == 200

def test_username_login(test_client, test_user):
    response = test_client.post("/login", data={"username": test_user["Username"], "password": test_user["Password"]})
    login_response = schemas.Token(**response.json())
    payload = jwt.decode(login_response.Access_token, settings.SECRET_KEY, settings.ALGORITHM)
    id = payload.get("user_id")
    assert id == test_user["User_id"]
    assert login_response.Token_type == "bearer"
    assert response.status_code == 200

@pytest.mark.parametrize("username, password, status_code", [
    ("test_1", "password123", 200),
    ("test_1", "wrong_password", 403),
    ("test_1@gmail.com", "wrong_password", 403),
    ("wrong_user", "password123", 403),
    ("wrong_user", "wrong_password", 403),
    (None, "password123", 422),
    ("test_1", None, 422)
])
def test_bad_login(test_client, test_user, username, password, status_code):
    response = test_client.post("/login", data={"username": username, "password": password})
    assert response.status_code == status_code
    if (status_code == 403):
        assert response.json().get("detail") == "Login Unsuccessful."