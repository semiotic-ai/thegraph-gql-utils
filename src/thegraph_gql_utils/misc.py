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


def ast2str(document: gql.language.ast.Node) -> str:
    """
    Print a graphql-core AST document with escape sequences removed.
    """

    return bytes(gql.print_ast(document), "utf-8").decode("unicode_escape")


def node2dict(node: gql.language.ast.Node) -> Dict[str, Any]:
    """
    Extract a node key-value pairs into a dictionnary. Better than
    gql.language.ast.Node.to_dict() in that it does not recurse down the values.
    """

    return {k: getattr(node, k) for k in node.keys}
