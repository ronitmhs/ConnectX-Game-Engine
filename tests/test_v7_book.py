import random
import time

from src.v7_book import V7OpeningBook


def test_v7_book_loads():
    book = V7OpeningBook()

    assert len(book) == 9_188_816


def test_v7_book_random_internal_lookups():
    book = V7OpeningBook()

    random.seed(42)

    samples = []

    for _ in range(1000):
        block = random.randrange(
            book.block_count
        )

        samples.append(
            book.block_keys[block]
        )

    start = time.perf_counter()

    for key in samples:
        assert book.lookup_key(key) is not None

    elapsed = time.perf_counter() - start

    # Catch catastrophic lookup regressions,
    # not small machine-to-machine differences.
    assert elapsed < 1.0