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
from gql_utils.tools import substitute_fragments


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (
            """
            {
                potato(first: 1) {
                    banana
                    ...fragment1
                    pear
                    ...fragment2
                    tomato {
                        ...fragment1
                    }
                }
            }

            fragment fragment1 on Food {
                something
                somethingelse {
                    id
                }
            }

            fragment fragment2 on MoreFood {
                importantthing {
                    indeed {
                        id
                    }
                }
                id
            }
            """,
            """
            {
                potato(first: 1) {
                    banana
                    something
                    somethingelse {
                        id
                    }
                    pear
                    importantthing {
                        indeed {
                            id
                        }
                    }
                    id
                    tomato {
                        something
                        somethingelse {
                            id
                        }
                    }
                }
            }
            """,
        ),
        (
            """
            query IntrospectionQuery {
              __schema {
                queryType {
                  name
                }
                mutationType {
                  name
                }
                subscriptionType {
                  name
                }
                types {
                  ...FullType
                }
                directives {
                  name
                  locations
                  args {
                    ...InputValue
                  }
                }
              }
            }

            fragment FullType on __Type {
              kind
              name
              fields(includeDeprecated: true) {
                name
                args {
                  ...InputValue
                }
                type {
                  ...TypeRef
                }
                isDeprecated
                deprecationReason
              }
              inputFields {
                ...InputValue
              }
              interfaces {
                ...TypeRef
              }
              enumValues(includeDeprecated: true) {
                name
                isDeprecated
                deprecationReason
              }
              possibleTypes {
                ...TypeRef
              }
            }

            fragment InputValue on __InputValue {
              name
              type {
                ...TypeRef
              }
              defaultValue
            }

            fragment TypeRef on __Type {
              kind
              name
              ofType {
                kind
                name
                ofType {
                  kind
                  name
                  ofType {
                    kind
                    name
                    ofType {
                      kind
                      name
                      ofType {
                        kind
                        name
                        ofType {
                          kind
                          name
                          ofType {
                            kind
                            name
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
            """,
            """
            query IntrospectionQuery {
              __schema {
                queryType {
                  name
                }
                mutationType {
                  name
                }
                subscriptionType {
                  name
                }
                types {
                  kind
                  name
                  fields(includeDeprecated: true) {
                    name
                    args {
                      name
                      type {
                        kind
                        name
                        ofType {
                          kind
                          name
                          ofType {
                            kind
                            name
                            ofType {
                              kind
                              name
                              ofType {
                                kind
                                name
                                ofType {
                                  kind
                                  name
                                  ofType {
                                    kind
                                    name
                                    ofType {
                                      kind
                                      name
                                    }
                                  }
                                }
                              }
                            }
                          }
                        }
                      }
                      defaultValue
                    }
                    type {
                      kind
                      name
                      ofType {
                        kind
                        name
                        ofType {
                          kind
                          name
                          ofType {
                            kind
                            name
                            ofType {
                              kind
                              name
                              ofType {
                                kind
                                name
                                ofType {
                                  kind
                                  name
                                  ofType {
                                    kind
                                    name
                                  }
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                    isDeprecated
                    deprecationReason
                  }
                  inputFields {
                    name
                    type {
                      kind
                      name
                      ofType {
                        kind
                        name
                        ofType {
                          kind
                          name
                          ofType {
                            kind
                            name
                            ofType {
                              kind
                              name
                              ofType {
                                kind
                                name
                                ofType {
                                  kind
                                  name
                                  ofType {
                                    kind
                                    name
                                  }
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                    defaultValue
                  }
                  interfaces {
                    kind
                    name
                    ofType {
                      kind
                      name
                      ofType {
                        kind
                        name
                        ofType {
                          kind
                          name
                          ofType {
                            kind
                            name
                            ofType {
                              kind
                              name
                              ofType {
                                kind
                                name
                                ofType {
                                  kind
                                  name
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                  enumValues(includeDeprecated: true) {
                    name
                    isDeprecated
                    deprecationReason
                  }
                  possibleTypes {
                    kind
                    name
                    ofType {
                      kind
                      name
                      ofType {
                        kind
                        name
                        ofType {
                          kind
                          name
                          ofType {
                            kind
                            name
                            ofType {
                              kind
                              name
                              ofType {
                                kind
                                name
                                ofType {
                                  kind
                                  name
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
                directives {
                  name
                  locations
                  args {
                    name
                    type {
                      kind
                      name
                      ofType {
                        kind
                        name
                        ofType {
                          kind
                          name
                          ofType {
                            kind
                            name
                            ofType {
                              kind
                              name
                              ofType {
                                kind
                                name
                                ofType {
                                  kind
                                  name
                                  ofType {
                                    kind
                                    name
                                  }
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                    defaultValue
                  }
                }
              }
            }
            """,
        ),
    ],
)
def test_substitute_fragments(test_input: str, expected: str):
    input_query = gql.parse(test_input)
    expected_query = gql.parse(expected)

    new_query = substitute_fragments(input_query)

    assert ast2str(new_query) == ast2str(expected_query)
