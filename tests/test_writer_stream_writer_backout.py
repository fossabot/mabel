import time
import os
import sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from mabel.adapters.disk import DiskWriter, DiskReader
from mabel.data import StreamWriter
from mabel import Reader
from mabel.data.validator import Schema
try:
    from rich import traceback
    traceback.install()
except ImportError:
    pass
import shutil
from pathlib import Path

DATA_SET = [
    {'key': 6},
    {'key': 10},
    {'key': 3},
    {'key': 9},
    {'key': 'eight'},
    {'key': 4},
    {'key': 7},
    {'key': 5},
    {'key': 'two'},
    {'key': 1}
]
SCHEMA = { "fields": [ { "name": "key", "type": "numeric" } ] }
TEST_FOLDER = '_temp/path'

def test_writer_backout():

    if Path(TEST_FOLDER).exists():
        shutil.rmtree(TEST_FOLDER)

    # none of these should do anything
    w = StreamWriter(
            dataset=TEST_FOLDER,
            inner_writer=DiskWriter,
            schema=Schema(SCHEMA),
            idle_timeout_seconds=2)

    for record in DATA_SET:
        w.append(record)

    time.sleep(3)

    r = Reader(
            dataset=TEST_FOLDER,
            inner_reader=DiskReader
    )

    assert len(list(r)) == 8

if __name__ == "__main__":
    test_writer_backout()

    print('okay')