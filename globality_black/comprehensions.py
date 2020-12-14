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

    Here we filter only the types that we explode, i.e:
        - dict comprehension or
        - if there is an if

    We don't explode multiple for loops for now
    """

    assert comp_for.type == ParsoTypes.SYNC_COMP_FOR.value

    is_dict = (
        comp_for.parent.type == ParsoTypes.DICTORSETMAKER.value
        and comp_for.parent.children[1] == ":"
    )
    ends_with_if = comp_for.children[-1].type == ParsoTypes.COMP_IF.value
    ends_with_for = comp_for.children[-1].type == ParsoTypes.SYNC_COMP_FOR.value
    has_ternary_operator = comp_for.parent.children[0].type == ParsoTypes.TERNARY_EXPRESSION.value
    # TODO: add more cases to ignore or to explode. Look at known_failed_comprehensions

    if (is_dict or ends_with_if or has_ternary_operator) and not ends_with_for:
        _reformat_comprehension(comp_for)


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

    # indent for
    set_prefix(comp_for, new_prefix)

    # indent comprehension if's
    for child in comp_for.children[1:]:
        if child.type in (ParsoTypes.COMP_IF.value,):
            set_prefix_for_all_comp_if(child, new_prefix)

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


def set_prefix_for_all_comp_if(comp_if: PythonNode, prefix: str):
    """
    indent if in comprehension + all other if's
    unfortunately parso treates each new comp_if after the first one (if any) as a child of the
    previous one. Hence, we need to recursively iterate on them

    """

    assert comp_if.type == "comp_if"

    set_prefix(comp_if, prefix)

    last_child = comp_if.children[-1]
    if last_child.type == "comp_if":
        set_prefix_for_all_comp_if(last_child, prefix)
