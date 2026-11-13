import subprocess

from src.bitboard import (
    play_move,
    valid_moves,
    has_won,
)

from src.v4_baseline import agent as v4_agent
from src.v6_agent import choose_move_with_info


SOLVER = "tools/connect4/c4solver"
BOOK = "tools/connect4/7x6.book"


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


def run_v4(board, mark):
    obs = Observation(
        board,
        mark,
    )

    return int(
        v4_agent(
            obs,
            CONFIG,
        )
    )


def solver_analyze(sequence):
    """
    Ask Pascal Pons' solver for exact scores
    of all seven candidate moves.
    """

    result = subprocess.run(
        [
            SOLVER,
            "-b",
            BOOK,
            "-a",
        ],
        input=sequence + "\n",
        text=True,
        capture_output=True,
        check=True,
    )

    line = result.stdout.strip()

    parts = line.split()

    # For the empty position there is no sequence token.
    if sequence:
        scores = list(
            map(int, parts[1:])
        )
    else:
        scores = list(
            map(int, parts)
        )

    if len(scores) != 7:
        raise ValueError(
            f"Unexpected solver output: {line}"
        )

    return scores


def best_solver_moves(scores):
    legal = [
        (score, col)
        for col, score in enumerate(scores)
        if score != -1000
    ]

    best_score = max(
        score
        for score, _ in legal
    )

    moves = [
        col
        for score, col in legal
        if score == best_score
    ]

    return best_score, moves


def play_oracle_game(v6_player):
    p1 = 0
    p2 = 0
    player = 1

    # Pons uses columns 1-7.
    sequence = ""

    print()
    print("=" * 72)

    if v6_player == 1:
        print("SOLVER ORACLE: V6 AS PLAYER 1")
    else:
        print("SOLVER ORACLE: V6 AS PLAYER 2")

    print("=" * 72)

    first_deviation = None

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
            print("RESULT: DRAW")
            break

        ply = (p1 | p2).bit_count()

        if player == v6_player:
            obs = Observation(
                board,
                player,
            )

            move, info = choose_move_with_info(
                obs,
                CONFIG,
            )

            # Exact solver analysis BEFORE V6 moves.
            scores = solver_analyze(
                sequence
            )

            solver_score, solver_moves = (
                best_solver_moves(scores)
            )

            correct = move in solver_moves

            print()
            print(
                f"Ply {ply:2} | "
                f"V6 -> {move} | "
                f"{info['source']}"
            )

            print(
                "  Solver scores:",
                scores,
            )

            print(
                f"  Solver best score: "
                f"{solver_score}"
            )

            print(
                f"  Solver best moves: "
                f"{solver_moves}"
            )

            print(
                "  V6 optimal:",
                "YES" if correct else "NO",
            )

            if (
                not correct
                and first_deviation is None
            ):
                first_deviation = {
                    "ply": ply,
                    "sequence": sequence,
                    "v6_move": move,
                    "solver_moves": solver_moves,
                    "solver_score": solver_score,
                    "scores": scores,
                    "source": info["source"],
                    "depth": info["depth"],
                    "nodes": info["nodes"],
                }

        else:
            move = run_v4(
                board,
                player,
            )

            print(
                f"Ply {ply:2} | "
                f"V4 -> {move}"
            )

        if move not in legal:
            print(
                "ILLEGAL MOVE:",
                move,
            )
            break

        # Pons uses 1-based columns.
        sequence += str(
            move + 1
        )

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
            winner = (
                "V6"
                if player == v6_player
                else "V4"
            )

            print()
            print(
                "RESULT:",
                winner,
                "WINS",
            )

            break

        player = 3 - player

    print()
    print("=" * 72)
    print("FIRST V6 DEVIATION FROM PERFECT PLAY")
    print("=" * 72)

    if first_deviation is None:
        print(
            "V6 never deviated from a solver-best move."
        )

    else:
        for key, value in first_deviation.items():
            print(
                f"{key}: {value}"
            )


if __name__ == "__main__":
    play_oracle_game(
        v6_player=1
    )

    play_oracle_game(
        v6_player=2
    )