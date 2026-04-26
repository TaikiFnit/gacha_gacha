"""Convert db/schema.sql + db/seed.sql to SQLite-compatible DDL/DML.

Used only by tests/test_e2e_sqlite.py to populate the in-memory test DB.
The PostgreSQL files in db/ remain the source of truth for production.
"""

from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent


_TYPE_RULES = [
    (re.compile(r"\bBIGSERIAL\b", re.I),
     "INTEGER PRIMARY KEY AUTOINCREMENT"),
    (re.compile(r"\bBIGINT\b", re.I),     "INTEGER"),
    (re.compile(r"\bSMALLINT\b", re.I),   "INTEGER"),
    (re.compile(r"\bTIMESTAMPTZ\b", re.I),"TIMESTAMP"),  # PARSE_DECLTYPES converts back to datetime
    (re.compile(r"\bDEFAULT NOW\(\)", re.I),
     "DEFAULT (datetime('now'))"),
]


def _translate_schema(sql: str) -> str:
    # Drop pg_get_serial_sequence helper calls (used after manual id seeds in PG)
    sql = re.sub(
        r"SELECT setval\(.*?\);", "", sql, flags=re.DOTALL | re.I,
    )
    # PRIMARY KEY happens twice if BIGSERIAL substitution lands next to "PRIMARY KEY".
    # First substitute BIGSERIAL alone (without trailing PRIMARY KEY duplication).
    sql = re.sub(
        r"\bBIGSERIAL\s+PRIMARY KEY\b", "INTEGER PRIMARY KEY AUTOINCREMENT", sql, flags=re.I,
    )
    for pat, rep in _TYPE_RULES:
        sql = pat.sub(rep, sql)
    return sql


def _translate_seed(sql: str) -> str:
    # `SELECT setval(pg_get_serial_sequence(...), ...)` is PG-only; drop it.
    sql = re.sub(
        r"SELECT setval\([^;]*?\);", "", sql, flags=re.DOTALL | re.I,
    )
    # `ON CONFLICT DO NOTHING` and `ON CONFLICT (col) DO NOTHING` are supported by SQLite.
    return sql


def get_translated_schema() -> str:
    return _translate_schema((ROOT / "db" / "schema.sql").read_text(encoding="utf-8"))


def get_translated_seed() -> str:
    return _translate_seed((ROOT / "db" / "seed.sql").read_text(encoding="utf-8"))


if __name__ == "__main__":
    print("---- translated schema.sql ----")
    print(get_translated_schema())
    print("---- translated seed.sql ----")
    print(get_translated_seed())
