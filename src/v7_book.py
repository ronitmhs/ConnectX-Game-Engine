import bisect
import struct
from pathlib import Path


BLOCK_SIZE = 512

MAGIC = b"C4V7"
VERSION = 1

HEADER = struct.Struct("<4sBII")
BLOCK_RECORD = struct.Struct("<QI")

DEFAULT_BOOK = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "v7"
    / "book_d12.bin"
)


def mirror_bitboard(position):
    mirrored = 0
    column_mask = (1 << 7) - 1

    for col in range(7):
        column = (
            position >> (col * 7)
        ) & column_mask

        mirrored |= (
            column
            << ((6 - col) * 7)
        )

    return mirrored


def canonical_key(
    current,
    mask,
):
    key = current + mask

    mirrored_current = (
        mirror_bitboard(current)
    )

    mirrored_mask = (
        mirror_bitboard(mask)
    )

    mirrored_key = (
        mirrored_current
        + mirrored_mask
    )

    return min(
        key,
        mirrored_key,
    )


def read_varint(
    data,
    position,
):
    value = 0
    shift = 0

    while True:
        byte = data[position]
        position += 1

        value |= (
            (byte & 0x7F)
            << shift
        )

        if byte < 0x80:
            return value, position

        shift += 7


class V7OpeningBook:
    def __init__(
        self,
        path=DEFAULT_BOOK,
    ):
        self.path = Path(path)

        self.data = (
            self.path.read_bytes()
        )

        (
            magic,
            version,
            self.count,
            self.block_count,
        ) = HEADER.unpack_from(
            self.data,
            0,
        )

        if magic != MAGIC:
            raise ValueError(
                "Invalid V7 opening book"
            )

        if version != VERSION:
            raise ValueError(
                f"Unsupported V7 book "
                f"version: {version}"
            )

        index_start = HEADER.size

        self.payload_start = (
            index_start
            + self.block_count
            * BLOCK_RECORD.size
        )

        self.block_keys = []
        self.block_offsets = []

        for index in range(
            self.block_count
        ):
            key, offset = (
                BLOCK_RECORD.unpack_from(
                    self.data,
                    index_start
                    + index
                    * BLOCK_RECORD.size,
                )
            )

            self.block_keys.append(
                key
            )

            self.block_offsets.append(
                offset
            )

        self.payload = memoryview(
            self.data
        )[self.payload_start:]

    def lookup_key(
        self,
        target,
    ):
        block = (
            bisect.bisect_right(
                self.block_keys,
                target,
            )
            - 1
        )

        if block < 0:
            return None

        key = self.block_keys[block]

        position = (
            self.block_offsets[block]
        )

        score = self.payload[
            position
        ]

        position += 1

        if key == target:
            return (
                score
                if score < 128
                else score - 256
            )

        first_index = (
            block * BLOCK_SIZE
        )

        entries = min(
            BLOCK_SIZE,
            self.count - first_index,
        )

        for _ in range(
            1,
            entries,
        ):
            delta, position = (
                read_varint(
                    self.payload,
                    position,
                )
            )

            key += delta

            score = self.payload[
                position
            ]

            position += 1

            if key == target:
                return (
                    score
                    if score < 128
                    else score - 256
                )

            if key > target:
                return None

        return None

    def lookup(
        self,
        p1,
        p2,
        player,
    ):
        mask = p1 | p2

        current = (
            p1
            if player == 1
            else p2
        )

        key = canonical_key(
            current,
            mask,
        )

        return self.lookup_key(
            key
        )

    def __len__(self):
        return self.count