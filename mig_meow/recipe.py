

import nbformat

from .input import valid_string, valid_path, check_input
from .constants import VALID_RECIPE, NAME, RECIPE, SOURCE, CHAR_UPPERCASE, \
    CHAR_LOWERCASE, CHAR_NUMERIC, CHAR_LINES


def create_recipe_dict(notebook, name, source):
    """
    Creates a recipe dictionary from the given parameters.

    :param notebook: Recipe code. Must be complete notebook.
    :param name: Name of recipe, Must be str
    :param source: Name of source notebook. Must be str
    :return: recipe dict
    """

    valid_string(name,
                 'recipe name',
                 CHAR_UPPERCASE
                 + CHAR_LOWERCASE
                 + CHAR_NUMERIC
                 + CHAR_LINES)
    valid_path(source,
               'recipe source')
    nbformat.validate(notebook)

    recipe = {
        NAME: name,
        SOURCE: source,
        RECIPE: notebook
    }
    return recipe


def is_valid_recipe_dict(to_test):
    """
    Validates that the passed dictionary expresses a recipe.

    :param to_test:
    :return: returns tuple. First value is boolean. True = to_test is recipe,
    False = to_test is not recipe. Second value is feedback string.
    """

    if not to_test:
        return False, 'A workflow recipe was not provided. '

    if not isinstance(to_test, dict):
        return False, 'The workflow recipe was incorrectly formatted. '

    message = 'The workflow recipe %s had an incorrect structure, ' % to_test
    for key, value in VALID_RECIPE.items():
        if key not in to_test:
            message += ' is missing key %s. ' % key
            return False, message
        if not isinstance(to_test[key], value):
            message += ' %s is expected to have type %s but actually has %s. ' \
                       % (to_test[key], value, type(to_test[key]))
            return False, message

    return True, ''
