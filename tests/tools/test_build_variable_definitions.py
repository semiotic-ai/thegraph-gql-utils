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
from thegraph_gql_utils.tools import build_variable_definitions


@pytest.mark.parametrize(
    "test_input,schema,expected",
    [
        (
            """
            {
                potato(banana: $firstvar, garlic: $secondvar) {
                    id
                    apple (orange: $thirdvar) {
                        name
                    }
                }
            }
            """,
            """
            type Apple {
                name: String
                fruit: ID
            }

            type Potato {
                id: ID
                apple(tomato: ID, orange: String): Apple
            }

            type Query {
                potato(
                    banana: Int
                    garlic: String
                ): Potato

                apple(
                    tomato: ID
                    orange: String
                ): Apple
            }
            """,
            """
            query ($firstvar: Int, $secondvar: String, $thirdvar: String) {
                potato(banana: $firstvar, garlic: $secondvar) {
                    id
                    apple (orange: $thirdvar) {
                        name
                    }
                }
            }
            """,
        )
    ],
)
def test_build_variable_definitions(test_input: str, schema: str, expected: str):
    input_query = gql.parse(test_input)
    gql_schema = gql.build_schema(schema)
    expected_query = ast2str(gql.parse(expected))

    new_query = ast2str(build_variable_definitions(input_query, gql_schema))

    assert new_query == expected_query
