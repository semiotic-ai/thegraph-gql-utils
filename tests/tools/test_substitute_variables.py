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

from typing import Any, Mapping, Union

import graphql as gql
import pytest

from thegraph_gql_utils.misc import ast2str
from thegraph_gql_utils.tools import insert_variables


@pytest.mark.parametrize(
    "test_input,input_vars_dict,expected",
    [
        (
            """
            {
                token(something: $first_var, id: {chimney: none, diesel: {piano: $secondvar}}) {
                    name
                    id
                }
            }
            """,
            {"first_var": "sdfsdf", "secondvar": 54},
            """
            {
                token(something: "sdfsdf", id: {chimney: none, diesel: {piano: 54}}) {
                    name
                    id
                }
            }
            """,
        ),
        (
            """
            {
                token(something: $first_var, id: {chimney: none, diesel: {piano: $secondvar}}) {
                    name
                    id
                }
            }
            """,
            """
            {
                "first_var": "sdfsdf",
                "secondvar": 54
            }
            """,
            """
            {
                token(something: "sdfsdf", id: {chimney: none, diesel: {piano: 54}}) {
                    name
                    id
                }
            }
            """,
        ),
        (
            """
            query ($first_var: sometype, $secondvar: someothertype) {
                token(something: $first_var, id: {chimney: none, diesel: {piano: $secondvar}}) {
                    name
                    id
                }
            }
            """,
            """
            {
                "first_var": "sdfsdf",
                "secondvar": 54
            }
            """,
            """
            query ($first_var: sometype, $secondvar: someothertype) {
                token(something: "sdfsdf", id: {chimney: none, diesel: {piano: 54}}) {
                    name
                    id
                }
            }
            """,
        ),
    ],
)
def test_insert_variabls(
    test_input: str,
    input_vars_dict: Union[str, bytes, Mapping[str, Any]],
    expected: str,
):
    input_query = gql.parse(test_input)
    expected_query = gql.parse(expected)

    new_query = insert_variables(input_query, input_vars_dict)

    assert ast2str(new_query) == ast2str(expected_query)
