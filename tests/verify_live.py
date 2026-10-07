import json
import time
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:5000"

def test_live():
    print("[1] Fetching homepage HTML...")
    with urllib.request.urlopen(f"{BASE_URL}/") as resp:
        assert resp.status == 200
        html = resp.read().decode("utf-8")
        assert "PyShort" in html
        assert "Performance Analytics" in html
        assert "Recently Shortened URLs" in html
        print(f"    Homepage OK ({len(html)} bytes)")

    print("[2] Verifying static assets (CSS & JS)...")
    with urllib.request.urlopen(f"{BASE_URL}/static/css/style.css") as resp:
        assert resp.status == 200
        css = resp.read().decode("utf-8")
        assert "--accent-gradient" in css
        print(f"    style.css OK ({len(css)} bytes)")

    with urllib.request.urlopen(f"{BASE_URL}/static/js/main.js") as resp:
        assert resp.status == 200
        js = resp.read().decode("utf-8")
        assert "copyShortUrl" in js
        print(f"    main.js OK ({len(js)} bytes)")

    print("[3] Shortening URL with custom alias...")
    alias = f"demo-{int(time.time())}"
    payload = json.dumps({"url": "https://github.com/torvalds/linux", "custom_alias": alias}).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/api/shorten",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        print("    Response:", res)
        assert res["success"] is True
        short_code = res["short_code"]
        assert short_code == alias

    print("[4] Testing duplicate alias conflict handling (409 Conflict)...")
    dup_payload = json.dumps({"url": "https://google.com", "custom_alias": alias}).encode("utf-8")
    dup_req = urllib.request.Request(
        f"{BASE_URL}/api/shorten",
        data=dup_payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(dup_req)
        assert False, "Should have returned 409 Conflict"
    except urllib.error.HTTPError as e:
        assert e.code == 409
        err_res = json.loads(e.read().decode("utf-8"))
        print(f"    Conflict handled correctly: {err_res['error']}")

    print("[5] Visiting short URL to trigger redirect & click tracking...")
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    no_redirect_opener = urllib.request.build_opener(NoRedirect)
    try:
        no_redirect_opener.open(f"{BASE_URL}/{short_code}")
    except urllib.error.HTTPError as e:
        print(f"    Redirect status code: {e.code}, Location: {e.headers.get('Location')}")
        assert e.code == 302
        assert "github.com/torvalds/linux" in e.headers.get("Location")

    print("[6] Checking stats...")
    req = urllib.request.Request(f"{BASE_URL}/api/stats")
    with urllib.request.urlopen(req) as resp:
        stats = json.loads(resp.read().decode("utf-8"))
        print("    Stats:", stats["stats"])
        assert stats["stats"]["total_urls"] >= 1
        assert stats["stats"]["total_clicks"] >= 1

    print("[7] Checking QR code endpoint...")
    req = urllib.request.Request(f"{BASE_URL}/qr/{short_code}")
    with urllib.request.urlopen(req) as resp:
        qr_bytes = resp.read()
        print(f"    QR PNG received, size: {len(qr_bytes)} bytes, content-type: {resp.headers.get('Content-Type')}")
        assert resp.headers.get("Content-Type") == "image/png"
        assert len(qr_bytes) > 100

    print("[8] Testing non-existent link 404...")
    try:
        urllib.request.urlopen(f"{BASE_URL}/this-link-does-not-exist")
    except urllib.error.HTTPError as e:
        print(f"    404 response received as expected: {e.code}")
        assert e.code == 404

    print("[9] Testing invalid URL input (400 Bad Request)...")
    bad_payload = json.dumps({"url": "invalid-url-string"}).encode("utf-8")
    bad_req = urllib.request.Request(
        f"{BASE_URL}/api/shorten",
        data=bad_payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(bad_req)
        assert False, "Should have returned 400"
    except urllib.error.HTTPError as e:
        assert e.code == 400
        print("    Invalid URL rejected with 400 as expected.")

    print("\n=======================================================")
    print("SUCCESS: ALL 9 COMPREHENSIVE LIVE END-TO-END TESTS PASSED!")
    print("=======================================================")

if __name__ == "__main__":
    test_live()
