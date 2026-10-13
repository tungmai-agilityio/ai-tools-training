def test_index_page_is_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "Clinic Booking" in r.text


def test_patients_endpoint_lists_seed_patients(client):
    body = client.get("/patients").json()
    assert [p["id"] for p in body] == [1, 2, 3]
    assert body[0]["insured"] is True
