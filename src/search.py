import time

from sympy import ordered

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
        """
        Check the clock periodically instead of on every node.
        """

        if self.nodes & 1023 == 0:
            if (
                time.perf_counter()
                - self.start_time
                >= self.time_limit
            ):
                raise SearchTimeout

    # ========================================================
    # FAST BITBOARD THREAT HELPERS
    # ========================================================

    def winning_columns(
        self,
        p1,
        p2,
        player,
    ):
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

    def winning_count(
        self,
        p1,
        p2,
        player,
    ):
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

    def evaluate(
        self,
        p1,
        p2,
        root_player,
    ):
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
        Order candidate moves for alpha-beta.

        Priority:
        1. TT/PV move
        2. Immediate win
        3. Immediate block
        4. Center preference
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

            # Principal variation / TT move.
            if col == tt_move:
                priority += 1_000_000

            # Immediate win.
            if col in winning:
                priority += 500_000

            # Immediate forced block.
            if col in blocks:
                priority += 250_000

            # Center-first ordering.
            priority += (
                20 - abs(3 - col)
            )

            scored.append(
                (
                    priority,
                    col,
                )
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

        previous_player = (
            3 - player
        )

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
        # FULL BOARD
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

        # Legal moves exist, but all allow an unavoidable
        # tactical loss.
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

        first_child = True

        for col in ordered:
            n1, n2 = play_move(
                p1,
                p2,
                col,
                player,
            )

            if first_child:
                score = -self.negamax(
                    n1,
                    n2,
                    3 - player,
                    depth - 1,
                    -beta,
                    -alpha,
                    ply + 1,
                )
                first_child = False
            else:
                score = -self.negamax(
                    n1,
                    n2,
                    3 - player,
                    depth - 1,
                    -alpha - 1,
                    -alpha,
                    ply + 1,
                )

                if alpha < score < beta:
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
        """
        Search one complete root depth.
        """

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

        # Apply non-losing filtering at the root.
        moves = non_losing_moves(
            p1,
            p2,
            player,
        )

        # If every move loses, still search legal moves so
        # the agent always returns a valid continuation.
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

        first_child = True

        for col in ordered:
            n1, n2 = play_move(
                p1,
                p2,
                col,
                player,
            )

            if first_child:
                score = -self.negamax(
                    n1,
                    n2,
                    3 - player,
                    depth - 1,
                    -beta,
                    -alpha,
                    1,
                )
                first_child = False
            else:
                score = -self.negamax(
                    n1,
                    n2,
                    3 - player,
                    depth - 1,
                    -alpha - 1,
                    -alpha,
                    1,
                )

                if alpha < score < beta:
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

        # Store the root result too.
        #
        # This lets us reconstruct the complete principal
        # variation beginning with the root move.
        self.tt[key] = (
            depth,
            best_score,
            EXACT,
            best_move,
        )

        return (
            best_move,
            best_score,
        )

    # ========================================================
    # PRINCIPAL VARIATION
    # ========================================================

    def get_principal_variation(
        self,
        p1,
        p2,
        player,
        max_length=42,
    ):
        """
        Reconstruct the engine's predicted best line by
        following TT best moves.

        Returns zero-based column numbers.
        """

        pv = []

        current_p1 = p1
        current_p2 = p2
        current_player = player

        for _ in range(
            max_length
        ):
            key = (
                current_p1,
                current_p2,
                current_player,
            )

            entry = self.tt.get(
                key
            )

            if entry is None:
                break

            (
                _,
                _,
                _,
                best_move,
            ) = entry

            if best_move is None:
                break

            legal = valid_moves(
                current_p1,
                current_p2,
            )

            if best_move not in legal:
                break

            pv.append(
                best_move
            )

            current_p1, current_p2 = (
                play_move(
                    current_p1,
                    current_p2,
                    best_move,
                    current_player,
                )
            )

            position = (
                current_p1
                if current_player == 1
                else current_p2
            )

            if has_won(
                position
            ):
                break

            current_player = (
                3 - current_player
            )

        return pv

    # ========================================================
    # DIRECT EXACT ENDGAME SEARCH
    # ========================================================

    def choose_move_exact(
        self,
        p1,
        p2,
        player,
        depth,
    ):
        """
        Direct exact-to-terminal search.

        Unlike normal choose_move(), this skips iterative
        deepening and immediately searches the requested
        terminal depth.

        If the search exceeds its time budget, return a
        tactically safe fallback rather than starting
        another expensive search.
        """

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
            self.completed_depth = depth
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
            self.completed_depth = depth
            return opponent_wins[0]

        # ----------------------------------------------------
        # NON-LOSING MOVES
        # ----------------------------------------------------

        safe_moves = non_losing_moves(
            p1,
            p2,
            player,
        )

        if len(safe_moves) == 1:
            self.completed_depth = depth
            return safe_moves[0]

        candidates = (
            safe_moves
            if safe_moves
            else moves
        )

        # ----------------------------------------------------
        # SAFE TIMEOUT FALLBACK
        # ----------------------------------------------------

        fallback = self.ordered_moves(
            p1,
            p2,
            player,
            moves=candidates,
        )[0]

        # ----------------------------------------------------
        # DIRECT TERMINAL SEARCH
        # ----------------------------------------------------

        try:
            move, _ = self.search_depth(
                p1,
                p2,
                player,
                depth,
            )

            self.completed_depth = depth

            return move

        except SearchTimeout:
            return fallback

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
        """
        Normal timed middlegame search.
        """

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

        # If exactly one move avoids an immediate tactical
        # loss, don't waste search time rediscovering it.
        if len(safe_moves) == 1:
            return safe_moves[0]

        # ----------------------------------------------------
        # INITIAL FALLBACK
        # ----------------------------------------------------

        candidates = (
            safe_moves
            if safe_moves
            else moves
        )

        ordered = self.ordered_moves(
            p1,
            p2,
            player,
            moves=candidates,
        )

        best_move = ordered[0]

        # ----------------------------------------------------
        # ITERATIVE DEEPENING
        # ----------------------------------------------------

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