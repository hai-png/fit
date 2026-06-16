"""Small SQLite persistence layer for coaching workflows.

This is intentionally thin: it stores client profiles, generated plan snapshots,
weight logs and adherence entries without imposing a web-app architecture.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS clients (
  id TEXT PRIMARY KEY,
  name TEXT,
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
  day INTEGER,
  weight_kg REAL NOT NULL,
  logged_at TEXT NOT NULL,
  FOREIGN KEY(client_id) REFERENCES clients(id)
);
CREATE TABLE IF NOT EXISTS adherence (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  client_id TEXT NOT NULL,
  day INTEGER,
  nutrition_pct REAL,
  training_pct REAL,
  notes TEXT,
  logged_at TEXT NOT NULL,
  FOREIGN KEY(client_id) REFERENCES clients(id)
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_default(obj: Any) -> Any:
    if is_dataclass(obj):
        return asdict(obj)
    if hasattr(obj, "value"):
        return obj.value
    return str(obj)


def connect(db_path: str = "clients.db") -> sqlite3.Connection:
    path = Path(db_path)
    if path.parent and str(path.parent) != ".":
        path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con


def init_db(db_path: str = "clients.db") -> None:
    with closing(connect(db_path)) as con, con:
        con.executescript(SCHEMA)


def store_client(
    client_id: str,
    name: str,
    profile: dict,
    plan: Optional[Any] = None,
    db_path: str = "clients.db",
) -> None:
    init_db(db_path)
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
    init_db(db_path)
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
    init_db(db_path)
    with closing(connect(db_path)) as con, con:
        con.execute(
            """
            INSERT INTO adherence(client_id, day, nutrition_pct, training_pct, notes, logged_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (client_id, day, nutrition_pct, training_pct, notes, _now()),
        )


def client_summary(client_id: str, db_path: str = "clients.db") -> dict:
    init_db(db_path)
    with closing(connect(db_path)) as con, con:
        client = con.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
        if client is None:
            raise KeyError(f"Unknown client_id: {client_id}")
        weights = [dict(row) for row in con.execute(
            "SELECT day, weight_kg, logged_at FROM weights WHERE client_id = ? ORDER BY COALESCE(day, id)",
            (client_id,),
        )]
        plans = [dict(row) for row in con.execute(
            "SELECT id, created_at FROM plans WHERE client_id = ? ORDER BY id DESC",
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
