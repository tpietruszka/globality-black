Globality black
===============


A wrapper for black, adding pre- and post-processing 
to better align with Globality conventions.

`globality-black` performs the following steps:

 - pre-processing: to protect from black actions.
 - black
 - postprocessing: to revert / correct black actions.
 

Features
--------

### Blank lines
 
Black would remove those blank lines after `wandb` and `scikit-learn` below:

```
graph.use(
    "wandb",

    "scikit-learn",

    # we love pandas
    "pandas",
)
```

`globality-black` protects those assuming the developer added them for readability. 

### Comprehensions 

Explode comprehensions
* all dict comprehensions
* any comprehension with an if
* any comprehension with multiple for lopps (see examples below)
* list / set comprehensions where the element:
   - has a ternary operator (see examples below)
   - has another comprehension

For everything else, we rely on `black`. Examples:

#### Before globality-black

```
[3 for _ in range(10)]

[3 for i in range(10) if i < 4]

{"a": 3 for _ in range(4)}

{"a": 3 for _ in range(4) if i < 4}

["odd" if i %% 2 == 0 else "even" for _ in range(10)]

double_comp1 = [3*i*j for i in range(10) for j in range(4)]

double_comp2 = [[i for i in range(7) if i < 5] for j in range(10)]

double_comp3 = {i: [i for i in range(7) if i < 5] for j in range(10) if i < 2}
```

#### After globality-black 

```
[3 for _ in range(10)]

[
    3
    for i in range(10)
    if i < 4
]

{
    "a": 3
    for _ in range(4)
}

{
    "a": 3
    for _ in range(4)
    if i < 4
}

[
    "odd" if i %% 2 == 0 else "even" 
    for _ in range(10)
]

double_comp1 = [
    3 * i * j 
    for i in range(10) 
    for j in range(4)
]

double_comp2 = [
    [i for i in range(7) if i < 5] 
    for j in range(10)
]

double_comp3 = {
    i: [i for i in range(7) if i < 5] 
    for j in range(10) 
    if i < 2
}
```

Note that in the last two comprehensions, the nested comprehensions are not exploded even though
having an if conditional. This is a limitation of `globality-black`, but we believe not very frequent
in everyday cases. If you would like to explode those and make `globality-black` respect it, 
please use the feature explained next.

### Partially disable globality-black

If you see some block where you don't want to apply `globality-black`, wrap it
with `# fmt.off` and `# fmt:on` and it will be ignored. Note that this is the same syntax as
for `black`. For example, for readability you might want to do something as:

```
# fmt: off
files_to_read = [
    (f"{key1}_{key2}", key1, key2, key1 + key2)
    for key1 in range(10)
]
# fmt: on
```

Note that by as a default (same as `black`), `globality-black` will write the expression above as a
one-liner.


Pending / Future work
------------

All done! Please give us feedback if you find any issues
