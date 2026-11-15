import argparse
import base64
import bisect
import lzma
import struct
import time
from pathlib import Path


RECORD_SIZE = 9
BLOCK_SIZE = 512

MAGIC = b"C4V7"
VERSION = 1

HEADER = struct.Struct("<4sBII")
BLOCK_RECORD = struct.Struct("<QI")


def read_records(path):
    data = path.read_bytes()

    if len(data) % RECORD_SIZE:
        raise ValueError(
            "Input must contain sorted "
            "9-byte <u64 key, i8 score> records"
        )

    count = len(data) // RECORD_SIZE

    keys = []
    scores = bytearray()

    previous = -1

    for offset in range(
        0,
        len(data),
        RECORD_SIZE,
    ):
        key = int.from_bytes(
            data[offset:offset + 8],
            "little",
        )

        score = data[offset + 8]

        if key <= previous:
            raise ValueError(
                "Input keys are not strictly sorted"
            )

        keys.append(key)
        scores.append(score)

        previous = key

    return keys, scores


def put_varint(value, output):
    while value >= 0x80:
        output.append(
            (value & 0x7F) | 0x80
        )
        value >>= 7

    output.append(value)


def read_varint(data, position):
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


def build_blocks(keys, scores):
    block_keys = []
    block_offsets = []
    payload = bytearray()

    count = len(keys)

    for start in range(
        0,
        count,
        BLOCK_SIZE,
    ):
        block_keys.append(
            keys[start]
        )

        block_offsets.append(
            len(payload)
        )

        end = min(
            start + BLOCK_SIZE,
            count,
        )

        # First key is already stored in
        # the block index.
        payload.append(
            scores[start]
        )

        previous = keys[start]

        for index in range(
            start + 1,
            end,
        ):
            key = keys[index]

            put_varint(
                key - previous,
                payload,
            )

            payload.append(
                scores[index]
            )

            previous = key

    return (
        block_keys,
        block_offsets,
        payload,
    )


def serialize(
    count,
    block_keys,
    block_offsets,
    payload,
):
    output = bytearray()

    output.extend(
        HEADER.pack(
            MAGIC,
            VERSION,
            count,
            len(block_keys),
        )
    )

    for key, offset in zip(
        block_keys,
        block_offsets,
    ):
        output.extend(
            BLOCK_RECORD.pack(
                key,
                offset,
            )
        )

    output.extend(payload)

    return bytes(output)


def parse_book(data):
    (
        magic,
        version,
        count,
        block_count,
    ) = HEADER.unpack_from(
        data,
        0,
    )

    if magic != MAGIC:
        raise ValueError(
            "Invalid V7 book magic"
        )

    if version != VERSION:
        raise ValueError(
            f"Unsupported version: {version}"
        )

    index_start = HEADER.size

    payload_start = (
        index_start
        + block_count
        * BLOCK_RECORD.size
    )

    block_keys = []
    block_offsets = []

    for index in range(
        block_count
    ):
        key, offset = (
            BLOCK_RECORD.unpack_from(
                data,
                index_start
                + index
                * BLOCK_RECORD.size,
            )
        )

        block_keys.append(key)
        block_offsets.append(offset)

    return (
        count,
        block_keys,
        block_offsets,
        data[payload_start:],
    )


def lookup(
    target,
    count,
    block_keys,
    block_offsets,
    payload,
):
    block = (
        bisect.bisect_right(
            block_keys,
            target,
        )
        - 1
    )

    if block < 0:
        return None

    key = block_keys[block]

    position = (
        block_offsets[block]
    )

    score = payload[position]
    position += 1

    if key == target:
        return score

    first_index = (
        block * BLOCK_SIZE
    )

    entries = min(
        BLOCK_SIZE,
        count - first_index,
    )

    for _ in range(
        1,
        entries,
    ):
        delta, position = (
            read_varint(
                payload,
                position,
            )
        )

        key += delta

        score = payload[position]
        position += 1

        if key == target:
            return score

        if key > target:
            return None

    return None


def verify(
    original_keys,
    original_scores,
    book_data,
):
    (
        count,
        block_keys,
        block_offsets,
        payload,
    ) = parse_book(book_data)

    if count != len(
        original_keys
    ):
        raise RuntimeError(
            "Entry count mismatch"
        )

    # Boundary + representative positions.
    indices = {
        0,
        1,
        BLOCK_SIZE - 1,
        BLOCK_SIZE,
        len(original_keys) // 4,
        len(original_keys) // 2,
        3 * len(original_keys) // 4,
        len(original_keys) - 2,
        len(original_keys) - 1,
    }

    # Deterministic spread across book.
    step = max(
        1,
        len(original_keys)
        // 1000,
    )

    indices.update(
        range(
            0,
            len(original_keys),
            step,
        )
    )

    for index in sorted(indices):
        expected = (
            original_scores[index]
        )

        actual = lookup(
            original_keys[index],
            count,
            block_keys,
            block_offsets,
            payload,
        )

        if actual != expected:
            raise RuntimeError(
                f"Verification failed "
                f"at index {index}: "
                f"{actual} != {expected}"
            )

    return len(indices)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "input",
        type=Path,
        help=(
            "Sorted 9-byte key/score "
            "records exported from "
            "connect-four-ai"
        ),
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "data/v7/book_d12.bin"
        ),
    )

    args = parser.parse_args()

    print("=" * 72)
    print("CONNECTX V7 DEPTH-12 BOOK BUILDER")
    print("=" * 72)

    start = time.perf_counter()

    keys, scores = read_records(
        args.input
    )

    print(
        "Entries:",
        f"{len(keys):,}",
    )

    print(
        "Input:",
        args.input,
    )

    print(
        "Block size:",
        BLOCK_SIZE,
    )

    (
        block_keys,
        block_offsets,
        payload,
    ) = build_blocks(
        keys,
        scores,
    )

    book_data = serialize(
        len(keys),
        block_keys,
        block_offsets,
        payload,
    )

    verified = verify(
        keys,
        scores,
        book_data,
    )

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    args.output.write_bytes(
        book_data
    )

    print(
        "Blocks:",
        f"{len(block_keys):,}",
    )

    print(
        "Payload:",
        f"{len(payload) / 1024**2:.2f} MB",
    )

    print(
        "Book:",
        f"{len(book_data) / 1024**2:.2f} MB",
    )

    print(
        "Verified lookups:",
        f"{verified:,}",
    )

    print(
        "Output:",
        args.output,
    )

    print()
    print("Testing submission compression...")

    compressed = lzma.compress(
        book_data,
        preset=9,
    )

    encoded = base64.b85encode(
        compressed
    )

    print(
        "LZMA:",
        f"{len(compressed) / 1024**2:.2f} MB",
    )

    print(
        "Base85:",
        f"{len(encoded) / 1024**2:.2f} MB",
    )

    print(
        "Total build time:",
        f"{time.perf_counter() - start:.2f}s",
    )

    print("=" * 72)


if __name__ == "__main__":
    main()