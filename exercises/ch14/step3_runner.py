"""ch14 / step 3 — 自前のマイグレーションランナー。

ゴール:
    指定ディレクトリの *.sql をファイル名順に列挙し、 schema_migrations に
    記録されていない (= 未適用) ものだけ順に流す。 1 ファイル = 1 トランザクション。

実行:
    python exercises/ch14/step3_runner.py exercises/ch14/migrations

設計のポイント:
    * ファイル並びは Python 側 sorted() に任せる (4 桁ゼロ埋めで安定)。
    * SQL 適用と schema_migrations への INSERT は<strong>同じトランザクション</strong>。
    * 1 ファイル失敗 = ロールバック + 終了。 次回はそのファイルから再開できる。
    * down マイグレーションは実装しない (失敗時は次の番号で打ち消すスタイル)。
"""
import os
import pathlib
import sys

import psycopg

DSN = os.environ.get(
    "DATABASE_URL",
    "host=127.0.0.1 port=5432 user=gacha password=gacha dbname=play_migrate",
)


def main():
    if len(sys.argv) < 2:
        print(f"usage: python {sys.argv[0]} <migrations-dir>", file=sys.stderr)
        sys.exit(2)
    migrations_dir = pathlib.Path(sys.argv[1])
    if not migrations_dir.is_dir():
        print(f"not a directory: {migrations_dir}", file=sys.stderr)
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

        files = sorted(p.name for p in migrations_dir.glob("*.sql"))
        pending = [f for f in files if f not in applied]
        if not pending:
            print("up to date.")
            return

        for name in pending:
            path = migrations_dir / name
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
