# Qwen API Guide

## Dùng để làm gì?

Qwen là model LLM dùng để viết câu trả lời cuối cùng cho chatbot.

Trong project này:

```text
retrieved context -> Qwen -> answer có citation
```

Qwen dùng OpenAI-compatible API, nên mình gọi bằng `OpenAI` SDK.

## Biến trong `.env`

Cần có:

```env
QWEN_API_KEY=your_qwen_api_key
QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
QWEN_MODEL_NAME=your_model_name
```

Rule quan trọng:

- Không hard-code API key.
- Không hard-code base URL.
- Không hard-code model name.
- Luôn đọc từ `.env`.
- Không viết `os.getenv("")`.

## Code mẫu đơn giản

```python
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

api_key = os.getenv("QWEN_API_KEY")
base_url = os.getenv("QWEN_BASE_URL")
model_name = os.getenv("QWEN_MODEL_NAME")

if not api_key:
    raise ValueError("Missing QWEN_API_KEY in .env")
if not base_url:
    raise ValueError("Missing QWEN_BASE_URL in .env")
if not model_name:
    raise ValueError("Missing QWEN_MODEL_NAME in .env")

client = OpenAI(api_key=api_key, base_url=base_url)

response = client.chat.completions.create(
    model=model_name,
    messages=[
        {"role": "user", "content": "Reply only: Qwen connection successful"}
    ],
)

print(response.choices[0].message.content)
```

## Cách dùng trong RAG

Qwen không nên tự đoán. Hãy đưa context vào prompt.

Prompt nên có dạng:

```text
Question:
{question}

Context:
{retrieved_context}

Rules:
- Chỉ trả lời dựa trên context.
- Mỗi ý quan trọng phải có citation [Source, Year].
- Nếu không đủ bằng chứng, trả lời: I cannot verify this information.
```

## Output mong muốn

Nên return dict:

```python
{
    "answer": "Câu trả lời có citation [Source, Year]",
    "sources": [...]
}
```

## Prompt mẫu cho Codex

```text
Đọc group_project/docs/qwen-api.md.
Viết group_project/src/qwen_client.py.
Yêu cầu:
- đọc QWEN_API_KEY, QWEN_BASE_URL, QWEN_MODEL_NAME từ .env
- dùng OpenAI SDK
- viết function generate_answer(question, contexts)
- answer phải có citation [Source, Year]
- nếu thiếu evidence thì trả "I cannot verify this information"
- không hard-code secret
```