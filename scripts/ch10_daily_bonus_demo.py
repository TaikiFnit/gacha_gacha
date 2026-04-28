"""第10章 / 練習: ログインボーナスを 2 回叩く。

サーバ (exercises/ch10/step3 か step6) を起動した状態で、 このスクリプトを
2 回続けて呼ぶと、 1 回目が 200 / 2 回目が 400 で弾かれることを観察できる。

実行:
    # 1. テーブル作成 (1回だけ)
    psql "$DATABASE_URL" -f exercises/ch10/step1_daily_bonuses_table.sql
    # 2. 当日分があれば消す (必要に応じて)
    psql "$DATABASE_URL" -c "DELETE FROM daily_bonuses WHERE user_id = 1;"
    # 3. サーバ起動
    python exercises/ch10/step6_coin_update_in_tx.py
    # 4. デモを実行
    python scripts/ch10_daily_bonus_demo.py
"""
import json
import urllib.error
import urllib.request

URL = "http://127.0.0.1:8001/api/daily/claim"
TOKEN = "1"


def _post():
    req = urllib.request.Request(
        URL, method="POST",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8") or "{}")


def main():
    print("--- 1 回目 ---")
    s, b = _post()
    print(s, b)
    print("--- 2 回目 ---")
    s, b = _post()
    print(s, b)


if __name__ == "__main__":
    main()
