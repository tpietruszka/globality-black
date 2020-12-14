# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: incorrectly_encoded_metadata,-execution
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.6.0
#   kernelspec:
#     display_name: Python [conda env:play]
#     language: python
#     name: conda-env-play-py
# ---

# %% [markdown]
# This is just an exploration notebook to experiment with parso and help in development of new
# features
#
# %%
import re
from ast import dump, parse
from copy import deepcopy
from pathlib import Path

import parso
from parso.normalizer import Normalizer
from parso.python.tree import Function


# %%
path = "sample.py"
path = "../globality_black/tests/fixtures/comprehensions_input.txt"

# %%
file_contents = Path(path).read_text()
module = parso.parse(file_contents)

# %%
module

# %%
output = module.get_code()
type(output)
print(file_contents == output)
print(output[:90])

# %%
x = module.children[0]
x

# %%
x.prefix

# %%
x.get_first_leaf()

# %%
x.children[0].children[0].prefix

# %%
y = module.get_leaf_for_position(x.start_pos)

# %%
y.prefix

# %%
x.get_first_leaf()

# %%
func = next(module.iter_funcdefs())
func

# %%
func.children[2].children[-1].get_first_leaf()


# %%
def detect_magic_comma(function: Function):
    # get last param in signature. get its children and
    # check if the last one equals ","
    if len(function.get_params()) > 0:
        return function.get_params()[-1].children[-1] == ","
    return False


# %% [markdown] toc-hr-collapsed=true toc-nb-collapsed=true
# ## detect magic comma for functions

# %%
print(module.children[0].type == "funcdef")

# %%
# go through every function (class methods TODO)
f = module.children[1]
print(f.get_code())

# %%
params = f.get_params()
params

# %%
params[-1].children

# %%
detect_magic_comma(f)

# %% [markdown]
# ## detect magic comma for class methods

# %%
c = module.children[3]
c

# %%
for function in c.iter_funcdefs():
    print(f"{function.name.value}: {detect_magic_comma(function)}")

# %%
cf = list(c.iter_funcdefs())[1]
list(cf.iter_funcdefs())


# %%
def get_indent_first_param(function):
    pos = function.get_params()[0].start_pos
    prefix = function.get_leaf_for_position(pos).prefix
    return get_indent_from_prefix(prefix)


# %%
def get_indent_from_prefix(prefix):
    if prefix:
        try:
            return re.findall("( *)$", prefix)[0]
        except Exception:
            breakpoint()
    else:
        return prefix


# %%
def correct_prefix_if_magic_comma(function):

    if detect_magic_comma(function):
        params = function.get_params()
        prefix = function.get_first_leaf().prefix
        base_indent = get_indent_from_prefix(prefix)
        for param in params:

            leaf = param.get_first_leaf()
            leaf.prefix = "\n" + base_indent + " " * 4

        # get right parentheses
        leaf = function.children[2].children[-1].get_first_leaf()
        leaf.prefix = "\n" + base_indent

    for nested_function in function.iter_funcdefs():
        correct_prefix_if_magic_comma(nested_function)


# %%
for c in module.children:
    print(c)

# %%
module.children[1].type

# %% [markdown]
# ## Experiment with function calls

# %%
print(module.get_code())


# %%
class TypeFinder:
    def __init__(self, types_to_find):
        self.types_to_find = types_to_find

    def __call__(self, node):
        if node.type in self.types_to_find:
            yield node
        if hasattr(node, "children"):
            for child in node.children:
                yield from self(child)


# %%
arglist = module.children[2].children[0].children[1].children[1]
arglist

# %%
# finder = TypeFinder(["funcdef", "arglist"])
finder = TypeFinder(["parameters", "arglist"])
for elem in finder(module):
    print(elem)
    break

# %%
elem.get_params()[-1]

# %%
elem.children[-2]

# %%
elem.get_params()[-1].children[-1]

# %%
print(elem.get_code())

# %%
elem.children

# %% [markdown]
# # Test it !

# %%
file_contents = Path("../tests/fixtures/defs_input.py").read_text()
module = parso.parse(file_contents)
# for child in module.children:
#     if child.type == "funcdef":
#         correct_prefix_if_magic_comma(child)
#     if child.type == "classdef":
#         for method in child.iter_funcdefs():
#             correct_prefix_if_magic_comma(method)

# with open("output.py", "w") as f:
#     f.write(module.get_code())

# %%
print(module.get_code()[:100])

# %%
module.children[0].children[2].children[1]

# %%
module.children[0].children[2].children[1].get_first_leaf()

# %%
prefix = module.children[0].children[2].children[1].get_first_leaf().prefix
prefix

# %%
re.findall("( *)$", prefix)[0]

# %%
re.search("( *)$", prefix).group(0)

# %%
file_contents = Path("../tests/fixtures/calls_input.py").read_text()
module = parso.parse(file_contents)
for child in module.children:
    if child.type == "funcdef":
        correct_prefix_if_magic_comma(child)
    if child.type == "classdef":
        for method in child.iter_funcdefs():
            correct_prefix_if_magic_comma(method)

with open("output.py", "w") as f:
    f.write(module.get_code())

# %%
list(c.iter_funcdefs())

# %%
cf.get_first_leaf().prefix

# %% [markdown]
# # SPEC if magic comma, always explode

# %%
# file_contents = Path("sample.py").read_text()

file_contents = """
x = foo(a=fee(3, 2,), b=5,)
"""
module = parso.parse(file_contents)
print(module.get_code())


# %%
def print_children(a):
    if hasattr(a, "children") and a.children:
        print()
        print(f"{a} has children {a.children}")
        for c in a.children:
            print_children(c)
    else:
        print(a)


# %%
print_children(module)

# %%
s = module.children[0].children[0]
s

# %%
rhs = s.get_rhs()
rhs

# %%
rhs.children

# %%
foo = module.children[0]
print(foo.get_params())
print(foo.get_params()[0].end_pos)
foo.get_leaf_for_position((2, 8)), foo.get_leaf_for_position((2, 9)), foo.get_leaf_for_position(
    (2, 12)
)

# %%
foo = module.children[1]
print(foo.get_params())
module.get_leaf_for_position((4, 10))

# %%

# %%

# %%

# %%
print(f"{function.name.value}: {repr(function.get_first_leaf().prefix)}")


# %%
class RefactoringNormalizer(Normalizer):
    def __init__(self, grammar):
        super(RefactoringNormalizer, self).__init__(grammar, None)
        self._replaced_leaves = {}

    def replace_leaf(self, leaf, prefix=None, value=None):
        self._replaced_leaves[leaf] = prefix, value

    def visit_leaf(self, leaf):
        try:
            prefix, value = self._replaced_leaves[leaf]
            return (
                leaf.prefix if prefix is None else prefix + leaf.value if value is None else value
            )
        except KeyError:
            return leaf.prefix + leaf.value


# %%

# %%

# %%

# %%
grammar = parso.load_grammar()
module = grammar.parse(file_contents)

# %%
foo = module.children[0]


foo2 = deepcopy(foo)

# %%
foo2.children.append(foo2.children[-1])
print(foo2.get_code())

# %%
pos = foo.get_params()[2].start_pos
leaf = foo.get_leaf_for_position(pos)
pos

# %%
normalizer = RefactoringNormalizer(grammar=grammar)
# normalizer.replace_leaf(first_leaf)
# leaf = foo.get_params()[2]
normalizer.replace_leaf(leaf, prefix="\n\n\n" + leaf.prefix)
# normalizer.replace_leaf(foo, value=foo2)


new_code = normalizer.walk(module)

# %%
print(new_code)

# %% [markdown]
# <!-- CHECK IF WE CAN APPEND CHILDREN WITH THE ABOVE CODE -->

# %%

# %%

# %%

# %%

# %% [markdown]
# # ORIGINAL

# %%
dump(parse("pokey.py"))

# %%
file_contents = Path("pokey.py").read_text()

# %%
module = parso.parse(file_contents)

# %%
print(module.get_code())

# %%
output = module.get_code()

# %%
file_contents == output

# %%
f = module.children[-2]

# %%
print(f.get_code())

# %%
for child in f.children:
    print(child)

# %%
print(f.children[4].get_code())

# %%
f.children[-1]

# %%
print("".join(node.get_code() for node in f.children[:-1]))

# %%
f.start_pos

# %%
[node.start_pos for node in f.children]

# %%
f.children[2]

# %%
param_list = f.children[2]

# %%
[node.start_pos for node in param_list.children]

# %%
param_list.children[-1]

# %%
param_list.children[0]

# %%
param_list.children

# %%
dir(param_list.children[1])

# %%
param_list.children[1].get_first_leaf().prefix = "\n\t"

# %%
param_list.children[1].get_first_leaf().prefix

# %%
print(param_list.get_code())

# %%
param_list.parent.get_last_leaf()

# %%
param_list.type

# %%
f.get_params()

# %%
f

# %%
graph_use = f.children[-1].children[4]

# %%
trailer = graph_use.children[0].children[2]

# %%
arglist = trailer.children[1]
print(arglist.get_code())

# %%
arglist.children[4].prefix

# %%
list(module.iter_funcdefs())


# %%
class TypeFinder:
    def __init__(self, type_to_find):
        self.type_to_find = type_to_find

    def __call__(self, node):
        if node.type == self.type_to_find:
            yield node
        if hasattr(node, "children"):
            for child in node.children:
                yield from self(child)


# %%
trailer_finder = TypeFinder("trailer")

# %%
arg_finder = TypeFinder("trailer")

# %%
for node in trailer_finder(module):
    print(node.get_code())

# %%
list(trailer_finder(module))[5]


# %%
class WhitespaceInTrailerFinder:
    def __init__(self):
        self.trailer_count = 0

    def __call__(self, node):
        if self.trailer_count > 0:
            if hasattr(node, "prefix") and "\n\n" in node.prefix:
                yield node
        if node.type == "trailer":
            self.trailer_count += 1

        if hasattr(node, "children"):
            for child in node.children:
                yield from self(child)

        if node.type == "trailer":
            self.trailer_count -= 1


# %%
finder = WhitespaceInTrailerFinder()

# %%
trailer_descendents_with_empty_line_prefixes = list(finder(module))

# %%
trailer_descendents_with_empty_line_prefixes

# %%
[param.get_first_leaf().prefix for param in f.get_params()]

# %%
trailer_descendents_with_empty_line_prefixes[0].parent.parent.parent.parent.parent

# %%
next(module.iter_funcdefs()).get_params()[0].get_first_leaf().prefix

# %%
