"""YOUR mitigation + observability layer."""
from __future__ import annotations
import time
import re
from telemetry.logger import logger

_TOTAL_RE    = re.compile(r'Tong cong\s*:\s*([\d\.,]+)\s*VND', re.IGNORECASE)
_NUMBER_RE   = re.compile(r'\b(\d[\d\.]{4,})\b')
_EMAIL_RE    = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
_PHONE_RE    = re.compile(r'\b\d{4}[\s.-]?\d{3}[\s.-]?\d{3}\b')
_INJECT_RE   = re.compile(r'(?i)(GHI\s*CH[UÚ]|Notes?)\s*:.+', re.DOTALL)
_REFUSE_KEYS = ['het hang', 'hết hàng', 'khong the', 'không thể',
                'khong ton tai', 'không tồn tại', 'khong phuc vu',
                'không phục vụ', 'khong giao', 'không giao',
                'out of stock', 'not found', 'cannot']


def _redact(text: str) -> str:
    if not text:
        return text
    text = _EMAIL_RE.sub('[REDACTED]', text)
    text = _PHONE_RE.sub('[REDACTED]', text)
    return text


def _sanitize_question(question: str) -> str:
    """Strip prompt-injection payloads from order notes."""
    return _INJECT_RE.sub('', question).strip()


def _is_refusal(text: str) -> bool:
    low = text.lower()
    return any(k in low for k in _REFUSE_KEYS)


def _fix_format(ans: str) -> str:
    """
    If answer has a number but missing 'Tong cong: X VND',
    extract the last large integer and append the correct line.
    """
    if not ans or not ans.strip():
        return ans
    # Already has correct format
    if _TOTAL_RE.search(ans):
        return ans
    # True refusal - don't add total
    if _is_refusal(ans):
        return ans
    # Look for a number (last occurrence = most likely the total)
    # Only numbers >= 10000 (VND amounts)
    nums = [m.group(1) for m in _NUMBER_RE.finditer(ans)]
    big_nums = [n.replace('.', '').replace(',', '') for n in nums
                if len(n.replace('.', '').replace(',', '')) >= 5]
    if big_nums:
        total = big_nums[-1]  # last big number = most likely the final total
        ans = ans.rstrip() + f'\nTong cong: {total} VND'
    return ans


def mitigate(call_next, question, config, context):
    t0 = time.time()
    safe_q = _sanitize_question(question)

    result = None
    max_retries = 3

    for attempt in range(max_retries):
        try:
            result = call_next(safe_q, config)
            ans = (result.get('answer') or '').strip()

            # Retry if empty answer and not final attempt
            if not ans and attempt < max_retries - 1:
                logger.log_event('RETRY', {
                    'qid': context.get('qid'),
                    'attempt': attempt,
                    'reason': 'empty_answer'
                })
                time.sleep(0.5)
                continue
            break

        except Exception:
            import traceback
            with open('wrapper_crash.txt', 'a') as f:
                f.write(traceback.format_exc() + '\n')
            if attempt == max_retries - 1:
                raise
            time.sleep(1.0)

    if result is None:
        raise RuntimeError('All retries exhausted')

    # OBSERVABILITY
    meta = result.get('meta') or {}
    logger.log_event('CALL', {
        'qid': context.get('qid'),
        'wall_ms': int((time.time() - t0) * 1000),
        'latency_ms': meta.get('latency_ms'),
        'usage': meta.get('usage'),
        'tools': meta.get('tools_used'),
        'steps': result.get('steps'),
        'status': result.get('status'),
    })

    # PII REDACTION
    ans = result.get('answer')
    if ans and isinstance(ans, str):
        ans = _redact(ans)
        # AUTO-FIX FORMAT: add Tong cong line if missing
        ans = _fix_format(ans)
        result['answer'] = ans

    return result
