def test_get_all_locations(authorized_client):
    response = authorized_client.get("/locations/")
    print(response.json())
    assert response.status_code == 200

    