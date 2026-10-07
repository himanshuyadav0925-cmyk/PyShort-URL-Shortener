import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:5000"

def test_pwa_live():
    print("[1] Verifying /manifest.json endpoint...")
    with urllib.request.urlopen(f"{BASE_URL}/manifest.json") as resp:
        assert resp.status == 200
        content_type = resp.headers.get("Content-Type", "")
        assert "json" in content_type
        manifest = json.loads(resp.read().decode("utf-8"))
        assert manifest["name"] == "PyShort — Smart URL Shortener"
        assert manifest["short_name"] == "PyShort"
        assert manifest["display"] == "standalone"
        assert manifest["start_url"] == "/"
        assert manifest["theme_color"] == "#0b0f19"
        assert len(manifest["icons"]) >= 4
        print(f"    manifest.json OK, {len(manifest['icons'])} icons defined")

    print("[2] Verifying /sw.js endpoint...")
    with urllib.request.urlopen(f"{BASE_URL}/sw.js") as resp:
        assert resp.status == 200
        sw_allowed = resp.headers.get("Service-Worker-Allowed", "")
        assert sw_allowed == "/"
        sw_js = resp.read().decode("utf-8")
        assert "pyshort-v1" in sw_js
        assert "PRECACHE_ASSETS" in sw_js
        assert "/api/" in sw_js
        assert "skipWaiting" in sw_js
        print(f"    sw.js OK ({len(sw_js)} bytes), Service-Worker-Allowed: / verified")

    print("[3] Verifying PWA Icon Assets...")
    icon_paths = [
        "/static/icons/icon-192.png",
        "/static/icons/icon-512.png",
        "/static/icons/icon-maskable.png",
        "/static/icons/apple-touch-icon.png",
        "/static/icons/favicon-32.png",
        "/static/icons/icon.svg",
    ]
    for p in icon_paths:
        with urllib.request.urlopen(f"{BASE_URL}{p}") as resp:
            assert resp.status == 200
            data = resp.read()
            assert len(data) > 50
            print(f"    Icon {p} OK ({len(data)} bytes)")

    print("[4] Verifying HTML PWA Meta Tags & Navigation...")
    with urllib.request.urlopen(f"{BASE_URL}/") as resp:
        html = resp.read().decode("utf-8")
        assert 'rel="manifest"' in html
        assert 'apple-touch-icon' in html
        assert 'viewport-fit=cover' in html
        assert 'meta name="theme-color"' in html
        assert 'apple-mobile-web-app-capable' in html
        assert 'bottom-nav' in html
        assert 'bottom-nav-home' in html
        assert 'bottom-nav-links' in html
        assert 'bottom-nav-analytics' in html
        assert 'bottom-nav-settings' in html
        assert 'view-home' in html
        assert 'view-links' in html
        assert 'view-analytics' in html
        assert 'view-settings' in html
        assert 'offline-banner' in html
        print(f"    HTML PWA Tags & 4 App Views OK")

    print("\n=======================================================")
    print("SUCCESS: ALL PWA INTEGRATION TESTS PASSED!")
    print("=======================================================")

if __name__ == "__main__":
    test_pwa_live()
