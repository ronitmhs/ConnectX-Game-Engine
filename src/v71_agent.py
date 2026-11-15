from src.bitboard import (
    board_to_bitboards,
    has_won,
    play_move,
    valid_moves,
)

from src.v6_agent import (
    choose_move_with_info as v61_choose,
)

from src.v7_book import V7OpeningBook


BOOK = V7OpeningBook()


def exact_book_move(
    p1,
    p2,
    player,
):
    """
    Return an exactly proven optimal move when
    the parent and every required child score
    are available in the V7 book.

    Otherwise return None.
    """

    parent_score = BOOK.lookup(
        p1,
        p2,
        player,
    )

    if parent_score is None:
        return None

    legal = valid_moves(
        p1,
        p2,
    )

    if not legal:
        return None

    ply = (
        p1 | p2
    ).bit_count()

    scored = []

    for col in legal:
        n1, n2 = play_move(
            p1,
            p2,
            col,
            player,
        )

        own_position = (
            n1
            if player == 1
            else n2
        )

        # Immediate win.
        if has_won(
            own_position
        ):
            score = (
                42
                - ply
                + 1
            ) // 2

            scored.append(
                (
                    col,
                    score,
                )
            )

            continue

        child_score = BOOK.lookup(
            n1,
            n2,
            3 - player,
        )

        # We only override V6.1 when the
        # entire decision is exactly proven.
        if child_score is None:
            return None

        scored.append(
            (
                col,
                -int(child_score),
            )
        )

    if not scored:
        return None

    best_score = max(
        score
        for _, score in scored
    )

    # Sanity check: child-derived result
    # must agree with exact parent score.
    if best_score != int(
        parent_score
    ):
        return None

    # Same center preference we've used
    # throughout the project.
    center_order = (
        3, 2, 4, 1, 5, 0, 6
    )

    best_moves = {
        col
        for col, score in scored
        if score == best_score
    }

    for col in center_order:
        if col in best_moves:
            return col

    return None


def choose_move_with_info(
    observation,
    configuration,
):
    p1, p2 = board_to_bitboards(
        observation.board
    )

    player = observation.mark

    move = exact_book_move(
        p1,
        p2,
        player,
    )

    if move is not None:
        return int(move), {
            "source": "V7_BOOK",
        }

    move, info = v61_choose(
        observation,
        configuration,
    )

    return int(move), {
        "source": "V6.1",
        "fallback_info": info,
    }


def agent(
    observation,
    configuration,
):
    move, _ = choose_move_with_info(
        observation,
        configuration,
    )

    return int(move)