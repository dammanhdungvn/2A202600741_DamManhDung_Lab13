"""YOUR mitigation + observability layer."""
from __future__ import annotations
import time
import re
from telemetry.logger import logger

def mitigate(call_next, question, config, context):
    try:
        t0 = time.time()
        
        # 1. SANITIZATION: Injection Defense
        safe_question = re.sub(r'(?i)(GHI CHÚ|Ghi ch\u00fa|Notes?):.*', '', question, flags=re.DOTALL)
        
        # 2. RUN LLM
        result = call_next(safe_question, config)
        
        # 3. OBSERVABILITY
        meta = result.get("meta") or {}
        logger.log_event("CALL", {
            "qid": context.get("qid"),
            "wall_ms": int((time.time() - t0) * 1000),
            "latency_ms": meta.get("latency_ms"),
            "usage": meta.get("usage"),
            "tools": meta.get("tools_used"),
            "steps": result.get("steps"),
            "status": result.get("status")
        })
        
        # 4. FALLBACK PII REDACTION
        ans = result.get("answer")
        if ans and isinstance(ans, str):
            ans = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[REDACTED]', ans)
            ans = re.sub(r'\b\d{4}[\s.-]?\d{3}[\s.-]?\d{3}\b', '[REDACTED]', ans)
            result["answer"] = ans
            
        return result
    except Exception as e:
        import traceback
        with open("wrapper_crash.txt", "a") as f:
            f.write(traceback.format_exc() + "\n")
        raise

