from typing import Any, Mapping, Union

import graphql as gql
import pytest

from thegraph_gql_utils.misc import ast2str
from thegraph_gql_utils.tools import insert_variables

test_schema = """
type Token {
    name: String
    id: ID
}

enum EnumType {
    TestEnumValue,
    OtherTestEnumValue,
}

input SomeObj {
    something_enum: EnumType
    something_float: Float
    something_str: String
}

type Query {
    token(
        something_int: Int
        some_obj: SomeObj
    ): Token
}
"""


@pytest.mark.parametrize(
    "test_input,schema,variables,expected",
    [
        (
            """
            {
                token(something_int: $_0, some_obj: {something_enum: $_1, something_float: $_2, something_str: $_3}) {
                    name
                    id
                }
            }
            """,
            test_schema,
            {"_0": 42, "_1": "TestEnumValue", "_2": 324.021, "_3": "test_string"},
            """
            {
                token(something_int: 42, some_obj: {something_enum: TestEnumValue, something_float: 324.021, something_str: "test_string"}) {
                    name
                    id
                }
            }
            """,
        ),
        (
            """
            {
                token(some_obj: $_1) {
                    name
                    id
                }
            }
            """,
            test_schema,
            # Should be able to insert an object from a Python dict.
            {
                "_1": {
                    "something_enum": "TestEnumValue",
                    "something_float": 123.456,
                    "something_str": "test",
                }
            },
            """
            {
                token(some_obj: {something_enum: TestEnumValue, something_float: 123.456, something_str: "test"}) {
                    name
                    id
                }
            }
            """,
        ),
        (
            """
            {
                token(some_obj: $_1) {
                    name
                    id
                }
            }
            """,
            test_schema,
            # Should be able to insert an object from a JSON string.
            {
                "_1": '{ "something_enum": "TestEnumValue", "something_float": 123.456, "something_str": "test" }'
            },
            """
            {
                token(some_obj: {something_enum: TestEnumValue, something_float: 123.456, something_str: "test"}) {
                    name
                    id
                }
            }
            """,
        ),
        (
            """
            {
                token(something_int: $_0, some_obj: {something_enum: $_1, something_float: $_2, something_str: $_3}) {
                    name
                    id
                }
            }
            """,
            test_schema,
            # Should be able to parse variables from JSON string.
            '{"_0": 42, "_1": "TestEnumValue", "_2": 324.021, "_3": "test_string"}',
            """
            {
                token(something_int: 42, some_obj: {something_enum: TestEnumValue, something_float: 324.021, something_str: "test_string"}) {
                    name
                    id
                }
            }
            """,
        ),
        (
            # Should work with variable definitions.
            """
            query ($_0: Int, $_1: EnumType, $_2: Float, $_3: String) {
                token(something_int: $_0, some_obj: {something_enum: $_1, something_float: $_2, something_str: $_3}) {
                    name
                    id
                }
            }
            """,
            test_schema,
            '{"_0": 42, "_1": "TestEnumValue", "_2": 324.021, "_3": "test_string"}',
            """
            query ($_0: Int, $_1: EnumType, $_2: Float, $_3: String) {
                token(something_int: 42, some_obj: {something_enum: TestEnumValue, something_float: 324.021, something_str: "test_string"}) {
                    name
                    id
                }
            }
            """,
        ),
    ],
)
def test_insert_variables(
    test_input: str,
    schema: str,
    expected: str,
    variables: Union[str, bytes, Mapping[str, Any]],
):
    input_query = gql.parse(test_input)
    gql_schema = gql.build_schema(schema)
    expected_query = gql.parse(expected)

    new_query = insert_variables(
        query=input_query, schema=gql_schema, variables=variables
    )
    print(ast2str(new_query))

    assert ast2str(new_query) == ast2str(expected_query)
