"""
Edge-case tests for text_embedder.
Run: python tests/test_embedder.py
"""
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.shared.utils.embedders import embed_chunks
from app.domain.entities.chunk import Chunk

PASS = "[PASS]"
FAIL = "[FAIL]"
results = []

DOC_ID = uuid4()


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


def _make_chunk(content: str, index: int = 0) -> Chunk:
    return Chunk(
        document_id=DOC_ID,
        content=content,
        chunk_index=index,
        token_count=len(content) // 4,
        char_count=len(content),
    )


def _cosine_sim(a: list[float], b: list[float]) -> float:
    from math import sqrt
    dot = sum(x * y for x, y in zip(a, b))
    na  = sqrt(sum(x * x for x in a))
    nb  = sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0


section("Basic behavior")


def t_empty_list():
    assert embed_chunks([]) == []


def t_single_chunk_returns_one_vector():
    chunks = [_make_chunk("Hello world")]
    vectors = embed_chunks(chunks)
    assert len(vectors) == 1


def t_output_length_matches_input():
    chunks = [_make_chunk(f"text {i}", i) for i in range(5)]
    vectors = embed_chunks(chunks)
    assert len(vectors) == len(chunks)


def t_vector_dimension_is_384():
    chunks = [_make_chunk("test sentence")]
    vectors = embed_chunks(chunks)
    assert len(vectors[0]) == 384, f"expected 384, got {len(vectors[0])}"


def t_all_values_are_floats():
    chunks = [_make_chunk("test")]
    vectors = embed_chunks(chunks)
    assert all(isinstance(v, float) for v in vectors[0])


def t_order_preserved():
    texts = ["first sentence", "second sentence", "third sentence"]
    chunks = [_make_chunk(t, i) for i, t in enumerate(texts)]
    v1 = embed_chunks(chunks)
    v2 = embed_chunks([chunks[0]])
    assert _cosine_sim(v1[0], v2[0]) > 0.9999, "order not preserved"


test("empty list returns []",               t_empty_list)
test("single chunk - one vector",           t_single_chunk_returns_one_vector)
test("output length matches input",         t_output_length_matches_input)
test("vector dimension is 384",             t_vector_dimension_is_384)
test("all values are floats",               t_all_values_are_floats)
test("order preserved across calls",        t_order_preserved)


section("Semantic similarity")


def t_similar_texts_have_high_cosine_sim():
    chunks = [
        _make_chunk("Eigenvalues describe how a matrix transforms vectors.", 0),
        _make_chunk("Eigenvectors are scaled by eigenvalues under transformation.", 1),
    ]
    v = embed_chunks(chunks)
    sim = _cosine_sim(v[0], v[1])
    assert sim > 0.5, f"expected similar texts to have sim > 0.5, got {sim:.4f}"


def t_unrelated_texts_have_low_cosine_sim():
    chunks = [
        _make_chunk("Linear algebra deals with vector spaces.", 0),
        _make_chunk("The recipe requires two cups of flour.", 1),
    ]
    v = embed_chunks(chunks)
    sim = _cosine_sim(v[0], v[1])
    assert sim < 0.5, f"expected unrelated texts to have sim < 0.5, got {sim:.4f}"


def t_identical_texts_have_sim_close_to_1():
    text = "Vector spaces are fundamental in mathematics."
    chunks = [_make_chunk(text, 0), _make_chunk(text, 1)]
    v = embed_chunks(chunks)
    sim = _cosine_sim(v[0], v[1])
    assert sim > 0.999, f"identical texts should have sim ~1.0, got {sim:.4f}"


test("similar texts - high cosine sim",     t_similar_texts_have_high_cosine_sim)
test("unrelated texts - low cosine sim",    t_unrelated_texts_have_low_cosine_sim)
test("identical texts - sim close to 1.0",  t_identical_texts_have_sim_close_to_1)


section("Model cache")


def t_second_call_uses_cached_model():
    import time
    chunks = [_make_chunk("warm up call")]
    embed_chunks(chunks)

    chunks = [_make_chunk(f"text {i}", i) for i in range(10)]
    start = time.time()
    embed_chunks(chunks)
    elapsed = time.time() - start
    # second call should not reload model — should complete in well under 5s
    assert elapsed < 5.0, f"second call took {elapsed:.2f}s, model may not be cached"


test("second call uses cached model",       t_second_call_uses_cached_model)


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
