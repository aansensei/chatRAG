"""
Re-embed all chunks in Supabase using BAAI/bge-m3 (1024 dims).

Run AFTER executing migration_bge_m3.sql in Supabase SQL editor.

Usage:
    cd backend
    python scripts/migrate_to_bge_m3.py
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv()

from sentence_transformers import SentenceTransformer
from supabase import create_client

MODEL_NAME = "BAAI/bge-m3"
BATCH_SIZE = 32


def main():
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_KEY"]
    client = create_client(url, key)

    print(f"Loading model {MODEL_NAME} (first run downloads ~2GB)...")
    model = SentenceTransformer(MODEL_NAME)
    print("Model loaded.")

    print("Fetching all chunks from Supabase...")
    rows = client.table("chunks").select("id, content").limit(100000).execute().data or []
    print(f"Found {len(rows)} chunks to re-embed.")

    if not rows:
        print("Nothing to do.")
        return

    updated = 0
    errors = 0
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        texts = [r["content"] for r in batch]
        try:
            vectors = model.encode(texts, batch_size=BATCH_SIZE, show_progress_bar=False)
            for row, vec in zip(batch, vectors):
                client.table("chunks").update({"embedding": vec.tolist()}).eq("id", row["id"]).execute()
                updated += 1
        except Exception as e:
            print(f"  ERROR batch {i//BATCH_SIZE}: {e}")
            errors += len(batch)
            continue

        done = min(i + BATCH_SIZE, len(rows))
        pct = done / len(rows) * 100
        print(f"  {done}/{len(rows)} ({pct:.1f}%) — {updated} updated, {errors} errors")

    print(f"\nDone. {updated} chunks re-embedded with {MODEL_NAME}.")
    if errors:
        print(f"WARNING: {errors} chunks failed — re-run script to retry.")


if __name__ == "__main__":
    main()
