"""Test-only adapter that lets `server/*` run against SQLite.

Production uses psycopg + PostgreSQL. For sandbox testing we substitute a
SQLite-backed connection that mimics the psycopg cursor / connection API the
server code touches:

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT ... WHERE x = %s", (1,))
            cur.fetchone()  # -> dict
            cur.fetchall()  # -> list[dict]
        # implicit commit on success / rollback on exception

Translation layer:
- `%s` placeholders         -> `?`
- `NOW()`                   -> `datetime('now')`
- `FOR UPDATE` / `FOR SHARE` -> stripped (sqlite is single-writer)
- datetime parameters       -> `'YYYY-MM-DD HH:MM:SS'` UTC string
- `RETURNING` is native in modern SQLite (>=3.35)
"""

from __future__ import annotations

import datetime as _dt
import re
import sqlite3
from contextlib import contextmanager
from typing import Any, Iterator


# ---------------------------------------------------------------------------
# Type conversion: make SQLite's TIMESTAMP columns come back as
# timezone-aware datetime (UTC), to match psycopg's TIMESTAMPTZ behaviour.
# ---------------------------------------------------------------------------
def _convert_ts(raw: bytes) -> _dt.datetime:
    s = raw.decode("ascii")
    # Accept "YYYY-MM-DD HH:MM:SS" and "YYYY-MM-DD HH:MM:SS.ffffff"
    fmt = "%Y-%m-%d %H:%M:%S.%f" if "." in s else "%Y-%m-%d %H:%M:%S"
    return _dt.datetime.strptime(s, fmt).replace(tzinfo=_dt.timezone.utc)


sqlite3.register_converter("TIMESTAMP", _convert_ts)


_FOR_LOCK_RE = re.compile(r"\s+FOR\s+(UPDATE|SHARE)\b", re.IGNORECASE)
_NOW_RE = re.compile(r"\bNOW\(\)", re.IGNORECASE)
_PCT_S_RE = re.compile(r"%s")


def _translate_sql(sql: str) -> str:
    sql = _FOR_LOCK_RE.sub("", sql)
    sql = _NOW_RE.sub("datetime('now')", sql)
    sql = _PCT_S_RE.sub("?", sql)
    return sql


def _translate_param(p: Any) -> Any:
    if isinstance(p, _dt.datetime):
        if p.tzinfo is not None:
            p = p.astimezone(_dt.timezone.utc).replace(tzinfo=None)
        return p.strftime("%Y-%m-%d %H:%M:%S")
    return p


def _translate_params(params: Any) -> Any:
    if params is None:
        return params
    if isinstance(params, dict):
        return {k: _translate_param(v) for k, v in params.items()}
    return tuple(_translate_param(p) for p in params)


class _Cursor:
    def __init__(self, conn: sqlite3.Connection):
        self._cur = conn.cursor()
        self._cur.row_factory = sqlite3.Row

    # cursor protocol used by server code -----------------------------------
    def execute(self, sql: str, params: Any = ()) -> "_Cursor":
        self._cur.execute(_translate_sql(sql), _translate_params(params))
        return self

    def fetchone(self) -> dict | None:
        row = self._cur.fetchone()
        return dict(row) if row is not None else None

    def fetchall(self) -> list[dict]:
        return [dict(r) for r in self._cur.fetchall()]

    def close(self) -> None:
        self._cur.close()

    # context manager
    def __enter__(self): return self
    def __exit__(self, *exc): self.close(); return False


class _Connection:
    """Thin wrapper around sqlite3.Connection that mimics psycopg.Connection."""

    def __init__(self, sqlite_conn: sqlite3.Connection):
        self._conn = sqlite_conn

    def cursor(self) -> _Cursor:
        return _Cursor(self._conn)

    def commit(self) -> None:
        self._conn.commit()

    def rollback(self) -> None:
        self._conn.rollback()

    def close(self) -> None:
        # don't actually close - shared in-memory db across test
        pass


# A single shared in-memory database for the whole test run.
# `:memory:` per connection would be a different DB, so we use a named
# shared cache.
_SHARED_URI = "file:gacha_test?mode=memory&cache=shared"
_keepalive: sqlite3.Connection | None = None


def init_shared_db(schema_sql: str, seed_sql: str) -> None:
    """Initialise the shared in-memory DB. Idempotent (drops then recreates)."""
    global _keepalive
    if _keepalive is not None:
        _keepalive.close()
    _keepalive = sqlite3.connect(_SHARED_URI, uri=True,
                                  detect_types=sqlite3.PARSE_DECLTYPES,
                                  isolation_level=None)  # autocommit
    _keepalive.execute("PRAGMA foreign_keys = ON")
    _keepalive.executescript(schema_sql)
    _keepalive.executescript(seed_sql)


@contextmanager
def get_conn() -> Iterator[_Connection]:
    """Drop-in replacement for `server.db.get_conn` during tests."""
    raw = sqlite3.connect(_SHARED_URI, uri=True,
                           detect_types=sqlite3.PARSE_DECLTYPES,
                           isolation_level="DEFERRED")
    raw.execute("PRAGMA foreign_keys = ON")
    conn = _Connection(raw)
    try:
        yield conn
        raw.commit()
    except Exception:
        raw.rollback()
        raise
    finally:
        raw.close()


def healthcheck() -> bool:
    try:
        with get_conn() as c, c.cursor() as cur:
            cur.execute("SELECT 1 AS ok")
            return cur.fetchone()["ok"] == 1
    except Exception:
        return False
