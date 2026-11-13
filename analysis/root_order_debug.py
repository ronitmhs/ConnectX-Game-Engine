from tests.test_solver_regressions import (
    position_from_sequence,
)

from src.search import SearchEngine
from src.bitboard import (
    non_losing_moves,
    valid_moves,
)


SEQUENCE = "444443333147"


class DebugSearchEngine(SearchEngine):
    def search_depth(
        self,
        p1,
        p2,
        player,
        depth,
    ):
        key = (
            p1,
            p2,
            player,
        )

        entry = self.tt.get(key)

        tt_move = (
            entry[3]
            if entry is not None
            else None
        )

        moves = non_losing_moves(
            p1,
            p2,
            player,
        )

        if not moves:
            moves = valid_moves(
                p1,
                p2,
            )

        ordered = self.ordered_moves(
            p1,
            p2,
            player,
            tt_move,
            moves,
        )

        if depth in (14, 15):
            print(
                f"DEPTH {depth} | "
                f"TT MOVE {tt_move} | "
                f"ORDER {ordered}"
            )

        return super().search_depth(
            p1,
            p2,
            player,
            depth,
        )


def main():
    p1, p2, player = (
        position_from_sequence(
            SEQUENCE
        )
    )

    engine = DebugSearchEngine(
        time_limit=10.0
    )

    move = engine.choose_move(
        p1,
        p2,
        player,
        max_depth=15,
    )

    print()
    print("=" * 60)
    print("RESULT")
    print("=" * 60)

    print(
        "Sequence:",
        SEQUENCE,
    )

    print(
        "Final move:",
        move,
    )

    print(
        "Completed depth:",
        engine.completed_depth,
    )

    print(
        "Nodes:",
        engine.nodes,
    )

    print(
        "TT hits:",
        engine.tt_hits,
    )


if __name__ == "__main__":
    main()