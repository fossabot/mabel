import os
import sys

sys.path.insert(1, os.path.join(sys.path[0], "../../.."))
from mabel.adapters.disk import DiskReader
from mabel.data.internals.dictset import STORAGE_CLASS
from mabel.data import Reader
from rich import traceback

traceback.install()


def test_can_read_lxml():
    r = Reader(
        inner_reader=DiskReader,
        dataset="tests/data/formats/lxml",
        raw_path=True,
        persistence=STORAGE_CLASS.MEMORY,
    )

    assert r.count() == 5, r.count()
    assert isinstance(r.first(), dict), r.first()


def test_can_read_xml():
    r = Reader(
        inner_reader=DiskReader,
        dataset="tests/data/formats/xml",
        raw_path=True,
        persistence=STORAGE_CLASS.MEMORY,
    )

    assert r.count() == 1, r.count()
    assert isinstance(r.first(), dict), r.first()


if __name__ == "__main__":  # pragma: no cover
    test_can_read_lxml()
    test_can_read_xml()

    print("okay")
