"""YOUR mitigation + observability layer."""
from __future__ import annotations
import time
import re
import threading
from telemetry.logger import logger

_TOTAL_RE = re.compile(r'Tong cong:\s*(\d[\d,\.]*)\s*VND', re.IGNORECASE)
_EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
_PHONE_RE = re.compile(r'\b\d{4}[\s.-]?\d{3}[\s.-]?\d{3}\b')
_INJECT_RE = re.compile(r'(?i)(GHI\s*CH[UÚ]|Notes?)\s*:.+', re.DOTALL)


def _redact(text: str) -> str:
    if not text:
        return text
    text = _EMAIL_RE.sub('[REDACTED]', text)
    text = _PHONE_RE.sub('[REDACTED]', text)
    return text


def _sanitize_question(question: str) -> str:
    """Strip prompt-injection payloads from order notes."""
    return _INJECT_RE.sub('', question).strip()


def mitigate(call_next, question, config, context):
    t0 = time.time()
    safe_q = _sanitize_question(question)

    result = None
    max_retries = 3

    for attempt in range(max_retries):
        try:
            result = call_next(safe_q, config)
            ans = result.get("answer") or ""

            # If answer is empty and order looks fulfillable, retry once
            if not ans.strip() and attempt < max_retries - 1:
                logger.log_event("RETRY", {
                    "qid": context.get("qid"),
                    "attempt": attempt,
                    "reason": "empty_answer"
                })
                time.sleep(0.5)
                continue

            break
        except Exception as e:
            import traceback
            with open("wrapper_crash.txt", "a") as f:
                f.write(traceback.format_exc() + "\n")
            if attempt == max_retries - 1:
                raise
            time.sleep(1.0)

    if result is None:
        raise RuntimeError("All retries exhausted")

    # OBSERVABILITY
    meta = result.get("meta") or {}
    logger.log_event("CALL", {
        "qid": context.get("qid"),
        "wall_ms": int((time.time() - t0) * 1000),
        "latency_ms": meta.get("latency_ms"),
        "usage": meta.get("usage"),
        "tools": meta.get("tools_used"),
        "steps": result.get("steps"),
        "status": result.get("status"),
        "attempt": max_retries,
    })

    # PII REDACTION
    ans = result.get("answer")
    if ans and isinstance(ans, str):
        result["answer"] = _redact(ans)

    return result
