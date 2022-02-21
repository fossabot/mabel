# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Implement a Relation, this analogous to a database table. It is called a Relation
in-line with terminology for Relational Algreba.

Internally the data for the Relation is stored as a list of Tuples and a dictionary
records the schema and other key information about the Relation. Tuples are faster
than Dicts for accessing data.

Some naive benchmarking with 135k records (with 269 columns) vs lists of dictionaries:
- Relation is 30% smaller (this doesn't hold true for all datasets)
- Relation was deduplicated 90% faster
- Relation selection was 75% faster


- self.data is a list of tuples
- self.schema is a dictionary
    {
        "attribute": {
            "type": type (domain)
            "min": smallest value in this attribute
            "max": largest value in this attribute
            "count": count of non-null values in attribute
            "unique": number of unique values in this attribute
            "nullable": are there nulls
        }
    }

    Only "type" can be assumed to be present, especially after a select operation
"""
import sys
import os

sys.path.insert(1, os.path.join(sys.path[0], "../../.."))

from typing import Iterable, Tuple
from mabel.data.types import (
    MABEL_TYPES,
    PARQUET_TYPES,
    PYTHON_TYPES,
    coerce_types,
)
from mabel.errors import MissingDependencyError

def _union(*its):
    for it in its:
        yield from it 


class Relation:

    __slots__ = ("schema", "data", "name")

    def __init__(
        self,
        data: Iterable[Tuple] = [],
        *,
        schema: dict = {},
        name: str = None,
        **kwargs,
    ):
        """
        Create a Relation.

        Parameters:
            data: Iterable
                An iterable which is the data in the Relation
            schema: Dictionary (optional)
                Schema and profile information for this Relation
            name: String (optional)
                A handle for this Relation, cosmetic only
        """
        self.schema = schema
        self.name = name

        if isinstance(data, list):
            first = data[0]
            if isinstance(first, dict):
                self.from_dictionaries(data)
            else:
                self.data = list(data)
        else:
            # expected to be a generator of dicts
            self.data = data

    @property
    def cursor(self):
        """
        If the DictSet supports cursors, return the cursor.
        """
        if hasattr(self.data, "cursor"):
            return self.data.cursor
        return None

    def apply_selection(self, predicate):
        """
        Apply a Selection operation to a Relation, this filters the data in the
        Relation to just the entries which match the predicate.

        Parameters:
            predicate (list or tuple):
                A DNF structured filter predicate.

        Returns:
            Relation
        """
        # selection invalidates what we thought we knew about counts etc
        new_schema = {k: {"type": v.get("type")} for k, v in self.schema.items()}

        # DNF filtering
        from mabel.data.internals.dnf_filters import DnfFilters
        filter_set = DnfFilters(predicate, self.schema)
        return Relation(
            DnfFilters.apply(filter_set, self.data),
            schema=new_schema,
        )


    def apply_projection(self, attributes):
        if not isinstance(attributes, (list, tuple)):
            attributes = [attributes]
        attribute_indices = []
        new_schema = {k: self.schema.get(k) for k in attributes}
        for index, attribute in enumerate(self.schema.keys()):
            if attribute in attributes:
                attribute_indices.append(index)

        def _inner_projection():
            for tup in self.data:
                yield tuple([tup[indice] for indice in attribute_indices])

        return Relation(_inner_projection(), schema=new_schema)

    def __getitem__(self, attributes):
        """
        Select the attributes from the Relation, alias for .apply_projection called
        like this Relation["column"]
        """
        return self.apply_projection(attributes)

    def materialize(self):
        if not isinstance(self.data, list):
            self.data = list(self.data)
        if len(self.data) >= 1 and isinstance(self.data[0], dict):
            self.from_dictionaries(self.data)

    def count(self):
        self.materialize()
        return len(self.data)

    @property
    def shape(self):
        self.materialize()
        return (len(self.schema), len(self.data))

    @property
    def columns(self):
        cols = [k for k in self.schema.copy().keys()]
        print(cols)
        return cols

    def distinct(self):
        """
        Return a new Relation with only unique values
        """
        hash_list = {}
        self.materialize()

        def do_dedupe(data):
            for item in data:
                hashed_item = hash(item)
                if hashed_item not in hash_list:
                    hash_list[hashed_item] = True
                    yield item

        return Relation(do_dedupe(self.data), schema=self.schema)

    def from_dictionaries(self, dictionaries, schema=None):

        def types(row):
            response = {}
            for k, v in row.items():
                value_type = PYTHON_TYPES.get(str(type(v).__name__), MABEL_TYPES.OTHER)
                if k not in response:
                    response[k] = {"type": value_type}
                elif response[k] != {"type": value_type}:
                    response[k] = {"type": MABEL_TYPES.OTHER}
            return response

        dicts = iter(dictionaries)

        first_dict = {}
        if not schema:
            first_dict = next(dicts)
            self.schema = types(first_dict)
        self.data = [
            tuple([coerce_types(row.get(k)) for k in self.schema.keys()])
            for row in _union([first_dict], dicts)
        ]

    def attributes(self):
        return [k for k in self.schema.keys()]

    def rename_attribute(self, current_name, new_name):
        self.schema[new_name] = self.schema.pop(current_name)

    def __str__(self):
        return f"{self.name or 'Relation'} ({', '.join([k + ':' + v.get('type') for k,v in self.schema.items()])})"

    def __len__(self):
        """
        Alias for .count
        """
        return self.count()

    def __iter__(self):
        from mabel.data.internals.dumb_iterator import DumbIterator
        return DumbIterator(self.i_fetchall())


    def serialize(self):
        """
        Serialize to Parquet, this is used for communicating and saving the Relation.
        """
        try:
            import pyarrow.parquet as pq
            import pyarrow.json
        except ImportError:  # pragma: no cover
            raise MissingDependencyError(
                "`pyarrow` is missing, please install or include in requirements.txt"
            )

        import io

        # load into pyarrow as a JSON dataset
        in_pyarrow_buffer = pyarrow.json.read_json(io.BytesIO(self.to_json()))

        # then we convert the pyarrow table to parquet
        pq_temp_buffer = io.BytesIO()
        pq.write_table(in_pyarrow_buffer, pq_temp_buffer, compression="ZSTD")

        # the read out the parquet formatted data
        pq_temp_buffer.seek(0, 0)
        buffer = pq_temp_buffer.read()
        pq_temp_buffer.close()

        return buffer

    def to_json(self):
        """
        Convert the relation to a JSONL byte string
        """
        import orjson

        return b"\n".join(map(orjson.dumps, self.fetchall()))

    def to_pandas(self):
        """
        Load the contents of the _DictSet_ to a _Pandas_ DataFrame.

        Returns:
            Pandas DataFrame
        """
        try:
            import pandas
        except ImportError:  # pragma: no cover
            raise MissingDependencyError(
                "`pandas` is missing, please install or include in requirements.txt"
            )
        return pandas.DataFrame(self.i_fetchall())

    def fetchone(self, offset: int = 0):
        self.materialize()
        try:
            return dict(zip(self.schema.keys(), self.data[offset]))
        except IndexError:
            return None

    def fetchmany(self, size: int = 100, offset: int = 0):
        keys = self.schema.keys()
        self.materialize()

        def _inner_fetch():
            for index in range(offset, min(len(self.data), offset + size)):
                yield dict(zip(keys, self.data[index]))

        return list(_inner_fetch())

    def i_fetchall(self, offset: int = 0):
        keys = self.schema.keys()
        self.materialize()

        for index in range(offset, len(self.data)):
            yield dict(zip(keys, self.data[index]))

    def fetchall(self, offset: int = 0):
        return list(self.i_fetchall(offset=offset))

    def collect_list(self, key: str = None):
        """
        Convert a _DictSet_ to a list, optionally, but probably usually, just extract
        a specific column.

        Return None if the value in the field is None, if the field doesn't exist in
        the record, don't return anything.
        """
        if not key:
            return self.fetchall()

        index = self.columns.index(key)
        return [record[index] for record in self.data]

    def min_max(self, key: str):
        """
        Find the minimum and maximum of a column at the same time.

        Parameters:
            key: string
                The column to perform the function on

        Returns:
            tuple (minimum, maximum)
        """

        def minmax(a, b):
            return min(a[0], b[0]), max(a[1], b[1])

        from functools import reduce
        return reduce(minmax, map(lambda x: (x, x), self.collect_list(key)))

    def min(self, key: str):
        """
        Find the minimum in a column of this _DictSet_.

        Parameters:
            key: string
                The column to perform the function on
        """
        from functools import reduce
        return reduce(min, self.collect_list(key))

    def sum(self, key: str):
        """
        Find the sum of a column of this _DictSet_.

        Parameters:
            key: string
                The column to perform the function on
        """
        from functools import reduce
        return reduce(lambda x, y: x + y, self.collect_list(key), 0)

    def max(self, key: str):
        """
        Find the maximum in a column of this _DictSet_.

        Parameters:
            key: string
                The column to perform the function on
        """
        from functools import reduce
        return reduce(max, self.collect_list(key))

    def collect_set(self, column, dedupe: bool = False):
        from mabel.data.internals.collected_set import CollectedSet

        return CollectedSet(self, column, dedupe=dedupe)

    def group_by(self, group_by_columns):
        """
        Group a dictset by a column or group of columns. Returns a GroupBy object.
        """
        from mabel.data.internals.group_by import GroupBy
        return GroupBy(self, group_by_columns)

    def __iter__(self):
        keys = self.schema.keys()
        self.materialize()

        def _inner_fetch():
            for index in range(len(self.data)):
                yield dict(zip(keys, self.data[index]))

        yield from _inner_fetch()

    def sample(self, fraction: float = 0.5):
        """
        Select a random sample of records, fraction indicates the portion of
        records to select.

        NOTE: records are randomly selected so is unlikely to perfectly match the
        fraction.
        """

        def inner_sampler(dictset):
            selector = int(1 / fraction)
            for row in dictset:
                random_value = int.from_bytes(os.urandom(2), "big")
                if random_value % selector == 0:
                    yield row

        return Relation(inner_sampler(self.data), schema=self.schema)

    def mean(self, key: str):
        """
        Find the mean in a column of this _DictSet_.

        Parameters:
            key: string
                The column to perform the function on
        """
        import statistics
        return statistics.mean(self.collect_list(key))

    def variance(self, key: str):
        """
        Find the variance in a column of this _DictSet_.

        Parameters:
            key: string
                The column to perform the function on
        """
        import statistics
        return statistics.variance(self.collect_list(key))

    def standard_deviation(self, key: str):
        """
        Find the standard deviation in a column of this _DictSet_.

        Parameters:
            key: string
                The column to perform the function on
        """
        import statistics
        return statistics.stdev(self.collect_list(key))

    def collect_column(self, column):
        def get_column(column):
            for index, attribute in enumerate(self.schema.keys()):
                if attribute == column:
                    return index
            raise Exception("Column not found")

        def _inner_fetch(column):
            for index in range(len(self.data)):
                yield self.data[index][column]

        return list(_inner_fetch(get_column(column)))

    @staticmethod
    def deserialize(stream):
        """
        Deserialize from a stream of bytes which is a Parquet file.

        Return a Relation with a basic schema.
        """
        try:
            import pyarrow.parquet as pq  # type:ignore
        except ImportError:  # pragma: no cover
            raise MissingDependencyError(
                "`pyarrow` is missing, please install or include in requirements.txt"
            )
        if not hasattr(stream, "read") or isinstance(stream, bytes):
            import io

            stream = io.BytesIO(stream)
        table = pq.read_table(stream)

        def _inner(table):
            for batch in table.to_batches():
                dict_batch = batch.to_pydict()
                for index in range(len(batch)):
                    yield tuple([v[index] for k, v in dict_batch.items()])

        def pq_schema_to_rel_schema(pq_schema):
            schema = {}
            for attribute in pq_schema:
                schema[attribute.name] = {
                    "type": PARQUET_TYPES.get(
                        str(attribute.type), MABEL_TYPES.OTHER
                    ).value
                }
            return schema

        return Relation(_inner(table), schema=pq_schema_to_rel_schema(table.schema))

    @staticmethod
    def load(file):
        with open(file, "rb") as pq_file:
            return Relation.deserialize(pq_file)

    def __repr__(self):  # pragma: no cover
        from mabel.utils.ipython import is_running_from_ipython
        from mabel.data.internals.display import html_table, ascii_table

        if is_running_from_ipython():
            from IPython.display import HTML, display  # type:ignore

            html = html_table(iter(self), 10)
            display(HTML(html))
            return ""  # __repr__ must return something
        else:
            return ascii_table(iter(self), 10)

    def __hash__(self, seed: int = 703115) -> int:
        """
        Creates a consistent hash of the _DictSet_ regardless of the order of
        the items in the _DictSet_.
        """
        from siphashc import siphash
        from functools import reduce

        def sip(v):
            return siphash("TheApolloMission", str(v))

        def sip_tuple(tup):
            hashed = map(sip, tup)
            return reduce(lambda x, y: x ^ y, hashed, seed)

        # The seed is the mission duration of the Apollo 11 mission.
        #   703115 = 8 days, 3 hours, 18 minutes, 35 seconds
        hashed = map(sip_tuple, self.data)
        return reduce(lambda x, y: x ^ y, hashed, seed)

if __name__ == "__main__":

    from mabel.utils.timer import Timer

    with Timer("load"):
        r = Relation.load("tests/data/formats/parquet/tweets.parquet")
    r.materialize()

    r.data = r.data * 10

    print(r.schema)
    print(r.data[10])

    print(r.count())
    print(r.attributes())
    r.distinct()
    print(r.attributes())
    print(r.apply_projection(["user_verified"]).distinct().count())
    print(len(r.fetchall()))

#    with Timer("s"):
#        s = r.serialize()

#    with Timer("d"):
#        s = Relation.deserialize(s)

    s = r.apply_selection(('followers', '=', 1234))

    print(s.count())
    print(s.to_json())
