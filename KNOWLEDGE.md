## 🎯 Tổng quan

> *"Agent bạn deploy hôm Day 12 chạy ngon. 3 ngày sau: latency tăng gấp đôi, cost tăng 300%, 1/20 câu trả lời là bịa. Bạn biết khi nào? — Khi user phàn nàn. Đó là cách tệ nhất để phát hiện vấn đề."*

---

## 1. Vì sao cần Observability?

**Monitoring** (theo dõi câu hỏi đã biết trước) khác với **Observability** (thuộc tính của hệ thống — có thể hỏi câu hỏi mới mà không cần deploy lại code).

AI khác phần mềm truyền thống vì:
- Cùng input nhưng output khác nhau → không thể test bằng "so sánh string"
- App vẫn trả `200 OK` nhưng câu trả lời ngày càng tệ — không có exception để bắt
- Mỗi request tốn tiền theo token → một bug loop có thể đốt budget trong vài giờ
- Có các lỗi đặc thù như: hallucinated tool args, vòng lặp vô tận, context overflow

---

## 2. 4 Pillars of Observability

| Pillar | Trả lời câu hỏi | Ví dụ công cụ |
|--------|----------------|---------------|
| **Metrics** | Bao nhiêu? Bao lâu? | Prometheus, Grafana |
| **Logs** | Gì xảy ra? | Loki, JSON logs |
| **Traces** | Tại sao? Chậm ở đâu? | Langfuse, Tempo |
| **Continuous Eval** (Pillar 4 — đặc thù AI) | Câu trả lời còn đúng không? | LLM-judge, RAGAS |

> "Logs = camera an ninh. Metrics = bảng điều khiển xe. Traces = bản đồ GPS. Eval = người kiểm định chất lượng."

---

## 3. AI-Specific Metrics

**6 Golden Signals** (4 của Google SRE + 2 cho AI):

- Latency (P50/P95/P99 + **TTFT** — Time To First Token)
- Traffic (request rate)
- Errors (theo taxonomy: LLM 5xx, timeout, tool fail, guardrail block, context overflow...)
- Saturation
- **Cost** ($/request, token in/out, cost/feature/user) — output đắt hơn input **5–6x**
- **Quality** (hallucination rate, task completion rate, thumbs up/down)

> P99 quan trọng hơn average: nếu P99 = 5s và user chat 10 lượt, xác suất gặp lag tệ là ~9.6%. Với 1.000 user/ngày → 96 người bức xúc, họ là người tweet tiêu cực và rời bỏ.

---

## 4. Structured Logging

Thay vì log text thô, dùng **JSON có cấu trúc**:

```json
{
  "ts": "2026-03-18T10:23:45Z", "level": "INFO",
  "correlation_id": "req-abc123", "event": "agent_response",
  "latency_ms": 1250, "input_tokens": 640, "output_tokens": 250,
  "cost_usd": 0.0057, "model": "claude-sonnet-4-6"
}
```

**Nên log:** input đã sanitize, output summary, tool calls, latency/tokens/cost, correlation ID.  
**KHÔNG log:** PII (tên, SĐT, CCCD), raw prompts chứa data nhạy cảm, API keys.

**Correlation ID** nối mọi log của 1 request xuyên nhiều service — là mầm của `trace_id`.

**Log sampling:** 100% ERROR + WARN · 10% INFO · 1% DEBUG. Giữ 100% errors là non-negotiable.

---

## 5. Distributed Tracing

**Trace** = toàn bộ hành trình end-to-end của 1 request. **Span** = 1 đơn vị công việc trong trace (có parent-child).

**OpenTelemetry (OTel)** là chuẩn mở vendor-neutral: instrument code 1 lần → gửi tới bất kỳ backend nào (không bị lock-in).

4 bottleneck patterns khi đọc trace:
- **Sequential chain** (A→B→C tuần tự) → parallelize nếu không phụ thuộc nhau
- **I/O wait** (span dài nhưng CPU idle) → parallelize, cache, timeout
- **N+1** (nhiều span ngắn cùng tên lặp lại) → batch/pre-fetch
- **Retry storm** (nhiều retry trong 1 trace) → exponential backoff + circuit breaker

---

## 6. Bộ Công Cụ LLM-Observability 2026

| Tool | Loại | Mạnh ở |
|------|------|--------|
| **Langfuse** | OSS (MIT), self-host + cloud | Tracing, cost, prompt mgmt, eval |
| **LangSmith** | SaaS | Eval sâu, trajectory, prompt hub |
| **Phoenix (Arize)** | OSS self-host | Tracing + eval, notebook→prod |
| **OpenLLMetry** | OTel auto-instrument | Vendor-neutral, mọi backend |
| **LiteLLM** | LLM Gateway | Cost nhiều provider, rate-limit |

Khuyến nghị: MVP → **Langfuse free tier**; đã dùng LangChain → **LangSmith**; không muốn lock-in → **OTel/OpenLLMetry**.

---

## 7. Production Stack: Prometheus + Grafana + OTel

```
AI Service → OTel Collector → Prometheus (metrics) → Grafana (dashboard)
                            → Loki (logs)
                            → Tempo (traces) + Langfuse (LLM UI)
```

Lưu ý về **label cardinality**: tránh dùng `user_id`, `request_id` làm label Prometheus — sẽ nổ số time-series (Coinbase từng nhận bill $65M vì lý do này).

---

## 8. Dashboard Design — 3 Layers

- **Layer 1 (Overview):** Health, uptime, key alerts → cho Leadership
- **Layer 2 (Detail):** Latency, cost, error rate, tokens → cho Engineering
- **Layer 3 (Drill-down):** Traces, log search, root cause → cho Debugging

**6 panel bắt buộc cho AI service:** Request rate · Latency P50/P95/P99 + TTFT · Error rate · Cost/token usage · Tool-call success rate · Quality/eval score.

---

## 9. Alerting & SLO

**SLI** (con số đo) → **SLO** (mục tiêu, ví dụ: 99.9% request < 5s/tháng) → **SLA** (hợp đồng có hậu quả pháp lý).

**Error budget** = (1 − SLO) × cửa sổ thời gian. Còn budget → ship nhanh; hết budget → đóng băng, ưu tiên ổn định.

Alert phải **symptom-based** (dựa trên điều user cảm nhận), không phải cause-based ("CPU 80%"). Alert không có runbook = alert không thể xử lý lúc 3h sáng.

---

## 10. Cost Monitoring & Optimization

4 chiến lược giảm cost:
1. **Right-size model** — dùng model nhỏ nhất đủ tốt (Haiku rẻ hơn Opus 5x)
2. **Semantic cache** — câu hỏi tương tự → trả lời từ cache (~70% hit, giảm cost ~70%)
3. **Prompt optimization** — bớt few-shot thừa, tóm tắt lịch sử, RAG top-k nhỏ
4. **Prompt cache (prefix)** — Anthropic: cache read = 0.1x giá input (rẻ hơn 90%)

**Cost attribution** phải gắn: `user_id` + `feature` + `model` vào mọi LLM call.

---

## 11. Debug Incident Bằng Trace

Quy trình chuẩn: **Metric → Log → Trace**
- Metric: khoanh vùng vấn đề và thời điểm
- Log: lọc theo correlation_id để tìm request bị ảnh hưởng
- Trace: mở span tree, xác định bước nào chậm/lỗi

> Case study: P95 latency tăng từ 2.5s → 5s từ 9h sáng. Mở trace → `rag_retrieve` chậm 4.6x (từ 600ms → 2800ms). Root cause: một index filter của vector store bị bỏ trong deploy 8h45.

---

## 12. Human Feedback & Online Eval

**Offline eval** (Day 14): test set cố định, chạy trước khi ship.  
**Online eval** (Day 13): traffic thật, chạy liên tục, bắt suy thoái & drift.

Loop: Sample 1% production → LLM-judge/RAGAS → Gauge metric → Alert khi tụt → Dataset cải thiện → Lặp lại.

---

## 13. Privacy & Compliance Khi Logging

- **Redact PII tại điểm phát sinh** (tên, SĐT, CCCD, bệnh án) — dùng Microsoft Presidio
- **Việt Nam PDPL (Luật 91/2025, hiệu lực 1/1/2026):** báo cáo vi phạm trong **72 giờ**; chuyển dữ liệu xuyên biên giới cần TIA; phạt tới **5% doanh thu**
- Gửi log chứa PII sang SaaS nước ngoài (Datadog, LangSmith) = chuyển dữ liệu xuyên biên giới

---

## 7 Anti-patterns Cần Tránh

1. *"We'll add monitoring later"* — later = never
2. Log full prompts/responses — vi phạm pháp lý + bill nổ
3. Alert trên mọi thứ → alert fatigue → bỏ qua alert thật
4. Không có runbook kèm theo alert
5. Config monitoring dev ≠ prod
6. Chỉ đo performance, quên cost
7. Tin vendor telemetry mặc định mà không đọc docs

---

## ✅ Deliverable Cuối Ngày (Lab #13)

- Structured logging: JSON + correlation ID + PII redaction
- ≥ 10 traces gửi tới Langfuse (hoặc backend offline)
- Dashboard: latency P50/95/99 + TTFT, cost/ngày, error rate, token usage, tool-call success
- ≥ 3 alert rules → Slack + 1 SLO + error budget
- 1 incident note đọc từ trace thật (metric → log → trace)