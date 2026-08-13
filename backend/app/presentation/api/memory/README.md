# presentation/api/memory

Per-user persistent memory (ChatGPT-memory-style) — short facts Ciel
remembers about a user across separate conversations, independent of the
6-message chat history window. Mounted at `/memory`, requires login.

Storage: single flat JSON file (`storage/memory.json`), every memory row
carries a `user_id` so entries are scoped per user even though they share
one file. `migrate_legacy_memories()` backfills `user_id` onto memories
created before per-user scoping existed.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/memory` | List the caller's memories |
| POST | `/memory` | Add a memory (`{content: string}`, max 3000 words) |
| DELETE | `/memory/{id}` | Remove one memory |

## Auto-extraction

`add_memory_internal()` is called from the retrieval pipeline
(`ask_question.py`) to auto-save facts noticed during a conversation —
skips duplicates (case-insensitive exact match) per user. Rows added this
way are flagged `"auto": true`.
