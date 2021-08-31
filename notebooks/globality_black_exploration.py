# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: incorrectly_encoded_metadata,-execution
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.10.2
#   kernelspec:
#     display_name: Python [conda env:gb]
#     language: python
#     name: conda-env-gb-py
# ---

# %% [markdown]
# This is just an exploration notebook to experiment with parso and help in development of new
# features
#
# %%
import re
from pathlib import Path

import pandas as pd
import parso
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
# ## Dotted chains

# %% tags=[]
path = "../globality_black/tests/fixtures/dotted_chains_input.txt"

# %% tags=[]
file_contents = Path(path).read_text()
module = parso.parse(file_contents)

# %% tags=[]
output = module.get_code().split("\n")
print("\n".join(output[:8]))

# %% tags=[]
block1 = module.children[1].children[4].children[1].children[0]
print(block1.get_code())
block1

# %% tags=[] jupyter={"outputs_hidden": true, "source_hidden": true}
block2 = module.children[2].children[0]
print(block2.get_code())
block2

# %% tags=[] jupyter={"outputs_hidden": true, "source_hidden": true}
block3 = module.children[3]
print(block3.get_code())
block3

# %% tags=[]
block1.children

# %% tags=[] jupyter={"source_hidden": true, "outputs_hidden": true}
block2.children[2].children

# %% tags=[] jupyter={"outputs_hidden": true, "source_hidden": true}
block3.children[1]  # .children[1].children[1]

# %% [markdown]
# atom_expr is the types to inspect here

# %% [markdown]
# ### is_dotted_chain


ae1 = block1.children[2].children[1]
print(ae1.get_code())
print(ae1.type)
pd.DataFrame(dict(elem=ae1.children)).assign(
    code=lambda df: df.elem.apply(lambda e: e.get_code()),
    _type=lambda df: df.elem.apply(lambda e: type(e).__name__),
    a_type=lambda df: df.elem.apply(lambda e: e.type),
    first_leaf_prefix=lambda df: df.elem.apply(lambda e: "'" + e.get_first_leaf().prefix) + "'",
)
# pd.Series(ae1).apply(lambda e: e.type)


# %% tags=[]
def is_dotted_chain(atom_expr):
    """
    Assert whether the given atom_expr is a dotted chain

    Examples:

    batch(a)(b)
    .sample(
        frac=param1,
        rs=param2,
    )
    .reset_index(drop1=True)(drop2=True)
    .reset_index(drop=True).reset_index(drop=True)
    --> True

    batch
    (batch)
    --> False

    batch,
    batch,
    --> False

    batch
    .batch
    --> True

    batch
    .batch(
        x=4,
    )
    --> True

    """
    # print(atom_expr.get_code())
    # print(atom_expr)
    children = atom_expr.children

    # first node should start with \n + tabs (sapces multiple of 4)
    prefix_child1 = children[0].get_first_leaf().prefix
    if not re.match(r"\n(?:\s{4})+", prefix_child1):
        return False

    # more than one child needed to be a dotted chain
    if len(children) < 2:
        return False

    # all children after the first one that start with \n + tabs should have a . afterwards
    # otherwise it's not a dotted chain
    for child in children[1:]:
        code = child.get_code()
        if re.match(r"\n(?:\s{4})+", code):
            if not code.strip().startswith("."):
                return False

    return True


def read_and_turn_to_ae(code):
    m = parso.parse("labels = (" + code + "\n)")
    #     breakpoint()
    return m.children[0].children[2].children[1]


print(
    is_dotted_chain(ae1),
    is_dotted_chain(read_and_turn_to_ae("\n    batch\n    (batch)")),
    is_dotted_chain(read_and_turn_to_ae("\n    batch,\n    batch,")),
    is_dotted_chain(read_and_turn_to_ae("\n    batch\n    .batch")),
    is_dotted_chain(read_and_turn_to_ae("\n    batch\n    .batch(\n        x=4,\n    )")),
)

# %% tags=[]
type(module.children[0])

# %% tags=[]
re.match(r"\n(?:\s{4})+", ae1.children[0].prefix)

# %% tags=[]
ae1.children[0].get_code()

# %% tags=[]
ae1.children[3].get_code().strip()

# %% tags=[]
ae1[1].children[0]
