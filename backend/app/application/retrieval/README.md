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
  |   1. query rewriting                    follow-up resolved to a standalone
  |                                          query against `history` before embedding
  |   2. embed(question)                     multilingual-e5-base (BGE-M3), plus
  |                                          HyDE + multi-query expansion
  |   3. extract_filename_tokens(question)   returns (tokens, has_strong)
  |        strong tokens = underscore-joined ("14_BangLuong_T12_2025")
  |                       or alphanumeric codes ("Cam7", "N5", "NASA")
  |   4. filename_search_chunks              tries longest token first,
  |                                          stops at first hit
  |        if strong tokens + no match -> "file not found" early-return
  |        (fires even in hybrid mode)
  |        skips tokens matching >3 distinct documents — too generic to
  |        trust as a fast path (bypasses ranking otherwise)
  |   5. search_chunks (hybrid BM25 + pgvector cosine, RRF fusion)
  |                                          supplemented with accent-stripped
  |                                          query if Vietnamese
  |   6. keyword_search_chunks (ilike)       skipped when filename hit found
  |   7. detect tabular chunks ("  |  " separator from CSV/XLSX)
  |   8. _bge_rerank cross-encoder + fetch_context_windows (parent-child
  |      expansion) — skipped for the filename/tabular fast paths
  |   9. GraphRAG block (_format_graph_block) appended as supplementary
  |      context — not yet fused into the ranking/scoring itself
  |
  | answer:
  |   if filename_doc_ids or has_tabular:
  |        skip LLM filter (avoids false negatives on tables)
  |        use directive prompt: "Summarize this. Do NOT say no info."
  |   else:
  |        _llm_filter_chunks drops irrelevant chunks
  |        use _SYSTEM_VI / _SYSTEM_EN
  |
  |   stream LLM tokens, then emit sources event (each source carries the
  |   originating PDF page number, so citations jump to the exact page)
  |   query + result metadata logged to storage/metrics.jsonl for audit
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

Query rewriting resolves follow-ups against `history` into a standalone
query before embedding — so "đề bài hỏi gì?" after a message about "Cam7"
recovers the filename context instead of embedding the bare follow-up.

---

## LLM backends

| Backend | Trigger | Notes |
|---|---|---|
| Ollama | `api_key` empty or doesn't start with `gsk_` | Streams via `/api/generate` |
| Groq | `api_key` starts with `gsk_` | Streams via OpenAI-compatible `/v1/chat/completions` |

Default Ollama model: `gemma3:4b` (override with `OLLAMA_MODEL` env var).
Frontend currently defaults to `gemma3:12b` for better quality.
