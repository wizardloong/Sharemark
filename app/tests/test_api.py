from fastapi.testclient import TestClient
from main import app
from unittest.mock import AsyncMock, patch

def test_post_share_success():
    payload = {
        "folder_id": "test_folder",
        "name": "Test Folder",
        "bookmarks": [{"id": "b1", "title": "Bookmark 1", "url": "https://example.com"}],
        "can_write": True,
        "sharemark_uuid": "uuid-123"
    }
    # 🔹 Используем context manager
    with TestClient(app) as client:
        response = client.post("/api/share", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "share_id" in data
    assert "share_url" in data
    assert data["share_id"].startswith(payload["sharemark_uuid"])

def test_post_share_empty_bookmarks():
    payload = {
        "folder_id": "test_folder",
        "name": "Test Folder",
        "bookmarks": [],
        "can_write": True,
        "sharemark_uuid": "uuid-123"
    }
    # 🔹 Используем context manager
    with TestClient(app) as client:
        response = client.post("/api/share", json=payload)
    assert response.status_code == 400
    assert "Bookmarks cannot be empty" in response.text

def test_get_share_success():
    with patch("main.rabbit.publish", new_callable=AsyncMock) as mock_publish:
        params = {"share_id": "test_folder", "sharemark_uuid": "uuid-123"}
        # 🔹 Используем context manager
        with TestClient(app) as client:
            response = client.get("/api/share", params=params)
        assert response.status_code == 200
        mock_publish.assert_awaited_once_with({
            "sharemark_uuid": "uuid-123",
            "share_id": "test_folder"
        })

def test_get_share_invalid_params():
    # 🔹 Используем context manager
    with TestClient(app) as client:
        response = client.get("/api/share", params={"sharemark_uuid": "uuid-123"})
    assert response.status_code == 422