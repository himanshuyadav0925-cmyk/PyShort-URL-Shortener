"""
PyShort Test Suite
Comprehensive automated unit and integration tests for URL Shortener functionality.
"""

import os
import sys
import tempfile
import pytest

# Ensure root directory is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from database.db import init_db, get_url_by_code, get_analytics_summary


@pytest.fixture
def client():
    """Configures test client with an isolated temporary SQLite database."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.environ["PYSHORT_DB_PATH"] = db_path
    app.config["TESTING"] = True

    with app.app_context():
        init_db(db_path=db_path)

    with app.test_client() as client:
        yield client

    # Cleanup temporary test database
    try:
        os.close(db_fd)
        if os.path.exists(db_path):
            os.remove(db_path)
    except OSError:
        pass


def test_index_page(client):
    """Test that the homepage renders with 200 OK and PyShort branding."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"PyShort" in response.data
    assert b"Shorten URL" in response.data


def test_shorten_valid_url(client):
    """Test generating a short URL for a valid destination."""
    response = client.post(
        "/api/shorten",
        json={"url": "https://python.org"},
    )
    assert response.status_code in (200, 201)
    data = response.get_json()
    assert data["success"] is True
    assert "short_code" in data
    assert data["original_url"] == "https://python.org"
    assert data["clicks"] == 0


def test_auto_prepend_https(client):
    """Test that URLs missing http/https scheme automatically get https://."""
    response = client.post(
        "/api/shorten",
        json={"url": "example.com/docs"},
    )
    assert response.status_code in (200, 201)
    data = response.get_json()
    assert data["success"] is True
    assert data["original_url"] == "https://example.com/docs"


def test_redirect_and_click_tracking(client):
    """Test that visiting the short URL redirects with 302 and increments clicks."""
    # 1. Create short link
    res = client.post("/api/shorten", json={"url": "https://flask.palletsprojects.com"})
    code = res.get_json()["short_code"]

    # 2. Access short URL
    redirect_res = client.get(f"/{code}")
    assert redirect_res.status_code == 302
    assert redirect_res.headers["Location"] == "https://flask.palletsprojects.com"

    # 3. Access again to check click counter
    client.get(f"/{code}")

    # 4. Check database directly
    with app.app_context():
        db_path = os.environ.get("PYSHORT_DB_PATH")
        record = get_url_by_code(code, db_path=db_path)
        assert record is not None
        assert record["clicks"] == 2
        assert record["last_clicked_at"] is not None


def test_custom_alias_success_and_conflict(client):
    """Test custom alias generation and duplicate rejection."""
    # Create with custom alias
    res1 = client.post(
        "/api/shorten",
        json={"url": "https://github.com", "custom_alias": "my-gh-link"},
    )
    assert res1.status_code == 201
    assert res1.get_json()["short_code"] == "my-gh-link"

    # Try duplicate alias
    res2 = client.post(
        "/api/shorten",
        json={"url": "https://gitlab.com", "custom_alias": "my-gh-link"},
    )
    assert res2.status_code == 409
    assert res2.get_json()["success"] is False
    assert "already in use" in res2.get_json()["error"]


def test_invalid_urls(client):
    """Test rejection of malformed or empty URLs."""
    # Empty
    res = client.post("/api/shorten", json={"url": ""})
    assert res.status_code == 400

    # Invalid characters or domain
    res = client.post("/api/shorten", json={"url": "not-a-valid-url"})
    assert res.status_code == 400


def test_nonexistent_short_code_404(client):
    """Test that navigating to a non-existent code returns a friendly 404 page."""
    response = client.get("/nonexistent-xyz-999")
    assert response.status_code == 404
    assert b"Link Not Found" in response.data


def test_analytics_summary_api(client):
    """Test the /api/stats endpoint reflects created URLs and click counts."""
    # Create 2 URLs
    res1 = client.post("/api/shorten", json={"url": "https://site-a.com", "custom_alias": "site-a"})
    res2 = client.post("/api/shorten", json={"url": "https://site-b.com", "custom_alias": "site-b"})

    # Click site-a three times
    client.get("/site-a")
    client.get("/site-a")
    client.get("/site-a")

    stats_res = client.get("/api/stats")
    assert stats_res.status_code == 200
    stats = stats_res.get_json()["stats"]
    assert stats["total_urls"] >= 2
    assert stats["total_clicks"] >= 3
    assert stats["most_active"]["short_code"] == "site-a"


def test_delete_link(client):
    """Test deleting a shortened URL."""
    res = client.post("/api/shorten", json={"url": "https://to-delete.com", "custom_alias": "temp-link"})
    code = res.get_json()["short_code"]

    with app.app_context():
        entry = get_url_by_code(code, db_path=os.environ.get("PYSHORT_DB_PATH"))
        url_id = entry["id"]

    del_res = client.delete(f"/api/links/{url_id}")
    assert del_res.status_code == 200
    assert del_res.get_json()["success"] is True

    # Confirm it's gone
    after_res = client.get(f"/{code}")
    assert after_res.status_code == 404


def test_qr_code_generation(client):
    """Test that QR endpoint returns a valid image/png."""
    res = client.post("/api/shorten", json={"url": "https://qr-test.com", "custom_alias": "qr-link"})
    qr_res = client.get("/qr/qr-link")
    assert qr_res.status_code == 200
    assert qr_res.mimetype == "image/png"
    assert len(qr_res.data) > 0
