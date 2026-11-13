from analysis.solver_oracle import (
    solver_analyze,
    best_solver_moves,
)
from src.bitboard import play_move
from src.search import SearchEngine


START_SEQUENCE = "44447465555"


def position_from_sequence(sequence):
    p1 = 0
    p2 = 0
    player = 1

    for ch in sequence:
        col = int(ch) - 1

        p1, p2 = play_move(
            p1,
            p2,
            col,
            player,
        )

        player = 3 - player

    return p1, p2, player


def main():
    # --------------------------------------------------------
    # BUILD STARTING POSITION
    # --------------------------------------------------------

    p1, p2, player = position_from_sequence(
        START_SEQUENCE
    )

    # --------------------------------------------------------
    # RUN V6 SEARCH
    # --------------------------------------------------------

    engine = SearchEngine(
        time_limit=1.65
    )

    root_move = engine.choose_move(
        p1,
        p2,
        player,
    )

    pv = engine.get_principal_variation(
        p1,
        p2,
        player,
    )

    print("=" * 76)
    print("V6 PRINCIPAL VARIATION vs PASCAL PONS")
    print("=" * 76)

    print("Starting sequence:", START_SEQUENCE)
    print("Root player:", player)
    print("V6 root move:", root_move)
    print("Completed depth:", engine.completed_depth)
    print("Nodes:", engine.nodes)
    print("TT hits:", engine.tt_hits)

    print()

    print(
        "V6 PV:",
        "".join(
            str(move + 1)
            for move in pv
        ),
    )

    print()

    # --------------------------------------------------------
    # WALK THE V6 PV
    # --------------------------------------------------------

    sequence = START_SEQUENCE

    current_player = player

    first_deviation = None

    optimal_count = 0

    for pv_index, move in enumerate(pv):
        scores = solver_analyze(
            sequence
        )

        (
            solver_score,
            solver_moves,
        ) = best_solver_moves(
            scores
        )

        chosen_score = scores[move]

        optimal = (
            move in solver_moves
        )

        if optimal:
            optimal_count += 1

        # ROOT means the same side that started the search.
        side = (
            "V6"
            if current_player == player
            else "OPP"
        )

        print("-" * 76)

        print(
            f"PV ply {pv_index:2} | "
            f"{side:3} | "
            f"position={sequence}"
        )

        print(
            f"V6-PV move: {move} "
            f"(Pons column {move + 1})"
        )

        print(
            "Solver scores:",
            scores,
        )

        print(
            "Solver best score:",
            solver_score,
        )

        print(
            "Solver best moves:",
            solver_moves,
        )

        print(
            "Chosen move score:",
            chosen_score,
        )

        print(
            "PV move optimal:",
            "YES" if optimal else "NO",
        )

        # ----------------------------------------------------
        # CLASSIFY THE DEVIATION
        # ----------------------------------------------------

        if (
            not optimal
            and first_deviation is None
        ):
            if solver_score > 0:
                before = "WIN"

            elif solver_score == 0:
                before = "DRAW"

            else:
                before = "LOSS"

            if chosen_score > 0:
                after = "WIN"

            elif chosen_score == 0:
                after = "DRAW"

            else:
                after = "LOSS"

            first_deviation = {
                "pv_index": pv_index,
                "sequence": sequence,
                "side": side,
                "move": move,
                "solver_moves": solver_moves,
                "solver_score": solver_score,
                "chosen_score": chosen_score,
                "before": before,
                "after": after,
            }

        # Add V6's predicted move to the Pons sequence.
        sequence += str(
            move + 1
        )

        current_player = (
            3 - current_player
        )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print()
    print("=" * 76)
    print("SUMMARY")
    print("=" * 76)

    print(
        "PV moves checked:",
        len(pv),
    )

    print(
        "Solver-optimal PV moves:",
        optimal_count,
    )

    if pv:
        print(
            "PV optimality rate:",
            f"{100.0 * optimal_count / len(pv):.1f}%",
        )

    print()

    if first_deviation is None:
        print(
            "V6's entire available PV follows "
            "a Pascal-Pons-best move at every position."
        )

    else:
        d = first_deviation

        print("FIRST PV DEVIATION")
        print()

        print(
            "PV index:",
            d["pv_index"],
        )

        print(
            "Side:",
            d["side"],
        )

        print(
            "Position:",
            d["sequence"],
        )

        print(
            "V6 predicted move:",
            d["move"],
        )

        print(
            "Pons column:",
            d["move"] + 1,
        )

        print(
            "Pons-best moves:",
            d["solver_moves"],
        )

        print(
            "Best score:",
            d["solver_score"],
        )

        print(
            "Chosen score:",
            d["chosen_score"],
        )

        print(
            "Game-theoretic transition:",
            f"{d['before']} -> {d['after']}",
        )

        print()

        if (
            d["before"] == d["after"]
        ):
            print(
                "The PV differs from solver-best play, "
                "but preserves the same game-theoretic result."
            )

        else:
            print(
                "This deviation changes the "
                "game-theoretic result."
            )


if __name__ == "__main__":
    main()