import pytest
import os
import sys

sys.path.insert(1, os.path.join(sys.path[0], ".."))
from mabel import Reader
from mabel.adapters.disk import DiskReader
from rich import traceback

traceback.install()


from mabel.logging import get_logger

get_logger().setLevel(5)


def test_reader_can_read():
    r = Reader(inner_reader=DiskReader, dataset="tests/data/tweets", partitioning=[])
    assert len(list(r)) == 50


def test_reader_to_pandas():
    r = Reader(inner_reader=DiskReader, dataset="tests/data/tweets", partitioning=[])
    df = r.to_pandas()

    assert len(df) == 50


def test_reader_can_read_alot():
    r = Reader(inner_reader=DiskReader, dataset="tests/data/nvd", partitioning=[])
    for i, row in enumerate(r):
        if i % 1000000 == 0:
            print(i)
        pass
    assert i == 135133 or i == 16066287, i


if __name__ == "__main__":  # pragma: no cover
    test_reader_can_read()
    test_reader_to_pandas()
    test_reader_can_read_alot()

    print("okay")
