import time

import numpy as np

from src.bitboard import board_to_bitboards
from src.v7_book import V7OpeningBook
from src.v7_compiled import (
    solve,
    find_optimal_move,
    next_tt_age,
    TT_KEYS,
    TT_VALUES,
    TT_FLAGS,
    TT_DEPTHS,
    TT_AGES,
)


BOOK = V7OpeningBook()


def exact_parent_score(
    p1,
    p2,
    player,
):
    """
    Return the exact strong score.

    Prefer the solved depth-12 book.
    If the position is outside the book,
    exact-solve it.
    """

    book_start = time.perf_counter()

    score = BOOK.lookup(
        p1,
        p2,
        player,
    )

    book_time = (
        time.perf_counter()
        - book_start
    )

    if score is not None:
        return int(score), {
            "source": "BOOK",
            "book_time": book_time,
            "solve_time": 0.0,
            "solve_nodes": 0,
            "solve_tt_hits": 0,
        }

    mask = p1 | p2

    current = (
        p1
        if player == 1
        else p2
    )

    moves_played = (
        mask.bit_count()
    )

    nodes = np.zeros(
        1,
        dtype=np.int64,
    )

    hits = np.zeros(
        1,
        dtype=np.int64,
    )

    age = next_tt_age()

    start = time.perf_counter()

    score = solve(
        np.uint64(current),
        np.uint64(mask),
        moves_played,
        nodes,
        hits,
        TT_KEYS,
        TT_VALUES,
        TT_FLAGS,
        TT_DEPTHS,
        TT_AGES,
        age,
    )

    solve_time = (
        time.perf_counter()
        - start
    )

    return int(score), {
        "source": "SOLVE",
        "book_time": book_time,
        "solve_time": solve_time,
        "solve_nodes": int(
            nodes[0]
        ),
        "solve_tt_hits": int(
            hits[0]
        ),
    }


def choose_move_from_bitboards(
    p1,
    p2,
    player,
):
    """
    Choose an exact optimal move and
    return diagnostic information.
    """

    total_start = time.perf_counter()

    score, info = (
        exact_parent_score(
            p1,
            p2,
            player,
        )
    )

    move_start = time.perf_counter()

    move, move_nodes, move_hits = (
        find_optimal_move(
            p1,
            p2,
            player,
            score,
        )
    )

    move_time = (
        time.perf_counter()
        - move_start
    )

    if move < 0:
        raise RuntimeError(
            "V7 exact solver failed to "
            "find a move preserving the "
            f"exact score {score}"
        )

    total_time = (
        time.perf_counter()
        - total_start
    )

    info.update({
        "score": score,
        "move": int(move),
        "move_time": move_time,
        "move_nodes": move_nodes,
        "move_tt_hits": move_hits,
        "total_nodes": (
            info["solve_nodes"]
            + move_nodes
        ),
        "total_tt_hits": (
            info["solve_tt_hits"]
            + move_hits
        ),
        "total_time": total_time,
    })

    return int(move), info


def choose_move_with_info(
    observation,
    configuration,
):
    p1, p2 = board_to_bitboards(
        observation.board
    )

    player = observation.mark

    return choose_move_from_bitboards(
        p1,
        p2,
        player,
    )


def agent(
    observation,
    configuration,
):
    move, _ = choose_move_with_info(
        observation,
        configuration,
    )

    return int(move)