-- Migration: all-MiniLM-L6-v2 (384 dims) → BAAI/bge-m3 (1024 dims)
-- Run in Supabase SQL editor BEFORE running scripts/migrate_to_bge_m3.py

-- Step 1: drop existing vector index (required before changing column type)
DROP INDEX IF EXISTS chunks_embedding_idx;

-- Step 2: change embedding column dimension
ALTER TABLE chunks
  ALTER COLUMN embedding TYPE vector(1024)
  USING NULL;

-- Step 3: recreate IVFFlat index for 1024-dim vectors
CREATE INDEX chunks_embedding_idx
  ON chunks USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- Step 4: replace match_chunks function for 1024 dims
CREATE OR REPLACE FUNCTION match_chunks(
  query_embedding vector(1024),
  match_threshold float,
  match_count int,
  filter_collections text[] DEFAULT NULL
)
RETURNS TABLE (
  id uuid,
  document_id uuid,
  content text,
  section_title text,
  chunk_index int,
  token_count int,
  metadata jsonb,
  collection text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    c.id,
    c.document_id,
    c.content,
    c.section_title,
    c.chunk_index,
    c.token_count,
    c.metadata,
    c.collection,
    1 - (c.embedding <=> query_embedding) AS similarity
  FROM chunks c
  WHERE
    1 - (c.embedding <=> query_embedding) > match_threshold
    AND (filter_collections IS NULL OR c.collection = ANY(filter_collections))
  ORDER BY c.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
