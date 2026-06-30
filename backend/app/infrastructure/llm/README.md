# infrastructure/llm

LLM client abstraction.

**Not implemented as a layer.** Ollama + Groq HTTP calls are inlined in `app/application/retrieval/ask_question.py` (`_stream_llm`, `_stream_groq`).
