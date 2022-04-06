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
    """Merges same-level identical selections.

    For each level, the merging of the selections will merge both arguments and
    sub-selections recursively. For example:

    .. code-block:: graphql

        {
            pairs(orderDirection: asc, first: 10) {
                id
                name
                reserve0
                liquidityPositions(first: 10) {
                    id
                }
            }
            pairs(orderDirection: desc, first: 5, skip: 2) {
                id
                name
                timestamp
                liquidityPositions(skip: 1) {
                    block
                }
            }
        }

    Becomes:

    .. code-block:: graphql

        {
            pairs(orderDirection: asc, first: 10, orderDirection: desc, first: 5, skip: 2) {
                id
                name
                reserve0
                liquidityPositions(first: 10, skip: 1) {
                    id
                    block
                }
                timestamp
            }
        }

    Args:
        query (gql.DocumentNode): input query AST

    Returns:
        gql.DocumentNode: output query AST
    """

    return gql.language.visit(query, FactorizeVisitor())


def sort(query: gql.DocumentNode) -> gql.DocumentNode:
    """Lexicographic sort of adjacent arguments and selections.

    For example:

    .. code-block:: graphql

        {
            pairs(orderDirection: asc, first: 10) {
                reserve0
                id
                name
            }
        }

    Becomes:

    .. code-block:: graphql

        {
            pairs(first: 10, orderDirection: asc) {
                id
                name
                reserve0
            }
        }

    Args:
        query (gql.DocumentNode): input query AST

    Returns:
        gql.DocumentNode: output query AST
    """

    return gql.language.visit(query, SortVisitor())


def prune_query_arguments(query: gql.DocumentNode) -> gql.DocumentNode:
    """Keep only the first instance of the same argument type in FieldNodes.

    For example:

    .. code-block:: graphql

        {
            things(arg1: 42, arg2: 5150, arg1: 314) {}
        }

    Becomes:

    .. code-block:: graphql

        {
            things(arg1: 42, arg2: 5150) {}
        }

    Args:
        query (gql.DocumentNode): input query AST

    Returns:
        gql.DocumentNode: output query AST
    """

    return gql.language.visit(query, PruneArgumentsVisitor())


def substitute_fragments(query: gql.DocumentNode) -> gql.DocumentNode:
    """Substitutes the fragment spread nodes with their definition.

    Will also remove the fragment definitions.
    For example:

    .. code-block:: graphql

        {
            pairs() {
                id
                ...f1
            }
        }
        fragment f1 on Pair {
            name
            reserve0
        }

    Becomes:

    .. code-block:: graphql

        {
            pairs() {
                id
                name
                reserve0
            }
        }

    Args:
        query (gql.DocumentNode): input query AST

    Returns:
        gql.DocumentNode: output query AST
    """
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
    """Removes arguments unknown by the schema.

    Args:
        query (gql.DocumentNode): input query AST
        schema (gql.GraphQLSchema): input schema AST

    Returns:
        gql.DocumentNode: output query AST
    """
    errors = gql.validate(schema, query, rules=[gql.validation.KnownArgumentNamesRule])
    return gql.visit(query, RemoveUnknownArgumentsVisitor(errors))


def remove_values(
    query: gql.DocumentNode,
    ignored_arguments: Optional[Container[str]] = None,
    existing_variables: Optional[Union[str, bytes, Mapping[str, Any]]] = None,
) -> Tuple[gql.DocumentNode, List[str]]:
    """Extracts all values, replaces them with variables.

    The new variables will be named `$_0` ... `$_n`, and an ordered list of the
    corresponding values will be returned in addition to the altered query AST.

    Already existing variables can be supplied. These will be renamed using the same
    convention as the other values, and the values will be included in the  returned
    list of variables.

    Example:

    .. code-block:: graphql

        {
            pairs(orderDirection: $orderDirection, first: 10, skip: 3) {
                id
            }
        }

    with

    .. code-block:: python

        existing_variables = {"$orderDirection": "asc"}
        ignored_arguments = ["skip"]

    Yields:

    .. code-block:: graphql

        {
            pairs(orderDirection: $_0, first: $_1, skip: 3) {
                id
            }
        }

    and

    .. code-block:: python

        ["asc", "10"]

    Args:
        query (gql.DocumentNode): input query AST
        ignored_arguments (Optional[Container[str]], optional): List of argument names
            whose values to ignore. Defaults to None.
        existing_variables (Optional[Union[str, bytes, Mapping[str, Any]]], optional):
            Existing query arguments. Defaults to None.

    Returns:
        Tuple[gql.DocumentNode, List[str]]: output query AST
    """
    visitor = RemoveValuesVisitor(
        ignored_arguments=ignored_arguments, existing_variables=existing_variables
    )
    new_gql_doc = gql.language.visit(query, visitor)

    return new_gql_doc, visitor.removed_arguments


def extract_root_queries(
    query: gql.DocumentNode, remove_aliases: bool = True
) -> Iterable[gql.language.ast.DocumentNode]:
    """Split query top level selections.

    Example:

    .. code-block:: graphql

        {
            pairs {
                id
            }
            mints {
                id
                pair {
                    name
                }
            }
        }

    Is split into:

    .. code-block:: graphql

        {
            pairs {
                id
            }
        }

    and

    .. code-block:: graphql

        {
            mints {
                id
                pair {
                    name
                }
            }
        }

    Args:
        query (gql.DocumentNode): input query AST
        remove_aliases (bool, optional): Remove alias names. Defaults to True.

    Raises:
        RuntimeError: Document contains more than one query node.
        RuntimeError: Unexpected type(selection) != FieldNode.

    Returns:
        Iterable[gql.language.ast.DocumentNode]: Iterable of output query AST's

    Yields:
        Iterator[Iterable[gql.language.ast.DocumentNode]]:
    """

    # No need for a visitor here, since we look only at the document's top level.
    # By default, remove root field aliases, as once isolated they do not serve any
    # purpose.

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
    """Remove all alias names.

    Args:
        query (gql.DocumentNode): input query AST

    Returns:
        gql.DocumentNode: output query AST
    """
    return gql.language.visit(query, RemoveAliasesVisitor())


def insert_variables(
    query: gql.DocumentNode, variables: Union[str, bytes, Mapping[str, Any]]
) -> gql.DocumentNode:
    """Inserts provided variable values in place of variables in the query.

    Note that it will not do type inference for now, so it might cause type issues in
    the resulting query.

    For example:

    .. code-block:: graphql

        {
            pairs(orderDirection: $_0, first: $_1, skip: 3) {
                id
            }
        }

    with:

    .. code-block: python

        {"_0": "asc", "_1": 24}

    Gives:

    .. code-block:: graphql

        {
            pairs(orderDirection: "asc", first: 24, skip: 3) {
                id
            }
        }

    Args:
        query (gql.DocumentNode): input query AST
        variables (Union[str, bytes, Mapping[str, Any]]): Variables mapping

    Returns:
        gql.DocumentNode: output query AST
    """
    return gql.language.visit(query, InsertVariables(variables))


def build_variable_definitions(
    query: gql.DocumentNode, schema: gql.GraphQLSchema
) -> gql.DocumentNode:
    """Builds the query variable definitions by inferring types based on schema.

    Example:

    .. code-block:: graphql

        {
            pairs(orderDirection: $orderDirection, first: 10, skip: 3) {
                id
            }
        }

    Gives (with supplying the appropriate schema):

    .. code-block:: graphql

        query ($orderDirection: OrderDirection) {
            pairs(orderDirection: $orderDirection, first: 10, skip: 3) {
                id
            }
        }

    Args:
        query (gql.DocumentNode): input query AST
        schema (gql.GraphQLSchema): schema AST

    Returns:
        gql.DocumentNode: output query AST
    """
    type_info = gql.utilities.TypeInfo(schema)

    return gql.language.visit(
        query,
        gql.utilities.TypeInfoVisitor(
            type_info, BuildArgumentDefinitionsVisitor(type_info)
        ),
    )


def remove_query_name(query: gql.DocumentNode) -> gql.DocumentNode:
    """Removes the query name.

    Example:

    .. code-block:: graphql

        query MyQuery {
            pairs {
                id
            }
        }

    Becomes:

    .. code-block:: graphql

        {
            pairs {
                id
            }
        }

    Args:
        query (gql.DocumentNode): input query AST

    Returns:
        gql.DocumentNode: output query AST
    """
    return gql.language.visit(query, RemoveQueryName())
