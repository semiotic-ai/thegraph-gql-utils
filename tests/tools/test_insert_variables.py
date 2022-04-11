from typing import Any, Mapping, Union

import graphql as gql
import pytest

from thegraph_gql_utils.misc import ast2str
from thegraph_gql_utils.tools import insert_variables


@pytest.mark.parametrize(
    "test_input,variables,expected",
    [
        (
            """
            {
                token(something_int: $_0, id: {something_enum: $_1, something_float: $_2, something_str: $_3}) {
                    name
                    id
                }
            }
            """,
            {"_0": 42, "_1": "test_enum_value", "_2": 324.021, "_3": "test_string"},
            # Enum values are currently inserted as strings.
            """
            {
                token(something_int: 42, id: {something_enum: "test_enum_value", something_float: 324.021, something_str: "test_string"}) {
                    name
                    id
                }
            }
            """,
        )
    ],
)
def test_insert_variables(
    test_input: str,
    expected: str,
    variables: Union[str, bytes, Mapping[str, Any]],
):
    input_query = gql.parse(test_input)
    expected_query = gql.parse(expected)

    new_query = insert_variables(input_query, variables)

    assert ast2str(new_query) == ast2str(expected_query)
