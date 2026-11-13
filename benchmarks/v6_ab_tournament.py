import json
import random
import time
from pathlib import Path

from src.bitboard import (
    board_to_bitboards,
    play_move,
    has_won,
    valid_moves,
)
from src.compact_book import CompactOpeningBook
from src.search import SearchEngine


EPISODE_DIR = Path("data/episodes")

BOOK = CompactOpeningBook()

TIME_LIMIT = 1.65
EXACT_TIME = 1.40
EXACT_ENDGAME_EMPTIES = 23

# Number of different starting positions.
NUM_POSITIONS = 25

# We want positions after the opening book but before
# the exact-endgame boundary.
MIN_PLY = 11
MAX_PLY = 18

RANDOM_SEED = 42


# ============================================================
# KAGGLE-LIKE OBJECTS
# ============================================================

class Observation:
    def __init__(self, board, mark):
        self.board = board
        self.mark = mark


class Configuration:
    rows = 6
    columns = 7
    inarow = 4
    timeout = 2


CONFIG = Configuration()


# ============================================================
# BOARD CONVERSION
# ============================================================

def bitboards_to_board(p1, p2):
    board = [0] * 42

    for r in range(6):
        for c in range(7):
            row_from_bottom = 5 - r

            bit = 1 << (
                c * 7 + row_from_bottom
            )

            index = r * 7 + c

            if p1 & bit:
                board[index] = 1

            elif p2 & bit:
                board[index] = 2

    return board


# ============================================================
# V6A
#
# Opening book + normal iterative search.
# No direct exact-endgame mode.
# ============================================================

def v6a_move(p1, p2, player):
    start = time.perf_counter()

    book_move = BOOK.choose_move(
        p1,
        p2,
    )

    if book_move is not None:
        return (
            int(book_move),
            time.perf_counter() - start,
            "BOOK",
        )

    engine = SearchEngine(
        time_limit=EXACT_TIME
    )

    move = engine.choose_move(
        p1,
        p2,
        player,
    )

    return (
        int(move),
        time.perf_counter() - start,
        "SEARCH",
    )


# ============================================================
# V6B
#
# Same engine, but direct exact search with <=23 empties.
# ============================================================

def v6b_move(p1, p2, player):
    start = time.perf_counter()

    book_move = BOOK.choose_move(
        p1,
        p2,
    )

    if book_move is not None:
        return (
            int(book_move),
            time.perf_counter() - start,
            "BOOK",
        )

    ply = (p1 | p2).bit_count()
    empties = 42 - ply

    if empties <= EXACT_ENDGAME_EMPTIES:
        engine = SearchEngine(
            time_limit=TIME_LIMIT
        )

        move = engine.choose_move_exact(
            p1,
            p2,
            player,
            depth=empties,
        )

        if move is not None:
            return (
                int(move),
                time.perf_counter() - start,
                "EXACT",
            )

    engine = SearchEngine(
        time_limit=TIME_LIMIT
    )

    move = engine.choose_move(
        p1,
        p2,
        player,
    )

    return (
        int(move),
        time.perf_counter() - start,
        "SEARCH",
    )


# ============================================================
# REAL-GAME STARTING POSITIONS
# ============================================================

def load_starting_positions():
    positions = []
    seen = set()

    for path in sorted(
        EPISODE_DIR.glob("*.json")
    ):
        with path.open() as f:
            episode = json.load(f)

        for step in episode["steps"]:
            board = None

            for state in step:
                obs = state.get(
                    "observation",
                    {}
                )

                candidate = obs.get(
                    "board"
                )

                if candidate:
                    board = candidate
                    break

            if board is None:
                continue

            ply = sum(
                1
                for cell in board
                if cell
            )

            if not (
                MIN_PLY
                <= ply
                <= MAX_PLY
            ):
                continue

            # Side to move follows parity:
            # P1 at even ply, P2 at odd ply.
            player = (
                1
                if ply % 2 == 0
                else 2
            )

            key = (
                tuple(board),
                player,
            )

            if key in seen:
                continue

            seen.add(key)

            p1, p2 = board_to_bitboards(
                board
            )

            # Ignore positions where game has already ended.
            if has_won(p1) or has_won(p2):
                continue

            positions.append(
                (
                    p1,
                    p2,
                    player,
                    path.stem,
                    ply,
                )
            )

    rng = random.Random(
        RANDOM_SEED
    )

    rng.shuffle(
        positions
    )

    return positions[
        :NUM_POSITIONS
    ]


# ============================================================
# PLAY ONE GAME
# ============================================================

def play_game(
    start_position,
    a_player,
):
    (
        p1,
        p2,
        player,
        episode,
        starting_ply,
    ) = start_position

    times_a = []
    times_b = []

    exact_b = 0
    illegal = 0

    while True:
        legal = valid_moves(
            p1,
            p2,
        )

        if not legal:
            return {
                "winner": 0,
                "times_a": times_a,
                "times_b": times_b,
                "exact_b": exact_b,
                "illegal": illegal,
            }

        if player == a_player:
            move, elapsed, source = (
                v6a_move(
                    p1,
                    p2,
                    player,
                )
            )

            times_a.append(
                elapsed
            )

        else:
            move, elapsed, source = (
                v6b_move(
                    p1,
                    p2,
                    player,
                )
            )

            times_b.append(
                elapsed
            )

            if source == "EXACT":
                exact_b += 1

        if move not in legal:
            illegal += 1

            # Illegal mover loses.
            winner = 3 - player

            return {
                "winner": winner,
                "times_a": times_a,
                "times_b": times_b,
                "exact_b": exact_b,
                "illegal": illegal,
            }

        p1, p2 = play_move(
            p1,
            p2,
            move,
            player,
        )

        position = (
            p1
            if player == 1
            else p2
        )

        if has_won(position):
            return {
                "winner": player,
                "times_a": times_a,
                "times_b": times_b,
                "exact_b": exact_b,
                "illegal": illegal,
            }

        player = 3 - player


# ============================================================
# TOURNAMENT
# ============================================================

def main():
    positions = (
        load_starting_positions()
    )

    print("=" * 64)
    print("V6A vs V6B EXACT-ENDGAME A/B TEST")
    print("=" * 64)

    print(
        "Starting positions:",
        len(positions),
    )

    print(
        "Paired games:",
        len(positions) * 2,
    )

    print(
        "Exact cutoff:",
        EXACT_ENDGAME_EMPTIES,
        "empty cells",
    )

    print()

    a_wins = 0
    b_wins = 0
    draws = 0

    a_as_p1_wins = 0
    a_as_p2_wins = 0

    b_as_p1_wins = 0
    b_as_p2_wins = 0

    all_a_times = []
    all_b_times = []

    exact_moves = 0
    illegal_moves = 0

    for index, position in enumerate(
        positions,
        start=1,
    ):
        (
            _,
            _,
            side_to_move,
            episode,
            ply,
        ) = position

        # --------------------------------------------
        # Game 1:
        # V6A owns Player 1
        # --------------------------------------------

        result = play_game(
            position,
            a_player=1,
        )

        all_a_times.extend(
            result["times_a"]
        )

        all_b_times.extend(
            result["times_b"]
        )

        exact_moves += (
            result["exact_b"]
        )

        illegal_moves += (
            result["illegal"]
        )

        if result["winner"] == 0:
            draws += 1

        elif result["winner"] == 1:
            a_wins += 1
            a_as_p1_wins += 1

        else:
            b_wins += 1
            b_as_p2_wins += 1

        # --------------------------------------------
        # Game 2:
        # V6B owns Player 1
        # --------------------------------------------

        result = play_game(
            position,
            a_player=2,
        )

        all_a_times.extend(
            result["times_a"]
        )

        all_b_times.extend(
            result["times_b"]
        )

        exact_moves += (
            result["exact_b"]
        )

        illegal_moves += (
            result["illegal"]
        )

        if result["winner"] == 0:
            draws += 1

        elif result["winner"] == 1:
            b_wins += 1
            b_as_p1_wins += 1

        else:
            a_wins += 1
            a_as_p2_wins += 1

        print(
            f"{index:2}/{len(positions)} | "
            f"episode={episode} | "
            f"ply={ply}"
        )

    total_games = (
        a_wins
        + b_wins
        + draws
    )

    print()
    print("=" * 64)
    print("RESULTS")
    print("=" * 64)

    print(
        "Games:",
        total_games,
    )

    print(
        "V6A wins:",
        a_wins,
    )

    print(
        "V6B wins:",
        b_wins,
    )

    print(
        "Draws:",
        draws,
    )

    print()

    print("--- V6A ---")
    print(
        "Wins as P1:",
        a_as_p1_wins,
    )
    print(
        "Wins as P2:",
        a_as_p2_wins,
    )

    print()

    print("--- V6B EXACT ---")
    print(
        "Wins as P1:",
        b_as_p1_wins,
    )
    print(
        "Wins as P2:",
        b_as_p2_wins,
    )

    print()

    print("--- PERFORMANCE ---")

    if all_a_times:
        print(
            "Average V6A move time:",
            f"{sum(all_a_times) / len(all_a_times):.4f}s",
        )

        print(
            "Worst V6A move time:",
            f"{max(all_a_times):.4f}s",
        )

    if all_b_times:
        print(
            "Average V6B move time:",
            f"{sum(all_b_times) / len(all_b_times):.4f}s",
        )

        print(
            "Worst V6B move time:",
            f"{max(all_b_times):.4f}s",
        )

    print(
        "V6B exact moves:",
        exact_moves,
    )

    print(
        "Illegal moves:",
        illegal_moves,
    )


if __name__ == "__main__":
    main()