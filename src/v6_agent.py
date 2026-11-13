from src.bitboard import board_to_bitboards
from src.compact_book import CompactOpeningBook
from src.search import SearchEngine


BOOK = CompactOpeningBook()

SEARCH_TIME = 1.65
EXACT_TIME = 1.40
EXACT_ENDGAME_EMPTIES = 23

def choose_move_with_info(observation, configuration):
    p1, p2 = board_to_bitboards(
        observation.board
    )

    player = observation.mark

    ply = (p1 | p2).bit_count()
    empties = 42 - ply

    # ========================================================
    # SOLVED OPENING BOOK
    # ========================================================

    book_result = BOOK.lookup(
        p1,
        p2,
    )

    if book_result is not None:
        score, _ = book_result

        move = BOOK.choose_move(
            p1,
            p2,
        )

        return int(move), {
            "source": "BOOK",
            "ply": ply,
            "empties": empties,
            "book_score": score,
            "book_moves": BOOK.get_best_moves(
                p1,
                p2,
            ),
            "depth": None,
            "nodes": 0,
        }

    # ========================================================
    # EXACT ENDGAME SEARCH
    # ========================================================

    if empties <= EXACT_ENDGAME_EMPTIES:
        engine = SearchEngine(
            time_limit=EXACT_TIME
        )

        move = engine.choose_move_exact(
            p1,
            p2,
            player,
            depth=empties,
        )

        # Safety fallback in case an unusually difficult
        # position exceeds the exact-search budget.
        if move is not None:
            return int(move), {
                "source": "EXACT",
                "ply": ply,
                "empties": empties,
                "book_score": None,
                "book_moves": None,
                "depth": engine.completed_depth,
                "nodes": engine.nodes,
            }

    # ========================================================
    # TIMED MIDDLEGAME SEARCH
    # ========================================================

    engine = SearchEngine(
        time_limit=SEARCH_TIME
    )

    move = engine.choose_move(
        p1,
        p2,
        player,
    )

    return int(move), {
        "source": "SEARCH",
        "ply": ply,
        "empties": empties,
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