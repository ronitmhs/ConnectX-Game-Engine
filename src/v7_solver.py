from dataclasses import dataclass

from src.bitboard import (
    BOARD_MASK,
    BOTTOM_MASK,
    CENTER_ORDER,
    winning_positions,
)

from src.v7_book import (
    V7OpeningBook,
    canonical_key,
)


BOARD_SIZE = 42

TT_EXACT = 0
TT_LOWER = 1
TT_UPPER = 2


def trunc_div2(value):
    """
    Match Rust/C/C++ signed integer division.

    Python // floors negative values.
    Rust integer division truncates toward zero.
    """
    if value >= 0:
        return value // 2

    return -((-value) // 2)


@dataclass(slots=True)
class TTEntry:
    value: int
    flag: int
    depth: int


class V7ExactSolver:
    def __init__(
        self,
        book=None,
    ):
        self.book = (
            book
            if book is not None
            else V7OpeningBook()
        )

        self.tt = {}

        self.nodes = 0
        self.tt_hits = 0
        self.book_hits = 0

    def reset(self):
        self.tt.clear()

        self.nodes = 0
        self.tt_hits = 0
        self.book_hits = 0

    @staticmethod
    def possible(mask):
        return (
            (mask + BOTTOM_MASK)
            & BOARD_MASK
        )

    @staticmethod
    def column_mask(col):
        return (
            ((1 << 6) - 1)
            << (col * 7)
        )

    @staticmethod
    def play(
        current,
        mask,
        col,
    ):
        next_current = (
            current ^ mask
        )

        bottom = (
            1 << (col * 7)
        )

        next_mask = (
            mask
            | (mask + bottom)
        )

        return (
            next_current,
            next_mask,
        )

    @staticmethod
    def can_win_next(
        current,
        mask,
    ):
        return bool(
            winning_positions(
                current,
                mask,
            )
            & V7ExactSolver.possible(
                mask
            )
        )

    @staticmethod
    def possible_non_losing_moves(
        current,
        mask,
    ):
        possible = (
            V7ExactSolver.possible(
                mask
            )
        )

        opponent = (
            current ^ mask
        )

        opponent_wins = (
            winning_positions(
                opponent,
                mask,
            )
        )

        forced = (
            possible
            & opponent_wins
        )

        if forced:
            if (
                forced
                & (forced - 1)
            ):
                return 0

            possible = forced

        return (
            possible
            & ~(
                opponent_wins >> 1
            )
            & BOARD_MASK
        )

    @staticmethod
    def score_move(
        current,
        mask,
        move_bit,
    ):
        return (
            winning_positions(
                current | move_bit,
                mask,
            ).bit_count()
        )

    def book_score(
        self,
        current,
        mask,
    ):
        key = canonical_key(
            current,
            mask,
        )

        score = (
            self.book.lookup_key(
                key
            )
        )

        if score is not None:
            self.book_hits += 1

        return score

    def solve(
        self,
        current,
        mask,
        moves,
    ):
        # ----------------------------------------
        # Opening book
        # ----------------------------------------

        score = self.book_score(
            current,
            mask,
        )

        if score is not None:
            return score

        # ----------------------------------------
        # Immediate win
        # ----------------------------------------

        if self.can_win_next(
            current,
            mask,
        ):
            return (
                BOARD_SIZE
                + 1
                - moves
            ) // 2

        # Rust:
        #
        # -(BOARD_SIZE - moves) / 2
        #
        # Must truncate toward zero.
        minimum = trunc_div2(
            -(
                BOARD_SIZE
                - moves
            )
        )

        maximum = (
            BOARD_SIZE
            + 1
            - moves
        ) // 2

        depth = (
            BOARD_SIZE
            - moves
        )

        # ----------------------------------------
        # Null-window binary solve
        # ----------------------------------------

        while minimum < maximum:
            mid = (
                minimum
                + (
                    maximum
                    - minimum
                ) // 2
            )

            minimum_half = (
                trunc_div2(
                    minimum
                )
            )

            if (
                mid <= 0
                and minimum_half < mid
            ):
                mid = minimum_half

            elif (
                mid >= 0
                and maximum // 2 > mid
            ):
                mid = (
                    maximum // 2
                )

            score = self.negamax(
                current,
                mask,
                moves,
                depth,
                mid,
                mid + 1,
            )

            if score <= mid:
                maximum = score

            else:
                minimum = score

        return minimum

    def negamax(
        self,
        current,
        mask,
        moves,
        depth,
        alpha,
        beta,
    ):
        self.nodes += 1

        if depth == 0:
            return 0

        original_alpha = alpha

        # ----------------------------------------
        # Transposition table
        # ----------------------------------------

        key = canonical_key(
            current,
            mask,
        )

        entry = self.tt.get(
            key
        )

        if (
            entry is not None
            and entry.depth >= depth
        ):
            self.tt_hits += 1

            if (
                entry.flag
                == TT_EXACT
            ):
                return entry.value

            if (
                entry.flag
                == TT_LOWER
                and entry.value >= beta
            ):
                return entry.value

            if (
                entry.flag
                == TT_UPPER
                and entry.value <= alpha
            ):
                return entry.value

        # ----------------------------------------
        # Non-losing move filtering
        # ----------------------------------------

        possible = (
            self.possible_non_losing_moves(
                current,
                mask,
            )
        )

        if possible == 0:
            # Rust:
            #
            # -(BOARD_SIZE - moves) / 2
            return trunc_div2(
                -(
                    BOARD_SIZE
                    - moves
                )
            )

        # ----------------------------------------
        # Score bounds
        # ----------------------------------------

        # Rust:
        #
        # -((BOARD_SIZE - moves) - 2) / 2
        minimum = trunc_div2(
            -(
                BOARD_SIZE
                - moves
                - 2
            )
        )

        if alpha < minimum:
            if minimum >= beta:
                return minimum

            alpha = minimum

        maximum = (
            BOARD_SIZE
            - moves
            - 1
        ) // 2

        if beta > maximum:
            if alpha >= maximum:
                return maximum

            beta = maximum

        # ----------------------------------------
        # Move ordering
        # ----------------------------------------

        candidates = []

        for col in reversed(
            CENTER_ORDER
        ):
            move_bit = (
                possible
                & self.column_mask(
                    col
                )
            )

            if not move_bit:
                continue

            score = self.score_move(
                current,
                mask,
                move_bit,
            )

            candidates.append(
                (
                    score,
                    col,
                )
            )

        rank = {
            col: index
            for index, col
            in enumerate(
                CENTER_ORDER
            )
        }

        candidates.sort(
            key=lambda item: (
                -item[0],
                rank[item[1]],
            )
        )

        # ----------------------------------------
        # Recursive search
        # ----------------------------------------

        for _, col in candidates:
            (
                child_current,
                child_mask,
            ) = self.play(
                current,
                mask,
                col,
            )

            score = -self.negamax(
                child_current,
                child_mask,
                moves + 1,
                depth - 1,
                -beta,
                -alpha,
            )

            if score > alpha:
                alpha = score

            if alpha >= beta:
                break

        # ----------------------------------------
        # TT store
        # ----------------------------------------

        if alpha <= original_alpha:
            flag = TT_UPPER

        elif alpha >= beta:
            flag = TT_LOWER

        else:
            flag = TT_EXACT

        self.tt[key] = TTEntry(
            value=alpha,
            flag=flag,
            depth=depth,
        )

        return alpha

    def move_scores(
        self,
        p1,
        p2,
        player,
    ):
        mask = (
            p1 | p2
        )

        current = (
            p1
            if player == 1
            else p2
        )

        moves = (
            mask.bit_count()
        )

        scores = [
            None
            for _ in range(7)
        ]

        playable = self.possible(
            mask
        )

        for col in CENTER_ORDER:
            move_bit = (
                playable
                & self.column_mask(
                    col
                )
            )

            if not move_bit:
                continue

            # Immediate win.
            if (
                winning_positions(
                    current,
                    mask,
                )
                & move_bit
            ):
                scores[col] = (
                    BOARD_SIZE
                    - moves
                    + 1
                ) // 2

                continue

            (
                child_current,
                child_mask,
            ) = self.play(
                current,
                mask,
                col,
            )

            scores[col] = -self.solve(
                child_current,
                child_mask,
                moves + 1,
            )

        return scores

    def best_moves(
        self,
        p1,
        p2,
        player,
    ):
        scores = self.move_scores(
            p1,
            p2,
            player,
        )

        legal = [
            score
            for score in scores
            if score is not None
        ]

        if not legal:
            return [], scores

        best = max(
            legal
        )

        moves = [
            col
            for col, score
            in enumerate(
                scores
            )
            if score == best
        ]

        return moves, scores