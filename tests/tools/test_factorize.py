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
from gql_utils.tools import factorize


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (
            """
            {
                sel_1(arg_1: 1) {
                    sel_2 (arg_2: val_1) {
                        sel_3
                        sel_4 (arg_3: val_2) {
                            sel_5
                        }
                    }
                    sel_2 (arg_4: val_3, arg_2: val_4) {
                        sel_4 (arg_3: val_5) {
                            sel_6
                        }
                    }
                    alias_1: sel_2 (arg_5: val_1) {
                        sel_7
                    }
                }
            }
            """,
            """
            {
                sel_1(arg_1: 1) {
                    sel_2(arg_2: val_1, arg_4: val_3, arg_2: val_4) {
                        sel_3
                        sel_4(arg_3: val_2, arg_3: val_5) {
                            sel_5
                            sel_6
                        }
                    }
                    alias_1: sel_2 (arg_5: val_1) {
                        sel_7
                    }
                }
            }
            """,
        )
    ],
)
def test_factorize(test_input: str, expected: str):
    input_query = gql.parse(test_input)
    expected_query = gql.parse(expected)

    new_query = factorize(input_query)

    assert ast2str(new_query) == ast2str(expected_query)
