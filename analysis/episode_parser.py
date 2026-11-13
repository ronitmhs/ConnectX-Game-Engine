import json
from pathlib import Path


EPISODE_DIR = Path("data/episodes")
OUR_NAME = "Ronit Shah"


def load_episode(path):
    with open(path, "r") as f:
        return json.load(f)


def get_result(episode):
    names = episode["info"]["TeamNames"]
    rewards = episode["rewards"]

    our_index = names.index(OUR_NAME)
    opponent_index = 1 - our_index

    reward = rewards[our_index]

    if reward == 1:
        result = "WIN"
    elif reward == -1:
        result = "LOSS"
    else:
        result = "DRAW"

    return {
        "episode_id": episode["info"]["EpisodeId"],
        "opponent": names[opponent_index],
        "our_player": our_index + 1,
        "result": result,
    }


def get_our_positions(episode):
    """
    Return every position immediately before one of our moves.

    Each record contains:
        board
        player
        actual_move
        step
    """
    names = episode["info"]["TeamNames"]
    our_index = names.index(OUR_NAME)
    our_player = our_index + 1

    positions = []

    steps = episode["steps"]

    for step_index in range(len(steps) - 1):
        agents = steps[step_index]

        our_state = agents[our_index]

        if our_state["status"] != "ACTIVE":
            continue

        observation = our_state.get("observation", {})
        board = observation.get("board")

        if board is None:
            continue

        # Kaggle stores the action taken in the following
        # state for this agent.
        next_state = steps[step_index + 1][our_index]
        actual_move = next_state.get("action")

        if actual_move is None:
            continue

        positions.append(
            {
                "step": step_index,
                "board": board,
                "player": our_player,
                "actual_move": actual_move,
            }
        )

    return positions


def load_all_episodes():
    episodes = []

    for path in sorted(EPISODE_DIR.glob("*.json")):
        episode = load_episode(path)

        episodes.append(
            {
                "path": path,
                "episode": episode,
                "result": get_result(episode),
                "positions": get_our_positions(episode),
            }
        )

    return episodes


if __name__ == "__main__":
    episodes = load_all_episodes()

    wins = 0
    losses = 0
    draws = 0
    positions = 0

    first_games = 0
    second_games = 0

    for item in episodes:
        info = item["result"]

        positions += len(item["positions"])

        if info["result"] == "WIN":
            wins += 1
        elif info["result"] == "LOSS":
            losses += 1
        else:
            draws += 1

        if info["our_player"] == 1:
            first_games += 1
        else:
            second_games += 1

    print("Episodes:", len(episodes))
    print("Wins:", wins)
    print("Losses:", losses)
    print("Draws:", draws)

    print()
    print("As Player 1:", first_games)
    print("As Player 2:", second_games)

    print()
    print("Recorded decision positions:", positions)