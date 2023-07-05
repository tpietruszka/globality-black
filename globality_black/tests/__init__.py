import difflib
import logging
from typing import Optional, Sequence

import click
from click.testing import CliRunner, Result


def show_diff(text, n_text):
    """
    Show difference between two texts, marking in red the differences
    Based on http://stackoverflow.com/a/788780
    """

    red = "\033[91m --> "
    end = "<-- \033[0m"
    seqm = difflib.SequenceMatcher(None, text, n_text)
    output = []
    for opcode, a0, a1, b0, b1 in seqm.get_opcodes():
        if opcode == "equal":
            output.append(seqm.a[a0:a1])
        elif opcode == "insert":
            output.append(red + seqm.b[b0:b1] + end)
        elif opcode == "delete":
            output.append(red + seqm.a[a0:a1] + end)
        elif opcode == "replace":
            # seqm.a[a0:a1] -> seqm.b[b0:b1]
            output.append(red + seqm.b[b0:b1] + end)
        else:
            raise (RuntimeError, "unexpected opcode")
    return "".join(output)


def run_and_check(
    runner: CliRunner,
    command_name: str,
    command: click.Command,
    args: Sequence[str],
    input: Optional[str],
) -> Result:
    logging.info(f"Running command: {command_name} {' '.join(args)}")
    result = runner.invoke(command, args, input=input)
    return result
