import requests
import json
import os

from .constants import VGRID_PATTERN_OBJECT_TYPE, VGRID_RECIPE_OBJECT_TYPE, \
    NAME, INPUT_FILE, TRIGGER_PATHS, OUTPUT, RECIPES, VARIABLES, \
    TRIGGER_ACTION, VGRID_CREATE, OBJECT_TYPE, PERSISTENCE_ID, VGRID, \
    MRSL_VGRID
# from .notebook import get_containing_vgrid
from .pattern import Pattern
from .recipe import is_valid_recipe_dict


def trigger(triggerable, print_feedback=True):
    if isinstance(triggerable, Pattern):
        return trigger_pattern(triggerable, print_feedback=print_feedback)
    return trigger_recipe(triggerable, print_feedback=print_feedback)


def trigger_pattern(vgrid, pattern, print_feedback=True):
    if not isinstance(pattern, Pattern):
        raise TypeError("The provided object '%s' is a %s, not a Pattern "
                        "as expected" % (pattern, type(pattern)))
    # TODO include some check on if this has been modified at all since last
    #  import

    try:
        persistence_id = pattern.persistence_id
    except AttributeError:
        raise Exception("The provided pattern has not been registered with "
                        "the VGrid already, so cannot be manually triggered. ")

    attributes = {
        OBJECT_TYPE: VGRID_PATTERN_OBJECT_TYPE,
        PERSISTENCE_ID: persistence_id
    }
    return vgrid_workflow_json_call(vgrid,
                                    VGRID_CREATE,
                                    TRIGGER_ACTION,
                                    attributes,
                                    print_feedback=print_feedback)


def trigger_recipe(vgrid, recipe, print_feedback=True):
    if not isinstance(recipe, dict):
        raise TypeError("The provided object '%s' is a %s, not a dict "
                        "as expected" % (recipe, type(recipe)))

    # TODO include some check on if this has been modified at all since last
    #  import

    try:
        persistence_id = recipe[PERSISTENCE_ID]
    except KeyError:
        raise Exception("The provided recipe has not been registered with "
                        "the VGrid already, so cannot be manually triggered. ")

    attributes = {
        OBJECT_TYPE: VGRID_RECIPE_OBJECT_TYPE,
        PERSISTENCE_ID: persistence_id
    }
    return vgrid_workflow_json_call(vgrid,
                                    VGRID_CREATE,
                                    TRIGGER_ACTION,
                                    attributes,
                                    print_feedback=print_feedback)


def export_pattern_to_vgrid(vgrid, pattern, print_feedback=True):
    """
    Exports a given pattern to a MiG based Vgrid. Raises an exception if
    the pattern object does not pass an integrity check before export.

    :param pattern: Pattern object to export. Must a Pattern
    :param print_feedback: (optional) In the event of feedback sets if it is
    printed
    to console or not. Default value is True.
    :return: returns output from _vgrid_json_call function
    """
    if not isinstance(pattern, Pattern):
        raise TypeError("The provided object '%s' is a %s, not a Pattern "
                        "as expected" % (pattern, type(pattern)))
    status, msg = pattern.integrity_check()
    if not status:
        raise Exception('The provided pattern is not a valid Pattern. '
                        '%s' % msg)

    attributes = {
        NAME: pattern.name,
        INPUT_FILE: pattern.trigger_file,
        TRIGGER_PATHS: pattern.trigger_paths,
        OUTPUT: pattern.outputs,
        RECIPES: pattern.recipes,
        VARIABLES: pattern.variables
    }
    return vgrid_workflow_json_call(vgrid,
                                    VGRID_CREATE,
                                    VGRID_PATTERN_OBJECT_TYPE,
                                    attributes,
                                    print_feedback=print_feedback)


def export_recipe_to_vgrid(vgrid, recipe, print_feedback=True):
    """
    Exports a given recipe to a MiG based Vgrid. Raises an exception if
    the recipe object does not a valid recipe.

    :param recipe: Recipe object to export. Must a dict
    :param print_feedback: (optional) In the event of feedback sets if it is
    printed
    to console or not. Default value is True.
    :return: returns output from _vgrid_json_call function
    """
    if not isinstance(recipe, dict):
        raise TypeError("The provided object '%s' is a %s, not a dict "
                        "as expected" % (recipe, type(recipe)))
    status, msg = is_valid_recipe_dict(recipe)
    if not status:
        raise Exception('The provided recipe is not valid. '
                        '%s' % msg)

    return vgrid_workflow_json_call(vgrid,
                                    VGRID_CREATE,
                                    VGRID_RECIPE_OBJECT_TYPE,
                                    recipe,
                                    print_feedback=print_feedback)


def vgrid_workflow_json_call(
        vgrid, operation, workflow_type, attributes, print_feedback=True):
    """
    """

    attributes[VGRID] = vgrid

    return vgrid_json_call(
        operation, workflow_type, attributes, print_feedback=print_feedback
    )


def vgrid_job_json_call(vgrid, operation, workflow_type, attributes,
                        print_feedback=True):
    """
    """

    attributes[MRSL_VGRID] = [vgrid]

    return vgrid_json_call(
        operation, workflow_type, attributes, print_feedback=print_feedback
    )


def vgrid_json_call(operation, workflow_type, attributes, print_feedback=True):

    url = \
        'https://sid.migrid.test/cgi-sid/workflowjsoninterface.py?output_for' \
        'mat=json'
    session_id = \
        "20fa14e5b13486b81592d1ed950dfcf4e8a581f3d8d0db25b60e850cfd9a1371"
    # TODO use this during deployment
    # try:
    #     url = os.environ['URL']
    # except KeyError:
    #     raise EnvironmentError('Migrid URL was not specified in the local '
    #                            'environment. This should be created '
    #                            'automatically as part of the Notebook '
    #                            'creation if the Notebook was created on '
    #                            'IDMC. ')
    # try:
    #     session_id = os.environ['SESSION_ID']
    # except KeyError:
    #     raise EnvironmentError('Migrid SESSION_ID was not specified in '
    #                            'the local environment. This should be '
    #                            'created automatically as part of the '
    #                            'Notebook creation if the Notebook was '
    #                            'created on IDMC. ')

    data = {
        'workflowsessionid': session_id,
        'operation': operation,
        'type': workflow_type,
        'attributes': attributes
    }

    response = requests.post(url, json=data, verify=False)
    try:
        json_response = response.json()
    except json.JSONDecodeError as err:
        raise Exception('No feedback from MiG. %s' % err)
    header = json_response[0]
    body = json_response[1]
    footer = json_response[2]

    if print_feedback:
        if "text" in body:
            print(body['text'])
        if "error_text" in body:
            print("Something went wrong, function cold not be completed. "
                  "%s" % body['text'])
        else:
            print('Unexpected response')
            print('header: %s' % header)
            print('body: %s' % body)
            print('footer: %s' % footer)

    return header, body, footer

