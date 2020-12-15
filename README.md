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
* list / set comprehensions where the element has a ternary operator (see examples below)

For everything else, we rely on `black`. Examples:

#### Before globality-black

```
[3 for _ in range(10)]

[3 for i in range(10) if i < 4]

{"a": 3 for _ in range(4)}

{"a": 3 for _ in range(4) if i < 4}

["odd" if i %% 2 == 0 else "even" for _ in range(10)]
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
```


### Partially disable globality-black

If you see some block where you don't want to apply `globality-black`, wrap it
with `# fmt.off` and `# fmt:on` and it will be ignored. Note that this is the same syntax as
for `black`. For example, some complex comprehensions 
are not covered yet, so you might want to do something as:

```
# fmt: off
files_to_read = [
    (f"{key1}_{key2}", key1 + key2)
    for key1 in range(10)
    for key2 in range(10)
]
# fmt: on
```

See `known_failed_comprehensions` for more examples.


Pending / Future work
------------
* Fix known_failures, mainly to cover all comprehensions
