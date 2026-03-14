"""
Database module for Lost and Found Telegram Bot.
Handles CSV operations for storing lost and found items.
"""

import csv
import os
from datetime import datetime
from typing import Optional

LOST_ITEMS_FILE = "lost_items.csv"
FOUND_ITEMS_FILE = "found_items.csv"

LOST_ITEMS_FIELDS = ["id", "user_id", "category", "description", "photo_file_id", "reward", "created_at", "is_matched"]
FOUND_ITEMS_FIELDS = ["id", "user_id", "category", "description", "photo_file_id", "contact_info", "created_at", "is_matched"]


def init_database():
    """Create CSV files with headers if they don't exist."""
    for filepath, fields in [
        (LOST_ITEMS_FILE, LOST_ITEMS_FIELDS),
        (FOUND_ITEMS_FILE, FOUND_ITEMS_FIELDS),
    ]:
        if not os.path.exists(filepath):
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()


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
    with open(LOST_ITEMS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=LOST_ITEMS_FIELDS)
        writer.writerow(row)
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
    with open(FOUND_ITEMS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FOUND_ITEMS_FIELDS)
        writer.writerow(row)
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


init_database()
