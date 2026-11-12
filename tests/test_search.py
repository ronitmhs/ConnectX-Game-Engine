from src.bitboard import play_move
from src.search import SearchEngine


def test_engine_takes_immediate_win():
    p1 = 0
    p2 = 0

    for col in [0, 1, 2]:
        p1, p2 = play_move(
            p1,
            p2,
            col,
            1,
        )

    engine = SearchEngine(
        time_limit=0.2
    )

    move = engine.choose_move(
        p1,
        p2,
        1,
    )

    assert move == 3


def test_engine_blocks_immediate_loss():
    p1 = 0
    p2 = 0

    for col in [0, 1, 2]:
        p1, p2 = play_move(
            p1,
            p2,
            col,
            2,
        )

    engine = SearchEngine(
        time_limit=0.2
    )

    move = engine.choose_move(
        p1,
        p2,
        1,
    )

    assert move == 3


def test_engine_chooses_legal_move():
    p1 = 0
    p2 = 0

    engine = SearchEngine(
        time_limit=0.1
    )

    move = engine.choose_move(
        p1,
        p2,
        1,
    )

    assert move in range(7)


def test_engine_prefers_center_on_empty_board():
    p1 = 0
    p2 = 0

    engine = SearchEngine(
        time_limit=0.1
    )

    move = engine.choose_move(
        p1,
        p2,
        1,
    )

    assert move == 3