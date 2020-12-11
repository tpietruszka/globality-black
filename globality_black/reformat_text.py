import black
import parso

from globality_black.blank_lines import cover_blank_lines, uncover_blank_lines
from globality_black.common import SyntaxTreeVisitor
from globality_black.comprehensions import reformat_comprehension
from globality_black.constants import BLANK_LINES_TYPES, COMPREHENSIONS_TYPES


class BlackError(Exception):
    pass


def reformat_text(file_contents, black_mode):

    module = parso.parse(file_contents)

    # PRE-PROCESSING

    finder = SyntaxTreeVisitor(module, BLANK_LINES_TYPES)

    for element in finder(module):

        # cover blank lines if needed
        cover_blank_lines(module, element)

    # BLACK

    try:
        code_after_black = black.format_str(module.get_code(), mode=black_mode)
    except Exception as e:
        raise BlackError(e)

    module = parso.parse(code_after_black)

    # POST-PROCESSING

    # comprehensions
    finder = SyntaxTreeVisitor(module, COMPREHENSIONS_TYPES)
    for element in finder(module):
        if element.type == "sync_comp_for":
            reformat_comprehension(element)

    # uncover blank lines protected during pre-processing
    finder = SyntaxTreeVisitor(module, BLANK_LINES_TYPES)
    for element in finder(module):
        if element.type in BLANK_LINES_TYPES:
            uncover_blank_lines(module, element)

    return module.get_code()
