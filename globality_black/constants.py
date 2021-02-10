from enum import Enum, unique


BLANK_LINE_TOKEN = "TOKEN"
BLANK_LINES_TYPES = ["arglist", "expr_stmt", "atom_expr", "atom"]
COMPREHENSIONS_TYPES = ["comp_if", "sync_comp_for"]
TYPES_TO_CHECK_FMT_ON_OFF = ("stmt", "funcdef", "classdef")
MAX_CHARACTERS_TO_FIND_INDENTATION_PARENT = 200
DEFAULT_BLACK_LINE_LENGTH = 100
NUM_FILES_TO_ENABLE_PARALLELIZATION = 5
ALL_DONE_STRING = "All done! ✨ 🍰 ✨"
OH_NO_STRING = "Oh no! 💥 💔 💥"


@unique
class ParsoTypes(Enum):
    DICTORSETMAKER = "dictorsetmaker"
    COMP_IF = "comp_if"
    SYNC_COMP_FOR = "sync_comp_for"
    TERNARY_EXPRESSION = "test"
    LISTCOMP = "testlist_comp"
