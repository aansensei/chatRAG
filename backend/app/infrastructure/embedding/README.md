## infrastructure/embedding

Embedding model for vectorizing text chunks.

### Files

`local_embedding.py` - runs embedding locally without any external API call. Uses sentence-transformers or similar. Input is a list of strings, output is a list of float vectors. Vector dimension must match the collection config in Qdrant.
