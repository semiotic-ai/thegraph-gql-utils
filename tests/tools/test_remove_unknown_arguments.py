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

from gql_utils.misc import ast2str
from gql_utils.tools import remove_unknown_arguments


@pytest.mark.parametrize(
    "test_input,schema,expected",
    [
        (
            """
            {
                potato(banana: 42, pear: 56, onion: "garlic") {
                    id
                    apple (orange: 12) {
                        name
                    }
                }
            }
            """,
            """
            type Potato {
                id: ID
                apple: Apple
            }

            type Apple {
                name: String
                fruit: ID
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
            {
                potato(banana: 42) {
                    id
                    apple {
                        name
                    }
                }
            }
            """,
        )
    ],
)
def test_remove_unknown_arguments(test_input: str, schema: str, expected: str):
    input_query = gql.parse(test_input)
    gql_schema = gql.build_schema(schema)
    expected_query = gql.parse(expected)

    new_query = remove_unknown_arguments(input_query, gql_schema)

    assert ast2str(new_query) == ast2str(expected_query)
