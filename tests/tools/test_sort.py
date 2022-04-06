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
from thegraph_gql_utils.tools import sort


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (
            """
            {
                polls(first: 1) {
                    votes (capital: fossil, a: b, a: a) {
                        voter (c: b, a: b, b: a, a: c) {
                            cthing
                            athing
                            bthing
                        }
                        id
                    }
                }
            }
            """,
            """
            {
                polls(first: 1) {
                    votes(a: a, a: b, capital: fossil) {
                        id
                        voter(a: b, a: c, b: a, c: b) {
                            athing,
                            bthing,
                            cthing
                        }
                    }
                }
            }
            """,
        ),
        (
            """
            {
                polls(first: 1) {
                    votes (capital: fossil, a: b, a: a) {
                        aaa: voter (c: b, b: a, a: z) {
                            az
                            cthing
                            bthing
                        }
                        bbb: voter (c: b, b: a, a: c) {
                            athing
                            bthing
                        }
                        id
                    }
                }
            }
            """,
            """
            {
                polls(first: 1) {
                    votes(a: a, a: b, capital: fossil) {
                        id
                        bbb: voter(a: c, b: a, c: b) {
                            athing
                            bthing
                        }
                        aaa: voter(a: z, b: a, c: b) {
                            az
                            bthing
                            cthing
                        }
                    }
                }
            }
            """,
        ),
        (
            """
            {
                polls(first: 1) {
                    votes (capital: fossil, a: b, a: a) {
                        aaa: voter (c: b, b: a, a: z) {
                            az
                            cthing
                            bthing
                        }
                        bbb: voter (c: b, b: a, a: z) {
                            athing
                            bthing
                        }
                        id
                    }
                }
            }
            """,
            """
            {
                polls(first: 1) {
                    votes(a: a, a: b, capital: fossil) {
                        id
                        bbb: voter(a: z, b: a, c: b) {
                            athing
                            bthing
                        }
                        aaa: voter(a: z, b: a, c: b) {
                            az
                            bthing
                            cthing
                        }
                    }
                }
            }
            """,
        ),
    ],
)
def test_sort(test_input: str, expected: str):
    input_query = gql.parse(test_input)
    expected_query = gql.parse(expected)

    new_query = sort(input_query)

    assert ast2str(new_query) == ast2str(expected_query)
