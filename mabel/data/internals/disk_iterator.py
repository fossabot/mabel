import os
import mmap
import orjson
import atexit
from tempfile import NamedTemporaryFile

BUFFER_SIZE = 16 * 1024 * 1024  # 16Mb


class DiskIterator(object):
    """
    This provides the reader for the DISK variation of STORAGE.
    """

    def __init__(self, iterator):

        self.inner_reader = None
        self.length = -1

        self.file = NamedTemporaryFile(prefix="mabel-dictset").name
        atexit.register(os.remove, self.file)

        buffer = bytearray()
        with open(self.file, "wb") as f:
            for self.length, row in enumerate(iterator):
                buffer.extend(orjson.dumps(row) + b"\n")
                if len(buffer) > (BUFFER_SIZE):
                    f.write(buffer)
                    buffer = bytearray()
            if len(buffer) > 0:
                f.write(buffer)
            f.flush()

    def _read_file(self):
        with open(self.file, mode="rb") as file_obj:
            with mmap.mmap(
                file_obj.fileno(), length=0, access=mmap.ACCESS_READ
            ) as mmap_obj:
                line = mmap_obj.readline()
                while line:
                    yield line
                    line = mmap_obj.readline()

    def _inner_reader(self, *locations):
        if locations:
            max_location = max(locations)
            min_location = min(locations)

            reader = self._read_file()

            for i in range(min_location):
                next(reader)

            for i, line in enumerate(reader, min_location):
                if i in locations:
                    yield orjson.loads(line)
                    if i == max_location:
                        return
        else:
            for line in self._read_file():
                # this is about 50% of the time
                yield orjson.loads(line)

    def __iter__(self):
        return self._inner_reader()

    def __len__(self):
        return self.length
