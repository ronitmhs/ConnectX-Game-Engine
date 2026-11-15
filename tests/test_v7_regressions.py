from src.bitboard import play_move
from src.v7_agent import (
    choose_move_from_bitboards,
)


def position_from_sequence(sequence):
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


def run(sequence):
    p1, p2, player = (
        position_from_sequence(sequence)
    )

    move, info = (
        choose_move_from_bitboards(
            p1,
            p2,
            player,
        )
    )

    return move, info


def test_v7_v61_failure_444443333147():
    # Pons:
    # best move = 5
    # score = +1
    move, info = run(
        "444443333147"
    )

    assert move == 5
    assert info["score"] == 1


def test_v7_critical_436333444467():
    # Pons:
    # best moves = 2, 5
    # score = +6
    move, info = run(
        "436333444467"
    )

    assert move in {2, 5}
    assert info["score"] == 6


def test_v7_critical_44444432655555():
    # Pons:
    # best move = 2
    # score = +1
    move, info = run(
        "44444432655555"
    )

    assert move == 2
    assert info["score"] == 1


def test_v7_real_v6_failure_44447465555():
    # Pons scores:
    # 0:+2, 1:+3, 2:-4,
    # 3:+2, 4:+1, 5:+2, 6:+2
    move, info = run(
        "44447465555"
    )

    assert move == 1
    assert info["score"] == 3


def test_v7_real_kaggle_win_preservation():
    # Pons:
    # winning moves = 0, 2, 6
    # best score = +2
    move, info = run(
        "44444435563355"
    )

    assert move in {0, 2, 6}
    assert info["score"] == 2


def test_v7_real_player2_win_preservation():
    # Pons:
    # best move = 1
    # score = +3
    move, info = run(
        "4444355552667"
    )

    assert move == 1
    assert info["score"] == 3