
from .constants import VALID_RECIPE, OBJECT_TYPE, PERSISTENCE_ID, TRIGGERS, \
    OWNER, NAME, RECIPE, VGRIDS, SOURCE


def create_recipe_from_notebook(notebook, name, source):
    recipe = {
        NAME: name,
        SOURCE: source,
        # OBJECT_TYPE: "",
        # PERSISTENCE_ID: "",
        # OWNER: "",
        # VGRIDS: "",
        # TRIGGERS: {},
        RECIPE: notebook
    }
    return recipe


def is_valid_recipe_dict(to_test):
    """Validates that the passed dictionary expresses a recipe"""

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
