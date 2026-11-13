import time

from tests.test_solver_regressions import (
    position_from_sequence,
)

from src.search import SearchEngine


SEQUENCE = "444443333147"


class OrderExperimentEngine(SearchEngine):
    def __init__(
        self,
        time_limit=10.0,
        forced_root_order=None,
    ):
        super().__init__(
            time_limit=time_limit
        )

        self.forced_root_order = (
            forced_root_order
        )

    def ordered_moves(
        self,
        p1,
        p2,
        player,
        tt_move=None,
        moves=None,
    ):
        ordered = super().ordered_moves(
            p1,
            p2,
            player,
            tt_move,
            moves,
        )

        if (
            self.forced_root_order
            is None
        ):
            return ordered

        # Only alter the root position used by this
        # diagnostic experiment.
        if (
            p1,
            p2,
            player,
        ) == self.root_position:
            available = set(ordered)

            result = [
                move
                for move
                in self.forced_root_order
                if move in available
            ]

            result.extend(
                move
                for move in ordered
                if move not in result
            )

            return result

        return ordered

    def run(
        self,
        p1,
        p2,
        player,
        max_depth,
    ):
        self.root_position = (
            p1,
            p2,
            player,
        )

        return self.choose_move(
            p1,
            p2,
            player,
            max_depth=max_depth,
        )


def run_case(
    name,
    order,
    p1,
    p2,
    player,
):
    engine = OrderExperimentEngine(
        time_limit=10.0,
        forced_root_order=order,
    )

    start = time.perf_counter()

    move = engine.run(
        p1,
        p2,
        player,
        max_depth=15,
    )

    elapsed = (
        time.perf_counter()
        - start
    )

    print(
        f"{name:20} | "
        f"move={move} | "
        f"nodes={engine.nodes:7} | "
        f"TT={engine.tt_hits:6} | "
        f"time={elapsed:.4f}s"
    )


def main():
    p1, p2, player = (
        position_from_sequence(
            SEQUENCE
        )
    )

    print("=" * 80)
    print("ROOT ORDER EXPERIMENT")
    print("=" * 80)

    print(
        "Sequence:",
        SEQUENCE,
    )

    print(
        "Pons-best move: 5",
    )

    print()

    # Current V6/PVS behavior.
    run_case(
        "CURRENT",
        None,
        p1,
        p2,
        player,
    )

    # Correct move first.
    run_case(
        "MOVE 5 FIRST",
        [5, 4, 2, 6, 0],
        p1,
        p2,
        player,
    )

    # Correct move second.
    run_case(
        "MOVE 5 SECOND",
        [4, 5, 2, 6, 0],
        p1,
        p2,
        player,
    )

    # Center-style ordering without TT first.
    run_case(
        "CENTER ORDER",
        [4, 2, 5, 1, 6, 0],
        p1,
        p2,
        player,
    )


if __name__ == "__main__":
    main()