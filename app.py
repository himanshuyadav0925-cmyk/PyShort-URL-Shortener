"""
PyShort - Smart URL Shortener
A modern, reliable, and secure URL shortening application with analytics.
"""

import io
import os
import re
import secrets
import string
from urllib.parse import urlparse

from flask import (
    Flask,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
)

from database.db import (
    code_exists,
    create_url,
    delete_url,
    get_analytics_summary,
    get_recent_urls,
    get_url_by_code,
    get_url_by_original,
    init_db,
    record_click,
)

# Optional QR code support
try:
    import qrcode
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False

# Application setup
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "pyshort-secure-default-key-2026")
app.config["JSON_SORT_KEYS"] = False

# Initialize the database on startup
with app.app_context():
    init_db()

# Reserved routes/paths that cannot be used as short codes or custom aliases
RESERVED_CODES = {
    "api",
    "static",
    "qr",
    "stats",
    "analytics",
    "health",
    "favicon.ico",
    "robots.txt",
    "sitemap.xml",
}

# Character pool for random short code generation (alphanumeric, case-sensitive)
CODE_CHARS = string.ascii_letters + string.digits
CODE_LENGTH = 6
CUSTOM_ALIAS_REGEX = re.compile(r"^[a-zA-Z0-9_-]{3,30}$")


def validate_and_normalize_url(raw_url: str) -> tuple[bool, str, str]:
    """
    Validates and normalizes the input long URL.
    Returns (is_valid: bool, normalized_url: str, error_message: str).
    """
    if not raw_url or not isinstance(raw_url, str):
        return False, "", "Please provide a valid URL."

    cleaned_url = raw_url.strip()

    if len(cleaned_url) > 2048:
        return False, "", "URL is too long (maximum 2048 characters)."

    # Automatically prepend https:// if missing a scheme
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", cleaned_url):
        cleaned_url = f"https://{cleaned_url}"

    parsed = urlparse(cleaned_url)

    if parsed.scheme.lower() not in ("http", "https"):
        return False, "", "Only HTTP and HTTPS URLs are supported."

    if not parsed.netloc:
        return False, "", "The URL must include a valid host or domain name."

    # Validate hostname structure (allow localhost or domain with period)
    host = parsed.netloc.split(":")[0].lower()
    if host != "localhost" and "." not in host:
        return False, "", "Please enter a valid domain name (e.g., example.com)."

    # Prevent loop redirects to PyShort itself
    current_host = request.host.split(":")[0].lower() if request.host else ""
    if host == current_host or host in ("localhost", "127.0.0.1") and parsed.port == (request.port or 5000):
        # Prevent shortening our own URLs
        return False, "", "You cannot shorten a PyShort short URL (prevents redirect loop)."

    return True, cleaned_url, ""


def generate_unique_code(length: int = CODE_LENGTH) -> str:
    """
    Generates a cryptographically random, collision-resistant short code.
    Guarantees no collisions with existing codes or reserved keywords.
    """
    for _ in range(15):
        code = "".join(secrets.choice(CODE_CHARS) for _ in range(length))
        if code.lower() not in RESERVED_CODES and not code_exists(code):
            return code
    # Fallback to longer code if space is tight
    for _ in range(10):
        code = "".join(secrets.choice(CODE_CHARS) for _ in range(length + 1))
        if code.lower() not in RESERVED_CODES and not code_exists(code):
            return code
    raise RuntimeError("Unable to generate a unique short code. Please try again.")


def build_full_short_url(short_code: str) -> str:
    """Constructs the absolute short URL from the incoming request host."""
    return f"{request.host_url}{short_code}"


# ---------------------------------------------------------------------------
# Web UI Routes
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    """Renders the main dashboard page."""
    recent_urls = get_recent_urls(limit=25)
    stats = get_analytics_summary()
    return render_template(
        "index.html",
        recent_urls=recent_urls,
        stats=stats,
        host_url=request.host_url,
    )


@app.route("/<short_code>")
def redirect_to_url(short_code):
    """
    Redirects a shortened code to its target destination.
    Tracks click analytics before redirecting.
    """
    # Check if short_code is a reserved route (e.g. static assets)
    if short_code.lower() in RESERVED_CODES:
        abort(404)

    url_entry = get_url_by_code(short_code)
    if not url_entry:
        return render_template("404.html", short_code=short_code), 404

    # Record click with metadata
    user_agent = request.headers.get("User-Agent", "")
    referrer = request.headers.get("Referer", "")
    record_click(short_code, user_agent=user_agent, referrer=referrer)

    # Perform 302 Found redirect
    return redirect(url_entry["original_url"], code=302)


# ---------------------------------------------------------------------------
# RESTful API Endpoints
# ---------------------------------------------------------------------------


@app.route("/api/shorten", methods=["POST"])
def api_shorten():
    """
    Creates a new short URL.
    Supports JSON body or form submissions.
    """
    if request.is_json:
        data = request.get_json(silent=True) or {}
    else:
        data = request.form

    raw_url = data.get("url", "")
    custom_alias = (data.get("custom_alias") or "").strip()

    # 1. Validate & normalize URL
    is_valid, original_url, err = validate_and_normalize_url(raw_url)
    if not is_valid:
        return jsonify({"success": False, "error": err}), 400

    # 2. Handle Custom Alias if provided
    if custom_alias:
        if not CUSTOM_ALIAS_REGEX.match(custom_alias):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Custom alias must be 3-30 characters long and contain only letters, numbers, hyphens, and underscores.",
                    }
                ),
                400,
            )

        if custom_alias.lower() in RESERVED_CODES:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"'{custom_alias}' is a reserved system keyword. Please choose a different alias.",
                    }
                ),
                400,
            )

        if code_exists(custom_alias):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"The alias '{custom_alias}' is already in use. Please pick another one.",
                    }
                ),
                409,
            )

        short_code = custom_alias
        is_custom = True
    else:
        # Check if this exact URL was already shortened without a custom alias (smart reuse)
        existing = get_url_by_original(original_url)
        if existing:
            return jsonify(
                {
                    "success": True,
                    "reused": True,
                    "short_code": existing["short_code"],
                    "short_url": build_full_short_url(existing["short_code"]),
                    "original_url": existing["original_url"],
                    "clicks": existing["clicks"],
                    "created_at": existing["created_at"],
                    "is_custom": bool(existing["is_custom"]),
                    "message": "Existing shortened link retrieved.",
                }
            )

        try:
            short_code = generate_unique_code()
        except RuntimeError as e:
            return jsonify({"success": False, "error": str(e)}), 500
        is_custom = False

    # 3. Store in SQLite
    new_url = create_url(original_url, short_code, is_custom=is_custom)
    full_short_url = build_full_short_url(new_url["short_code"])

    return (
        jsonify(
            {
                "success": True,
                "reused": False,
                "short_code": new_url["short_code"],
                "short_url": full_short_url,
                "original_url": new_url["original_url"],
                "clicks": new_url["clicks"],
                "created_at": new_url["created_at"],
                "is_custom": bool(new_url["is_custom"]),
                "message": "URL successfully shortened!",
            }
        ),
        201,
    )


@app.route("/api/links", methods=["GET"])
def api_get_links():
    """Returns list of recent shortened URLs with full short URL added."""
    limit = request.args.get("limit", 50, type=int)
    urls = get_recent_urls(limit=limit)
    for u in urls:
        u["short_url"] = build_full_short_url(u["short_code"])
        u["is_custom"] = bool(u["is_custom"])
    return jsonify({"success": True, "links": urls})


@app.route("/api/links/<int:url_id>", methods=["DELETE"])
def api_delete_link(url_id):
    """Deletes a shortened URL and its audit logs."""
    success = delete_url(url_id)
    if success:
        return jsonify({"success": True, "message": "Link deleted successfully."})
    return jsonify({"success": False, "error": "Link not found or already deleted."}), 404


@app.route("/api/stats", methods=["GET"])
def api_get_stats():
    """Returns real-time dashboard analytics summary."""
    stats = get_analytics_summary()
    if stats.get("most_active"):
        stats["most_active"]["short_url"] = build_full_short_url(
            stats["most_active"]["short_code"]
        )
    return jsonify({"success": True, "stats": stats})


@app.route("/qr/<short_code>")
def get_qr_code(short_code):
    """
    Generates and serves a high-resolution QR code image for the short URL.
    """
    url_entry = get_url_by_code(short_code)
    if not url_entry:
        abort(404)

    target_url = build_full_short_url(short_code)

    if not HAS_QRCODE:
        return jsonify({"error": "QR code generator library not installed."}), 501

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=3,
    )
    qr.add_data(target_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return send_file(
        buf,
        mimetype="image/png",
        as_attachment=False,
        download_name=f"qr-{short_code}.png",
    )


@app.route("/health")
def health_check():
    """Health check endpoint for deployment monitoring."""
    return jsonify({"status": "healthy", "service": "PyShort", "version": "1.0.0"})


# ---------------------------------------------------------------------------
# Error Handlers
# ---------------------------------------------------------------------------


@app.errorhandler(404)
def handle_404(e):
    """Custom friendly 404 error page."""
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "error": "Resource not found"}), 404
    return render_template("404.html"), 404


@app.errorhandler(500)
def handle_500(e):
    """Custom friendly 500 error page."""
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "error": "Internal server error"}), 500
    return render_template("500.html"), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1")
    print(f"[PyShort] Running at: http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
