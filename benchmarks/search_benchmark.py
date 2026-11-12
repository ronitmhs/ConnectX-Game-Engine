import time

from src.bitboard import play_move
from src.search import SearchEngine


def run_benchmark(name, p1, p2, player):
    engine = SearchEngine(time_limit=1.65)

    start = time.perf_counter()

    move = engine.choose_move(
        p1,
        p2,
        player,
    )

    elapsed = time.perf_counter() - start

    print()
    print("=" * 50)
    print(name)
    print("=" * 50)
    print("Best move:", move)
    print("Completed depth:", engine.completed_depth)
    print("Nodes:", engine.nodes)
    print("TT hits:", engine.tt_hits)
    print("Time:", round(elapsed, 4), "seconds")

    if elapsed > 0:
        print(
            "Nodes/sec:",
            round(engine.nodes / elapsed)
        )


# ------------------------------------------------------------
# Position 1: Empty board
# ------------------------------------------------------------

run_benchmark(
    "EMPTY BOARD",
    0,
    0,
    1,
)


# ------------------------------------------------------------
# Position 2: Typical midgame
# ------------------------------------------------------------

p1 = 0
p2 = 0
player = 1

moves = [
    3, 2,
    3, 4,
    2, 4,
    1, 5,
    5, 1,
]

for col in moves:
    p1, p2 = play_move(
        p1,
        p2,
        col,
        player,
    )

    player = 3 - player


run_benchmark(
    "MIDGAME",
    p1,
    p2,
    player,
)