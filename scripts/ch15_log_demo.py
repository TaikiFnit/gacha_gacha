"""第15章 / 練習: 構造化 JSON ログを試す。

実行:
    python scripts/ch15_log_demo.py
    # → JSON 1 行ずつ stdout に出る。 jq で集計練習にも使える:
    #   python scripts/ch15_log_demo.py | jq 'select(.level=="ERROR")'
"""
import os
import sys

sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "exercises", "ch15"),
)
from step1_json_logger import setup_logging   # noqa: E402

import logging   # noqa: E402

setup_logging()
log = logging.getLogger("demo")

log.info("user login", extra={"ctx_user_id": 42, "ctx_ip": "127.0.0.1"})
log.warning("low coins", extra={"ctx_user_id": 42, "ctx_coins": 3})
try:
    int("not-a-number")
except ValueError:
    log.exception("parse failed", extra={"ctx_input": "not-a-number"})
log.info("session end", extra={"ctx_user_id": 42, "ctx_duration_ms": 1234})
