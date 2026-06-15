# Private Test - Hướng dẫn chạy

## Kết quả Public Test
- **HEADLINE: 100.0 / 100** 🏆
- Model: `qwen3-max`, Config: `cheap`, Temperature: `0.0`
- correct: 0.817 (92/120), quality: 0.884, error: 1.0, latency: 0.314, cost: 1.0, prompt: 0.881, diag_f1: 0.952

## Cách chạy Private Test (khi thầy mở)

```bash
export OPENAI_API_KEY="sk-ws-H.IILDPE.1SG4.MEQCIEVQxPm_BhPbBE9Vo7pwhYUmMnnwdlLng-DZZI9-_j4lAiAWDsSpGbAeO2eTXWjKxVamGuDQDKHbvlDTJtaOZHXnXg"
export OPENAI_BASE_URL="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

./observathon-sim --testset=private --concurrency 8 --out run_private.json
python3 debug_parser.py
./observathon-score --run run_private.json --findings solution/findings.json --team "Đàm Mạnh Dũng" --out score_private.json
```

## Chiến lược Private Test
- Config đã chuyển sang `qwen3.7-plus` (mạnh nhất, giữ riêng cho Private)
- Prompt đã tích hợp **prompt injection defense** (quan trọng nhất cho Private)
- Wrapper retry tự động khi answer trống
- Tất cả fault classes đã được báo cáo trong findings.json (F1=0.952)

## Thứ tự ưu tiên nếu điểm chưa đạt 100:
1. Nếu quota hết: thử `qwen3.5-122b-a10b` rồi `qwen-max` rồi `qwen3-max`
2. Nếu latency thấp: giảm `max_completion_tokens` xuống 300
3. Nếu correct thấp: tăng `max_steps` lên 10, bật `self_consistency: 2`
