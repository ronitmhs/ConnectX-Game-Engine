from src.bitboard import play_move
from src.search import SearchEngine


SEQUENCE = "44447465555"


def position_from_sequence(seq):
    p1 = 0
    p2 = 0
    player = 1

    for ch in seq:
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
    p1, p2, player = (
        position_from_sequence(
            SEQUENCE
        )
    )

    engine = SearchEngine(
        time_limit=1.65
    )

    move = engine.choose_move(
        p1,
        p2,
        player,
    )

    pv = engine.get_principal_variation(
        p1,
        p2,
        player,
    )

    print("=" * 64)
    print("V6 PRINCIPAL VARIATION")
    print("=" * 64)

    print("Sequence:", SEQUENCE)
    print("Player:", player)
    print("Best move:", move)

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

    print()

    print(
        "PV zero-based:",
        pv,
    )

    print(
        "PV Pons notation:",
        "".join(
            str(move + 1)
            for move in pv
        ),
    )

    print()

    current_player = player

    for ply, move in enumerate(pv):
        side = (
            "ROOT"
            if ply == 0
            else (
                "OPP"
                if current_player
                != player
                else "ROOT"
            )
        )

        print(
            f"{ply:2} | "
            f"{side:4} | "
            f"column {move}"
        )

        current_player = (
            3 - current_player
        )


if __name__ == "__main__":
    main()