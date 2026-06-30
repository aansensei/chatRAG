# application/retrieval

Use cases for the RAG retrieval pipeline. `ask_question.py` is the single
entry point — everything below describes one function: `stream_ask`.

---

## Files

| File | Purpose |
|---|---|
| `ask_question.py` | Full pipeline: intercepts -> filename search -> vector -> keyword -> filter -> LLM stream |

---

## Pipeline

```
stream_ask(question, collections, hybrid, model, api_key, history)
  |
  | language detection (vi / en / ja)
  | format history (last 4 turns, capped at 1500 chars)
  |
  +--> is_wakeup_query?    -> random greeting (typewriter), done
  +--> is_identity_query?  -> identity system prompt -> LLM, done
  +--> is_rag_query?       -> RAG-explainer system prompt -> LLM, done
  |
  | retrieval:
  |   1. embed(question)                     multilingual-e5-base
  |   2. extract_filename_tokens(question)   returns (tokens, has_strong)
  |        strong tokens = underscore-joined ("14_BangLuong_T12_2025")
  |                       or alphanumeric codes ("Cam7", "N5", "NASA")
  |   3. filename_search_chunks              tries longest token first,
  |                                          stops at first hit
  |        if strong tokens + no match -> "file not found" early-return
  |        (fires even in hybrid mode)
  |   4. search_chunks (pgvector cosine)     supplemented with accent-stripped
  |                                          query if Vietnamese
  |   5. keyword_search_chunks (ilike)       skipped when filename hit found
  |   6. detect tabular chunks ("  |  " separator from CSV/XLSX)
  |
  | answer:
  |   if filename_doc_ids or has_tabular:
  |        skip LLM filter (avoids false negatives on tables)
  |        use directive prompt: "Summarize this. Do NOT say no info."
  |   else:
  |        _llm_filter_chunks drops irrelevant chunks
  |        use _SYSTEM_VI / _SYSTEM_EN
  |
  |   stream LLM tokens, then emit sources event
```

---

## Intercepts (before retrieval)

| Intent | Trigger examples | Behavior |
|---|---|---|
| Wake-up | `ciel ơi`, `hey ciel`, `シエルさん` | Random greeting from `_GREETINGS_*`, typewriter, no LLM |
| Identity | `bạn là ai`, `who are you`, `/help`, `ciel có tạo ảnh không` | `_IDENTITY_SYSTEM_*` -> LLM |
| RAG explainer | `rag là gì`, `what is rag`, `chatrag là gì` | `_RAG_SYSTEM_*` -> LLM |

---

## System prompts

| Prompt | When used |
|---|---|
| `_CIEL_IDENTITY` | Prefix for identity/RAG/general prompts. Says "you are Ciel, no emoji, do not introduce yourself unless asked." |
| `_SYSTEM_VI` / `_SYSTEM_EN` | Default RAG prompt. Has "secondary rule": fall back to general knowledge if context irrelevant. |
| Directive prompt (inline) | Used when filename match found OR chunks contain tables. Forbids "no information" responses, forbids self-introduction. |
| `_IDENTITY_SYSTEM_*` | For identity queries — specific feature questions answered with yes/no. |
| Hybrid fallback | Used when no chunks found AND `hybrid=True`. Notes answer is from general knowledge. |

---

## LLM relevance filter

`_llm_filter_chunks` asks the LLM to return the indexes of chunks that genuinely
answer the question. Skipped when:

- `filename_doc_ids` is non-empty (high-confidence file match)
- Top chunks contain `  |  ` (tabular data — filter often misreads numbers)

If the filter returns nothing, the original chunk list is kept (fail-open).

---

## Conversation history

`history` is `list[{role, content}]` of up to last 6 messages. `_format_history`
prepends them to the user prompt as `Người dùng: ... / Ciel: ...` lines.

Each message is capped at 400 chars; total block capped at 1500 chars.
This unlocks follow-ups like "nó là gì", "thêm chi tiết", "ngắn hơn nữa".

Note: history is currently NOT used to rewrite the embedding query, so
queries like "đề bài hỏi gì?" won't recover the previous filename
("Cam7"). Query rewriting is a planned improvement.

---

## LLM backends

| Backend | Trigger | Notes |
|---|---|---|
| Ollama | `api_key` empty or doesn't start with `gsk_` | Streams via `/api/generate` |
| Groq | `api_key` starts with `gsk_` | Streams via OpenAI-compatible `/v1/chat/completions` |

Default Ollama model: `gemma3:4b` (override with `OLLAMA_MODEL` env var).
Frontend currently defaults to `gemma3:12b` for better quality.
