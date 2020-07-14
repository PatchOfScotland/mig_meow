
import threading

from .constants import VGRID_READ, VGRID_ANY_OBJECT_TYPE, \
    VGRID_WORKFLOWS_OBJECT, OBJECT_TYPE, VGRID_PATTERN_OBJECT_TYPE, \
    VGRID_RECIPE_OBJECT_TYPE, NAME, VGRID_ERROR_TYPE, VGRID_TEXT_TYPE, VGRID, \
    VGRID_DELETE, PERSISTENCE_ID, RECIPE_NAME, PATTERN_NAME, INPUT_FILE, \
    SWEEP, TRIGGER_PATHS, OUTPUT, RECIPES, VARIABLES, VGRID_CREATE, \
    VGRID_UPDATE, PATTERNS, RECIPE, SOURCE
from .inputs import check_input, is_valid_recipe_dict, valid_pattern_name, \
    valid_recipe_name
from .mig import vgrid_workflow_json_call
from .meow import is_valid_pattern_object, Pattern
from .workflow_widget import WorkflowWidget
from .monitor_widget import MonitorWidget, update_monitor


def workflow_widget(**kwargs):
    """
    Creates and displays a widget for workflow definitions. Passes any given
    keyword arguments to the WorkflowWidget constructor.

    :return: (function call to 'WorkflowWidget.display_widget)
    """

    widget = WorkflowWidget(**kwargs)

    return widget.display_widget()


def monitor_widget(**kwargs):
    """
    Creates and displays a widget for monitoring Vgrid job queues. Passes
    any given keyword arguments to the MonitorWidget constructor.

    :return: (function call to 'MonitorWidget.display_widget)
    """

    widget = MonitorWidget(**kwargs)

    monitor_thread = threading.Thread(
        target=update_monitor,
        args=(widget,),
        daemon=True
    )

    monitor_thread.start()

    return widget.display_widget()


def read_vgrid(vgrid):
    '''
    Reads a given vgrid. Returns a dict of Patterns and a dict of Recipes .

    :param vgrid: (str) A vgrid to read

    :return: (dict) A dictionary of responses. Contains separate keys for the
    patterns and the recipes.
    '''

    check_input(vgrid, str, VGRID)

    _, response, _ = vgrid_workflow_json_call(
        vgrid,
        VGRID_READ,
        VGRID_ANY_OBJECT_TYPE,
        {}
    )

    output = {
        PATTERNS: {},
        RECIPES: {}
    }
    response_patterns = {}
    response_recipes = {}
    if VGRID_WORKFLOWS_OBJECT in response:
        for response_object in response[VGRID_WORKFLOWS_OBJECT]:
            if response_object[OBJECT_TYPE] == VGRID_PATTERN_OBJECT_TYPE:
                response_patterns[response_object[NAME]] = \
                    Pattern(response_object)
            elif response_object[OBJECT_TYPE] == VGRID_RECIPE_OBJECT_TYPE:
                response_recipes[response_object[NAME]] = response_object

        output[PATTERNS] = response_patterns
        output[RECIPES] = response_recipes
        return output

    elif OBJECT_TYPE in response and response[OBJECT_TYPE] == VGRID_ERROR_TYPE:
        print("Could not retrieve workflow objects. %s"
              % response[VGRID_TEXT_TYPE])
        return output
    else:
        print("Unexpected response: {}".format(response))
        return output


def write_vgrid(patterns, recipes, vgrid):
    '''
    Writes a collection of patterns and recipes to a given vgrid.

    :param patterns: (dict) A dictionary of pattern objects.

    :param recipes: (recipes) A dictionary of recipes.

    :param vgrid: (str) The vgrid to write to.

    :return: (dict) Dicts of updated patterns and recipes.
    '''
    check_input(vgrid, str, VGRID)
    check_input(patterns, dict, 'patterns', or_none=True)
    check_input(recipes, dict, 'recipes', or_none=True)

    updated_patterns = {}
    for pattern in patterns.values():
        new_pattern = write_vgrid_pattern(pattern, vgrid)
        updated_patterns[pattern.name] = new_pattern

    updated_recipes = {}
    for recipe in recipes.values():
        new_recipe = write_vgrid_recipe(recipe, vgrid)
        updated_recipes[recipe[NAME]] = new_recipe

    return {
        PATTERNS: updated_patterns,
        RECIPES: updated_recipes
    }


def read_vgrid_pattern(pattern, vgrid):
    '''
    Reads a given pattern from a given vgrid.

    :param pattern: (str) The pattern name to read.

    :param vgrid: (str) The Vgrid to read from

    :return: (Pattern) A pattern object, or None if a Pattern could not be found
    '''
    check_input(vgrid, str, VGRID)
    valid_pattern_name(pattern)

    attributes = {
        NAME: pattern
    }

    _, response, _ = vgrid_workflow_json_call(
        vgrid,
        VGRID_READ,
        VGRID_PATTERN_OBJECT_TYPE,
        attributes
    )

    if OBJECT_TYPE in response \
            and response[OBJECT_TYPE] == VGRID_WORKFLOWS_OBJECT \
            and VGRID_WORKFLOWS_OBJECT in response:
        pattern_list = response[VGRID_WORKFLOWS_OBJECT]
        if len(pattern_list) > 1:
            print("Got several matching %ss: %s"
                  % (PATTERN_NAME, [entry[NAME] for entry in pattern_list]))
        return Pattern(pattern_list[0])
    elif OBJECT_TYPE in response and response[OBJECT_TYPE] == VGRID_ERROR_TYPE:
        print("Could not retrieve workflow %s. %s"
              % (PATTERN_NAME, response[VGRID_TEXT_TYPE]))
        return None
    else:
        print("Got unexpected response. %s" % response)
        return None


def read_vgrid_recipe(recipe, vgrid):
    '''
    Reads a given recipe from a given vgrid.

    :param recipe: (str) The recipe name to read.

    :param vgrid: (str) The Vgrid to read from

    :return: (dict) A recipe dict, or None if a recipe could not be found
    '''
    check_input(vgrid, str, VGRID)
    valid_recipe_name(recipe)

    attributes = {
        NAME: recipe
    }

    _, response, _ = vgrid_workflow_json_call(
        vgrid,
        VGRID_READ,
        VGRID_RECIPE_OBJECT_TYPE,
        attributes
    )

    if OBJECT_TYPE in response \
            and response[OBJECT_TYPE] == VGRID_WORKFLOWS_OBJECT \
            and VGRID_WORKFLOWS_OBJECT in response:
        recipe_list = response[VGRID_WORKFLOWS_OBJECT]
        if len(recipe_list) > 1:
            print("Got several matching %ss: %s"
                  % (RECIPE_NAME, [entry[NAME] for entry in recipe_list]))
        return recipe_list[0]
    elif OBJECT_TYPE in response and response[OBJECT_TYPE] == VGRID_ERROR_TYPE:
        print("Could not retrieve workflow %s. %s"
              % (RECIPE_NAME, response[VGRID_TEXT_TYPE]))
        return None
    else:
        print("Got unexpected response. %s" % response)
        return None


def write_vgrid_pattern(pattern, vgrid):
    '''
    Creates a new Pattern on a given VGrid, or updates an existing Pattern.

    :param pattern: (Pattern) The pattern object to write to the VGrid.

    :param vgrid: (str) The vgrid to write the pattern to.

    :return: (Pattern) The registered Pattern object.
    '''

    check_input(vgrid, str, VGRID)
    is_valid_pattern_object(pattern)

    attributes = {
        NAME: pattern.name,
        INPUT_FILE: pattern.trigger_file,
        TRIGGER_PATHS: pattern.trigger_paths,
        OUTPUT: pattern.outputs,
        RECIPES: pattern.recipes,
        VARIABLES: pattern.variables,
        SWEEP: pattern.sweep
    }

    if hasattr(pattern, 'persistence_id'):
        attributes[PERSISTENCE_ID] = pattern.persistence_id,
        operation = VGRID_UPDATE
    else:
        operation = VGRID_CREATE

    _, response, _ = vgrid_workflow_json_call(
        vgrid,
        operation,
        VGRID_PATTERN_OBJECT_TYPE,
        attributes
    )

    if response['object_type'] != 'error_text':
        if operation == VGRID_UPDATE:
            print("%s '%s' updated on VGrid '%s'"
                  % (PATTERN_NAME, pattern.name, vgrid))
        else:
            pattern.persistence_id = response['text']
            print("%s '%s' created on VGrid '%s'"
                  % (PATTERN_NAME, pattern.name, vgrid))
    else:
        if hasattr(pattern, 'persistence_id'):
            delattr(pattern, 'persistence_id')
        print(response['text'])
    return pattern


def write_vgrid_recipe(recipe, vgrid):
    '''
    Creates a new recipe on a given VGrid, or updates an existing recipe.

    :param recipe: (dict) The recipe to write to the VGrid.

    :param vgrid: (str) The vgrid to write the recipe to.

    :return: (dict) The registered Recipe dict.
    '''

    check_input(vgrid, str, VGRID)
    is_valid_recipe_dict(recipe)

    attributes = {
        NAME: recipe[NAME],
        RECIPE: recipe[RECIPE],
        SOURCE: recipe[SOURCE]
    }

    if PERSISTENCE_ID in recipe:
        attributes[PERSISTENCE_ID] = recipe[PERSISTENCE_ID],
        operation = VGRID_UPDATE
    else:
        operation = VGRID_CREATE

    _, response, _ = vgrid_workflow_json_call(
        vgrid,
        operation,
        VGRID_RECIPE_OBJECT_TYPE,
        attributes
    )

    if response['object_type'] != 'error_text':
        if operation == VGRID_UPDATE:
            print("%s '%s' updated on VGrid '%s'"
                  % (RECIPE_NAME, recipe[NAME], vgrid))
        else:
            recipe[PERSISTENCE_ID] = response['text']
            print("%s '%s' created on VGrid '%s'"
                  % (RECIPE_NAME, recipe[NAME], vgrid))
    else:
        if PERSISTENCE_ID in recipe:
            recipe.pop(PERSISTENCE_ID)
        print(response['text'])
    return recipe


def delete_vgrid_pattern(pattern, vgrid):
    '''
    Attempts to delete a given pattern from a given VGrid.

    :param pattern: (Pattern) A valid workflow Pattern object

    :param vgrid: (str) A MiG Vgrid to connect to

    :return: (dict) Returns a Pattern object. If the deletion is successful
    the persistence_id attribute is removed
    '''

    check_input(vgrid, str, VGRID)
    is_valid_pattern_object(pattern)

    try:
        attributes = {
            PERSISTENCE_ID: pattern.persistence_id,
            NAME: pattern.name
        }
    except AttributeError:
        msg = "Cannot delete a %s that has not been previously registered " \
              "with the VGrid. If you have registered this %s with a Vgrid " \
              "before, then please re-read it again, as necessary data has " \
              "been lost. " % (PATTERN_NAME, PATTERN_NAME)
        print(msg)
        return pattern

    _, response, _ = vgrid_workflow_json_call(
        vgrid,
        VGRID_DELETE,
        VGRID_PATTERN_OBJECT_TYPE,
        attributes
    )

    if response['object_type'] != 'error_text':
        delattr(pattern, 'persistence_id')
        print("%s '%s' deleted from VGrid '%s'"
              % (PATTERN_NAME, pattern.name, vgrid))
    else:
        print(response['text'])
    return pattern


def delete_vgrid_recipe(recipe, vgrid):
    '''
    Attempts to delete a given recipe from a given VGrid.

    :param recipe: (dict) A valid workflow recipe

    :param vgrid: (str) A MiG Vgrid to connect to

    :return: (dict) Returns a recipe dictionary. If the deletion is successful
    the persistence_id attribute is removed
    '''

    check_input(vgrid, str, VGRID)
    is_valid_recipe_dict(recipe)

    if PERSISTENCE_ID not in recipe:
        msg = "Cannot delete a %s that has not been previously registered " \
              "with the VGrid. If you have registered this %s with a Vgrid " \
              "before, then please re-read it again, as necessary data has " \
              "been lost. " % (RECIPE_NAME, RECIPE_NAME)
        print(msg)
        return recipe
    attributes = {
        PERSISTENCE_ID: recipe[PERSISTENCE_ID],
        NAME: recipe[NAME]
    }

    _, response, _ = vgrid_workflow_json_call(
        vgrid,
        VGRID_DELETE,
        VGRID_RECIPE_OBJECT_TYPE,
        attributes
    )

    if response['object_type'] != 'error_text':
        recipe.pop(PERSISTENCE_ID)
        print("%s '%s' deleted from VGrid '%s'"
              % (RECIPE_NAME, recipe[NAME], vgrid))
    else:
        print(response['text'])
    return recipe
