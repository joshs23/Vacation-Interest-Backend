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