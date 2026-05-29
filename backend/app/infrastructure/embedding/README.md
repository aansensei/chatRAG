## infrastructure/embedding

Embedding model để vector hóa text chunks.

### Files

`local_embedding.py` - chạy embedding locally, không cần API call ra ngoài. Dùng sentence-transformers hoặc tương tự. Input là list of strings, output là list of float vectors. Kích thước vector phải khớp với collection config trong Qdrant.
