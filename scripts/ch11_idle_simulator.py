"""第11章 / 練習: last_collected_at を意図的に過去にずらして collect() を観察。

実行:
    # exercises/ch11/step1 でテーブル拡張済み + alice (id=1) に装備済み前提
    python scripts/ch11_idle_simulator.py --user 1 --back 60
"""
import argparse
import os
import sys

import psycopg
from psycopg.rows import dict_row

sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "exercises", "ch11"),
)
from step4_collect_for_update import collect   # noqa: E402

DSN = os.environ.get(
    "DATABASE_URL",
    "host=127.0.0.1 port=5432 user=gacha password=gacha dbname=gacha",
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", type=int, default=1)
    ap.add_argument("--back", type=int, default=60,
                    help="last_collected_at を何秒ぶん過去にずらすか")
    args = ap.parse_args()

    with psycopg.connect(DSN, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users "
                "   SET last_collected_at = NOW() - (%s || ' seconds')::interval "
                " WHERE id = %s",
                (args.back, args.user),
            )
            cur.execute("SELECT coins FROM users WHERE id = %s", (args.user,))
            before = cur.fetchone()["coins"]

        gained = collect(conn, args.user)

        with conn.cursor() as cur:
            cur.execute("SELECT coins FROM users WHERE id = %s", (args.user,))
            after = cur.fetchone()["coins"]

    print(f"user_id={args.user}  back={args.back}s")
    print(f"  coins: {before} -> {after}  (+{gained})")


if __name__ == "__main__":
    main()
