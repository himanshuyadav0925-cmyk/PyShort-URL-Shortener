# ⚡ PyShort — Smart URL Shortener

An internship-grade, full-stack URL Shortener built with **Python**, **Flask**, **SQLite**, **HTML5**, **CSS3**, and **Vanilla JavaScript**. 

Designed for high reliability, zero bloat, intuitive ergonomics, and comprehensive real-time click analytics.

---

## 🌟 Highlights & Key Features

- **⚡ Fast URL Shortening**: Converts any valid long URL into a short, collision-free 6-character alphanumeric slug (or custom alias).
- **🛡️ Parameterized SQLite Database**: Uses parameterized SQL queries everywhere to eliminate SQL injection vulnerabilities.
- **📈 Real-Time Click Tracking & Analytics**:
  - Automatically records click counts upon HTTP 302 redirection.
  - Logs user-agent, referrers, and timestamps in an audit log (`click_logs`).
  - Live metric dashboard: Total URLs, Total Clicks, Average Clicks/Link, and Top Performing Link.
- **🎨 Custom Aliases & Validation**:
  - Allows users to specify branded custom vanity links (e.g., `pyshort.link/my-project`).
  - Enforces length constraints, character checks, and prevents collision with system routes.
- **🔄 Smart Deduplication**: Detects identical submitted long URLs and returns existing short links without cluttering storage.
- **📱 Instant QR Code Engine**: Generates high-contrast QR codes dynamically for every short link, with direct PNG download.
- **📋 One-Click Clipboard Copying**: Instant copy-to-clipboard with visual feedback tooltips and toast alerts.
- **🔍 Live Search & Filter**: Instant client-side filtering of recently shortened links by title, slug, or target destination.
- **🌓 Theme Engine (Dark & Light Mode)**: Fully bespoke, glassmorphic theme system with smooth toggle transitions and `localStorage` persistence.
- **🚫 Graceful Error & 404 Handling**: Branded custom 404 page for missing/expired short codes and 500 error safeguards.
- **🧪 Comprehensive Test Suite**: Full `pytest` integration covering core business logic, edge cases, redirects, and API contracts.

---

## 🛠️ Tech Stack & Architecture

| Layer | Technology | Rationale |
|---|---|---|
| **Backend** | Python 3 + Flask 3.1 | Minimalist, fast, and unopinionated microframework. |
| **Database** | SQLite3 (Built-in) | Zero-configuration ACID database with foreign keys and indexes. |
| **Frontend** | Semantic HTML5 + Vanilla JS | No bulky frameworks; fast load times and clean code. |
| **Styling** | Modern Vanilla CSS | CSS variables, glassmorphism, responsive flex/grid, and theme toggling. |
| **QR Engine** | `qrcode` | In-memory stream generation without disk bloat. |
| **Testing** | `pytest` | Isolated automated integration and unit testing. |

---

## 📁 Project Structure

```text
PyShort — Smart URL Shortener/
├── app.py                     # Main Flask application, routes, and API endpoints
├── requirements.txt           # Python package dependencies
├── .gitignore                 # Standard Python & database ignore rules
├── README.md                  # Comprehensive documentation and recruiter guide
│
├── database/
│   ├── __init__.py            # Database module exports
│   ├── db.py                  # Parameterized SQLite query engine & CRUD operations
│   ├── schema.sql             # SQL table definitions and indexes
│   └── pyshort.db             # Local SQLite database file (created automatically)
│
├── templates/
│   ├── base.html              # Layout shell, navbar, theme toggle, modals, and toasts
│   ├── index.html             # Main dashboard (shortener form, stats, recent links)
│   ├── 404.html               # Custom 404 error page for expired or invalid short codes
│   └── 500.html               # Custom 500 server error page
│
├── static/
│   ├── css/
│   │   └── style.css          # Custom design system, dark/light theme, and animations
│   └── js/
│       └── main.js            # Vanilla JS AJAX handler, clipboard, search, and QR modal
│
└── tests/
    └── test_app.py            # Automated pytest test cases verifying all features
```

---

## 🚀 Getting Started Locally

### 1. Prerequisites
- Python 3.10+ installed on your system.

### 2. Set Up Virtual Environment

**Windows (PowerShell):**
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python app.py
```

The application will start at:
👉 **`http://127.0.0.1:5000`**

Open your web browser and navigate to this URL.

---

## 🧪 Running the Test Suite

PyShort comes with automated tests that verify URL shortening, redirection, click tracking, custom alias validation, and error states.

Run all tests:
```bash
pytest -v
```

---

## 📡 RESTful API Reference

### 1. Shorten a URL
- **Endpoint**: `POST /api/shorten`
- **Content-Type**: `application/json`
- **Request Body**:
  ```json
  {
    "url": "https://github.com/internship-project",
    "custom_alias": "intern-demo"  // optional
  }
  ```
- **Response** (`201 Created` or `200 OK` if reused):
  ```json
  {
    "success": true,
    "reused": false,
    "short_code": "intern-demo",
    "short_url": "http://127.0.0.1:5000/intern-demo",
    "original_url": "https://github.com/internship-project",
    "clicks": 0,
    "created_at": "2026-10-07 14:00:00",
    "is_custom": true,
    "message": "URL successfully shortened!"
  }
  ```

### 2. Retrieve Recent Links
- **Endpoint**: `GET /api/links?limit=25`
- **Response** (`200 OK`):
  ```json
  {
    "success": true,
    "links": [
      {
        "id": 1,
        "original_url": "https://github.com/internship-project",
        "short_code": "intern-demo",
        "short_url": "http://127.0.0.1:5000/intern-demo",
        "clicks": 5,
        "created_at": "2026-10-07 14:00:00",
        "is_custom": true
      }
    ]
  }
  ```

### 3. Retrieve Live Analytics
- **Endpoint**: `GET /api/stats`
- **Response** (`200 OK`):
  ```json
  {
    "success": true,
    "stats": {
      "total_urls": 12,
      "total_clicks": 48,
      "avg_clicks": 4.0,
      "most_active": {
        "id": 1,
        "short_code": "intern-demo",
        "clicks": 18
      }
    }
  }
  ```

### 4. Delete a Short URL
- **Endpoint**: `DELETE /api/links/<int:id>`
- **Response** (`200 OK`):
  ```json
  {
    "success": true,
    "message": "Link deleted successfully."
  }
  ```

### 5. Instant QR Code
- **Endpoint**: `GET /qr/<short_code>`
- **Returns**: `image/png` image stream.

---

## 💡 Internship Assessment Review Guide

When evaluating or demonstrating this project:
1. **Shorten a link**: Paste any long link (e.g. `https://en.wikipedia.org/wiki/URL_shortening`) and click **"Shorten URL"**.
2. **Instant Feedback**: Note the animated result card, copy button feedback, and automatic entry into the recent URLs table.
3. **Redirection Test**: Click on the generated short link or the "Visit" icon. Notice how the click count badge instantly updates.
4. **Custom Alias**: Expand the "Add Custom Alias" drawer, enter a custom name like `my-portfolio`, and shorten. Re-enter the same alias with a different URL to see conflict detection.
5. **QR Code Generator**: Click the QR icon on any link card or table row. Preview and test downloading the PNG image.
6. **Search & Filter**: Type into the search input above the table to filter results in real-time.
7. **Invalid Links**: Try accessing a non-existent short URL like `http://127.0.0.1:5000/does-not-exist` to inspect the custom 404 page.
8. **Dark/Light Theme**: Click the theme toggle icon in the top right to switch palettes.

---

## 🔒 Security Practices Implemented
- Parameterized SQLite queries (`?` placeholders) prevent SQL injection.
- URL scheme verification ensures only `http` and `https` targets are shortened.
- Domain validation and loop-back protection prevent redirect loops back to PyShort itself.
- Sanitized HTML output escapes text to prevent Cross-Site Scripting (XSS).
