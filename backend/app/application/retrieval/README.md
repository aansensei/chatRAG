## application/retrieval

Use cases cho RAG retrieval pipeline.

### Files

`ask_question.py` - luồng chính của RAG: embed câu hỏi → tìm chunks liên quan từ vector DB → build context từ chunks → gọi LLM với context → stream response về. Document-level permission check xảy ra trước khi search.
