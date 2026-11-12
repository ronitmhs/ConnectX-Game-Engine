from src.bitboard import board_to_bitboards
from src.compact_book import CompactOpeningBook
from src.search import SearchEngine


BOOK = CompactOpeningBook()


def choose_move_with_info(observation, configuration):
    p1, p2 = board_to_bitboards(
        observation.board
    )

    player = observation.mark

    # Current number of played pieces
    ply = (p1 | p2).bit_count()

    # ========================================================
    # SOLVED OPENING BOOK
    # ========================================================

    book_result = BOOK.lookup(
        p1,
        p2,
    )

    if book_result is not None:
        score, move_mask = book_result

        move = BOOK.choose_move(
            p1,
            p2,
        )

        return int(move), {
            "source": "BOOK",
            "ply": ply,
            "book_score": score,
            "book_moves": BOOK.get_best_moves(
                p1,
                p2,
            ),
            "depth": None,
            "nodes": 0,
        }

    # ========================================================
    # SEARCH AFTER BOOK MISS
    # ========================================================

    engine = SearchEngine(
        time_limit=1.65
    )

    move = engine.choose_move(
        p1,
        p2,
        player,
    )

    return int(move), {
        "source": "SEARCH",
        "ply": ply,
        "book_score": None,
        "book_moves": None,
        "depth": engine.completed_depth,
        "nodes": engine.nodes,
    }


def agent(observation, configuration):
    move, _ = choose_move_with_info(
        observation,
        configuration,
    )

    return int(move)