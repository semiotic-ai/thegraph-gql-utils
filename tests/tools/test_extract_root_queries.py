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

from typing import Iterable

import graphql as gql
import pytest

from thegraph_gql_utils.misc import ast2str
from thegraph_gql_utils.tools import extract_root_queries


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (
            """
            {
                alias1: token(something: "sdgsdfg") {
                    name
                    id
                }
                alias2: token(something: "nyrwef") {
                    name
                    id
                }
                pair(first: 13) {
                    id
                }
                swap(skip: 1) {
                    amount
                }
            }
            """,
            [
                """
                {
                    token(something: "sdgsdfg") {
                        name
                        id
                    }
                }
                """,
                """
                {
                    token(something: "nyrwef") {
                        name
                        id
                    }
                }
                """,
                """
                {
                    pair(first: 13) {
                        id
                    }
                }
                """,
                """
                {
                    swap(skip: 1) {
                        amount
                    }
                }
                """,
            ],
        ),
        (
            """
            query QueryName ($var1: sometype, $var2: someothertype) {
                alias1: token(something: "sdgsdfg") {
                    name
                    id
                }
                alias2: token(something: "nyrwef") {
                    name
                    id
                }
                pair(first: 13) {
                    id
                }
                swap(skip: 1) {
                    amount
                }
            }
            """,
            [
                """
                query ($var1: sometype, $var2: someothertype) {
                    token(something: "sdgsdfg") {
                        name
                        id
                    }
                }
                """,
                """
                query ($var1: sometype, $var2: someothertype) {
                    token(something: "nyrwef") {
                        name
                        id
                    }
                }
                """,
                """
                query ($var1: sometype, $var2: someothertype) {
                    pair(first: 13) {
                        id
                    }
                }
                """,
                """
                query ($var1: sometype, $var2: someothertype) {
                    swap(skip: 1) {
                        amount
                    }
                }
                """,
            ],
        ),
    ],
)
def test_extract_root_queries(test_input: str, expected: Iterable[str]):
    input_query = gql.parse(test_input)

    for new_query, expected_query in zip(extract_root_queries(input_query), expected):
        assert ast2str(new_query) == ast2str(gql.parse(expected_query))
