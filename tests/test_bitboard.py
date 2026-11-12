from src.bitboard import (
    board_to_bitboards,
    play_move,
    valid_moves,
    has_won,
    immediate_wins,
)


def empty_board():
    return [0] * 42


def test_empty_board():
    p1, p2 = board_to_bitboards(
        empty_board()
    )

    assert p1 == 0
    assert p2 == 0

    assert valid_moves(p1, p2) == [
        3, 2, 4, 1, 5, 0, 6
    ]


def test_vertical_win():
    p1 = 0
    p2 = 0

    for _ in range(4):
        p1, p2 = play_move(
            p1,
            p2,
            3,
            1
        )

    assert has_won(p1)


def test_horizontal_win():
    p1 = 0
    p2 = 0

    for col in [0, 1, 2, 3]:
        p1, p2 = play_move(
            p1,
            p2,
            col,
            1
        )

    assert has_won(p1)


def test_immediate_horizontal_win():
    p1 = 0
    p2 = 0

    for col in [0, 1, 2]:
        p1, p2 = play_move(
            p1,
            p2,
            col,
            1
        )

    wins = immediate_wins(
        p1,
        p2,
        1
    )

    assert 3 in wins


def test_full_column():
    p1 = 0
    p2 = 0

    for i in range(6):
        player = 1 if i % 2 == 0 else 2

        p1, p2 = play_move(
            p1,
            p2,
            3,
            player
        )

    assert 3 not in valid_moves(p1, p2)
    

def test_diagonal_up_right_win():
    p1 = 0
    p2 = 0

    # Build supports for a / diagonal.
    # P1 ends at:
    # (col,row-from-bottom)
    # (0,0), (1,1), (2,2), (3,3)

    p1, p2 = play_move(p1, p2, 0, 1)

    p1, p2 = play_move(p1, p2, 1, 2)
    p1, p2 = play_move(p1, p2, 1, 1)

    p1, p2 = play_move(p1, p2, 2, 2)
    p1, p2 = play_move(p1, p2, 2, 2)
    p1, p2 = play_move(p1, p2, 2, 1)

    p1, p2 = play_move(p1, p2, 3, 2)
    p1, p2 = play_move(p1, p2, 3, 2)
    p1, p2 = play_move(p1, p2, 3, 2)
    p1, p2 = play_move(p1, p2, 3, 1)

    assert has_won(p1)


def test_diagonal_down_right_win():
    p1 = 0
    p2 = 0

    # Mirror of previous test.

    p1, p2 = play_move(p1, p2, 6, 1)

    p1, p2 = play_move(p1, p2, 5, 2)
    p1, p2 = play_move(p1, p2, 5, 1)

    p1, p2 = play_move(p1, p2, 4, 2)
    p1, p2 = play_move(p1, p2, 4, 2)
    p1, p2 = play_move(p1, p2, 4, 1)

    p1, p2 = play_move(p1, p2, 3, 2)
    p1, p2 = play_move(p1, p2, 3, 2)
    p1, p2 = play_move(p1, p2, 3, 2)
    p1, p2 = play_move(p1, p2, 3, 1)

    assert has_won(p1)


def test_kaggle_board_conversion():
    board = [0] * 42

    # Kaggle bottom row: columns 0,1,2,3 = Player 1
    board[35] = 1
    board[36] = 1
    board[37] = 1
    board[38] = 1

    p1, p2 = board_to_bitboards(board)

    assert has_won(p1)
    assert not has_won(p2)