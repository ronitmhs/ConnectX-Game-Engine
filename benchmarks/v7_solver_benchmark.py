import time

from src.bitboard import play_move
from src.v7_book import V7OpeningBook
from src.v7_solver import V7ExactSolver


SEQUENCE = "444443333147"

EXPECTED_SCORE = 1
EXPECTED_MOVES = [5]


def sequence_to_position(sequence):
    p1 = 0
    p2 = 0
    player = 1

    for char in sequence:
        p1, p2 = play_move(
            p1,
            p2,
            int(char) - 1,
            player,
        )

        player = 3 - player

    return p1, p2, player


def main():
    print("=" * 72)
    print("V7 EXACT SOLVER BENCHMARK")
    print("=" * 72)

    book = V7OpeningBook()

    p1, p2, player = (
        sequence_to_position(
            SEQUENCE
        )
    )

    parent_score = book.lookup(
        p1,
        p2,
        player,
    )

    print("Sequence:", SEQUENCE)
    print("Ply:", len(SEQUENCE))
    print("Player:", player)
    print("Book parent score:", parent_score)
    print("Expected score:", EXPECTED_SCORE)
    print()

    solver = V7ExactSolver(
        book=book
    )

    start = time.perf_counter()

    moves, scores = (
        solver.best_moves(
            p1,
            p2,
            player,
        )
    )

    elapsed = (
        time.perf_counter()
        - start
    )

    print("Move scores:", scores)
    print("Best moves:", moves)
    print("Expected moves:", EXPECTED_MOVES)
    print(
        "Correct:",
        moves == EXPECTED_MOVES,
    )
    print(
        "Nodes:",
        f"{solver.nodes:,}",
    )
    print(
        "TT hits:",
        f"{solver.tt_hits:,}",
    )
    print(
        "Book hits:",
        f"{solver.book_hits:,}",
    )
    print(
        "TT size:",
        f"{len(solver.tt):,}",
    )
    print(
        "Time:",
        f"{elapsed:.4f}s",
    )


if __name__ == "__main__":
    main()