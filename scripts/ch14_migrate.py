"""第14章 / 練習: マイグレーションランナー (本物の db/migrations を見る前提)。

これは exercises/ch14/step3_runner.py を「本物の db/migrations/」 に向けた版。
本物の db/ は本教材では <code>db/init.sql</code> 1 ファイルだけで運用しているので、
このスクリプトは「将来 db/migrations/ を作るときのテンプレ」 として置いてある。

実行:
    # まず本物の db/ にマイグレーション置き場を作る (後日)
    mkdir -p db/migrations
    # 既存スキーマを 0001_initial.sql として切り出す:
    cp db/init.sql db/migrations/0001_initial.sql
    # ランナーを起動
    python scripts/ch14_migrate.py
"""
import os
import pathlib
import sys

import psycopg

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = REPO_ROOT / "db" / "migrations"
DSN = os.environ.get(
    "DATABASE_URL",
    "host=127.0.0.1 port=5432 user=gacha password=gacha dbname=gacha",
)


def main():
    if not MIGRATIONS_DIR.is_dir():
        print(f"{MIGRATIONS_DIR} がありません。 まず作ってください。", file=sys.stderr)
        sys.exit(2)

    with psycopg.connect(DSN, autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations ("
                "  filename   TEXT PRIMARY KEY,"
                "  applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW())"
            )
            conn.commit()
            cur.execute("SELECT filename FROM schema_migrations")
            applied = {row[0] for row in cur.fetchall()}

        files = sorted(p.name for p in MIGRATIONS_DIR.glob("*.sql"))
        pending = [f for f in files if f not in applied]
        if not pending:
            print("up to date.")
            return

        for name in pending:
            path = MIGRATIONS_DIR / name
            print(f"applying {name} ...", flush=True)
            sql = path.read_text(encoding="utf-8")
            try:
                with conn.cursor() as cur:
                    cur.execute(sql)
                    cur.execute(
                        "INSERT INTO schema_migrations (filename) VALUES (%s)",
                        (name,),
                    )
                conn.commit()
                print("  ok")
            except Exception as e:  # noqa: BLE001
                conn.rollback()
                print(f"  FAILED: {e}", file=sys.stderr)
                sys.exit(1)


if __name__ == "__main__":
    main()
