# =============================================================================
# 🌾 AgriAlert — SQLite Caller Memory Database
#
# Stores returning caller data so the agent can greet farmers by name
# and recall their farm context (crops, district, land size, irrigation).
# =============================================================================

import json
import os
import sqlite3
from datetime import datetime, timezone

# Default database path: backend/data/agrialert.db
DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "agrialert.db",
)


def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """Create the callers table if it doesn't already exist."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS callers (
                user_id             TEXT PRIMARY KEY,
                name                TEXT,
                language_preference TEXT DEFAULT 'mr',
                last_interaction    TEXT,
                facts               TEXT DEFAULT '{}'
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def get_caller(db_path: str, user_id: str) -> dict | None:
    """Look up a caller by user_id.

    Returns a dict with all fields (facts parsed from JSON) or None if
    the caller is not found.
    """
    if not os.path.exists(db_path):
        return None
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT * FROM callers WHERE user_id = ?", (user_id,)
        ).fetchone()
        if row is None:
            return None

        data = dict(row)
        # Parse the JSON facts field into a Python dict
        try:
            data["facts"] = json.loads(data["facts"])
        except (json.JSONDecodeError, TypeError):
            data["facts"] = {}

        # Touch last_interaction timestamp on every lookup
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "UPDATE callers SET last_interaction = ? WHERE user_id = ?",
            (now, user_id),
        )
        conn.commit()
        return data
    finally:
        conn.close()


def upsert_caller(
    db_path: str,
    user_id: str,
    name: str | None = None,
    language_preference: str = "mr",
    facts: dict | None = None,
) -> dict:
    """Insert a new caller or update an existing one.

    If the caller already exists, supplied fields are merged — existing
    facts are updated (not replaced) with any new keys.

    Returns the final saved record as a dict.
    """
    now = datetime.now(timezone.utc).isoformat()
    if not os.path.exists(db_path):
        init_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        existing = conn.execute(
            "SELECT * FROM callers WHERE user_id = ?", (user_id,)
        ).fetchone()

        if existing is not None:
            # Merge facts
            try:
                old_facts = json.loads(existing["facts"])
            except (json.JSONDecodeError, TypeError):
                old_facts = {}
            if facts:
                old_facts.update(facts)
            merged_facts = json.dumps(old_facts, ensure_ascii=False)

            final_name = name if name is not None else existing["name"]
            final_lang = language_preference or existing["language_preference"]

            conn.execute(
                """
                UPDATE callers
                SET name = ?, language_preference = ?,
                    last_interaction = ?, facts = ?
                WHERE user_id = ?
                """,
                (final_name, final_lang, now, merged_facts, user_id),
            )
        else:
            merged_facts = json.dumps(facts or {}, ensure_ascii=False)
            conn.execute(
                """
                INSERT INTO callers
                    (user_id, name, language_preference, last_interaction, facts)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, name, language_preference, now, merged_facts),
            )
        conn.commit()

        # Return the saved record
        row = conn.execute(
            "SELECT * FROM callers WHERE user_id = ?", (user_id,)
        ).fetchone()
        data = dict(row)
        try:
            data["facts"] = json.loads(data["facts"])
        except (json.JSONDecodeError, TypeError):
            data["facts"] = {}
        return data
    finally:
        conn.close()
