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


def test_dangerous_url_schemes(client):
    """Test rejection of dangerous non-web schemes."""
    dangerous_urls = [
        "javascript:alert('xss')",
        "javascript://test",
        "data:text/html,<script>alert(1)</script>",
        "file:///etc/passwd",
        "file://C:/Windows/win.ini",
        "vbscript:msgbox('hello')",
    ]
    for bad_url in dangerous_urls:
        res = client.post("/api/shorten", json={"url": bad_url})
        assert res.status_code == 400, f"Expected 400 for {bad_url}"
        data = res.get_json()
        assert data["success"] is False


def test_private_and_local_urls_rejected(client):
    """Test rejection of private, link-local, and localhost network addresses."""
    private_urls = [
        "http://127.0.0.1",
        "http://127.0.0.1:8080/admin",
        "http://10.0.0.1",
        "http://10.255.0.1/dashboard",
        "http://172.16.0.1",
        "http://172.31.255.254",
        "http://192.168.1.1",
        "http://192.168.0.100/router",
        "http://169.254.169.254/latest/meta-data/",
        "http://localhost",
        "http://localhost:3000",
        "https://app.localhost",
    ]
    for priv_url in private_urls:
        res = client.post("/api/shorten", json={"url": priv_url})
        assert res.status_code == 400, f"Expected 400 for {priv_url}"
        data = res.get_json()
        assert data["success"] is False


def test_pagination_navigation_and_metadata(client):
    """Test pagination retrieval, metadata correctness, and disjoint pages."""
    # Create 35 distinct URLs to span multiple pages
    total_created = 35
    for i in range(total_created):
        res = client.post("/api/shorten", json={"url": f"https://example-{i}.org/page"})
        assert res.status_code in (200, 201)

    # 1. Page 1 (per_page = 10)
    p1_res = client.get("/api/links?page=1&per_page=10")
    assert p1_res.status_code == 200
    p1_data = p1_res.get_json()
    assert len(p1_data["links"]) == 10
    assert p1_data["pagination"]["page"] == 1
    assert p1_data["pagination"]["per_page"] == 10
    assert p1_data["pagination"]["total_count"] == total_created
    assert p1_data["pagination"]["total_pages"] == 4
    assert p1_data["pagination"]["has_next"] is True
    assert p1_data["pagination"]["has_prev"] is False

    # 2. Page 2 (per_page = 10)
    p2_res = client.get("/api/links?page=2&per_page=10")
    assert p2_res.status_code == 200
    p2_data = p2_res.get_json()
    assert len(p2_data["links"]) == 10
    assert p2_data["pagination"]["page"] == 2
    assert p2_data["pagination"]["has_next"] is True
    assert p2_data["pagination"]["has_prev"] is True

    # Confirm page 1 and page 2 contain disjoint records (no duplicate items)
    p1_ids = {u["id"] for u in p1_data["links"]}
    p2_ids = {u["id"] for u in p2_data["links"]}
    assert p1_ids.isdisjoint(p2_ids)

    # 3. Final Page 4 (per_page = 10 -> remaining 5 records)
    p4_res = client.get("/api/links?page=4&per_page=10")
    assert p4_res.status_code == 200
    p4_data = p4_res.get_json()
    assert len(p4_data["links"]) == 5
    assert p4_data["pagination"]["page"] == 4
    assert p4_data["pagination"]["has_next"] is False
    assert p4_data["pagination"]["has_prev"] is True
    p4_ids = {u["id"] for u in p4_data["links"]}
    assert p4_ids.isdisjoint(p1_ids)
    assert p4_ids.isdisjoint(p2_ids)

    # 4. Safe handling of invalid page/per_page values
    inv_res = client.get("/api/links?page=-10&per_page=-5")
    assert inv_res.status_code == 200
    inv_data = inv_res.get_json()
    assert inv_data["pagination"]["page"] == 1
    assert inv_data["pagination"]["per_page"] >= 1

    large_res = client.get("/api/links?page=1&per_page=5000")
    assert large_res.status_code == 200
    large_data = large_res.get_json()
    assert large_data["pagination"]["per_page"] <= 100


def test_pwa_manifest(client):
    """Test that Web App Manifest is served with 200 OK and valid metadata."""
    res = client.get("/manifest.json")
    assert res.status_code == 200
    assert "application/manifest+json" in res.mimetype or "json" in res.mimetype
    data = res.get_json()
    assert data["name"] == "PyShort — Smart URL Shortener"
    assert data["short_name"] == "PyShort"
    assert data["display"] == "standalone"
    assert data["start_url"] == "/"
    assert len(data["icons"]) >= 4


def test_pwa_service_worker(client):
    """Test that Service Worker is served with root scope permission."""
    res = client.get("/sw.js")
    assert res.status_code == 200
    assert "javascript" in res.mimetype
    assert res.headers.get("Service-Worker-Allowed") == "/"
    assert b"pyshort-v1" in res.data


def test_pwa_reserved_slugs(client):
    """Test that PWA core files cannot be registered as custom aliases."""
    for slug in ("manifest.json", "sw.js"):
        res = client.post(
            "/api/shorten",
            json={"url": "https://example.com", "custom_alias": slug},
        )
        assert res.status_code == 400
        assert res.get_json()["success"] is False
