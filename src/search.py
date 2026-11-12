import time

from src.bitboard import (
    valid_moves,
    play_move,
    has_won,
    playable_winning_positions,
    non_losing_moves,
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

    # ========================================================
    # TIME MANAGEMENT
    # ========================================================

    def check_time(self):
        # Avoid calling perf_counter() on every node.
        if self.nodes & 1023 == 0:
            if (
                time.perf_counter() - self.start_time
                >= self.time_limit
            ):
                raise SearchTimeout

    # ========================================================
    # FAST BITBOARD THREAT HELPERS
    # ========================================================

    def winning_columns(self, p1, p2, player):
        """
        Return columns where player can win immediately.
        """

        wins = playable_winning_positions(
            p1,
            p2,
            player,
        )

        columns = []

        for col in range(7):
            column_mask = (
                ((1 << 6) - 1)
                << (col * 7)
            )

            if wins & column_mask:
                columns.append(col)

        return columns

    def winning_count(self, p1, p2, player):
        """
        Number of immediately playable winning squares.
        """

        wins = playable_winning_positions(
            p1,
            p2,
            player,
        )

        return wins.bit_count()

    # ========================================================
    # EVALUATION
    # ========================================================

    def evaluate(self, p1, p2, root_player):
        """
        Lightweight tactical evaluation.
        """

        opponent = 3 - root_player

        my_wins = self.winning_count(
            p1,
            p2,
            root_player,
        )

        opp_wins = self.winning_count(
            p1,
            p2,
            opponent,
        )

        score = 0

        if my_wins >= 2:
            score += 5000

        elif my_wins == 1:
            score += 500

        if opp_wins >= 2:
            score -= 6000

        elif opp_wins == 1:
            score -= 700

        return score

    # ========================================================
    # MOVE ORDERING
    # ========================================================

    def ordered_moves(
        self,
        p1,
        p2,
        player,
        tt_move=None,
        moves=None,
    ):
        """
        Order either a supplied candidate-move list or
        all legal moves.

        Search passes the already-filtered non-losing moves
        here so unsafe moves are never reintroduced.
        """

        if moves is None:
            moves = valid_moves(
                p1,
                p2,
            )

        if not moves:
            return moves

        opponent = 3 - player

        winning = set(
            self.winning_columns(
                p1,
                p2,
                player,
            )
        )

        blocks = set(
            self.winning_columns(
                p1,
                p2,
                opponent,
            )
        )

        scored = []

        for col in moves:
            priority = 0

            # TT / principal variation move
            if col == tt_move:
                priority += 1_000_000

            # Immediate win
            if col in winning:
                priority += 500_000

            # Immediate forced block
            if col in blocks:
                priority += 250_000

            # Center-first positional ordering
            priority += (
                20 - abs(3 - col)
            )

            scored.append(
                (priority, col)
            )

        scored.sort(
            reverse=True
        )

        return [
            col
            for _, col in scored
        ]

    # ========================================================
    # NEGAMAX + ALPHA-BETA
    # ========================================================

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

        # ----------------------------------------------------
        # TERMINAL WIN CHECK
        # ----------------------------------------------------

        previous_player = 3 - player

        previous_position = (
            p1
            if previous_player == 1
            else p2
        )

        if has_won(
            previous_position
        ):
            return (
                -WIN_SCORE + ply
            )

        # ----------------------------------------------------
        # FULL BOARD CHECK
        # ----------------------------------------------------

        legal_moves = valid_moves(
            p1,
            p2,
        )

        if not legal_moves:
            return 0

        # ----------------------------------------------------
        # SEARCH HORIZON
        # ----------------------------------------------------

        if depth == 0:
            return self.evaluate(
                p1,
                p2,
                player,
            )

        # ----------------------------------------------------
        # NON-LOSING MOVE FILTER
        # ----------------------------------------------------

        moves = non_losing_moves(
            p1,
            p2,
            player,
        )

        # If legal moves exist but none are non-losing,
        # the opponent has an unavoidable tactical win.
        if not moves:
            return (
                -WIN_SCORE + ply
            )

        # ----------------------------------------------------
        # TRANSPOSITION TABLE
        # ----------------------------------------------------

        alpha_original = alpha
        beta_original = beta

        key = (
            p1,
            p2,
            player,
        )

        entry = self.tt.get(
            key
        )

        tt_move = None

        if entry is not None:
            (
                stored_depth,
                value,
                flag,
                tt_move,
            ) = entry

            if stored_depth >= depth:
                self.tt_hits += 1

                if flag == EXACT:
                    return value

                if flag == LOWER:
                    alpha = max(
                        alpha,
                        value,
                    )

                elif flag == UPPER:
                    beta = min(
                        beta,
                        value,
                    )

                if alpha >= beta:
                    return value

        # ----------------------------------------------------
        # SEARCH CHILDREN
        # ----------------------------------------------------

        best = -INF
        best_move = None

        ordered = self.ordered_moves(
            p1,
            p2,
            player,
            tt_move,
            moves,
        )

        for col in ordered:
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

            if score > alpha:
                alpha = score

            if alpha >= beta:
                break

        # ----------------------------------------------------
        # STORE TT BOUND
        # ----------------------------------------------------

        if best <= alpha_original:
            flag = UPPER

        elif best >= beta_original:
            flag = LOWER

        else:
            flag = EXACT

        old = self.tt.get(
            key
        )

        if (
            old is None
            or depth >= old[0]
        ):
            self.tt[key] = (
                depth,
                best,
                flag,
                best_move,
            )

        return best

    # ========================================================
    # ROOT SEARCH
    # ========================================================

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

        entry = self.tt.get(
            key
        )

        tt_move = (
            entry[3]
            if entry is not None
            else None
        )

        # Apply the same tactical filtering at the root.
        moves = non_losing_moves(
            p1,
            p2,
            player,
        )

        # If everything is losing, search legal moves anyway
        # so the agent still returns a valid continuation.
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

        for col in ordered:
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

            if best_score > alpha:
                alpha = best_score

        return (
            best_move,
            best_score,
        )

    # ========================================================
    # ITERATIVE DEEPENING
    # ========================================================

    def choose_move(
        self,
        p1,
        p2,
        player,
        max_depth=42,
    ):
        self.start_time = (
            time.perf_counter()
        )

        self.tt.clear()

        self.nodes = 0
        self.tt_hits = 0
        self.completed_depth = 0

        moves = valid_moves(
            p1,
            p2,
        )

        if not moves:
            return None

        # ----------------------------------------------------
        # IMMEDIATE WIN
        # ----------------------------------------------------

        wins = self.winning_columns(
            p1,
            p2,
            player,
        )

        if wins:
            return wins[0]

        # ----------------------------------------------------
        # FORCED IMMEDIATE BLOCK
        # ----------------------------------------------------

        opponent_wins = (
            self.winning_columns(
                p1,
                p2,
                3 - player,
            )
        )

        if len(opponent_wins) == 1:
            return opponent_wins[0]

        # ----------------------------------------------------
        # NON-LOSING ROOT MOVES
        # ----------------------------------------------------

        safe_moves = non_losing_moves(
            p1,
            p2,
            player,
        )

        # If only one move avoids immediate tactical loss,
        # there is no reason to spend search time rediscovering it.
        if len(safe_moves) == 1:
            return safe_moves[0]

        # ----------------------------------------------------
        # ITERATIVE DEEPENING
        # ----------------------------------------------------

        best_move = (
            safe_moves[0]
            if safe_moves
            else moves[0]
        )

        try:
            for depth in range(
                1,
                max_depth + 1,
            ):
                move, score = (
                    self.search_depth(
                        p1,
                        p2,
                        player,
                        depth,
                    )
                )

                # Only retain fully completed iterations.
                best_move = move
                self.completed_depth = depth

                # Proven forced win.
                if (
                    score
                    >= WIN_SCORE - 100
                ):
                    break

        except SearchTimeout:
            pass

        return best_move