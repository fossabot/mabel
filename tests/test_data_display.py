import os
import sys

sys.path.insert(1, os.path.join(sys.path[0], ".."))
from mabel import Reader, Relation
from mabel.data.internals.display import html_table
from mabel.adapters.disk import DiskReader
from mabel.logging import get_logger

get_logger().setLevel(5)


def get_ds(**kwargs):
    ds = Reader(
        inner_reader=DiskReader, dataset="tests/data/tweets", date_partitions=[], **kwargs
    )
    return ds


def test_html_table():

    ds = get_ds()
    html = html_table(ds)

    assert "<table" in html
    assert "<th" in html
    assert "<tr" in html
    assert "</table>" in html


if __name__ == "__main__":
    test_html_table()

    print("OKAY")
