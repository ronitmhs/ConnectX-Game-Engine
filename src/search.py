import time

from src.bitboard import (
    valid_moves,
    play_move,
    has_won,
    immediate_wins,
)

WIN_SCORE = 1_000_000
INF = 10**9

EXACT = 0
LOWER = 1
UPPER = 2


class SearchTimeout(Exception):
    pass


class SearchEngine:
    def __init__(self, time_limit=1.65):
        self.time_limit = time_limit
        self.start_time = 0.0

        self.tt = {}

        self.nodes = 0
        self.tt_hits = 0
        self.completed_depth = 0

    def check_time(self):
        # Don't call perf_counter on literally every node.
        if self.nodes & 1023 == 0:
            if time.perf_counter() - self.start_time >= self.time_limit:
                raise SearchTimeout

    def evaluate(self, p1, p2, root_player):
        """
        Temporary evaluation.

        We intentionally keep this simple for now.
        Tactical correctness comes from search.
        Strong Connect-Four evaluation comes later.
        """

        opponent = 3 - root_player

        my_wins = immediate_wins(
            p1,
            p2,
            root_player,
        )

        opp_wins = immediate_wins(
            p1,
            p2,
            opponent,
        )

        score = 0

        if len(my_wins) >= 2:
            score += 5000
        elif len(my_wins) == 1:
            score += 500

        if len(opp_wins) >= 2:
            score -= 6000
        elif len(opp_wins) == 1:
            score -= 700

        return score

    def ordered_moves(self, p1, p2, player, tt_move=None):
        moves = valid_moves(p1, p2)

        if not moves:
            return moves

        opponent = 3 - player

        winning = set(
            immediate_wins(
                p1,
                p2,
                player,
            )
        )

        blocks = set(
            immediate_wins(
                p1,
                p2,
                opponent,
            )
        )

        scored = []

        for col in moves:
            priority = 0

            if col == tt_move:
                priority += 1_000_000

            if col in winning:
                priority += 500_000

            if col in blocks:
                priority += 250_000

            # Center-first ordering
            priority += 20 - abs(3 - col)

            scored.append(
                (priority, col)
            )

        scored.sort(reverse=True)

        return [
            col
            for _, col in scored
        ]

    def negamax(
        self,
        p1,
        p2,
        player,
        depth,
        alpha,
        beta,
        ply,
    ):
        self.nodes += 1
        self.check_time()

        # The previous player may have won.
        previous_player = 3 - player
        previous_position = (
            p1 if previous_player == 1 else p2
        )

        if has_won(previous_position):
            return -WIN_SCORE + ply

        moves = valid_moves(p1, p2)

        if not moves:
            return 0

        if depth == 0:
            return self.evaluate(
                p1,
                p2,
                player,
            )

        alpha_original = alpha
        beta_original = beta

        key = (
            p1,
            p2,
            player,
        )

        entry = self.tt.get(key)
        tt_move = None

        if entry is not None:
            stored_depth, value, flag, tt_move = entry

            if stored_depth >= depth:
                self.tt_hits += 1

                if flag == EXACT:
                    return value

                if flag == LOWER:
                    alpha = max(alpha, value)

                elif flag == UPPER:
                    beta = min(beta, value)

                if alpha >= beta:
                    return value

        best = -INF
        best_move = None

        for col in self.ordered_moves(
            p1,
            p2,
            player,
            tt_move,
        ):
            n1, n2 = play_move(
                p1,
                p2,
                col,
                player,
            )

            score = -self.negamax(
                n1,
                n2,
                3 - player,
                depth - 1,
                -beta,
                -alpha,
                ply + 1,
            )

            if score > best:
                best = score
                best_move = col

            alpha = max(alpha, score)

            if alpha >= beta:
                break

        if best <= alpha_original:
            flag = UPPER

        elif best >= beta_original:
            flag = LOWER

        else:
            flag = EXACT

        old = self.tt.get(key)

        if old is None or depth >= old[0]:
            self.tt[key] = (
                depth,
                best,
                flag,
                best_move,
            )

        return best

    def search_depth(
        self,
        p1,
        p2,
        player,
        depth,
    ):
        best_move = None
        best_score = -INF

        alpha = -INF
        beta = INF

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

        for col in self.ordered_moves(
            p1,
            p2,
            player,
            tt_move,
        ):
            n1, n2 = play_move(
                p1,
                p2,
                col,
                player,
            )

            score = -self.negamax(
                n1,
                n2,
                3 - player,
                depth - 1,
                -beta,
                -alpha,
                1,
            )

            if score > best_score:
                best_score = score
                best_move = col

            alpha = max(
                alpha,
                best_score,
            )

        return best_move, best_score

    def choose_move(
        self,
        p1,
        p2,
        player,
        max_depth=42,
    ):
        self.start_time = time.perf_counter()

        self.tt.clear()

        self.nodes = 0
        self.tt_hits = 0
        self.completed_depth = 0

        moves = valid_moves(p1, p2)

        if not moves:
            return None

        # Tactical shortcuts
        wins = immediate_wins(
            p1,
            p2,
            player,
        )

        if wins:
            return wins[0]

        opponent_wins = immediate_wins(
            p1,
            p2,
            3 - player,
        )

        if len(opponent_wins) == 1:
            return opponent_wins[0]

        best_move = moves[0]

        try:
            for depth in range(
                1,
                max_depth + 1,
            ):
                move, score = self.search_depth(
                    p1,
                    p2,
                    player,
                    depth,
                )

                best_move = move
                self.completed_depth = depth

                if score >= WIN_SCORE - 100:
                    break

        except SearchTimeout:
            pass

        return best_move