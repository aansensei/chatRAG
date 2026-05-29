## infrastructure/llm

LLM client implementations.

### Files

`ollama.py` - client gọi Ollama local LLM server. Nhận context string + câu hỏi, trả về response stream. Dùng trong `application/retrieval/ask_question.py`.
