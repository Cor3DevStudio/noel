"""MariaDB/MySQL backup and restore via JSON — no mysqldump/mysql CLI required."""

from __future__ import annotations

import base64
import json
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from config.settings import DB_NAME, SCHEMA_VERSION

BACKUP_FORMAT_VERSION = 1


def _format_timedelta(value: timedelta) -> str:
    """Convert MariaDB TIME / timedelta values to HH:MM:SS for JSON storage."""
    total = int(value.total_seconds())
    if total < 0:
        total = (86400 + total) % 86400
    hours, rem = divmod(total, 3600)
    minutes, seconds = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _encode(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, time):
        return value.isoformat()
    if isinstance(value, timedelta):
        return _format_timedelta(value)
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, bytes):
        return {"__bytes__": base64.b64encode(value).decode("ascii")}
    if isinstance(value, dict):
        return {k: _encode(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_encode(v) for v in value]
    if isinstance(value, (bool, int, float, str)):
        return value
    return str(value)


def _decode(value: Any) -> Any:
    if isinstance(value, dict) and "__bytes__" in value:
        return base64.b64decode(value["__bytes__"])
    return value


def backup_database_json(engine: Engine, backup_path: Path) -> int:
    """Export all tables to a JSON file. Returns total row count."""
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    payload: dict[str, Any] = {
        "format_version": BACKUP_FORMAT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "database": DB_NAME,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source": "MariaDB/MySQL via PyMySQL",
        "tables": {},
    }
    total_rows = 0

    with engine.connect() as conn:
        for table in table_names:
            result = conn.execute(text(f"SELECT * FROM `{table}`"))
            rows = [
                {col: _encode(val) for col, val in zip(result.keys(), row)}
                for row in result.fetchall()
            ]
            payload["tables"][table] = rows
            total_rows += len(rows)

    backup_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return total_rows


def restore_database_json(engine: Engine, backup_path: Path) -> int:
    """Restore all tables from a JSON backup. Returns total rows restored."""
    raw = backup_path.read_text(encoding="utf-8")
    payload = json.loads(raw)

    if not isinstance(payload, dict) or "tables" not in payload:
        raise ValueError("Invalid backup file. Expected JSON export from this application.")

    tables: dict[str, list[dict]] = payload["tables"]
    if not isinstance(tables, dict):
        raise ValueError("Invalid backup file: 'tables' must be an object.")

    total_rows = 0
    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for table in tables:
            conn.execute(text(f"TRUNCATE TABLE `{table}`"))
        for table, rows in tables.items():
            if not rows:
                continue
            columns = list(rows[0].keys())
            col_sql = ", ".join(f"`{col}`" for col in columns)
            val_sql = ", ".join(f":{col}" for col in columns)
            stmt = text(f"INSERT INTO `{table}` ({col_sql}) VALUES ({val_sql})")
            for row in rows:
                params = {col: _decode(row.get(col)) for col in columns}
                conn.execute(stmt, params)
            total_rows += len(rows)
        conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))

    return total_rows
