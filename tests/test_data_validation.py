"""
Validator Tests
"""
import datetime
import os
import sys

import pytest

sys.path.insert(1, os.path.join(sys.path[0], ".."))
from mabel.data.validator import Schema
from mabel.errors import ValidationError
from rich import traceback
import orjson

traceback.install()


def test_validator_all_valid_values():

    TEST_DATA = {
        "string_field": "string",
        "integer_field": 100,
        "boolean_field": True,
        "date_field": datetime.datetime.today(),
        "nullable_field": None,
        "list_field": ["a", "b", "c"],
        "enum_field": "RED",
    }
    TEST_SCHEMA = {
        "fields": [
            {"name": "string_field", "type": "VARCHAR"},
            {"name": "integer_field", "type": "NUMERIC"},
            {"name": "boolean_field", "type": "BOOLEAN"},
            {"name": "date_field", "type": "TIMESTAMP"},
            {"name": "nullable_field", "type": "VARCHAR"},
            {"name": "list_field", "type": "LIST"},
            {
                "name": "enum_field",
                "type": "VARCHAR",
                "symbols": ["RED", "GREEN", "BLUE"],
            },
        ]
    }

    test = Schema(TEST_SCHEMA)
    assert test.validate(TEST_DATA), test.last_error


def test_validator_invalid_string():

    TEST_DATA = {"string_field": 100}
    TEST_SCHEMA = {"fields": [{"name": "string_field", "type": "VARCHAR"}]}

    test = Schema(TEST_SCHEMA)
    assert not test.validate(TEST_DATA)


def test_validator_invalid_number():

    TEST_DATA = {"number_field": "one hundred"}
    TEST_SCHEMA = {"fields": [{"name": "number_field", "type": "NUMERIC"}]}

    test = Schema(TEST_SCHEMA)
    assert not test.validate(TEST_DATA)

    TEST_DATA = {"number_field": print}
    TEST_SCHEMA = {"fields": [{"name": "number_field", "type": "NUMERIC"}]}

    test = Schema(TEST_SCHEMA)
    assert not test.validate(TEST_DATA)


def test_validator_invalid_schema():

    result = True
    try:
        Schema({"name": "string"})
    except:  # pragma: no cover
        result = False
    assert not result


def test_validator_invalid_boolean():

    TEST_DATA = {"boolean_field": "not true"}
    TEST_SCHEMA = {"fields": [{"name": "boolean_field", "type": "BOOLEAN"}]}

    test = Schema(TEST_SCHEMA)
    assert not test.validate(TEST_DATA)


def test_validator_nonnative_types():

    TEST_DATA = {
        "integer_field": "100",
        "boolean_field": "True",
        "date_field": "2000-01-01 00:00:00.0000",
        "date_field2": "2022-02-16T23:27:08.892Z",
        "nullable_field": "",
    }
    TEST_SCHEMA = {
        "fields": [
            {"name": "integer_field", "type": "NUMERIC"},
            {"name": "boolean_field", "type": "BOOLEAN"},
            {"name": "date_field", "type": "TIMESTAMP"},
            {"name": "date_field2", "type": "TIMESTAMP"},
            {"name": "nullable_field", "type": "VARCHAR"},
        ]
    }

    test = Schema(TEST_SCHEMA)
    assert not test.validate(TEST_DATA), test.last_error


def test_validator_extended_schema():
    """
    Ensure the validator will ignore additional fields in the schema
    """
    TEST_DATA = {"string_field": "the"}
    TEST_SCHEMA = {
        "table": "this is a test schema",
        "fields": [
            {
                "name": "string_field",
                "type": "VARCHAR",
                "description": "character array",
                "last_updated": datetime.datetime.today(),
            }
        ],
    }

    test = Schema(TEST_SCHEMA)
    assert test.validate(TEST_DATA)


def test_validator_loaders():
    """
    Ensure dictionary, json and json files load
    """

    TEST_SCHEMA_DICT = {"fields": [{"name": "string_field", "type": "VARCHAR"}]}
    TEST_SCHEMA_STRING = orjson.dumps(TEST_SCHEMA_DICT).decode()
    TEST_SCHEMA_FILE = "temp"

    with open(TEST_SCHEMA_FILE, "w") as file:
        file.write(TEST_SCHEMA_STRING)

    failed = False
    try:
        test = Schema(TEST_SCHEMA_DICT)
        test.validate({"string_field": "pass"})
    except Exception:  # pragma: no cover
        failed = True
    assert not failed, "load schema from dictionary"

    failed = False
    try:
        test = Schema(TEST_SCHEMA_STRING)
        test.validate({"string_field": "pass"})
    except Exception:  # pragma: no cover
        failed = True
    assert not failed, "load schema from string"

    failed = False
    try:
        test = Schema(TEST_SCHEMA_FILE)
        test.validate({"string_field": "pass"})
    except Exception:  # pragma: no cover
        failed = True
    assert not failed, "load schema from file"


def test_validator_list():

    INVALID_TEST_DATA = {"key": "not a list"}
    VALID_TEST_DATA = {"key": ["is", "a", "list"]}
    TEST_SCHEMA = {"fields": [{"name": "key", "type": "LIST"}]}

    test = Schema(TEST_SCHEMA)
    assert not test.validate(INVALID_TEST_DATA)
    assert test.validate(VALID_TEST_DATA)


def test_validator_date():

    INVALID_TEST_DATA_1 = {"key": "tomorrow"}
    INVALID_TEST_DATA_2 = {"key": "2020001001"}
    INVALID_TEST_DATA_3 = {"key": "2020-00-01"}
    VALID_TEST_DATA = {"key": datetime.datetime.utcnow()}
    TEST_SCHEMA = {"fields": [{"name": "key", "type": "TIMESTAMP"}]}

    test = Schema(TEST_SCHEMA)
    assert not test.validate(INVALID_TEST_DATA_1)
    assert not test.validate(INVALID_TEST_DATA_2)
    assert not test.validate(INVALID_TEST_DATA_3)
    assert test.validate(VALID_TEST_DATA)


def test_unknown_type():

    TEST_SCHEMA = {"fields": [{"name": "key", "type": "not_a_known_type"}]}

    failed = False
    try:
        test = Schema(TEST_SCHEMA)
    except ValueError:  # pragma: no cover
        failed = True

    assert failed


def test_raise_exception():

    INVALID_FORM_DATA = {"number_field": "one hundred"}
    EXTRA_FIELD_DATA = {"number_field": 100, "extra": True}
    MISSING_FIELD_DATA = {}
    TEST_SCHEMA = {"fields": [{"name": "number_field", "type": "NUMERIC"}]}

    test = Schema(TEST_SCHEMA)
    with pytest.raises(ValidationError):
        test.validate(INVALID_FORM_DATA, raise_exception=True)
    with pytest.raises(ValidationError):
        test.validate(EXTRA_FIELD_DATA, raise_exception=True)

    # missing data is None - don't fail schema validation
    # if it should fail it needs an Expectation
    test.validate(MISSING_FIELD_DATA, raise_exception=True)


def test_call_alias():

    TEST_DATA = {"number_field": 100}
    TEST_SCHEMA = {"fields": [{"name": "number_field", "type": "NUMERIC"}]}

    test = Schema(TEST_SCHEMA)
    assert test(TEST_DATA)


if __name__ == "__main__":  # pragma: no cover
    test_validator_all_valid_values()
    test_validator_invalid_string()
    test_validator_invalid_number()
    test_validator_invalid_schema()
    test_validator_invalid_boolean()
    test_validator_nonnative_types()
    test_validator_extended_schema()
    test_validator_loaders()
    test_validator_list()
    test_validator_date()
    test_unknown_type()
    test_raise_exception()
    test_call_alias()

    print("okay")
