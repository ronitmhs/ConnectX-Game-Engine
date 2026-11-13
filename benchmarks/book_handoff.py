from src.bitboard import (
    play_move,
    has_won,
    valid_moves,
)

from src.v4_baseline import agent as v4_agent
from src.v6_agent import choose_move_with_info


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


def play_diagnostic(v6_player):
    p1 = 0
    p2 = 0
    player = 1

    move_number = 0

    print()
    print("=" * 70)

    if v6_player == 1:
        print("V6 = PLAYER 1")
    else:
        print("V6 = PLAYER 2")

    print("=" * 70)

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
            return

        move_number += 1

        if player == v6_player:
            obs = Observation(
                board,
                player,
            )

            move, info = choose_move_with_info(
                obs,
                CONFIG,
            )

            print(
                f"Ply {info['ply']:2} | "
                f"V6 -> {move} | "
                f"{info['source']}",
                end=""
            )

            if info["source"] == "BOOK":
                print(
                    f" | score={info['book_score']} "
                    f"| optimal={info['book_moves']}"
                )

            else:
                print(
                    f" | depth={info['depth']} "
                    f"| nodes={info['nodes']}"
                )

        else:
            move = run_v4(
                board,
                player,
            )

            print(
                f"Ply {(p1 | p2).bit_count():2} | "
                f"V4 -> {move}"
            )

        if move not in legal:
            print(
                "ILLEGAL MOVE:",
                move,
            )
            return

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

            print(
                "RESULT:",
                winner,
                "WINS"
            )

            return

        player = 3 - player


if __name__ == "__main__":
    play_diagnostic(
        v6_player=1
    )

    play_diagnostic(
        v6_player=2
    )