"""
Edge-case tests for text_chunker.
Run: python tests/test_chunker.py
"""
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.shared.utils.chunkers import chunk_text, ChunkConfig

DOC_ID = uuid4()
PASS = "[PASS]"
FAIL = "[FAIL]"

results = []


def test(name, fn):
    try:
        fn()
        print(f"  {PASS} {name}")
        results.append((name, True, None))
    except Exception as e:
        print(f"  {FAIL} {name}")
        print(f"       {type(e).__name__}: {e}")
        results.append((name, False, e))


def section(title):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print(f"{'='*55}")


# helper to build a text that exceeds max_tokens
def _long_text(word: str = "word", count: int = 600) -> str:
    return " ".join([word] * count)


section("Basic behavior")


def t_empty_text():
    chunks = chunk_text("", DOC_ID)
    assert chunks == [], f"expected [], got {chunks}"


def t_whitespace_only():
    chunks = chunk_text("   \n\n   ", DOC_ID)
    assert chunks == []


def t_short_text_no_heading():
    chunks = chunk_text("Simple short text.", DOC_ID)
    assert len(chunks) == 1
    assert chunks[0].section_title is None
    assert chunks[0].chunk_index == 0
    assert "Simple short text." in chunks[0].content


def t_chunk_index_sequential():
    text = "# A\nbody a\n\n# B\nbody b\n\n# C\nbody c"
    chunks = chunk_text(text, DOC_ID)
    indexes = [c.chunk_index for c in chunks]
    assert indexes == list(range(len(chunks))), f"indexes not sequential: {indexes}"


def t_token_and_char_count_populated():
    chunks = chunk_text("Hello world this is a test.", DOC_ID)
    assert all(c.token_count > 0 for c in chunks)
    assert all(c.char_count > 0 for c in chunks)
    assert all(c.char_count == len(c.content) for c in chunks)


def t_document_id_propagated():
    doc_id = uuid4()
    chunks = chunk_text("Some text.", doc_id)
    assert all(c.document_id == doc_id for c in chunks)


test("empty text returns []",                  t_empty_text)
test("whitespace-only returns []",             t_whitespace_only)
test("short text, no heading - 1 chunk",       t_short_text_no_heading)
test("chunk_index is sequential",              t_chunk_index_sequential)
test("token_count and char_count populated",   t_token_and_char_count_populated)
test("document_id propagated to all chunks",   t_document_id_propagated)


section("Section detection")


def t_markdown_heading_detected():
    text = "# Introduction\nThis is the intro.\n\n# Conclusion\nThis is the end."
    chunks = chunk_text(text, DOC_ID)
    titles = [c.section_title for c in chunks]
    assert "Introduction" in titles
    assert "Conclusion" in titles


def t_markdown_h2_h3_detected():
    text = "## Methods\nbody\n\n### Detail\nmore body"
    chunks = chunk_text(text, DOC_ID)
    titles = [c.section_title for c in chunks]
    assert "Methods" in titles
    assert "Detail" in titles


def t_allcaps_heading_detected():
    text = "INTRODUCTION\nsome content here\n\nMETHODS\nother content"
    chunks = chunk_text(text, DOC_ID)
    titles = [c.section_title for c in chunks]
    assert "INTRODUCTION" in titles
    assert "METHODS" in titles


def t_preamble_before_first_heading_title_none():
    text = "This text comes before any heading.\n\n# Section One\nbody"
    chunks = chunk_text(text, DOC_ID)
    # first chunk is preamble - no heading so title is None
    assert chunks[0].section_title is None
    assert "This text comes before" in chunks[0].content


def t_no_heading_all_chunks_title_none():
    text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
    chunks = chunk_text(text, DOC_ID)
    assert all(c.section_title is None for c in chunks)


def t_heading_hash_stripped_from_title():
    text = "## My Section\ncontent"
    chunks = chunk_text(text, DOC_ID)
    assert chunks[0].section_title == "My Section"
    assert "#" not in chunks[0].section_title


test("Markdown # headings detected",           t_markdown_heading_detected)
test("Markdown ## and ### detected",           t_markdown_h2_h3_detected)
test("ALL CAPS line detected as heading",      t_allcaps_heading_detected)
test("preamble before first heading - None",   t_preamble_before_first_heading_title_none)
test("no heading - all titles are None",       t_no_heading_all_chunks_title_none)
test("## stripped from section_title",         t_heading_hash_stripped_from_title)


section("Sliding window (long text)")


def t_long_section_split_into_multiple_chunks():
    text = "# Big Section\n" + _long_text(count=600)
    cfg = ChunkConfig(max_tokens=500, overlap_tokens=50)
    chunks = chunk_text(text, DOC_ID, cfg)
    assert len(chunks) > 1, "long section should produce multiple chunks"


def t_all_window_chunks_share_same_section_title():
    text = "# Big Section\n" + _long_text(count=600)
    cfg = ChunkConfig(max_tokens=500, overlap_tokens=50)
    chunks = chunk_text(text, DOC_ID, cfg)
    assert all(c.section_title == "Big Section" for c in chunks)


def t_overlap_words_appear_in_consecutive_chunks():
    text = "# Long\n" + " ".join(f"word{i}" for i in range(300))
    cfg = ChunkConfig(max_tokens=100, overlap_tokens=20)
    chunks = chunk_text(text, DOC_ID, cfg)
    assert len(chunks) >= 2
    words_first  = set(chunks[0].content.split())
    words_second = set(chunks[1].content.split())
    overlap = words_first & words_second
    assert len(overlap) > 0, "no overlapping words between consecutive chunks"


def t_no_chunk_exceeds_max_tokens():
    text = "# Section\n" + _long_text(count=1000)
    cfg = ChunkConfig(max_tokens=500, overlap_tokens=50)
    chunks = chunk_text(text, DOC_ID, cfg)
    for c in chunks:
        assert c.token_count <= cfg.max_tokens * 1.1, (
            f"chunk {c.chunk_index} has {c.token_count} tokens, limit {cfg.max_tokens}"
        )


def t_short_section_not_split():
    text = "# Short\nJust a sentence."
    cfg = ChunkConfig(max_tokens=500, overlap_tokens=50)
    chunks = chunk_text(text, DOC_ID, cfg)
    assert len(chunks) == 1


test("long section produces multiple chunks",  t_long_section_split_into_multiple_chunks)
test("all window chunks share section_title",  t_all_window_chunks_share_same_section_title)
test("overlap words in consecutive chunks",    t_overlap_words_appear_in_consecutive_chunks)
test("no chunk exceeds max_tokens",            t_no_chunk_exceeds_max_tokens)
test("short section stays as 1 chunk",         t_short_section_not_split)


section("Config")


def t_custom_config_respected():
    text = "# S\n" + _long_text(count=200)
    cfg_tight = ChunkConfig(max_tokens=50, overlap_tokens=5)
    cfg_loose = ChunkConfig(max_tokens=500, overlap_tokens=50)
    tight = chunk_text(text, DOC_ID, cfg_tight)
    loose = chunk_text(text, DOC_ID, cfg_loose)
    assert len(tight) > len(loose), "tighter config should produce more chunks"


def t_default_config_used_when_none():
    chunks = chunk_text("# S\nsome text", DOC_ID, config=None)
    assert len(chunks) >= 1


test("tight config produces more chunks",      t_custom_config_respected)
test("config=None uses defaults",              t_default_config_used_when_none)


# summary
passed = sum(1 for _, ok, _ in results if ok)
failed = [(n, e) for n, ok, e in results if not ok]
total  = len(results)

print(f"\n{'='*55}")
print(f"  Result: {passed}/{total} passed")
if failed:
    print(f"\n  Failed:")
    for name, err in failed:
        print(f"    - {name}: {type(err).__name__}: {err}")
print(f"{'='*55}\n")

sys.exit(0 if not failed else 1)
