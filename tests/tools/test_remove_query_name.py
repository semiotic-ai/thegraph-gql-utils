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


import graphql as gql
import pytest

from thegraph_gql_utils.misc import ast2str
from thegraph_gql_utils.tools import remove_query_name


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (
            """
            query queryname {
                alias1: polls(first: $first) {
                    votes(a: a) {
                        id
                    }
                }
            }
            """,
            """
            {
                alias1: polls(first: $first) {
                    votes(a: a) {
                        id
                    }
                }
            }
            """,
        )
    ],
)
def test_remove_query_name(test_input: str, expected: str):
    input_query = gql.parse(test_input)
    expected_query = gql.parse(expected)

    new_query = remove_query_name(input_query)

    assert ast2str(new_query) == ast2str(expected_query)
