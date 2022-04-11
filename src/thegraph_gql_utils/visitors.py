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

import json
from copy import deepcopy
from typing import (
    Any,
    Container,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Union,
)

import graphql as gql
from more_itertools import collapse, flatten

from .misc import ast2str, node2dict


class FactorizeVisitor(gql.language.Visitor):
    """
    Merges identical adjacent selections.
    """

    @staticmethod
    def merge_nodes(node1, node2):
        assert type(node1) is type(node2)

        args = {attr_name: getattr(node1, attr_name) for attr_name in node1.keys}

        for attr_name, attr_value in args.items():
            if isinstance(attr_value, Sequence):
                args[attr_name] = attr_value + getattr(node2, attr_name)
            elif isinstance(attr_value, gql.language.SelectionSetNode):
                selections1 = getattr(attr_value, "selections", [])
                selections2 = getattr(getattr(node2, attr_name), "selections", [])
                args[attr_name].selections = selections1 + selections2

        return type(node1)(**args)

    def enter_selection_set(self, node, _key, _parent, _path, _ancestors):
        selections_dict = {}

        for elem in node.selections:
            if isinstance(elem, gql.language.FieldNode):
                # Identify the fields by (name. alias) tuple
                name_alias = (elem.name.value, getattr(elem.alias, "value", None))

                if name_alias in selections_dict.keys():
                    selections_dict[name_alias] = self.merge_nodes(
                        selections_dict[name_alias], elem
                    )
                else:
                    selections_dict[name_alias] = elem
            else:
                return gql.language.Visitor.IDLE

        node_type = type(node)
        node_dict = node2dict(node)
        node_dict["selections"] = gql.pyutils.FrozenList(selections_dict.values())
        node = node_type(**node_dict)

        return node


class SortVisitor(gql.language.Visitor):
    """
    Lexicographic sort of adjacent selections and arguments.
    """

    @staticmethod
    def node_sort_key(node: gql.language.ast.Node) -> str:
        # Remove aliases for the purposes of sorting
        node = gql.visit(node, RemoveAliasesVisitor())
        node_str = ast2str(node)
        return node_str

    def leave_field(self, node, _key, _parent, _path, _ancestors):
        # Sort by argument name, and if equal by argument value
        arguments = gql.pyutils.FrozenList(
            sorted(
                node.arguments,
                key=self.node_sort_key,
            )
        )

        node_type = type(node)
        node_dict = node2dict(node)
        node_dict["arguments"] = arguments
        node = node_type(**node_dict)

        return node

    def leave_object_value(self, node, _key, _parent, _path, _ancestors):
        # Here we take care of field arguments. We don't expect to have multiple
        # instances of the same argument name.

        # Sort by field name, and if equal by field value
        fields = gql.pyutils.FrozenList(
            sorted(
                node.fields,
                key=self.node_sort_key,
            )
        )

        node_type = type(node)
        node_dict = node2dict(node)
        node_dict["fields"] = fields
        node = node_type(**node_dict)

        return node

    def leave_selection_set(self, node, _key, _parent, _path, _ancestors):

        selections = gql.pyutils.FrozenList(
            sorted(node.selections, key=self.node_sort_key)
        )

        node_type = type(node)
        node_dict = node2dict(node)
        node_dict["selections"] = selections
        node = node_type(**node_dict)

        return node


class PruneArgumentsVisitor(gql.language.Visitor):
    """Keep only the first instance of the same argument type in FieldNodes.

    Example::

        {
            things(arg1: 42, arg2: 5150, arg1: 314) {...}
        }

    Becomes::

        {
            things(arg1: 42, arg2: 5150) {...}
        }

    """

    # pylint: disable=no-self-use
    def enter_field(self, node, _key, _parent, _path, _ancestors):
        arguments_dict = {}
        for elem in node.arguments:
            name = elem.name.value
            # Keep only the first instance of specific argument name
            if name not in arguments_dict.keys():
                arguments_dict[name] = elem

        node_type = type(node)
        node_dict = node2dict(node)
        node_dict["arguments"] = gql.pyutils.FrozenList(arguments_dict.values())
        node = node_type(**node_dict)

        return node


class RemoveFragmentsVisitor(gql.language.Visitor):
    """
    Will remove the fragments and store them in the `fragments` attribute.
    """

    def __init__(self) -> None:
        super().__init__()

        # Fragments will be stored there
        self.fragments = {}

    def enter_fragment_definition(self, node, _key, _parent, _path, _ancestors):
        # Note that if the same fragment name is defined multiple times, the last
        # instance prevails.
        self.fragments[node.name.value] = node.selection_set.selections
        return gql.language.Visitor.REMOVE


class SubstituteFragmentsVisitor(gql.language.Visitor):
    """
    Will insert the fragments where they belong.
    """

    def __init__(self, fragments: Dict[str, gql.pyutils.FrozenDict]) -> None:
        super().__init__()

        # Fragments will be stored there
        self.fragments = fragments

    def enter_selection_set(self, node, _key, _parent, _path, _ancestors):
        new_selections = []
        for s in node.selections:
            if isinstance(s, gql.FragmentSpreadNode):
                # Append all the selections from the correcponding fragment
                new_selections += list(self.fragments[s.name.value])
            else:
                new_selections += [s]

        node_type = type(node)
        node_dict = node2dict(node)
        node_dict["selections"] = gql.pyutils.FrozenList(new_selections)
        node = node_type(**node_dict)

        return node


class RemoveUnknownArgumentsVisitor(gql.language.Visitor):
    def __init__(self, unknown_arg_errors: Iterable[gql.error.GraphQLError]) -> None:
        super().__init__()

        self.unknown_arg_nodes = set(
            flatten(map(lambda e: e.nodes if e.nodes else [], unknown_arg_errors))
        )

    def enter_argument(self, node, _key, _parent, _path, _ancestors):
        if node in self.unknown_arg_nodes:
            return gql.language.Visitor.REMOVE

        return gql.language.Visitor.IDLE


class RemoveValuesVisitor(gql.language.Visitor):
    def __init__(
        self,
        ignored_arguments: Optional[Container[str]] = None,
        existing_variables: Optional[Union[str, bytes, Mapping[str, Any]]] = None,
    ) -> None:
        super().__init__()

        # JSON str to dict
        if isinstance(existing_variables, (str, bytes)):
            self.existing_variables = json.loads(existing_variables)
        elif existing_variables:
            self.existing_variables = existing_variables
        else:
            self.existing_variables = {}

        self.ignored_arguments = ignored_arguments
        self.removed_arguments: List[str] = []
        self._placeholder_counter = 0

    def enter(self, node, _key, parent, _path, ancestors):
        if any(
            isinstance(a, gql.language.VariableDefinitionNode)
            for a in collapse(ancestors)
        ):
            return gql.language.visitor.IDLE

        if isinstance(node, gql.language.ValueNode) and not isinstance(
            node, gql.language.ObjectValueNode
        ):
            if (
                self.ignored_arguments is None
                or parent.name.value not in self.ignored_arguments
            ):
                if isinstance(node, gql.language.VariableNode):
                    self.removed_arguments += [
                        str(self.existing_variables[node.name.value])
                    ]
                else:
                    self.removed_arguments += [
                        gql.utilities.value_from_ast_untyped(node)
                    ]

                # Create placeholder variable
                placeholder_var = gql.language.parse_value(
                    f"$_{self._placeholder_counter}"
                )
                self._placeholder_counter += 1
                return placeholder_var

        return gql.language.Visitor.IDLE


class BuildArgumentDefinitionsVisitor(gql.language.Visitor):
    def __init__(
        self,
        type_info: gql.utilities.TypeInfo,
    ) -> None:
        super().__init__()

        self.type_info = type_info
        self.vardefs = {}

    # pylint: disable=no-self-use
    def enter_variable_definition(self, _node, _key, _parent, _path, _ancestors):
        # Removes existing variable definitions
        return gql.language.visitor.REMOVE

    def enter_variable(self, node, _key, _parent, _path, _ancestors):
        self.vardefs[node.name.value] = self.type_info.get_input_type()

    def leave_operation_definition(self, node, _key, _parent, _path, _ancestors):
        opdef_vardefs = []
        for varname, vartype in self.vardefs.items():
            opdef_vardefs += [
                gql.language.ast.VariableDefinitionNode(
                    type=gql.language.ast.NamedTypeNode(
                        name=gql.language.NameNode(value=str(vartype))
                    ),
                    variable=gql.language.ast.VariableNode(
                        name=gql.language.NameNode(value=varname)
                    ),
                )
            ]

        new_node = node2dict(node)
        new_node["variable_definitions"] = opdef_vardefs
        return gql.language.ast.OperationDefinitionNode(**new_node)


class RemoveAliasesVisitor(gql.language.Visitor):
    """
    Useful for certain operations that require ignoring the aliases, such as sort.
    """

    # pylint: disable=no-self-use
    def enter_field(self, node, _key, _parent, _path, _ancestors):
        """
        Only FieldNodes define an alias.
        """

        node = deepcopy(node)
        node.alias = None

        return node


class InsertVariables(gql.language.Visitor):
    """
    Replace variables placeholders with the variable values provided with the query.
    """

    def __init__(
        self,
        variables: Union[str, bytes, Mapping[str, Any]],
        type_info: gql.utilities.TypeInfo,
    ) -> None:
        super().__init__()

        self.type_info = type_info

        # JSON str to dict
        if isinstance(variables, (str, bytes)):
            self.variables = json.loads(variables)
        else:
            self.variables = variables

    def enter_variable(self, node, _key, _parent, _path, ancestors):
        if any(
            isinstance(a, gql.language.VariableDefinitionNode)
            for a in collapse(ancestors)
        ):
            return gql.language.visitor.IDLE

        if node.name.value in self.variables.keys():
            variable_type = self.type_info.get_input_type()
            if isinstance(variable_type, gql.GraphQLInputObjectType) and isinstance(
                self.variables[node.name.value], str
            ):
                # The object is stored as JSON. Deserialize it first.
                self.variables[node.name.value] = json.loads(
                    self.variables[node.name.value]
                )

            return gql.utilities.ast_from_value(
                self.variables[node.name.value], variable_type
            )

        raise RuntimeError(f"No value provided for variable {node.name.value}")


class RemoveQueryName(gql.language.Visitor):
    # pylint: disable=no-self-use
    def enter_operation_definition(self, node, _key, _parent, _path, _ancestors):
        if node.name:
            new_node = node2dict(node)
            new_node["name"] = None
            new_node = gql.language.ast.OperationDefinitionNode(**new_node)
            return new_node

        return gql.language.visitor.IDLE
