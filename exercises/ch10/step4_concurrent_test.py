"""ch10 / step 4 — 同じ user で 2 リクエスト同時投入。

ゴール:
    step2 (素朴版) と step3 (UNIQUE 版) のどちらが走っているかで、
    結果が変わるのを目視確認する。

実行手順:
    1. 別ターミナルで step3 を起動: python exercises/ch10/step3_unique_safe_endpoint.py
    2. 当日分の行があれば消す (再実行のため):
       psql "$DATABASE_URL" -c "DELETE FROM daily_bonuses WHERE user_id = 1;"
    3. このスクリプトを起動: python exercises/ch10/step4_concurrent_test.py

期待結果:
    step3 が起動中: [(200, ...), (400, ...)]   (片方だけ通る = 期待挙動)
    step2 が起動中: [(200, ...), (200, ...)]   (両方通る = TOCTTOU バグ顕在化)

注意:
    step2 でバグが再現しないこともある (タイミング次第)。
    DB に少し負荷をかけて並行性を出すため、 投入回数を増やすと再現しやすい。
"""
import json
import sys
import threading
import urllib.error
import urllib.request

URL = "http://127.0.0.1:8001/api/daily/claim"
TOKEN = "1"   # step1〜3 と同じく user_id=1 を Bearer に流用


def fire(results: list) -> None:
    req = urllib.request.Request(
        URL,
        method="POST",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            results.append((r.status, r.read().decode("utf-8")))
    except urllib.error.HTTPError as e:
        results.append((e.code, e.read().decode("utf-8")))


def main() -> int:
    results: list = []
    threads = [threading.Thread(target=fire, args=(results,)) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(json.dumps(results, ensure_ascii=False, indent=2))

    statuses = sorted(s for s, _ in results)
    if statuses == [200, 400]:
        print("OK: 片方が成功 / 片方が拒否 (UNIQUE 制約が機能している)")
        return 0
    if statuses == [200, 200]:
        print("BUG: 両方とも 200 を返した = TOCTTOU が発火している (step2 を直しましょう)")
        return 1
    print(f"UNEXPECTED: statuses={statuses}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
