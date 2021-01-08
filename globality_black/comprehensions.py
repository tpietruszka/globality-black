"""
Module to explode comprehensions:
- all dict comprehensions
- all comprehensions with `if`

"""
from parso.python.tree import PythonNode

from globality_black.common import find_indentation_parent_prefix, get_indent_from_prefix
from globality_black.constants import ParsoTypes


def reformat_comprehension(comp_for: PythonNode):
    """
    comp_for represents a subset of the comprehension, e.g. in

    [(3, i): "globality" for i in range(4) if i < 2]

    comp_for is a PythonNode with type "sync_comp_for" and code
        "for i in range(4) if i < 2"

    comp is a PythonNode with type "testlist_comp" and code
        "(3, i): "globality" for i in range(4) if i < 2"

    We explode if at least one of the following requirements are met:
        - dict comprehension
        - there is an if
        - there is a ternary operator
        - there are multiple for's

    We don't explode:
        - comprehension inside of comprehension (the inner one will be kept as is)
        - if multiple for's, the first one already explodes the rest
        (with `set_prefix_for_all_last_children`), so they are ignored
    """

    assert comp_for.type == ParsoTypes.SYNC_COMP_FOR.value

    comp = comp_for.parent

    is_dict = comp.type == ParsoTypes.DICTORSETMAKER.value and comp.children[1] == ":"
    ends_with_if = comp_for.children[-1].type == ParsoTypes.COMP_IF.value
    ends_with_for = comp_for.children[-1].type == ParsoTypes.SYNC_COMP_FOR.value
    value_is_ternary_expression = comp.children[0].type == ParsoTypes.TERNARY_EXPRESSION.value
    value_is_comprehension = find_if_value_is_comprehension(comp)

    parent_is_for = comp.type == ParsoTypes.SYNC_COMP_FOR.value
    comprehension_types = (ParsoTypes.DICTORSETMAKER.value, ParsoTypes.LISTCOMP.value)
    nested_comp = comp.parent.parent.type in comprehension_types

    requirements = is_dict or ends_with_if or ends_with_for
    requirements = requirements or value_is_ternary_expression or value_is_comprehension
    can_be_ignored = parent_is_for or nested_comp

    if requirements and not can_be_ignored:
        _reformat_comprehension(comp_for)


def find_if_value_is_comprehension(comp):
    value = comp.children[0]
    for child in getattr(value, "children", []):
        if child.type == "testlist_comp":
            return True
    return False


def _reformat_comprehension(comp_for: PythonNode):
    """
    Here we do the actual reformatting
    """
    comp = comp_for.parent
    prefix = find_indentation_parent_prefix(comp)
    base_indent = get_indent_from_prefix(prefix)
    new_prefix = "\n" + base_indent + " " * 4

    # indent element of comp
    set_prefix(comp, new_prefix)

    set_prefix_for_all_last_children(comp_for, new_prefix)

    # set closing bracket
    set_prefix(comp.parent.children[-1], "\n" + base_indent)


def set_prefix(element: PythonNode, prefix: str):

    leaf = element.get_first_leaf()

    # if there's only space, replace
    if not leaf.prefix.strip():
        leaf.prefix = prefix

    # otherwise, add prefix to previous prefix (to keep comments)
    else:
        last_eol_position = leaf.prefix.rindex("\n")
        leaf.prefix = leaf.prefix[:last_eol_position] + prefix


def set_prefix_for_all_last_children(comp_for: PythonNode, prefix: str):
    """
    indent for in comprehension + all for and if underneath
    unfortunately parso treates each new comp_for and comp_if after the comp_for (if any) as a child
    of the
    previous one. Hence, we need to recursively iterate on them

    """

    set_prefix(comp_for, prefix)

    last_child = comp_for.children[-1]
    if last_child.type in {ParsoTypes.COMP_IF.value, ParsoTypes.SYNC_COMP_FOR.value}:
        set_prefix_for_all_last_children(last_child, prefix)
