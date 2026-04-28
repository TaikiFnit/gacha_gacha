"""ch15 / step 1 — JSON 構造化ロガー。

ゴール:
    print の代わりに logging を使い、 1 ログ = 1 行 JSON で出す。
    extra={"ctx_key": value} で文脈を付ける慣習を作る。

実行:
    python exercises/ch15/step1_json_logger.py
"""
import json
import logging
import sys
import time


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        for k, v in record.__dict__.items():
            if k.startswith("ctx_"):
                payload[k[4:]] = v
        return json.dumps(payload, ensure_ascii=False, default=str)


def setup_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    # 既存ハンドラがある場合の重複出力を防ぐ
    for h in list(root.handlers):
        root.removeHandler(h)
    root.addHandler(handler)
    root.setLevel(level)


def main():
    setup_logging()
    log = logging.getLogger("gacha")
    log.info("server boot", extra={"ctx_port": 8000, "ctx_pid": 12345})
    log.warning("low coins", extra={"ctx_user_id": 1, "ctx_coins": 5})
    try:
        1 / 0
    except ZeroDivisionError:
        log.exception("boom", extra={"ctx_where": "demo"})


if __name__ == "__main__":
    main()
