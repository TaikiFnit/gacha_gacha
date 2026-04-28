"""ch13 / step 6 — keyset pagination でランキングを高速にめくる。

ゴール:
    OFFSET 50, OFFSET 100 ... 方式は後ろのページほど遅くなる (全行を読み飛ばす)。
    keyset pagination は「直前のページの最後の値を WHERE で渡す」 方式で、
    どのページでも一定速度。

    ランキング (owned, user_id) という 2 軸でソートしているので、 keyset も
    (owned, user_id) のタプル比較で表現する。

実行:
    python exercises/ch13/step6_pagination_keyset.py            # 1 ページ目
    python exercises/ch13/step6_pagination_keyset.py 5 100      # owned=5 / user_id=100 の次から 50 件
"""
import os
import sys

import psycopg
from psycopg.rows import dict_row

DSN = os.environ.get(
    "DATABASE_URL",
    "host=127.0.0.1 port=5432 user=gacha password=gacha dbname=gacha",
)
PAGE = 50


def main():
    last_owned = int(sys.argv[1]) if len(sys.argv) > 1 else None
    last_uid   = int(sys.argv[2]) if len(sys.argv) > 2 else None

    with psycopg.connect(DSN, row_factory=dict_row) as conn, conn.cursor() as cur:
        if last_owned is None:
            cur.execute(
                """
                SELECT u.id, u.name, COUNT(uc.character_id) AS owned
                  FROM users u
                  LEFT JOIN user_characters uc ON uc.user_id = u.id
                 GROUP BY u.id
                 ORDER BY owned DESC, u.id ASC
                 LIMIT %s
                """,
                (PAGE,),
            )
        else:
            cur.execute(
                """
                SELECT u.id, u.name, COUNT(uc.character_id) AS owned
                  FROM users u
                  LEFT JOIN user_characters uc ON uc.user_id = u.id
                 GROUP BY u.id
                HAVING (COUNT(uc.character_id), u.id) < (%s, %s)
                 ORDER BY owned DESC, u.id ASC
                 LIMIT %s
                """,
                (last_owned, last_uid, PAGE),
            )
        rows = cur.fetchall()

    for r in rows:
        print(f"{r['owned']:>4}  user_id={r['id']:>4}  {r['name']}")
    if rows:
        last = rows[-1]
        print(f"\n次ページ: python {sys.argv[0]} {last['owned']} {last['id']}")


if __name__ == "__main__":
    main()
