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

from typing import Any, Dict

import graphql as gql
import pytest

from thegraph_gql_utils.misc import ast2str
from thegraph_gql_utils.tools import remove_default_values


@pytest.mark.parametrize(
    "test_input,expected,expected_default_values",
    [
        (
            """
            query get_all_nfts_by_wallet_and_contract(
                $wallet: ID! = "0xa508c16666c5b8981fa46eb32784fccc01942a71",
                $contract: String = "0xdb3b2e1f699caf230ee75bfbe7d97d70f81bc945"
            ) {
                accounts(
                    where: {id: $wallet},
                    block: {hash: "0x0d99e70148a03565db60ed24a8210ac907ecfd928bab9fa67c87dfd7bdd99fd5"}
                ) {
                    id
                    ERC721tokens(where: {contract: $contract}) {
                        identifier
                        contract {
                            id
                        }
                    }
                }
            }
            """,
            """
            query get_all_nfts_by_wallet_and_contract(
                $wallet: ID!,
                $contract: String
            ) {
                accounts(
                    where: {id: $wallet},
                    block: {hash: "0x0d99e70148a03565db60ed24a8210ac907ecfd928bab9fa67c87dfd7bdd99fd5"}
                ) {
                    id
                    ERC721tokens(where: {contract: $contract}) {
                        identifier
                        contract {
                            id
                        }
                    }
                }
            }
            """,
            {
                "wallet": "0xa508c16666c5b8981fa46eb32784fccc01942a71",
                "contract": "0xdb3b2e1f699caf230ee75bfbe7d97d70f81bc945",
            },
        )
    ],
)
def test_remove_values(
    test_input: str, expected: str, expected_default_values: Dict[str, Any]
):
    input_query = gql.parse(test_input)
    expected_query = gql.parse(expected)

    new_query, default_values = remove_default_values(input_query)

    assert ast2str(new_query) == ast2str(expected_query)
    assert default_values == expected_default_values
