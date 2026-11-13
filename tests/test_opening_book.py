from src.bitboard import play_move
from src.opening_book import OpeningBook


def position_from_sequence(sequence):
    p1 = 0
    p2 = 0
    player = 1

    for char in sequence:
        col = int(char) - 1

        p1, p2 = play_move(
            p1,
            p2,
            col,
            player,
        )

        player = 3 - player

    return p1, p2, player


def test_book_loads():
    book = OpeningBook()

    assert len(book) == 11094


def test_empty_board():
    book = OpeningBook()

    scores = book.get_scores(
        0,
        0,
        1,
    )

    assert scores == [
        -2, -1, 0, 1, 0, -1, -2
    ]

    assert book.choose_move(
        0,
        0,
        1,
    ) == 3


def test_sequence_4():
    book = OpeningBook()

    p1, p2, player = position_from_sequence(
        "4"
    )

    scores = book.get_scores(
        p1,
        p2,
        player,
    )

    assert scores == [
        -4, -2, -2, -1, -2, -2, -4
    ]


def test_sequence_44():
    book = OpeningBook()

    p1, p2, player = position_from_sequence(
        "44"
    )

    scores = book.get_scores(
        p1,
        p2,
        player,
    )

    assert scores == [
        -3, -3, -2, 1, -2, -3, -3
    ]

    assert book.choose_move(
        p1,
        p2,
        player,
    ) == 3


def test_sequence_443():
    book = OpeningBook()

    p1, p2, player = position_from_sequence(
        "443"
    )

    scores = book.get_scores(
        p1,
        p2,
        player,
    )

    assert scores == [
        -18, 2, -18, -18, 2, -18, -18
    ]

    best = book.get_best_moves(
        p1,
        p2,
        player,
    )

    assert set(best) == {1, 4}