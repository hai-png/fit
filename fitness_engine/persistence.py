"""Small SQLite persistence layer for coaching workflows.

This is intentionally thin: it stores client profiles, generated plan snapshots,
weight logs and adherence entries without imposing a web-app architecture.

Schema versioning (F68): the schema version is tracked via
``PRAGMA user_version``. ``init_db`` is idempotent and runs the schema script
plus any pending migrations. Callers no longer need to call ``init_db`` before
every write operation (F69); a one-time call at startup is sufficient, and
write functions will auto-initialize only if the schema version is stale.

Indexes (F71): the ``weights`` and ``adherence`` tables now have indexes on
``(client_id, day)`` so ``client_summary`` queries are fast even with years
of daily logs.

``delete_client`` (F70): cascade-deletes a client and all associated logs.

Concurrency (P2 #32, #33): ``init_db`` and ``_ensure_init`` use a
``threading.Lock`` so concurrent callers cannot corrupt the schema cache.
``connect`` now sets ``PRAGMA journal_mode=WAL`` and ``PRAGMA busy_timeout``
so concurrent readers don't block writers.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import closing
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Current schema version. Increment when the schema changes; add a migration
# step in `_migrate` below. See audit finding F68.
SCHEMA_VERSION = 3

SCHEMA = """
CREATE TABLE IF NOT EXISTS clients (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  profile_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS plans (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  client_id TEXT NOT NULL,
  plan_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(client_id) REFERENCES clients(id)
);
CREATE TABLE IF NOT EXISTS weights (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  client_id TEXT NOT NULL,
  day INTEGER NOT NULL,
  weight_kg REAL NOT NULL,
  logged_at TEXT NOT NULL,
  FOREIGN KEY(client_id) REFERENCES clients(id)
);
CREATE TABLE IF NOT EXISTS adherence (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  client_id TEXT NOT NULL,
  day INTEGER NOT NULL,
  nutrition_pct REAL,
  training_pct REAL,
  notes TEXT,
  logged_at TEXT NOT NULL,
  FOREIGN KEY(client_id) REFERENCES clients(id)
);
CREATE INDEX IF NOT EXISTS idx_weights_client_day ON weights(client_id, day);
CREATE INDEX IF NOT EXISTS idx_adherence_client_day ON adherence(client_id, day);
CREATE INDEX IF NOT EXISTS idx_plans_client ON plans(client_id);
"""

# Per-process set of db_paths that have been initialized in this session.
# This avoids re-running the schema script on every write call (F69).
# P2 #32 — guarded by _init_lock so concurrent threads don't race on init.
_initialized_dbs: set = set()
_init_lock = threading.Lock()


def _now() -> str:
    """UTC ISO-8601 timestamp for created_at / updated_at columns."""
    return datetime.now(timezone.utc).isoformat()


def _json_default(obj: Any) -> Any:
    """JSON serializer for dataclasses and enums; raises TypeError for unknown types."""
    if is_dataclass(obj):
        return asdict(obj)
    if hasattr(obj, "value"):
        return obj.value
    # P2 #36 — previously fell back to str(obj), which silently stringified
    # unknown objects and hid serialization bugs. Now raise so the caller
    # must convert explicitly.
    raise TypeError(
        f"Object of type {type(obj).__name__} is not JSON serializable; "
        f"convert to a dict / primitive before persisting."
    )


def connect(db_path: str = "clients.db") -> sqlite3.Connection:
    path = Path(db_path)
    if path.parent and str(path.parent) != ".":
        path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    # Enable foreign-key enforcement so cascade deletes work.
    con.execute("PRAGMA foreign_keys = ON")
    # P2 #33 — WAL journal mode allows concurrent readers to not block
    # writers; busy_timeout makes writers wait briefly instead of raising
    # SQLITE_BUSY on contention.
    try:
        con.execute("PRAGMA journal_mode = WAL")
        con.execute("PRAGMA busy_timeout = 5000")
    except sqlite3.OperationalError:
        # WAL may be unavailable on some backends (e.g., :memory:); fall back
        # to default journal mode silently.
        pass
    return con


def _get_user_version(con: sqlite3.Connection) -> int:
    """Read PRAGMA user_version for the connected database."""
    row = con.execute("PRAGMA user_version").fetchone()
    return int(row[0]) if row else 0


def _set_user_version(con: sqlite3.Connection, version: int) -> None:
    # PRAGMA does not support parameter binding; the int() cast rejects
    # non-numeric input (verified: '_set_user_version(con, "2; DROP TABLE
    # clients")' raises ValueError) — safe. See P2 #34.
    con.execute(f"PRAGMA user_version = {int(version)}")


def _migrate(con: sqlite3.Connection, current_version: int) -> int:
    """Run migrations from ``current_version`` to ``SCHEMA_VERSION``.

    Each migration step is a function that takes the connection and performs
    the schema change. Steps are applied in order. See audit finding F68.
    """
    version = current_version
    # Migration: version 0 → 1 (add indexes; idempotent because of IF NOT EXISTS).
    if version < 1:
        con.execute("CREATE INDEX IF NOT EXISTS idx_weights_client_day ON weights(client_id, day)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_adherence_client_day ON adherence(client_id, day)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_plans_client ON plans(client_id)")
        version = 1
    # Migration: version 1 → 2 (no schema change; this is an intentional
    # marker that foreign-key enforcement was added per-connection in
    # connect(). Bumping the version lets future migrations detect this
    # state. See P2 #31.
    if version < 2:
        version = 2
    # Migration: version 2 → 3 (P2 #35, NEW-P2 #17 — tighten NOT NULL on
    # clients.name, weights.day, adherence.day). SQLite cannot ALTER COLUMN
    # in place, so we rebuild the affected tables via the standard
    # "create new table, copy data, drop old, rename" pattern. Existing rows
    # with NULL values get sane defaults so the copy succeeds.
    if version < 3:
        # Backfill any NULL names with 'Client' before tightening.
        con.execute("UPDATE clients SET name = 'Client' WHERE name IS NULL")
        # Backfill any NULL days with 0 before tightening (rare but possible).
        con.execute("UPDATE weights SET day = 0 WHERE day IS NULL")
        con.execute("UPDATE adherence SET day = 0 WHERE day IS NULL")
        # Rebuild clients table with NOT NULL on name.
        con.executescript("""
        CREATE TABLE clients_new (
          id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          profile_json TEXT NOT NULL,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        INSERT INTO clients_new(id, name, profile_json, created_at, updated_at)
          SELECT id, name, profile_json, created_at, updated_at FROM clients;
        DROP TABLE clients;
        ALTER TABLE clients_new RENAME TO clients;
        """)
        # Rebuild weights table with NOT NULL on day.
        con.executescript("""
        CREATE TABLE weights_new (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          client_id TEXT NOT NULL,
          day INTEGER NOT NULL,
          weight_kg REAL NOT NULL,
          logged_at TEXT NOT NULL,
          FOREIGN KEY(client_id) REFERENCES clients(id)
        );
        INSERT INTO weights_new(id, client_id, day, weight_kg, logged_at)
          SELECT id, client_id, day, weight_kg, logged_at FROM weights;
        DROP TABLE weights;
        ALTER TABLE weights_new RENAME TO weights;
        CREATE INDEX IF NOT EXISTS idx_weights_client_day ON weights(client_id, day);
        """)
        # Rebuild adherence table with NOT NULL on day.
        con.executescript("""
        CREATE TABLE adherence_new (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          client_id TEXT NOT NULL,
          day INTEGER NOT NULL,
          nutrition_pct REAL,
          training_pct REAL,
          notes TEXT,
          logged_at TEXT NOT NULL,
          FOREIGN KEY(client_id) REFERENCES clients(id)
        );
        INSERT INTO adherence_new(id, client_id, day, nutrition_pct, training_pct, notes, logged_at)
          SELECT id, client_id, day, nutrition_pct, training_pct, notes, logged_at FROM adherence;
        DROP TABLE adherence;
        ALTER TABLE adherence_new RENAME TO adherence;
        CREATE INDEX IF NOT EXISTS idx_adherence_client_day ON adherence(client_id, day);
        """)
        version = 3
    return version


def init_db(db_path: str = "clients.db") -> None:
    """Initialize the database schema and run any pending migrations.

    Idempotent: safe to call multiple times. Tracks the schema version via
    ``PRAGMA user_version`` so future schema changes can be migrated
    incrementally. See audit findings F68, F69.
    """
    # P2 #32 — serialize init across threads so the schema cache cannot
    # race. Two threads calling init_db simultaneously on the same path
    # could both pass the cache check and both try to write the schema.
    with _init_lock:
        with closing(connect(db_path)) as con, con:
            con.executescript(SCHEMA)
            current = _get_user_version(con)
            if current < SCHEMA_VERSION:
                new_version = _migrate(con, current)
                _set_user_version(con, new_version)
        _initialized_dbs.add(str(Path(db_path).resolve()))


def _ensure_init(db_path: str) -> None:
    """Initialize the DB if it hasn't been initialized in this process.

    This avoids the per-call init_db overhead while still guaranteeing the
    schema exists. See audit finding F69.
    """
    resolved = str(Path(db_path).resolve())
    # P2 #32 — double-checked locking: read the set without the lock first
    # (fast path), then re-check under the lock before init (slow path).
    if resolved in _initialized_dbs:
        return
    with _init_lock:
        if resolved not in _initialized_dbs:
            init_db(db_path)


def store_client(
    client_id: str,
    name: str,
    profile: dict,
    plan: Optional[Any] = None,
    db_path: str = "clients.db",
) -> None:
    # P2 #37 — validate profile is a dict; previously a list or None would
    # silently stringify and store, producing an unreadable profile_json.
    if not isinstance(profile, dict):
        raise TypeError(
            f"profile must be a dict, got {type(profile).__name__}: {profile!r}"
        )
    _ensure_init(db_path)
    now = _now()
    profile_json = json.dumps(profile, indent=2, default=_json_default)
    with closing(connect(db_path)) as con, con:
        existing = con.execute("SELECT id FROM clients WHERE id = ?", (client_id,)).fetchone()
        if existing:
            con.execute(
                "UPDATE clients SET name = ?, profile_json = ?, updated_at = ? WHERE id = ?",
                (name, profile_json, now, client_id),
            )
        else:
            con.execute(
                "INSERT INTO clients(id, name, profile_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (client_id, name, profile_json, now, now),
            )
        if plan is not None:
            con.execute(
                "INSERT INTO plans(client_id, plan_json, created_at) VALUES (?, ?, ?)",
                (client_id, json.dumps(plan, indent=2, default=_json_default), now),
            )


def add_weight(client_id: str, weight_kg: float, day: Optional[int] = None, db_path: str = "clients.db") -> None:
    """Add a weight log entry. Validates ``weight_kg`` is positive and reasonable."""
    if not isinstance(weight_kg, (int, float)) or weight_kg <= 0:
        raise ValueError(f"weight_kg must be positive (got {weight_kg})")
    if weight_kg > 500:
        raise ValueError(f"weight_kg must be ≤ 500 kg (got {weight_kg})")
    _ensure_init(db_path)
    with closing(connect(db_path)) as con, con:
        con.execute(
            "INSERT INTO weights(client_id, day, weight_kg, logged_at) VALUES (?, ?, ?, ?)",
            (client_id, day, weight_kg, _now()),
        )


def add_adherence(
    client_id: str,
    nutrition_pct: Optional[float] = None,
    training_pct: Optional[float] = None,
    day: Optional[int] = None,
    notes: str = "",
    db_path: str = "clients.db",
) -> None:
    """Add an adherence log entry. Validates percentages are in [0, 100]."""
    for label, val in [("nutrition_pct", nutrition_pct), ("training_pct", training_pct)]:
        if val is not None:
            if not isinstance(val, (int, float)):
                raise ValueError(f"{label} must be a number (got {type(val).__name__})")
            if val < 0 or val > 100:
                raise ValueError(f"{label} must be in [0, 100] (got {val})")
    _ensure_init(db_path)
    with closing(connect(db_path)) as con, con:
        con.execute(
            """
            INSERT INTO adherence(client_id, day, nutrition_pct, training_pct, notes, logged_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (client_id, day, nutrition_pct, training_pct, notes, _now()),
        )


def delete_client(client_id: str, db_path: str = "clients.db") -> bool:
    """Delete a client and all associated plans, weights, and adherence logs.

    Returns ``True`` if the client existed and was deleted, ``False`` if the
    client was not found. See audit finding F70.
    """
    _ensure_init(db_path)
    with closing(connect(db_path)) as con, con:
        existing = con.execute("SELECT id FROM clients WHERE id = ?", (client_id,)).fetchone()
        if existing is None:
            return False
        # Foreign-key cascade is not enabled at the column level; delete
        # child rows explicitly so the operation works regardless of FK state.
        con.execute("DELETE FROM weights WHERE client_id = ?", (client_id,))
        con.execute("DELETE FROM adherence WHERE client_id = ?", (client_id,))
        con.execute("DELETE FROM plans WHERE client_id = ?", (client_id,))
        con.execute("DELETE FROM clients WHERE id = ?", (client_id,))
        return True


def client_summary(client_id: str, db_path: str = "clients.db") -> dict:
    """Return all client data (profile, plans, weights, adherence) as a dict."""
    _ensure_init(db_path)
    with closing(connect(db_path)) as con, con:
        client = con.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
        if client is None:
            raise KeyError(f"Unknown client_id: {client_id}")
        weights = [dict(row) for row in con.execute(
            "SELECT day, weight_kg, logged_at FROM weights WHERE client_id = ? ORDER BY COALESCE(day, id)",
            (client_id,),
        )]
        plans = [dict(row) for row in con.execute(
            "SELECT id, plan_json, created_at FROM plans WHERE client_id = ? ORDER BY id DESC",
            (client_id,),
        )]
        adherence = [dict(row) for row in con.execute(
            "SELECT day, nutrition_pct, training_pct, notes, logged_at FROM adherence WHERE client_id = ? ORDER BY COALESCE(day, id)",
            (client_id,),
        )]
    return {
        "client": dict(client),
        "weights": weights,
        "plans": plans,
        "adherence": adherence,
    }


def schema_version(db_path: str = "clients.db") -> int:
    """Return the current schema version of the database (for diagnostics)."""
    with closing(connect(db_path)) as con:
        return _get_user_version(con)
