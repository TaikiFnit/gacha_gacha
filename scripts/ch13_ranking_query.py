"""第13章 / 練習: 所持数ランキングをコンソールに出す。

実行:
    python scripts/ch13_ranking_query.py
    python scripts/ch13_ranking_query.py 5      # 上位 5 件だけ
"""
import os
import sys

import psycopg
from psycopg.rows import dict_row

DSN = os.environ.get(
    "DATABASE_URL",
    "host=127.0.0.1 port=5432 user=gacha password=gacha dbname=gacha",
)


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    with psycopg.connect(DSN, row_factory=dict_row) as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT u.id, u.name,
                   COUNT(uc.character_id)                                AS owned,
                   RANK() OVER (ORDER BY COUNT(uc.character_id) DESC)    AS rank
              FROM users u
              LEFT JOIN user_characters uc ON uc.user_id = u.id
             GROUP BY u.id
             ORDER BY rank, u.id
             LIMIT %s
            """,
            (limit,),
        )
        rows = cur.fetchall()

    print(f"{'rank':>4}  {'owned':>5}  {'user_id':>6}  name")
    print("-" * 50)
    for r in rows:
        print(f"{r['rank']:>4}  {r['owned']:>5}  {r['id']:>6}  {r['name']}")


if __name__ == "__main__":
    main()
