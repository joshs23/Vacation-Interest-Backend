root_message = "Welcome to my Vacation Interest project! Visit vacation-interest-api.com/docs for the documentation page of this API."

def test_root(test_client):
    response = test_client.get("/")
    assert response.json().get("message") == root_message
    assert response.status_code == 200

