"""
Backfill entities/relationships into graph_entities/graph_relations for one
collection, using an LLM to extract them chunk by chunk.

Run migration_graph.sql in Supabase first.

Usage:
    cd backend
    python scripts/build_graph.py --collection "AanJSC_Documents/Engineering" --limit 5
    python scripts/build_graph.py --collection "AanJSC_Documents/Engineering"
"""
import argparse
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv()

from app.application.graph.extract_graph import extract_entities_relations
from app.infrastructure.vector.supabase.graph_repository import (
    graph_stats,
    insert_relation,
    list_chunks_for_collection,
    upsert_entity,
)

MODEL = "llama-3.3-70b-versatile"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--collection", required=True)
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N chunks (test mode)")
    args = parser.parse_args()

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("GROQ_API_KEY not set in .env — aborting.")
        sys.exit(1)

    chunks = list_chunks_for_collection(args.collection, limit=args.limit)
    print(f"Found {len(chunks)} chunk(s) in '{args.collection}'.")
    if not chunks:
        return

    total_entities = 0
    total_relations = 0
    skipped = 0

    for i, chunk in enumerate(chunks, 1):
        content = chunk.get("content") or ""
        if not content.strip():
            skipped += 1
            continue
        entities, relations = extract_entities_relations(content, MODEL, api_key)
        if not entities:
            skipped += 1
            print(f"  [{i}/{len(chunks)}] chunk {chunk['id'][:8]} — no entities extracted, skipped")
            time.sleep(0.3)
            continue

        name_to_id: dict[str, str] = {}
        for e in entities:
            entity_id = upsert_entity(args.collection, e["name"], e["type"], "")
            name_to_id[e["name"]] = entity_id
            total_entities += 1

        for r in relations:
            src_id = name_to_id.get(r["source"])
            tgt_id = name_to_id.get(r["target"])
            if not src_id or not tgt_id:
                continue
            insert_relation(args.collection, src_id, tgt_id, r["relation"], r["description"], chunk["id"])
            total_relations += 1

        print(f"  [{i}/{len(chunks)}] chunk {chunk['id'][:8]} — {len(entities)} entities, {len(relations)} relations")
        time.sleep(0.3)  # stay well under Groq rate limits

    stats = graph_stats(args.collection)
    print(f"\nDone. This run: {total_entities} entity upserts, {total_relations} relation upserts, {skipped} chunks skipped.")
    print(f"Graph totals for '{args.collection}': {stats['entities']} entities, {stats['relations']} relations.")


if __name__ == "__main__":
    main()
