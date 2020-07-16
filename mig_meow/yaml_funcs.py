
import copy

from .constants import NAME, PERSISTENCE_ID, INPUT_FILE, TRIGGER_PATHS, \
    RECIPES, OUTPUT, VARIABLES, OBJECT_TYPE, VGRID, TASK_FILE, \
    TRIGGER_RECIPES, SWEEP
from .meow import Pattern


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
