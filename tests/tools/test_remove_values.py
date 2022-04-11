# Copyright (c) 2022, Semiotic AI, Inc.  All rights reserved.
#
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

from typing import Any, List, Mapping, Optional, Union

import graphql as gql
import pytest

from thegraph_gql_utils.misc import ast2str
from thegraph_gql_utils.tools import remove_values


@pytest.mark.parametrize(
    "test_input,ignored_arguments,existing_variables,expected,expected_removed_values",
    [
        (
            """
            {
                token(something: "sdgsdfg", id: {chimney: 42, diesel: {piano: 54}}) {
                    name
                    id
                }
            }
            """,
            ["piano"],
            None,
            """
            {
                token(something: $_0, id: {chimney: $_1, diesel: {piano: 54}}) {
                    name
                    id
                }
            }
            """,
            ["sdgsdfg", 42],
        ),
        (
            """
            {
                token(something: "sdgsdfg", id: {chimney: 42, diesel: $var}) {
                    name
                    id
                }
            }
            """,
            ["piano"],
            {"var": "{piano: 54}"},
            """
            {
                token(something: $_0, id: {chimney: $_1, diesel: $_2}) {
                    name
                    id
                }
            }
            """,
            ["sdgsdfg", 42, "{piano: 54}"],
        ),
    ],
)
def test_remove_values(
    test_input: str,
    expected: str,
    ignored_arguments: List[str],
    existing_variables: Optional[Union[str, bytes, Mapping[str, Any]]],
    expected_removed_values: List[str],
):
    input_query = gql.parse(test_input)
    expected_query = gql.parse(expected)

    new_query, removed_values = remove_values(
        input_query, ignored_arguments, existing_variables
    )

    assert ast2str(new_query) == ast2str(expected_query)
    assert removed_values == expected_removed_values
