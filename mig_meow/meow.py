import re
import os

from PIL import Image

from .input import check_input, valid_path
from .constants import WORKFLOW_NODE, OUTPUT_MAGIC_CHAR, \
    DEFAULT_WORKFLOW_FILENAME, WORKFLOW_IMAGE_EXTENSION, DESCENDANTS, \
    WORKFLOW_INPUTS, WORKFLOW_OUTPUTS, ANCESTORS
from .pattern import is_valid_pattern_object
from .recipe import is_valid_recipe_dict
from graphviz import Digraph


def build_workflow_object(patterns, recipes):
    # TODO update this description
    """
    Builds a workflow dict from a dict of provided patterns and recipes.
    Workflow is a dictionary of different nodes each with a set of descendants.
    Will return exceptions if patterns and recipes are not properly formatted.

    :param patterns:
    :param recipes
    :return dict of nodes connecting patterns together into workflow.
    """

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
            # TODO remove this placeholder
            recipe['mount_user_dir'] = True

            valid, feedback = is_valid_recipe_dict(recipe)
            if not valid:
                raise Exception('Recipe %s was not valid. %s'
                                % (recipe, feedback))

    workflow = {}
    # create all required nodes
    for pattern in patterns.values():
        input_paths = {}
        output_paths = {}
        input_paths[pattern.trigger_file] = pattern.trigger_paths
        for file, path in pattern.outputs.items():
            output_paths[file] = path
        workflow[pattern.name] = {
            DESCENDANTS: {},
            ANCESTORS: {},
            WORKFLOW_INPUTS: input_paths,
            WORKFLOW_OUTPUTS: output_paths
        }

    # populate nodes with ancestors and descendants
    for pattern in patterns.values():
        input_regex_list = pattern.trigger_paths
        for other in patterns.values():
            other_output_dict = other.outputs
            for input_regex in input_regex_list:
                for key, value in other_output_dict.items():
                    filename = value
                    if os.path.sep in filename:
                        filename = filename[filename.rfind(os.path.sep)+1:]
                    match_dict = {
                        'output_pattern': other.name,
                        'output_file': key,
                        'value': value,
                        'filename': filename
                    }
                    if re.match(input_regex, value):
                        workflow[other.name][DESCENDANTS][pattern.name] = \
                            match_dict
                        workflow[pattern.name][ANCESTORS][other.name] = \
                            match_dict
                        if pattern.trigger_file in \
                                workflow[pattern.name][WORKFLOW_INPUTS]:
                            workflow[pattern.name][WORKFLOW_INPUTS].pop(
                                pattern.trigger_file
                            )
                    if OUTPUT_MAGIC_CHAR in value:
                        magic_value = value.replace(OUTPUT_MAGIC_CHAR, '.*')
                        if re.match(magic_value, input_regex):
                            workflow[other.name][DESCENDANTS][pattern.name] = \
                                match_dict
                            workflow[pattern.name][ANCESTORS][other.name] = \
                                match_dict
                            if pattern.trigger_file in \
                                    workflow[pattern.name][WORKFLOW_INPUTS]:
                                workflow[pattern.name][WORKFLOW_INPUTS].pop(
                                    pattern.trigger_file
                                )
    return workflow


def get_linear_workflow(workflow, patterns, recipes):
    workflow_tops = get_workflow_tops(workflow, patterns)

    linear_workflow = []

    msg = ""
    if not workflow_tops:
        msg = "No linear workflow first steps. "
    if len(workflow_tops) > 1:
        msg = "%d linear workflows first steps identified. "\
              % len(workflow_tops)
    if msg:
        return (False, msg)
    linear_workflow.append(patterns[workflow_tops[0]])

    flag = True
    while flag:
        descendants = workflow[linear_workflow[-1].name][DESCENDANTS]
        if len(descendants) > 1:
            return (False, "Workflow branches. Currently only linear "
                           "workflows are supported. ")
        if not descendants:
            flag = False
        else:
            descendant = min(descendants)
            if descendant in linear_workflow:
                return (False, "Workflow path is cyclical. ")
            linear_workflow.append(patterns[descendant])

    for pattern in linear_workflow:
        if not pattern_has_recipes(pattern, recipes):
            return (False, "Pattern %s lacks one of more of its required "
                           "recipes %s " % (pattern.name, pattern.recipes))
    if not workflow:
        return (False, "No workflow identified. ")
    return (True, linear_workflow)


def get_workflow_tops(workflow, patterns):
    # TODO validation

    workflow_tops = []

    for name, workflow_pattern in workflow.items():
        if len(workflow_pattern[WORKFLOW_INPUTS]) == (
                len(patterns[name].trigger_paths) + len(patterns[name].inputs)
        ):
            workflow_tops.append(name)
    return workflow_tops


def create_workflow_dag(workflow, patterns, recipes, filename=None):
    # TODO update this description

    if not patterns and not recipes:
        extended_filename = filename + WORKFLOW_IMAGE_EXTENSION
        blank_image = Image.new('RGB', (1, 1), (255, 255, 255))
        blank_image.save(extended_filename, 'PNG')

    if filename:
        check_input(filename, str, 'filename')
        valid_path(filename, 'filename')
    else:
        filename = DEFAULT_WORKFLOW_FILENAME

    dot = Digraph(comment='Workflow', format='png')
    colours = ['green', 'red']

    for pattern, descendants in workflow.items():
        if pattern_has_recipes(patterns[pattern], recipes):
            dot.node(
                pattern, patterns[pattern].display_str(), color=colours[0]
            )
        else:
            dot.node(
                pattern, patterns[pattern].display_str(), color=colours[1]
            )
        for descendant in descendants:
            dot.edge(pattern, descendant)

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
        return False, 'A workflow was not provided'

    if not isinstance(to_test, dict):
        return False, 'The provided workflow was incorrectly formatted'

    for node in to_test.keys():
        for key, value in WORKFLOW_NODE.items():
            message = 'A workflow node %s was incorrectly formatted' % node
            if key not in node.keys():
                return False, message
            if not isinstance(node[key], type(value)):
                return False, message
    return True, ''
