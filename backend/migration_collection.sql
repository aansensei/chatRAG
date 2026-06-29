-- 1. Add collection column
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS collection TEXT NOT NULL DEFAULT 'default';
CREATE INDEX IF NOT EXISTS idx_chunks_collection ON chunks(collection);

-- 2. Update match_chunks to filter by collection
CREATE OR REPLACE FUNCTION match_chunks(
  query_embedding vector(384),
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
