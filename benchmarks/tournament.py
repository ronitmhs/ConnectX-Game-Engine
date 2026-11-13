import time

from src.bitboard import (
    board_to_bitboards,
    play_move,
    has_won,
    valid_moves,
)

from submission import agent as v6_kaggle_agent


# ============================================================
# CONFIG
# ============================================================

# We start small.
# Once everything works, increase this.
GAMES_PER_SIDE = 5


# ============================================================
# LOAD V4
# ============================================================

# v4_baseline.py is the frozen copy of the Kaggle submission.
from src.v4_baseline import agent as v4_agent


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
    """
    Convert our bitboards back into Kaggle's
    42-element board representation.
    """

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
# V6 WRAPPER
# ============================================================

def v6_agent(board, mark):
    obs = Observation(
        board,
        mark,
    )

    start = time.perf_counter()

    move = v6_kaggle_agent(
        obs,
        CONFIG,
    )

    elapsed = time.perf_counter() - start

    return int(move), elapsed


# ============================================================
# V4 WRAPPER
# ============================================================

def run_v4(board, mark):
    obs = Observation(
        board,
        mark,
    )

    start = time.perf_counter()

    move = v4_agent(
        obs,
        CONFIG,
    )

    elapsed = time.perf_counter() - start

    return int(move), elapsed


# ============================================================
# PLAY ONE GAME
# ============================================================

def play_game(v6_player):
    """
    v6_player:
        1 -> V6 goes first
        2 -> V6 goes second
    """

    p1 = 0
    p2 = 0

    player = 1

    v6_time = 0.0
    v4_time = 0.0

    v6_moves = 0
    v4_moves = 0

    while True:

        board = bitboards_to_board(
            p1,
            p2,
        )

        legal = valid_moves(
            p1,
            p2,
        )

        if not legal:
            return {
                "result": "DRAW",
                "v6_time": v6_time,
                "v4_time": v4_time,
                "v6_moves": v6_moves,
                "v4_moves": v4_moves,
            }

        # ----------------------------------------------------
        # Choose move
        # ----------------------------------------------------

        if player == v6_player:

            move, elapsed = v6_agent(
                board,
                player,
            )

            v6_time += elapsed
            v6_moves += 1

        else:

            move, elapsed = run_v4(
                board,
                player,
            )

            v4_time += elapsed
            v4_moves += 1

        # ----------------------------------------------------
        # Illegal move protection
        # ----------------------------------------------------

        if move not in legal:

            loser = (
                "V6"
                if player == v6_player
                else "V4"
            )

            winner = (
                "V4"
                if loser == "V6"
                else "V6"
            )

            return {
                "result": winner,
                "illegal": loser,
                "v6_time": v6_time,
                "v4_time": v4_time,
                "v6_moves": v6_moves,
                "v4_moves": v4_moves,
            }

        # ----------------------------------------------------
        # Play move
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Win
        # ----------------------------------------------------

        if has_won(position):

            winner = (
                "V6"
                if player == v6_player
                else "V4"
            )

            return {
                "result": winner,
                "v6_time": v6_time,
                "v4_time": v4_time,
                "v6_moves": v6_moves,
                "v4_moves": v4_moves,
            }

        player = 3 - player


# ============================================================
# TOURNAMENT
# ============================================================

def run_tournament():

    v6_wins = 0
    v4_wins = 0
    draws = 0

    v6_first_wins = 0
    v6_second_wins = 0

    v6_first_losses = 0
    v6_second_losses = 0

    total_v6_time = 0.0
    total_v4_time = 0.0

    total_v6_moves = 0
    total_v4_moves = 0

    illegal_moves = []

    total_games = GAMES_PER_SIDE * 2

    print()
    print("=" * 60)
    print("V6 vs V4 TOURNAMENT")
    print("=" * 60)

    print(
        "Games:",
        total_games,
    )

    print()

    game_number = 0

    # --------------------------------------------------------
    # V6 FIRST
    # --------------------------------------------------------

    for _ in range(GAMES_PER_SIDE):

        game_number += 1

        result = play_game(
            v6_player=1
        )

        total_v6_time += result["v6_time"]
        total_v4_time += result["v4_time"]

        total_v6_moves += result["v6_moves"]
        total_v4_moves += result["v4_moves"]

        if result["result"] == "V6":
            v6_wins += 1
            v6_first_wins += 1

        elif result["result"] == "V4":
            v4_wins += 1
            v6_first_losses += 1

        else:
            draws += 1

        if "illegal" in result:
            illegal_moves.append(
                (
                    game_number,
                    result["illegal"],
                )
            )

        print(
            f"Game {game_number}/{total_games}: "
            f"V6 first -> {result['result']}"
        )

    # --------------------------------------------------------
    # V6 SECOND
    # --------------------------------------------------------

    for _ in range(GAMES_PER_SIDE):

        game_number += 1

        result = play_game(
            v6_player=2
        )

        total_v6_time += result["v6_time"]
        total_v4_time += result["v4_time"]

        total_v6_moves += result["v6_moves"]
        total_v4_moves += result["v4_moves"]

        if result["result"] == "V6":
            v6_wins += 1
            v6_second_wins += 1

        elif result["result"] == "V4":
            v4_wins += 1
            v6_second_losses += 1

        else:
            draws += 1

        if "illegal" in result:
            illegal_moves.append(
                (
                    game_number,
                    result["illegal"],
                )
            )

        print(
            f"Game {game_number}/{total_games}: "
            f"V6 second -> {result['result']}"
        )

    # --------------------------------------------------------
    # RESULTS
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)

    print()
    print("V6 wins:", v6_wins)
    print("V4 wins:", v4_wins)
    print("Draws:", draws)

    score = (
        v6_wins + 0.5 * draws
    ) / total_games

    print(
        "V6 score:",
        f"{score * 100:.1f}%"
    )

    print()
    print("--- V6 AS PLAYER 1 ---")
    print(
        "Wins:",
        v6_first_wins,
    )
    print(
        "Losses:",
        v6_first_losses,
    )

    first_draws = (
        GAMES_PER_SIDE
        - v6_first_wins
        - v6_first_losses
    )

    print(
        "Draws:",
        first_draws,
    )

    print()
    print("--- V6 AS PLAYER 2 ---")
    print(
        "Wins:",
        v6_second_wins,
    )
    print(
        "Losses:",
        v6_second_losses,
    )

    second_draws = (
        GAMES_PER_SIDE
        - v6_second_wins
        - v6_second_losses
    )

    print(
        "Draws:",
        second_draws,
    )

    print()
    print("--- PERFORMANCE ---")

    if total_v6_moves:
        print(
            "Average V6 move time:",
            round(
                total_v6_time
                / total_v6_moves,
                4,
            ),
            "seconds",
        )

    if total_v4_moves:
        print(
            "Average V4 move time:",
            round(
                total_v4_time
                / total_v4_moves,
                4,
            ),
            "seconds",
        )

    print(
        "Illegal moves:",
        len(illegal_moves),
    )

    if illegal_moves:
        print(
            illegal_moves
        )


if __name__ == "__main__":
    run_tournament()