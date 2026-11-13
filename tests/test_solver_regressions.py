from src.bitboard import play_move
from src.search import SearchEngine


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


def test_known_v6_player2_failure():
    """
    Real V6 failure discovered with the exact solver.

    Sequence:
        44447465555

    Pascal Pons solver:
        col 0 -> +2
        col 1 -> +3  BEST
        col 2 -> -4  OLD V6 MOVE
        col 3 -> +2
        col 4 -> +1
        col 5 -> +2
        col 6 -> +2

    Correct zero-based move: 1
    """

    p1, p2, player = position_from_sequence(
        "44447465555"
    )

    engine = SearchEngine(
        time_limit=1.65
    )

    move = engine.choose_move(
        p1,
        p2,
        player,
    )

    # Current V6 is EXPECTED to fail this test.
    assert move == 1
    
def test_real_v6_kaggle_win_preservation_failure():
    """
    Real V6 Kaggle failure from episode 126636478.

    Sequence:
        44444435563355

    Pascal Pons:
        col 0 -> +2  WIN
        col 1 -> -2  LOSS
        col 2 -> +2  WIN
        col 3 -> illegal
        col 4 -> -2  LOSS  (submitted V6 move)
        col 5 -> -2  LOSS
        col 6 -> +2  WIN

    V6 must preserve the forced win.
    """

    p1, p2, player = position_from_sequence(
        "44444435563355"
    )

    engine = SearchEngine(
        time_limit=1.65
    )

    move = engine.choose_move(
        p1,
        p2,
        player,
    )

    assert move in {0, 2, 6}
    
def test_real_v6_player2_win_preservation_failure():
    """
    Real V6 Kaggle failure from episode 126637123.

    Sequence:
        4444355552667

    Pascal Pons:
        best move: col 1
        best score: +3

    Submitted V6 played col 3, scoring -2.

    V6 must preserve the forced win.
    """

    p1, p2, player = position_from_sequence(
        "4444355552667"
    )

    engine = SearchEngine(
        time_limit=1.65
    )

    move = engine.choose_move(
        p1,
        p2,
        player,
    )

    assert move == 1
    

def test_real_v61_player1_win_preservation_failure():
    """
    Real V6.1 Kaggle failure from episode 126638838.

    Sequence:
        444443333147

    Pascal Pons:
        best move: col 5
        best score: +1

    V6.1 played col 4, scoring -3.

    V6 must preserve the forced win.
    """

    p1, p2, player = position_from_sequence(
        "444443333147"
    )

    engine = SearchEngine(
        time_limit=1.65
    )

    move = engine.choose_move(
        p1,
        p2,
        player,
    )

    assert move == 5