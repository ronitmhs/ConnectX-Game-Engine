import time

from src.bitboard import (
    play_move,
    immediate_wins,
    winning_positions,
)


# Build a realistic midgame position
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


ITERATIONS = 100_000


# ------------------------------------------------------------
# Existing method
# ------------------------------------------------------------

start = time.perf_counter()

for _ in range(ITERATIONS):
    immediate_wins(
        p1,
        p2,
        player,
    )

old_time = time.perf_counter() - start


# ------------------------------------------------------------
# Bitboard method
# ------------------------------------------------------------

position = p1 if player == 1 else p2
mask = p1 | p2

start = time.perf_counter()

for _ in range(ITERATIONS):
    winning_positions(
        position,
        mask,
    )

new_time = time.perf_counter() - start


# ------------------------------------------------------------
# Results
# ------------------------------------------------------------

print()
print("=" * 50)
print("THREAT DETECTION BENCHMARK")
print("=" * 50)

print(
    "Iterations:",
    f"{ITERATIONS:,}"
)

print(
    "immediate_wins:",
    round(old_time, 4),
    "seconds",
)

print(
    "winning_positions:",
    round(new_time, 4),
    "seconds",
)

print(
    "Speedup:",
    round(old_time / new_time, 2),
    "x",
)