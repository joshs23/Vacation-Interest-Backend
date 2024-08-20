from fastapi.testclient import TestClient
from app.main import app

root_message = "Welcome to my Vacation Interest project! Visit vacation-interest-api.com/docs for the documentation page of this API."

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.json().get("message") == root_message
    assert response.status_code == 200