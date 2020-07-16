
import os
import threading
import yaml

from .constants import VGRID_READ, VGRID_ANY_OBJECT_TYPE, \
    VGRID_WORKFLOWS_OBJECT, OBJECT_TYPE, VGRID_PATTERN_OBJECT_TYPE, \
    VGRID_RECIPE_OBJECT_TYPE, NAME, VGRID_ERROR_TYPE, VGRID_TEXT_TYPE, VGRID, \
    VGRID_DELETE, PERSISTENCE_ID, RECIPE_NAME, PATTERN_NAME, INPUT_FILE, \
    SWEEP, TRIGGER_PATHS, OUTPUT, RECIPES, VARIABLES, VGRID_CREATE, \
    VGRID_UPDATE, PATTERNS, RECIPE, SOURCE, DEFAULT_MEOW_IMPORT_EXPORT_DIR
from .inputs import check_input, is_valid_recipe_dict, valid_pattern_name, \
    valid_recipe_name, valid_dir_path, dir_exists
from .mig import vgrid_workflow_json_call
from .meow import is_valid_pattern_object, Pattern, check_patterns_dict, \
    check_recipes_dict
from .workflow_widget import WorkflowWidget
from .monitor_widget import MonitorWidget, update_monitor
from .yaml_funcs import pattern_from_yaml_dict, patten_to_yaml_dict, \
    recipe_from_yaml_dict, recipe_to_yaml_dict


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


def read_dir(directory=DEFAULT_MEOW_IMPORT_EXPORT_DIR):
    '''
    Reads in MEOW Patterns and Recipes from yaml files, contained in a local
    directory. This expects there to be two directories within the given
    directory, one containing the Patterns and another containing the Recipes.

    :param directory: (str) The directory to read from. Default is
    'meow_directory'.

    :return: (dict) A dict of Patterns and Recipe pbjects.
    '''
    valid_dir_path(directory, 'directory')
    dir_exists(directory)

    pattern_dir = os.path.join(directory, PATTERNS)
    recipe_dir = os.path.join(directory, RECIPES)

    result = {
        PATTERNS: {},
        RECIPES: {}
    }

    if os.path.exists(pattern_dir):
        pattern_files = [
            f for f in os.listdir(pattern_dir)
            if os.path.isfile(os.path.join(pattern_dir, f))
        ]
        for file_name in pattern_files:
            pattern = read_dir_pattern(
                file_name,
                directory=directory,
                print_errors=True
            )
            result[PATTERNS][file_name] = pattern

    if os.path.exists(recipe_dir):
        recipe_files = [
            f for f in os.listdir(recipe_dir)
            if os.path.isfile(os.path.join(recipe_dir, f))
        ]
        for file_name in recipe_files:
            recipe = read_dir_recipe(
                file_name,
                directory=directory,
                print_errors=True
            )
            result[RECIPES][file_name] = recipe

    return result


def write_dir(patterns, recipes, directory=DEFAULT_MEOW_IMPORT_EXPORT_DIR):
    '''
    Saves the given patterns and recipes in the given directory.

    :param patterns: (dict) A dict of Pattern objects

    :param recipes: (dict) A dict of Recipe dictionaries

    :param directory: (str) The directory to save the object in. Default is
    'meow_directory'

    :return: (No return)
    '''
    valid, feedback = check_patterns_dict(patterns, integrity=True)
    if not valid:
        raise ValueError(feedback)

    valid, feedback = check_recipes_dict(recipes)
    if not valid:
        raise ValueError(feedback)

    dir_exists(directory, create=True)

    for pattern in patterns.values():
        write_dir_pattern(pattern, directory=directory)

    for recipe in recipes.values():
        write_dir_recipe(recipe, directory=directory)


def read_dir_pattern(pattern_name, directory=DEFAULT_MEOW_IMPORT_EXPORT_DIR,
                     print_errors=False):
    '''
    Read a specific Pattern within the given local directory. There should be
    an intermediate directory, 'Patterns' between the two.

    :param pattern_name: (str) the pattern file to read.

    :param directory: (str) a local directory to read from. Default is
    'meow_directory'.

    :param print_errors: (bool) Toggle for if encountered errors result in a
    print statement or throwing an exception. Default is to throw an exception.

    :return: (Pattern) The read in pattern object.
    '''
    valid_pattern_name(pattern_name)
    valid_dir_path(directory, 'directory')
    dir_exists(directory)

    pattern_dir = os.path.join(directory, PATTERNS)
    dir_exists(pattern_dir)

    try:
        with open(os.path.join(pattern_dir, pattern_name), 'r') \
                as yaml_file:
            pattern_yaml_dict = yaml.full_load(yaml_file)
            if '.' in pattern_name:
                pattern_name = pattern_name[:pattern_name.index('.')]

            pattern = \
                pattern_from_yaml_dict(pattern_yaml_dict, pattern_name)

            return pattern
    except Exception as ex:
        msg = "Tried to import %s '%s', but could not. %s" \
              % (PATTERN_NAME, pattern_name, ex)
        if print_errors:
            print(msg)
        else:
            raise Exception(msg)


def read_dir_recipe(recipe_name, directory=DEFAULT_MEOW_IMPORT_EXPORT_DIR,
                    print_errors=False):
    '''
    Read a specific recipe within the given local directory. There should be
    an intermediate directory, 'Recipes' between the two.

    :param recipe_name: (str) the recipe file to read.

    :param directory: (str) a local directory to read from. Default is
    'meow_directory'.

    :param print_errors: (bool) Toggle for if encountered errors result in a
    print statement or throwing an exception. Default is to throw an exception.

    :return: (dict) The read in recipe dict.
    '''
    valid_recipe_name(recipe_name)
    valid_dir_path(directory, 'directory')
    dir_exists(directory)

    recipe_dir = os.path.join(directory, RECIPES)
    dir_exists(recipe_dir)

    try:
        with open(os.path.join(recipe_dir, recipe_name), 'r') \
                as yaml_file:
            recipe_yaml_dict = yaml.full_load(yaml_file)
            if '.' in recipe_name:
                recipe_name = recipe_name[:recipe_name.index('.')]

            recipe = recipe_from_yaml_dict(recipe_yaml_dict, recipe_name)

            return recipe
    except Exception as ex:
        msg = "Tried to import %s '%s', but could not. %s" \
              % (RECIPE_NAME, recipe_name, ex)
        if print_errors:
            print(msg)
        else:
            raise Exception(msg)


def write_dir_pattern(pattern, directory=DEFAULT_MEOW_IMPORT_EXPORT_DIR):
    '''
    Saves a given pattern locally.

    :param pattern: (Pattern) the pattern to save.

    :param directory: (str) The directory to write the Pattern to.

    :return: (No return)
    '''
    valid, feedback = is_valid_pattern_object(pattern, integrity=True)

    if not valid:
        msg = "Could not export %s %s. %s" \
              % (PATTERN_NAME, pattern.name, feedback)
        raise ValueError(msg)

    dir_exists(directory, create=True)
    pattern_dir = os.path.join(directory, PATTERNS)
    dir_exists(pattern_dir, create=True)

    pattern_file_path = os.path.join(pattern_dir, pattern.name)
    pattern_yaml = patten_to_yaml_dict(pattern)

    with open(pattern_file_path, 'w') as pattern_file:
        yaml.dump(
            pattern_yaml,
            pattern_file,
            default_flow_style=False
        )


def write_dir_recipe(recipe, directory=DEFAULT_MEOW_IMPORT_EXPORT_DIR):
    '''
    Saves a given recipe locally.

    :param recipe: (dict) the recipe dict to save.

    :param directory: (str) The directory to write the Recipe to.

    :return: (No return)
    '''
    valid, feedback = is_valid_recipe_dict(recipe)
    dir_exists(directory, create=True)

    if not valid:
        msg = "Could not export %s %s. %s" \
              % (RECIPE_NAME, recipe['NAME'], feedback)
        raise ValueError(msg)

    recipe_dir = os.path.join(directory, RECIPES)
    dir_exists(recipe_dir, create=True)

    recipe_file_path = os.path.join(recipe_dir, recipe[NAME])
    recipe_yaml = recipe_to_yaml_dict(recipe)

    with open(recipe_file_path, 'w') as recipe_file:
        yaml.dump(
            recipe_yaml,
            recipe_file,
            default_flow_style=False
        )


def delete_dir_pattern(pattern_name, directory=DEFAULT_MEOW_IMPORT_EXPORT_DIR):
    '''
    Removes a a saved pattern by the given name.

    :param pattern_name: (str or Pattern) Name of pattern to delete, or
    complete Pattern object to delete.

    :param directory: (str) Directory containing pattern saves. Default is
    'meow_directory'

    :return: (No return)
    '''
    if isinstance(pattern_name, Pattern):
        pattern_name = Pattern.name
    if not isinstance(pattern_name, str):
        raise ValueError("'pattern_name' must be either a string or a Pattern")
    valid_pattern_name(pattern_name)
    dir_exists(directory)

    pattern_dir = os.path.join(directory, PATTERNS)
    dir_exists(pattern_dir)

    file_path = os.path.join(pattern_dir, pattern_name)
    if os.path.exists(file_path):
        os.remove(file_path)


def delete_dir_recipe(recipe_name, directory=DEFAULT_MEOW_IMPORT_EXPORT_DIR):
    '''
    Removes a a saved recipe by the given name.

    :param recipe_name: (str or dict) Name of recipe to delete, or a recipe
    dict to delete.

    :param directory: (str) Directory containing recipe saves. Default is
    'meow_directory'

    :return: (No return)
    '''
    if isinstance(recipe_name, dict):
        recipe_name = recipe_name[NAME]
    if not isinstance(recipe_name, str):
        raise ValueError("'recipe_name' must be either a string or a dict")
    valid_recipe_name(recipe_name)
    dir_exists(directory)

    recipe_dir = os.path.join(directory, RECIPES)
    dir_exists(recipe_dir)

    file_path = os.path.join(recipe_dir, recipe_name)
    if os.path.exists(file_path):
        os.remove(file_path)



