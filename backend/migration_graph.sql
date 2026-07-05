-- GraphRAG POC: lightweight entity/relationship graph scoped by collection.
-- Run in Supabase SQL editor before using scripts/build_graph.py.

CREATE TABLE IF NOT EXISTS graph_entities (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  collection text NOT NULL,
  name text NOT NULL,
  type text NOT NULL,
  description text,
  created_at timestamptz DEFAULT now(),
  UNIQUE (collection, name)
);

CREATE TABLE IF NOT EXISTS graph_relations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  collection text NOT NULL,
  source_entity_id uuid NOT NULL REFERENCES graph_entities(id) ON DELETE CASCADE,
  target_entity_id uuid NOT NULL REFERENCES graph_entities(id) ON DELETE CASCADE,
  relation text NOT NULL,
  description text,
  chunk_id uuid REFERENCES chunks(id) ON DELETE SET NULL,
  created_at timestamptz DEFAULT now(),
  UNIQUE (source_entity_id, target_entity_id, relation, chunk_id)
);

CREATE INDEX IF NOT EXISTS idx_graph_entities_collection ON graph_entities(collection);
CREATE INDEX IF NOT EXISTS idx_graph_relations_collection ON graph_relations(collection);
CREATE INDEX IF NOT EXISTS idx_graph_relations_source ON graph_relations(source_entity_id);
CREATE INDEX IF NOT EXISTS idx_graph_relations_target ON graph_relations(target_entity_id);
