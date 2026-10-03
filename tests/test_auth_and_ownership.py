from tests.conftest import signup


def create_request(client, title="Report"):
    return client.post("/api/requests", json={
        "title": title,
        "description": "A valid fictional clinical data request.",
        "request_type": "Report",
        "priority": "Medium",
        "status": "New",
        "due_date": "2026-10-10",
    })


def test_signup_login_logout_and_protected_route(client):
    assert client.get("/api/requests").status_code == 401
    response = signup(client, "alice", "alice@example.com")
    assert response.status_code == 201
    assert response.get_json()["user"]["email"] == "alice@example.com"
    assert client.get("/api/check_session").status_code == 200
    assert client.delete("/api/logout").status_code == 204
    assert client.get("/api/check_session").status_code == 401
    assert client.post("/api/login", json={"email": "alice@example.com", "password": "password123"}).status_code == 200


def test_request_crud_note_crud_and_pagination(client):
    signup(client, "alice", "alice@example.com")
    first = create_request(client, "First request")
    assert first.status_code == 201
    request_id = first.get_json()["id"]
    assert client.patch(f"/api/requests/{request_id}", json={"status": "In Progress"}).status_code == 200
    note = client.post(f"/api/requests/{request_id}/notes", json={"content": "Started validating requirements."})
    assert note.status_code == 201
    note_id = note.get_json()["id"]
    assert client.get(f"/api/notes/{note_id}").status_code == 200
    assert client.patch(f"/api/notes/{note_id}", json={"content": "Requirements validated."}).status_code == 200
    assert client.delete(f"/api/notes/{note_id}").status_code == 204
    for index in range(11):
        assert create_request(client, f"Paginated request {index}").status_code == 201
    payload = client.get("/api/requests?page=1&per_page=5").get_json()
    assert payload["total"] == 12
    assert len(payload["items"]) == 5
    assert payload["pages"] == 3
    assert client.delete(f"/api/requests/{request_id}").status_code == 204


def test_user_cannot_access_another_users_records(app):
    first = app.test_client()
    second = app.test_client()
    signup(first, "alice", "alice@example.com")
    created = create_request(first, "Alice private request")
    request_id = created.get_json()["id"]
    signup(second, "bob", "bob@example.com")
    assert second.get(f"/api/requests/{request_id}").status_code == 403
    assert second.patch(f"/api/requests/{request_id}", json={"status": "Completed"}).status_code == 403
    assert second.delete(f"/api/requests/{request_id}").status_code == 403
    assert second.get("/api/requests").get_json()["total"] == 0
