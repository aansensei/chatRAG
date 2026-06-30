# presentation/api/chat

RAG chat routes for Ciel. Wraps `stream_ask` from
`app/application/retrieval/ask_question.py` and exposes it as SSE.

---

## Endpoints

### `POST /chat`

Main RAG endpoint. Returns SSE stream.

Request body:
```json
{
  "question": "Tóm tắt Cam7 test 2 writing task 2",
  "collections": ["IELTS"],
  "hybrid": false,
  "model": "gemma3:12b",
  "api_key": "gsk_...",
  "history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

| Field | Type | Notes |
|---|---|---|
| `question` | string | Required |
| `collections` | string[] \| null | null = search all folders |
| `hybrid` | bool | Blend KB with general knowledge when KB empty |
| `model` | string | Ollama model name OR Groq model id |
| `api_key` | string \| null | Required when `model` is a Groq model |
| `history` | message[] \| null | Last 6 messages for multi-turn context |

If the request has a valid `X-API-Key` header, `collections` is overridden by
the key's allowed list (see `presentation/api/auth`).

### `GET /chat/suggestions?collections=foo,bar`

Returns 4 starter prompts based on filenames in the given folders.
Deterministic, no LLM call.

---

## SSE event types

| Event | Payload | Meaning |
|---|---|---|
| `step` | `{step: "embedding" \| "searching" \| "filtering" \| "generating"}` | Pipeline progress for UI spinner |
| `sources` | `{sources: Source[]}` | Retrieved chunks (sent once before tokens) |
| `token` | `{token: string}` | One LLM token |
| `done` | `{sources?: Source[], answer?: string}` | End of stream. `answer` is used for non-LLM final messages like "file not found" |

`Source` shape:
```ts
{
  id: string,
  content: string,        // first 200 chars of chunk
  section: string | null,
  similarity: number,     // 0..1, rounded to 3 decimals
  filename: string,
  document_id: string,
}
```
