import time


WIDTH = 7
HEIGHT = 6
SIZE = WIDTH * HEIGHT

MIN_SCORE = -(WIDTH * HEIGHT) // 2 + 3
MAX_SCORE = (WIDTH * HEIGHT + 1) // 2 - 3

COLUMN_ORDER = [3, 4, 2, 5, 1, 6, 0]


def _bottom_mask():
    mask = 0

    for col in range(WIDTH):
        mask |= 1 << (
            col * (HEIGHT + 1)
        )

    return mask


BOTTOM_MASK = _bottom_mask()

BOARD_MASK = (
    BOTTOM_MASK
    * ((1 << HEIGHT) - 1)
)


def bottom_mask_col(col):
    return 1 << (
        col * (HEIGHT + 1)
    )


def top_mask_col(col):
    return 1 << (
        HEIGHT - 1
        + col * (HEIGHT + 1)
    )


def column_mask(col):
    return (
        ((1 << HEIGHT) - 1)
        << (col * (HEIGHT + 1))
    )


def compute_winning_position(
    position,
    mask,
):
    """
    Return all currently empty squares that would
    complete a Connect Four for `position`.

    Port of Pascal Pons' Position.hpp.
    """

    # Vertical.
    result = (
        (position << 1)
        & (position << 2)
        & (position << 3)
    )

    # Horizontal.
    shift = HEIGHT + 1

    p = (
        (position << shift)
        & (position << (2 * shift))
    )

    result |= (
        p
        & (position << (3 * shift))
    )

    result |= (
        p
        & (position >> shift)
    )

    p = (
        (position >> shift)
        & (position >> (2 * shift))
    )

    result |= (
        p
        & (position << shift)
    )

    result |= (
        p
        & (position >> (3 * shift))
    )

    # Diagonal /.
    shift = HEIGHT

    p = (
        (position << shift)
        & (position << (2 * shift))
    )

    result |= (
        p
        & (position << (3 * shift))
    )

    result |= (
        p
        & (position >> shift)
    )

    p = (
        (position >> shift)
        & (position >> (2 * shift))
    )

    result |= (
        p
        & (position << shift)
    )

    result |= (
        p
        & (position >> (3 * shift))
    )

    # Diagonal \.
    shift = HEIGHT + 2

    p = (
        (position << shift)
        & (position << (2 * shift))
    )

    result |= (
        p
        & (position << (3 * shift))
    )

    result |= (
        p
        & (position >> shift)
    )

    p = (
        (position >> shift)
        & (position >> (2 * shift))
    )

    result |= (
        p
        & (position << shift)
    )

    result |= (
        p
        & (position >> (3 * shift))
    )

    return (
        result
        & (BOARD_MASK ^ mask)
    )


class SolverTimeout(Exception):
    pass


class Position:
    """
    Pons-style position representation.

    current_position:
        Stones belonging to the player whose turn
        it currently is.

    mask:
        All occupied board cells.
    """

    __slots__ = (
        "current_position",
        "mask",
        "moves",
    )

    def __init__(
        self,
        current_position=0,
        mask=0,
        moves=0,
    ):
        self.current_position = (
            current_position
        )

        self.mask = mask
        self.moves = moves

    def copy(self):
        return Position(
            self.current_position,
            self.mask,
            self.moves,
        )

    def key(self):
        return (
            self.current_position
            + self.mask
        )

    def nb_moves(self):
        return self.moves

    def can_play(self, col):
        return (
            self.mask
            & top_mask_col(col)
        ) == 0

    def possible(self):
        return (
            (self.mask + BOTTOM_MASK)
            & BOARD_MASK
        )

    def winning_position(self):
        return compute_winning_position(
            self.current_position,
            self.mask,
        )

    def opponent_winning_position(self):
        return compute_winning_position(
            self.current_position
            ^ self.mask,
            self.mask,
        )

    def can_win_next(self):
        return bool(
            self.winning_position()
            & self.possible()
        )

    def is_winning_move(self, col):
        return bool(
            self.winning_position()
            & self.possible()
            & column_mask(col)
        )

    def play(self, move):
        """
        Play a move represented by one bit.
        """

        self.current_position ^= (
            self.mask
        )

        self.mask |= move
        self.moves += 1

    def play_col(self, col):
        move = (
            (self.mask + bottom_mask_col(col))
            & column_mask(col)
        )

        self.play(move)

    def possible_non_losing_moves(self):
        """
        Pons' Connect-Four-specific pruning.

        Assumes the current player cannot already
        win immediately.
        """

        possible_mask = self.possible()

        opponent_win = (
            self.opponent_winning_position()
        )

        forced_moves = (
            possible_mask
            & opponent_win
        )

        if forced_moves:
            # Two or more forced blocks means the
            # opponent has an unavoidable double threat.
            if (
                forced_moves
                & (forced_moves - 1)
            ):
                return 0

            possible_mask = forced_moves

        # Never play immediately underneath a square
        # that would become an opponent winning move.
        return (
            possible_mask
            & ~(opponent_win >> 1)
        )

    def move_score(self, move):
        """
        Number of future winning squares created
        by playing this move.
        """

        return compute_winning_position(
            self.current_position | move,
            self.mask,
        ).bit_count()


def from_bitboards(
    p1,
    p2,
    player,
):
    """
    Convert the project's absolute p1/p2 bitboards
    into Pons' relative-to-side-to-move representation.

    The project and Pons both use seven bits per
    column, so no board remapping is necessary.
    """

    mask = p1 | p2

    if player == 1:
        current = p1
    else:
        current = p2

    return Position(
        current_position=current,
        mask=mask,
        moves=mask.bit_count(),
    )


class ExactSolver:
    """
    Connect-Four-specific exact solver based on
    Pascal Pons' null-window negamax design.

    This implementation intentionally starts with a
    Python dict TT so correctness can be established
    before storage-level optimization.
    """

    def __init__(
        self,
        time_limit=None,
    ):
        self.time_limit = time_limit

        self.start_time = 0.0

        self.nodes = 0
        self.tt_hits = 0

        # key -> encoded Pons bound
        self.tt = {}

    def reset(self):
        self.nodes = 0
        self.tt_hits = 0
        self.tt.clear()

        self.start_time = (
            time.perf_counter()
        )

    def check_time(self):
        if self.time_limit is None:
            return

        # Avoid calling perf_counter at every node.
        if self.nodes & 1023:
            return

        if (
            time.perf_counter()
            - self.start_time
            >= self.time_limit
        ):
            raise SolverTimeout

    def ordered_moves(
        self,
        position,
        possible,
    ):
        """
        Pons-style ordering.

        Candidate moves are scored by the number
        of winning squares created.

        COLUMN_ORDER provides the deterministic
        center-first tie preference.
        """

        moves = []

        # Pons inserts using reverse traversal of
        # its center-first column order and retrieves
        # the highest scored move first.
        for col in reversed(
            COLUMN_ORDER
        ):
            move = (
                possible
                & column_mask(col)
            )

            if not move:
                continue

            score = (
                position.move_score(move)
            )

            moves.append(
                (
                    score,
                    col,
                    move,
                )
            )

        # Stable sort preserves the insertion order
        # for equal scores.
        moves.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return [
            move
            for _, _, move in moves
        ]

    def negamax(
        self,
        position,
        alpha,
        beta,
    ):
        """
        Exact bound-search negamax.

        This has no heuristic depth horizon.
        """

        self.nodes += 1
        self.check_time()

        possible = (
            position
            .possible_non_losing_moves()
        )

        # No non-losing continuation:
        # opponent wins next move.
        if possible == 0:
            return -(
                SIZE
                - position.nb_moves()
            ) // 2

        # At most two cells remain and the current
        # player cannot win immediately.
        if (
            position.nb_moves()
            >= SIZE - 2
        ):
            return 0

        # --------------------------------------------------
        # MATHEMATICAL SCORE BOUNDS
        # --------------------------------------------------

        minimum = -(
            SIZE
            - 2
            - position.nb_moves()
        ) // 2

        if alpha < minimum:
            alpha = minimum

            if alpha >= beta:
                return alpha

        maximum = (
            SIZE
            - 1
            - position.nb_moves()
        ) // 2

        if beta > maximum:
            beta = maximum

            if alpha >= beta:
                return beta

        # --------------------------------------------------
        # TRANSPOSITION BOUNDS
        # --------------------------------------------------

        key = position.key()

        value = self.tt.get(key)

        if value is not None:
            self.tt_hits += 1

            threshold = (
                MAX_SCORE
                - MIN_SCORE
                + 1
            )

            if value > threshold:
                # Stored lower bound.
                minimum = (
                    value
                    + 2 * MIN_SCORE
                    - MAX_SCORE
                    - 2
                )

                if alpha < minimum:
                    alpha = minimum

                    if alpha >= beta:
                        return alpha

            else:
                # Stored upper bound.
                maximum = (
                    value
                    + MIN_SCORE
                    - 1
                )

                if beta > maximum:
                    beta = maximum

                    if alpha >= beta:
                        return beta

        # --------------------------------------------------
        # SEARCH CHILDREN
        # --------------------------------------------------

        ordered = self.ordered_moves(
            position,
            possible,
        )

        for move in ordered:
            child = position.copy()
            child.play(move)

            score = -self.negamax(
                child,
                -beta,
                -alpha,
            )

            if score >= beta:
                # Store lower bound.
                self.tt[key] = (
                    score
                    + MAX_SCORE
                    - 2 * MIN_SCORE
                    + 2
                )

                return score

            if score > alpha:
                alpha = score

        # Store upper bound.
        self.tt[key] = (
            alpha
            - MIN_SCORE
            + 1
        )

        return alpha

    def solve(
        self,
        position,
        weak=False,
        reset=True,
    ):
        """
        Return exact Pons-style game score.

        Positive = current player wins.
        Zero     = draw.
        Negative = current player loses.
        """

        if reset:
            self.reset()

        if position.can_win_next():
            return (
                SIZE
                + 1
                - position.nb_moves()
            ) // 2

        minimum = -(
            SIZE
            - position.nb_moves()
        ) // 2

        maximum = (
            SIZE
            + 1
            - position.nb_moves()
        ) // 2

        if weak:
            minimum = -1
            maximum = 1

        while minimum < maximum:
            middle = (
                minimum
                + (
                    maximum
                    - minimum
                ) // 2
            )

            if (
                middle <= 0
                and minimum // 2
                < middle
            ):
                middle = (
                    minimum // 2
                )

            elif (
                middle >= 0
                and maximum // 2
                > middle
            ):
                middle = (
                    maximum // 2
                )

            result = self.negamax(
                position,
                middle,
                middle + 1,
            )

            if result <= middle:
                maximum = result
            else:
                minimum = result

        return minimum

    def analyze(
        self,
        position,
        weak=False,
    ):
        """
        Exact score of every playable column.

        None means the column is illegal.
        """

        self.reset()

        scores = [None] * WIDTH

        for col in range(WIDTH):
            if not position.can_play(col):
                continue

            if position.is_winning_move(
                col
            ):
                scores[col] = (
                    SIZE
                    + 1
                    - position.nb_moves()
                ) // 2

                continue

            child = position.copy()
            child.play_col(col)

            scores[col] = -self.solve(
                child,
                weak=weak,
                reset=False,
            )

        return scores

    def best_moves(
        self,
        position,
        weak=False,
    ):
        scores = self.analyze(
            position,
            weak=weak,
        )

        legal_scores = [
            score
            for score in scores
            if score is not None
        ]

        if not legal_scores:
            return (
                None,
                [],
                scores,
            )

        best_score = max(
            legal_scores
        )

        moves = [
            col
            for col, score
            in enumerate(scores)
            if score == best_score
        ]

        return (
            best_score,
            moves,
            scores,
        )