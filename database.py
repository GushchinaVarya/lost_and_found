"""
Database module for Lost and Found Telegram Bot.
Handles CSV operations for storing lost and found items.
"""

import csv
import logging
import os
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

LOST_ITEMS_FILE = "lost_items.csv"
FOUND_ITEMS_FILE = "found_items.csv"
UNIQUE_USERS_FILE = "unique_users.csv"
UNIQUE_USERS_FIELDS = ["user_id", "username", "first_seen"]

LOST_ITEMS_FIELDS = ["id", "user_id", "category", "description", "photo_file_id", "reward", "created_at", "is_matched"]
FOUND_ITEMS_FIELDS = ["id", "user_id", "category", "description", "photo_file_id", "contact_info", "created_at", "is_matched"]


def init_database():
    """Create CSV files with headers if they don't exist."""
    for filepath, fields in [
        (LOST_ITEMS_FILE, LOST_ITEMS_FIELDS),
        (FOUND_ITEMS_FILE, FOUND_ITEMS_FIELDS),
        (UNIQUE_USERS_FILE, UNIQUE_USERS_FIELDS),
    ]:
        if not os.path.exists(filepath):
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
            logger.info("[DB_INIT] Created %s", filepath)
    logger.info("[DB_INIT] Database initialized")


def _load_known_user_ids() -> set[int]:
    """Load the set of already tracked user IDs from the CSV file."""
    ids: set[int] = set()
    if not os.path.exists(UNIQUE_USERS_FILE):
        return ids
    with open(UNIQUE_USERS_FILE, "r", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                ids.add(int(row["user_id"]))
            except (ValueError, KeyError):
                continue
    return ids


_known_users: set[int] = set()


def track_user(user_id: int, username: str | None = None) -> bool:
    """
    Record a user if they haven't been seen before.
    Returns True when the user is new, False otherwise.
    """
    global _known_users
    if not _known_users:
        _known_users = _load_known_user_ids()

    if user_id in _known_users:
        return False

    row = {
        "user_id": user_id,
        "username": username or "",
        "first_seen": datetime.now().isoformat(),
    }
    try:
        with open(UNIQUE_USERS_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=UNIQUE_USERS_FIELDS)
            writer.writerow(row)
        _known_users.add(user_id)
        logger.info("[DB] New unique user tracked: user_id=%d username=%s", user_id, username or "N/A")
        return True
    except Exception:
        logger.exception("[DB] Failed to track user user_id=%d", user_id)
        return False


def _next_id(filepath: str) -> int:
    """Return the next auto-increment ID for the given CSV file."""
    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        return 1
    with open(filepath, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        max_id = 0
        for row in reader:
            try:
                max_id = max(max_id, int(row["id"]))
            except (ValueError, KeyError):
                continue
        return max_id + 1


def _read_all_rows(filepath: str, fields: list[str]) -> list[dict]:
    """Read all rows from a CSV file and return them as a list of dicts."""
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def save_lost_item(
    user_id: int,
    category: str,
    description: str,
    photo_file_id: Optional[str] = None,
    reward: Optional[str] = None,
) -> int:
    """
    Save a lost item to lost_items.csv.
    Returns the ID of the inserted record.
    """
    item_id = _next_id(LOST_ITEMS_FILE)
    row = {
        "id": item_id,
        "user_id": user_id,
        "category": category,
        "description": description,
        "photo_file_id": photo_file_id or "",
        "reward": reward or "",
        "created_at": datetime.now().isoformat(),
        "is_matched": "false",
    }
    try:
        with open(LOST_ITEMS_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=LOST_ITEMS_FIELDS)
            writer.writerow(row)
        logger.info("[DB] Saved lost item #%d (user_id=%s, category=%s)", item_id, user_id, category)
    except Exception:
        logger.exception("[DB] Failed to save lost item for user_id=%s", user_id)
        raise
    return item_id


def save_found_item(
    user_id: int,
    category: str,
    description: str,
    photo_file_id: Optional[str] = None,
    contact_info: Optional[str] = None,
) -> int:
    """
    Save a found item to found_items.csv.
    Returns the ID of the inserted record.
    """
    item_id = _next_id(FOUND_ITEMS_FILE)
    row = {
        "id": item_id,
        "user_id": user_id,
        "category": category,
        "description": description,
        "photo_file_id": photo_file_id or "",
        "contact_info": contact_info or "",
        "created_at": datetime.now().isoformat(),
        "is_matched": "false",
    }
    try:
        with open(FOUND_ITEMS_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FOUND_ITEMS_FIELDS)
            writer.writerow(row)
        logger.info("[DB] Saved found item #%d (user_id=%s, category=%s)", item_id, user_id, category)
    except Exception:
        logger.exception("[DB] Failed to save found item for user_id=%s", user_id)
        raise
    return item_id


def get_lost_items(limit: int = 10) -> list:
    """Get recent lost items."""
    rows = _read_all_rows(LOST_ITEMS_FILE, LOST_ITEMS_FIELDS)
    rows.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    return rows[:limit]


def get_found_items(limit: int = 10) -> list:
    """Get recent found items."""
    rows = _read_all_rows(FOUND_ITEMS_FILE, FOUND_ITEMS_FIELDS)
    rows.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    return rows[:limit]


def is_similar(lost_item: dict, found_item: dict) -> bool:
    """
    Compare a lost item and a found item to determine if they might be the same object.
    Currently matches by category only; will be extended with smarter comparison logic.
    """
    return lost_item.get("category", "").lower() == found_item.get("category", "").lower()


def get_unmatched_lost_items() -> list[dict]:
    """Get all lost items that haven't been matched yet."""
    rows = _read_all_rows(LOST_ITEMS_FILE, LOST_ITEMS_FIELDS)
    return [r for r in rows if r.get("is_matched", "false") == "false"]


def find_similar_lost_items(found_item: dict) -> list[dict]:
    """Find unmatched lost items that are similar to the given found item."""
    unmatched = get_unmatched_lost_items()
    results = [item for item in unmatched if is_similar(item, found_item)]
    logger.info("[DB] find_similar_lost_items for found category='%s': %d unmatched, %d similar",
                found_item.get("category", ""), len(unmatched), len(results))
    return results


def get_unmatched_found_items() -> list[dict]:
    """Get all found items that haven't been matched yet."""
    rows = _read_all_rows(FOUND_ITEMS_FILE, FOUND_ITEMS_FIELDS)
    return [r for r in rows if r.get("is_matched", "false") == "false"]


def find_similar_found_items(lost_item: dict) -> list[dict]:
    """Find unmatched found items that are similar to the given lost item."""
    unmatched = get_unmatched_found_items()
    results = [item for item in unmatched if is_similar(lost_item, item)]
    logger.info("[DB] find_similar_found_items for lost category='%s': %d unmatched, %d similar",
                lost_item.get("category", ""), len(unmatched), len(results))
    return results


def get_lost_item_by_id(item_id: int) -> Optional[dict]:
    """Get a specific lost item by its ID."""
    rows = _read_all_rows(LOST_ITEMS_FILE, LOST_ITEMS_FIELDS)
    for row in rows:
        if str(row.get("id")) == str(item_id):
            return row
    return None


def get_found_item_by_id(item_id: int) -> Optional[dict]:
    """Get a specific found item by its ID."""
    rows = _read_all_rows(FOUND_ITEMS_FILE, FOUND_ITEMS_FIELDS)
    for row in rows:
        if str(row.get("id")) == str(item_id):
            return row
    return None


def _update_match(filepath: str, fields: list[str], item_id: int, matched_with_id: int):
    """Update the is_matched field for a specific item in a CSV file."""
    rows = _read_all_rows(filepath, fields)
    found = False
    for row in rows:
        if str(row.get("id")) == str(item_id):
            row["is_matched"] = str(matched_with_id)
            found = True
            break
    if not found:
        logger.warning("[DB] _update_match: item #%d not found in %s", item_id, filepath)
        return
    try:
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        logger.info("[DB] Updated match: item #%d in %s -> matched_with #%d", item_id, filepath, matched_with_id)
    except Exception:
        logger.exception("[DB] Failed to update match for item #%d in %s", item_id, filepath)
        raise


def update_lost_item_match(lost_item_id: int, found_item_id: int):
    """Set is_matched on a lost item to the matching found item's ID."""
    _update_match(LOST_ITEMS_FILE, LOST_ITEMS_FIELDS, lost_item_id, found_item_id)


def update_found_item_match(found_item_id: int, lost_item_id: int):
    """Set is_matched on a found item to the matching lost item's ID."""
    _update_match(FOUND_ITEMS_FILE, FOUND_ITEMS_FIELDS, found_item_id, lost_item_id)


init_database()
