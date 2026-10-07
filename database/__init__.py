"""Database package for PyShort."""
from .db import (
    init_db,
    get_db,
    get_url_by_code,
    get_url_by_id,
    get_url_by_original,
    create_url,
    record_click,
    get_recent_urls,
    get_paginated_urls,
    get_analytics_summary,
    delete_url,
    code_exists,
)

__all__ = [
    "init_db",
    "get_db",
    "get_url_by_code",
    "get_url_by_id",
    "get_url_by_original",
    "create_url",
    "record_click",
    "get_recent_urls",
    "get_paginated_urls",
    "get_analytics_summary",
    "delete_url",
    "code_exists",
]
