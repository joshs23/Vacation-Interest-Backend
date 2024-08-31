from .test_database import client
import pytest
from .test_database import create_all, drop_all

root_message = "Welcome to my Vacation Interest project! Visit vacation-interest-api.com/docs for the documentation page of this API."

@pytest.fixture
def test_client():
    drop_all()
    create_all()
    yield client

def test_root(test_client):
    response = client.get("/")
    assert response.json().get("message") == root_message
    assert response.status_code == 200

