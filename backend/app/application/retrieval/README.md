## application/retrieval

Use cases for the RAG retrieval pipeline.

### Files

`ask_question.py` - the main RAG flow: embed the question → search for relevant chunks in the vector DB → build context from chunks → call the LLM with context → stream response back. Document-level permission check happens before the vector search.
