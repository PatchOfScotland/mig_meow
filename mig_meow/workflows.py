import re
import os
from PIL import Image

from .input import _check_input, _valid_path
from .constants import WORKFLOW_NODE, OUTPUT_MAGIC_CHAR, \
    DEFAULT_WORKFLOW_FILENAME, WORKFLOW_IMAGE_EXTENSION, CHAR_UPPERCASE, \
    CHAR_LOWERCASE, CHAR_NUMERIC, CHAR_LINES
from .pattern import is_valid_pattern_object
from .recipe import is_valid_recipe_dict
from graphviz import Digraph


def build_workflow_object(patterns, recipes):
    # TODO update this description
    """
    Builds a workflow dict from a dict of provided patterns and recipes.
    Workflow is a dictionary of different nodes each with a set of descendents.
    Will return exceptions if patterns and recipes are not propperly formatted.

    :param patterns:
    :param recipes
    :return Ddict of nodes connecting patterns together into workflow.
    """

    if not patterns:
        raise Exception('A pattern dict was not provided')
    if not isinstance(patterns, dict):
        raise Exception('The provided patterns were not in a dict')
    for pattern in patterns.values():
        valid, feedback = is_valid_pattern_object(pattern)
        if not valid:
            raise Exception('Pattern %s was not valid. %s'
                            % (pattern, feedback))


    if not isinstance(recipes, dict):
        raise Exception('The provided recipes were not in a dict')
    else:
        for recipe in recipes.values():
            valid, feedback = is_valid_recipe_dict(recipe)
            if not valid:
                raise Exception('Recipe %s was not valid. %s'
                                % (recipe, feedback))

    workflow = {}
    # create all required nodes
    for pattern in patterns.values():
        workflow[pattern.name] = set()
    # populate nodes with ancestors and descendents
    for pattern in patterns.values():
        input_regex_list = pattern.trigger_paths
        for other_pattern in patterns.values():
            other_output_dict = other_pattern.outputs
            for input in input_regex_list:
                for key, value in other_output_dict.items():
                    if re.match(input, value):
                        workflow[other_pattern.name].add(pattern.name)
                    if OUTPUT_MAGIC_CHAR in value:
                        value = value.replace(OUTPUT_MAGIC_CHAR, '.*')
                        if re.match(value, input):
                            workflow[other_pattern.name].add(pattern.name)

    return workflow


def create_workflow_dag(workflow, patterns, recipes, filename=None):
    # TODO update this description

    if not patterns and not recipes:
        extended_filename = filename + WORKFLOW_IMAGE_EXTENSION
        blank_image = Image.new('RGB', (1, 1), (255, 255, 255))
        blank_image.save(extended_filename, 'PNG')

    if filename:
        _check_input(filename, str, 'filename')
        _valid_path(filename, 'filename')
    else:
        filename = DEFAULT_WORKFLOW_FILENAME

    dot = Digraph(comment='Workflow', format='png')
    colours = ['green', 'red']

    for pattern, descendents in workflow.items():
        if pattern_has_recipes(patterns[pattern], recipes):
            dot.node(pattern, patterns[pattern]._image_str(), color=colours[0])
        else:
            dot.node(pattern, patterns[pattern]._image_str(), color=colours[1])
        for descendent in descendents:
            dot.edge(pattern, descendent)

    dot.render(filename)


def pattern_has_recipes(pattern, recipes):
    """Checks that a pattern has all required recipes in the workflow for it
    to be triggerable"""

    valid, feedback = is_valid_pattern_object(pattern)

    if not valid:
        raise Exception("Pattern %s is not valid. %s" % (pattern, feedback))

    if not recipes:
        return False

    if not isinstance(recipes, dict):
        return False

    for recipe in recipes.values():
        if not isinstance(recipe, dict):
            raise Exception('Recipe %s was incorrectly formatted. Expected '
                            '%s but got %s'
                            % (recipe, dict, type(recipe)))
        valid, feedback = is_valid_recipe_dict(recipe)
        if not valid:
            raise Exception("Recipe %s is not valid. %s" % (recipe, feedback))

    for recipe in pattern.recipes:
        if recipe not in recipes:
            return False
    return True


def is_valid_workflow(to_test):
    # TODO update this description

    """Validates that a workflow object is correctly formatted"""

    if not to_test:
        return (False, 'A workflow was not provided')

    if not isinstance(to_test, dict):
        return (False, 'The provided workflow was incorrectly formatted')

    for node in to_test.keys():
        for key, value in WORKFLOW_NODE.items():
            message = 'A workflow node %s was incorrectly formatted' % node
            if key not in node.keys():
                return (False, message)
            if not isinstance(node[key], type(value)):
                return (False, message)
    return (True, '')





