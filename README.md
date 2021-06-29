Globality black
===============


A wrapper for [black](https://github.com/psf/black), adding pre- and post-processing 
to better align with Globality conventions.

`globality-black` performs the following steps:

 - pre-processing: to protect from black actions.
 - black
 - postprocessing: to revert / correct black actions.
 
Note: if you are not familiar with black (or need a refresh), please read our [Black refresh](#black-refresh).


Usage
-----

There are two ways to use `globality-black`, via CLI, or importing the helpers in the library. 
Next, we show some typical use cases:

### CLI

Please see command line arguments running `globality-black --help`. 

### Pycharm

To use `globality-black` in PyCharm, go to PyCharm -> Preferences... -> Tools -> External Tools -> Click + symbol 
to add new external tool.

![img](docs/pycharm-external-tools.png)
Recommended configuration to format the current file:
* Program: path to `globality-black`, e.g. `/Users/marty-mcfly/miniconda3/envs/gb/bin/globality-black`
* Arguments: `$FilePath$`
* Working directory: `$ProjectFileDir$`

Recommended configuration to check the whole repo (but not formatting it it):
* Program: path to `globality-black`, e.g. `/Users/marty-mcfly/miniconda3/envs/gb/bin/globality-black`
* Arguments: `. --check`
* Working directory: `$ProjectFileDir$`

Next, configure a keymap, as in [here](https://www.jetbrains.com/help/pycharm/configuring-keyboard-and-mouse-shortcuts.html).

![img](docs/pycharm-shortcuts.png)

### Jupyterlab

We can leverage [this](https://jupyterlab-code-formatter.readthedocs.io/en/latest/how-to-use.html#custom-formatter) extension,
with a custom formatter. Here we explain how to get the following options:

![img](docs/jupyter-lab-new-buttons.png)


There are two ways to apply `globality-black`, see left-hand-side, or by clicking on the button next to "Code". We will configure
the extension to make it apply the `isort + globality-black` pipeline when clicking such button.

To do so, install the extension, generate the config for jupyter lab and edit it:

```shell script
pip install jupyterlab_code_formatter
jupyter notebook --generate-config
vim ~/.jupyter/jupyter_notebook_config.py
```

with the following code:

```python
from jupyterlab_code_formatter.formatters import SERVER_FORMATTERS
from globality_black.jupyter_formatter import GlobalityBlackFormatter
SERVER_FORMATTERS['globality-black'] = GlobalityBlackFormatter(line_length=100)
```

Then, go to the extension preferences, and add:

```json
{
    "preferences": {
        "default_formatter": {
            "python": [
                "isort",
                "globality-black",
            ],
        }
    },
    "isort": {            
           "combine_as_imports": true,
           "force_grid_wrap": 4,
           "force_to_top": "true",
           "include_trailing_comma": true,
           "known_third_party": ["wandb", "tqdm"],
           "line_length": 100,
           "lines_after_imports": 2,
           "multi_line_output": 3,
    }
}
```

Notes:
 - The extension is applied to all cells in the notebook. It can be configured to be applied just to 
 the current cell, if interested.
 - The extension is applied to each cell in isolation. Hence, if multiple imports appear in different
 cells, they won't be merged together on top of the notebook. 


### VScode

To use `globality-black` in VScode go to Preferences: Keyboard Shortcuts (JSON) from the Palette (command+shift+p)   
It will open a file named `keybindings.json`, then add to this file :
```json
[
    {
        "key": "the shortcut you want (ctrl+b for example)",
        "command": "workbench.action.terminal.sendSequence",
        "args": {
          "text": "globality-black ${file}"
        }
    }
]
```
This will allow you to run `globality-black` per file.
To run `globality-black` to the folder opened in VSCode just replace **file** by **workspaceFolder**.  
You can also add any arguments supported by the CLI (--check or --diff are recommended to avoid formatting the whole repo)


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
* any comprehension with multiple for loops (see examples below)
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
having an if. This is a limitation of `globality-black`, but we believe not very frequent
in everyday cases. If you really want to explode those and make `globality-black` respect it, 
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

- Usage in VScode  

Please give us feedback if you find any issues


Black refresh
--------

`black` is an opinionated Python formatter that tries to save as much vertical space as possible. In
this regard, it compresses lines to the maximum character length that has been configured. `black`'s
default is 88, whereas in `globality-black` we use a default of 100 characters, as agreed for 
Globality repos globally. If you want to have a custom max character length, add a `pyproject.toml`
file to the root of your repo. This works the same way as in `black`, and `globality-black` will 
take your config from there.

See how `black` works in their [README](https://github.com/psf/black). It is especially useful to 
review [this section](https://github.com/psf/black/blob/master/docs/the_black_code_style.md), where 
important recent features are explained.

### Magic comma
 
`black` added a feature at the end of 2020 that we used to call the "magic comma". It's one of the 
first examples where `black` is giving a bit of freedom to the developer on how the final code will 
look like (apart from `fmt:off` and `fmt:on` to ignore `black` entirely). Read more about it 
[here](https://github.com/psf/black/blob/main/docs/the_black_code_style/current_style.md#the-magic-trailing-comma).
