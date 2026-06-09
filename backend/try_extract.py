"""
Manual test: extract a real file and print the result.
Usage: python try_extract.py <file_path>
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.shared.utils.extractors import extract
from app.shared.utils.chunkers import chunk_text, ChunkConfig
from uuid import uuid4

if len(sys.argv) < 2:
    print("Usage: python try_extract.py <file_path>")
    sys.exit(1)

file_path = sys.argv[1]

print(f"\nFile   : {file_path}")
print(f"{'='*60}")

result = extract(file_path, image_output_dir="extracted_images")

print(f"Text   : {len(result.text)} chars")
print(f"Tables : {len(result.tables)}")
print(f"Images : {len(result.images)}")
print(f"Meta   : {result.metadata}")

print(f"\n--- Text preview (first 500 chars) ---")
print(result.text[:500])

if result.tables:
    print(f"\n--- Tables ---")
    for t in result.tables:
        print(json.dumps(t, ensure_ascii=False, indent=2, default=str))

if result.images:
    print(f"\n--- Images saved ---")
    for p in result.images:
        print(f"  {p}")

print(f"\n{'='*60}")
print("Chunking...")

chunks = chunk_text(result.text, uuid4(), ChunkConfig(max_tokens=500, overlap_tokens=50))
print(f"Total chunks: {len(chunks)}")
for c in chunks:
    print(f"  [{c.chunk_index}] title={c.section_title!r:30} tokens={c.token_count:4} | {c.content[:60]!r}")
