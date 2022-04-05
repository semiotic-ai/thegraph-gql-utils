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

from copy import deepcopy
from typing import Any, Container, Iterable, List, Mapping, Optional, Tuple, Union

import graphql as gql

from .visitors import (
    BuildArgumentDefinitionsVisitor,
    FactorizeVisitor,
    InsertVariables,
    PruneArgumentsVisitor,
    RemoveAliasesVisitor,
    RemoveFragmentsVisitor,
    RemoveQueryName,
    RemoveUnknownArgumentsVisitor,
    RemoveValuesVisitor,
    SortVisitor,
    SubstituteFragmentsVisitor,
)


def factorize(query: gql.DocumentNode) -> gql.DocumentNode:
    """
    Merges identical adjacent selections.
    """

    return gql.language.visit(query, FactorizeVisitor())


def sort(query: gql.DocumentNode) -> gql.DocumentNode:
    """
    Lexicographic sort of adjacent selections and arguments.
    """

    return gql.language.visit(query, SortVisitor())


def prune_query_arguments(query: gql.DocumentNode) -> gql.DocumentNode:
    """
    Keep only the first instance of the same argument type in FieldNodes.

    Example:
        {
            things(arg1: 42, arg2: 5150, arg1: 314) {...}
        }
        # Becomes:
        {
            things(arg1: 42, arg2: 5150) {...}
        }
    """

    return gql.language.visit(query, PruneArgumentsVisitor())


def substitute_fragments(query: gql.DocumentNode) -> gql.DocumentNode:
    extract_fragments_visitor = RemoveFragmentsVisitor()

    # Extract and remove the fragments
    query = gql.language.visit(query, extract_fragments_visitor)
    fragments = extract_fragments_visitor.fragments

    # Insert the fragments
    query = gql.language.visit(query, SubstituteFragmentsVisitor(fragments))

    return query


def remove_unknown_arguments(
    query: gql.DocumentNode, schema: gql.GraphQLSchema
) -> gql.DocumentNode:
    errors = gql.validate(schema, query, rules=[gql.validation.KnownArgumentNamesRule])
    return gql.visit(query, RemoveUnknownArgumentsVisitor(errors))


def remove_values(
    query: gql.DocumentNode,
    ignored_arguments: Optional[Container[str]] = None,
    existing_variables: Optional[Union[str, bytes, Mapping[str, Any]]] = None,
) -> Tuple[gql.DocumentNode, List[str]]:
    visitor = RemoveValuesVisitor(
        ignored_arguments=ignored_arguments, existing_variables=existing_variables
    )
    new_gql_doc = gql.language.visit(query, visitor)

    return new_gql_doc, visitor.removed_arguments


def extract_root_queries(
    query: gql.DocumentNode, remove_aliases: bool = True
) -> Iterable[gql.language.ast.DocumentNode]:
    """
    No need for a visitor here, since we look only at the document's top level.
    By default, remove root field aliases, as once isolated they do not serve any
    purpose.
    """

    query_operations_count = 0

    for definition_node in query.definitions:
        if isinstance(definition_node, gql.language.ast.OperationDefinitionNode):
            if definition_node.operation in [
                gql.language.ast.OperationType.QUERY,
                gql.language.ast.OperationType.SUBSCRIPTION,
            ]:
                if query_operations_count > 0:
                    raise RuntimeError("Document contains more than one query node")

                query_operations_count += 1

                for selection in definition_node.selection_set.selections:
                    if isinstance(selection, gql.language.ast.FieldNode):
                        selection = deepcopy(selection)

                        # Optionally remove alias
                        if remove_aliases:
                            selection.alias = None

                        # Create a fresh document and add the root query to it
                        document = gql.DocumentNode(
                            definitions=gql.pyutils.FrozenList(
                                [
                                    gql.OperationDefinitionNode(
                                        selection_set=gql.SelectionSetNode(
                                            selections=gql.pyutils.FrozenList(
                                                # Add the root query
                                                [selection]
                                            )
                                        ),
                                        operation=definition_node.operation,
                                        variable_definitions=deepcopy(
                                            definition_node.variable_definitions
                                        ),
                                    )
                                ]
                            )
                        )

                        yield document
                    else:
                        raise RuntimeError(f"Unexpected {type(selection)=}")


def remove_aliases(query: gql.DocumentNode) -> gql.DocumentNode:
    return gql.language.visit(query, RemoveAliasesVisitor())


def insert_variables(
    query: gql.DocumentNode, variables: Union[str, bytes, Mapping[str, Any]]
) -> gql.DocumentNode:
    return gql.language.visit(query, InsertVariables(variables))


def build_variable_definitions(
    query: gql.DocumentNode, schema: gql.GraphQLSchema
) -> gql.DocumentNode:
    type_info = gql.utilities.TypeInfo(schema)

    return gql.language.visit(
        query,
        gql.utilities.TypeInfoVisitor(
            type_info, BuildArgumentDefinitionsVisitor(type_info)
        ),
    )


def remove_query_name(query: gql.DocumentNode) -> gql.DocumentNode:
    return gql.language.visit(query, RemoveQueryName())
