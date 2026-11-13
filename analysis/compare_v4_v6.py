from collections import Counter

from analysis.episode_parser import load_all_episodes
from src.bitboard import board_to_bitboards
from src.search import SearchEngine


# Use a short search for bulk analysis.
# 305 positions * 1.65 sec would take too long.
TIME_LIMIT = 0.15


def analyze():
    episodes = load_all_episodes()

    total_positions = 0
    agreements = 0
    disagreements = 0

    win_agreements = 0
    loss_agreements = 0

    win_disagreements = 0
    loss_disagreements = 0

    v4_moves = Counter()
    v6_moves = Counter()

    disagreement_records = []

    for item in episodes:
        result_info = item["result"]
        result = result_info["result"]

        episode_id = result_info["episode_id"]
        opponent = result_info["opponent"]

        for position in item["positions"]:
            total_positions += 1

            board = position["board"]
            player = position["player"]
            v4_move = position["actual_move"]

            p1, p2 = board_to_bitboards(board)

            engine = SearchEngine(
                time_limit=TIME_LIMIT
            )

            v6_move = engine.choose_move(
                p1,
                p2,
                player,
            )

            v4_moves[v4_move] += 1
            v6_moves[v6_move] += 1

            if v4_move == v6_move:
                agreements += 1

                if result == "WIN":
                    win_agreements += 1

                elif result == "LOSS":
                    loss_agreements += 1

            else:
                disagreements += 1

                if result == "WIN":
                    win_disagreements += 1

                elif result == "LOSS":
                    loss_disagreements += 1

                disagreement_records.append(
                    {
                        "episode_id": episode_id,
                        "opponent": opponent,
                        "result": result,
                        "step": position["step"],
                        "player": player,
                        "v4_move": v4_move,
                        "v6_move": v6_move,
                        "depth": engine.completed_depth,
                        "nodes": engine.nodes,
                    }
                )

    agreement_rate = (
        agreements / total_positions * 100
        if total_positions
        else 0
    )

    print("=" * 60)
    print("V4 vs V6 REAL-GAME DECISION ANALYSIS")
    print("=" * 60)

    print()
    print("Positions:", total_positions)
    print("Agreements:", agreements)
    print("Disagreements:", disagreements)

    print(
        "Agreement rate:",
        f"{agreement_rate:.1f}%"
    )

    print()
    print("Disagreements from V4 wins:", win_disagreements)
    print("Disagreements from V4 losses:", loss_disagreements)

    print()
    print("V4 move distribution:")
    print(dict(sorted(v4_moves.items())))

    print()
    print("V6 move distribution:")
    print(dict(sorted(v6_moves.items())))

    print()
    print("=" * 60)
    print("FIRST 20 DISAGREEMENTS")
    print("=" * 60)

    for record in disagreement_records[:20]:
        print()

        print(
            f"Episode {record['episode_id']} "
            f"vs {record['opponent']}"
        )

        print(
            f"Result: {record['result']} | "
            f"Step: {record['step']} | "
            f"Player: {record['player']}"
        )

        print(
            f"V4: {record['v4_move']} | "
            f"V6: {record['v6_move']}"
        )

        print(
            f"V6 depth: {record['depth']} | "
            f"nodes: {record['nodes']}"
        )


if __name__ == "__main__":
    analyze()