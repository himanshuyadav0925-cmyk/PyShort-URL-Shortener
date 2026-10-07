-- PyShort Database Schema
-- SQLite schema for storing shortened URLs and click audit logs

CREATE TABLE IF NOT EXISTS urls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_url TEXT NOT NULL,
    short_code TEXT NOT NULL UNIQUE COLLATE NOCASE,
    is_custom INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_clicked_at TIMESTAMP DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS click_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url_id INTEGER NOT NULL,
    clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_agent TEXT,
    referrer TEXT,
    FOREIGN KEY (url_id) REFERENCES urls (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_urls_short_code ON urls (short_code);
CREATE INDEX IF NOT EXISTS idx_urls_created_at ON urls (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_click_logs_url_id ON click_logs (url_id);
