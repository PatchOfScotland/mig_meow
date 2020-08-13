
import copy
import os
import yaml

from .constants import NAME, PERSISTENCE_ID, INPUT_FILE, TRIGGER_PATHS, \
    RECIPES, OUTPUT, VARIABLES, OBJECT_TYPE, VGRID, TASK_FILE, \
    TRIGGER_RECIPES, SWEEP, DEFAULT_MEOW_IMPORT_EXPORT_DIR, PATTERNS, \
    RECIPE_NAME, PATTERN_NAME
from .meow import Pattern, check_patterns_dict, check_recipes_dict, \
    is_valid_pattern_object
from .validation import valid_pattern_name, dir_exists, valid_dir_path, \
    is_valid_recipe_dict, valid_recipe_name


def make_dir(path, can_exist=True):
    if not os.path.exists(path):
        print("Creating dir at: %s" % path)
        os.mkdir(path)
    elif os.path.isfile(path):
        raise ValueError('Cannot make directory in %s as it already '
                         'exists and is a file' % path)
    else:
        if can_exist:
            print("Directory %s already exists" % path)
        else:
            raise ValueError("Directory %s already exists. " % path)


def patten_to_yaml_dict(pattern):
    """
    Creates a dictionary from a Pattern object to be exported using YAML. This
    hides internal variables that should not be user accessible

    :param pattern: (Pattern) The Pattern object to be exported

    :return: (dict) A dict, expressing the given Pattern
    """
    # Don't export the name, as that will be taken from the file name.
    # Don't export the persistence_id as that is an internal system variable
    # and should not be user editable.
    pattern_yaml = {
        INPUT_FILE: pattern.trigger_file,
        TRIGGER_PATHS: pattern.trigger_paths,
        RECIPES: pattern.recipes,
        OUTPUT: pattern.outputs,
        VARIABLES: pattern.variables,
        SWEEP: pattern.sweep
    }
    return pattern_yaml


def pattern_from_yaml_dict(yaml, name):
    """
    Creates a Pattern object from an imported YAML dict.

    :param yaml: (dict) The imported YAML dict.

    :param name: (str) The name of the imported Pattern.

    :return: (dict) A dict, expressing the given Pattern
    """
    yaml[NAME] = name
    if RECIPES in yaml and TRIGGER_RECIPES not in yaml:
        trigger_id = 'placeholder_id'
        recipe_dict = {
            trigger_id: {}
        }
        for recipe in yaml[RECIPES]:
            recipe_dict[trigger_id][recipe] = {}
        yaml[TRIGGER_RECIPES] = recipe_dict
        yaml.pop(RECIPES)
    pattern = Pattern(yaml)
    return pattern


def recipe_to_yaml_dict(recipe):
    """
    Creates a dictionary from a Recipe dict to be exported using YAML. This
    hides internal variables that should not be user accessible

    :param recipe: (dict) The Recipe dict to be exported

    :return: (dict) A dict, expressing the given Recipe
    """
    recipe_yaml = {}
    for k, v in recipe.items():
        # Don't export the name, as that will be taken from the file name.
        # Don't export the persistence_id, object_type, vgrid or task_file
        # as these are internal system variables and should not be user
        # editable.
        if k not in [NAME, PERSISTENCE_ID, OBJECT_TYPE, VGRID, TASK_FILE]:
            recipe_yaml[k] = v
    return recipe_yaml


def recipe_from_yaml_dict(yaml, name):
    """
    Creates a Recipe dict from an imported YAML dict.

    :param yaml: (dict) The imported YAML dict.

    :param name: (str) The name of the imported Recipe.

    :return: (dict) A dict, expressing the given Recipe
    """
    recipe_dict = {}
    recipe_dict.update(yaml)
    recipe_dict[NAME] = name
    return recipe_dict


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

    :param print_errors: (bool) [Optional] Toggle for if encountered errors
    result in a print statement or throwing an exception. Default is to throw
    an exception.

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


