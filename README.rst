thegraph-gql-utils
==================

GraphQL language utilities designed for use on GraphQL queries targeted at
`The Graph Protocol`_.

Contains tools to normalize or otherwise manipulate GraphQL queries.

.. _The Graph Protocol: https://thegraph.com

Building
--------

The project is managed by `Poetry`_. You will need to install
Poetry version v1.2.0b2 or above.

.. _Poetry: https://python-poetry.org

Example
-------

.. code-block:: python

    from graphql import parse, print_ast
    from thegraph_gql_utils import tools

    query = parse("""
    {
        pairs(orderDirection: asc, first: 10) {
            reserve0
            id
            name
        }
    }
    """)

    new_query = tools.sort(query)

    print(print_ast(new_query))

Output::

    {
        pairs(first: 10, orderDirection: asc) {
            id
            name
            reserve0
        }
    }
