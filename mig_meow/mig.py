import requests
import json
import traceback
import os

from .constants import VGRID_PATTERN_OBJECT_TYPE, VGRID_RECIPE_OBJECT_TYPE, \
    NAME, INPUT_FILE, TRIGGER_PATHS, OUTPUT, RECIPES, VARIABLES, \
    VGRID_CREATE, VGRID, VGRID_READ, VGRID_DELETE, VGRID_ANY_OBJECT_TYPE, \
    VALID_OPERATIONS, VALID_WORKFLOW_TYPES, VALID_JOB_TYPES, \
    DEFAULT_JSON_TIMEOUT, PATTERNS, VGRID_WORKFLOWS_OBJECT, VGRID_TEXT_TYPE, \
    OBJECT_TYPE, VGRID_ERROR_TYPE, RECIPE_NAME, RECIPE, SOURCE, VGRID_UPDATE, \
    PERSISTENCE_ID, PATTERN_NAME, SWEEP
from .validation import check_input, valid_recipe_name, is_valid_recipe_dict, \
    valid_pattern_name
from .logging import write_to_log
from .meow import Pattern, is_valid_pattern_object


MRSL_VGRID = 'VGRID'


def export_pattern_to_vgrid(vgrid, pattern, timeout=DEFAULT_JSON_TIMEOUT):
    """
    Exports a given pattern to a MiG based Vgrid. Raises a TypeError or
    ValueError if the pattern is not valid. Note this function is not used
    within mig_meow and is intended for users who want to programmatically
    alter vgrid workflows.

    :param vgrid: (str) Vgrid to which pattern will be exported.

    :param pattern: (Pattern) Pattern object to export.

    :param timeout: (int) [optional] Timeout duration in seconds for Vgrid
    call. Default is 60

    :return: (function call to vgrid_workflow_json_call) if pattern is valid,
    will call function 'vgrid_workflow_json_call'.
    """
    check_input(vgrid, str, 'vgrid')

    if not isinstance(pattern, Pattern):
        raise TypeError(
            "The provided object '%s' is a %s, not a Pattern as expected"
            % (pattern, type(pattern))
        )
    status, msg = pattern.integrity_check()
    if not status:
        raise ValueError(
            'The provided pattern is not a valid Pattern. %s' % msg
        )

    attributes = {
        NAME: pattern.name,
        INPUT_FILE: pattern.trigger_file,
        TRIGGER_PATHS: pattern.trigger_paths,
        OUTPUT: pattern.outputs,
        RECIPES: pattern.recipes,
        VARIABLES: pattern.variables
    }
    return vgrid_workflow_json_call(
        vgrid,
        VGRID_CREATE,
        VGRID_PATTERN_OBJECT_TYPE,
        attributes,
        timeout=timeout
    )


def export_recipe_to_vgrid(vgrid, recipe, timeout=DEFAULT_JSON_TIMEOUT):
    """
    Exports a given recipe to a MiG based Vgrid. Raises a TypeError or
    ValueError if the recipe is not valid. Note this function is not used
    within mig_meow and is intended for users who want to programmatically
    alter vgrid workflows.

    :param vgrid: (str) Vgrid to which recipe will be exported.

    :param recipe: (dict) Recipe object to export.

    :param timeout: (int) [optional] Timeout duration in seconds for Vgrid
    call. Default is 60

    :return: (function call to vgrid_workflow_json_call) if recipe is valid,
    will call function 'vgrid_workflow_json_call'.
    """
    check_input(vgrid, str, 'vgrid')

    if not isinstance(recipe, dict):
        raise TypeError("The provided object '%s' is a %s, not a dict "
                        "as expected" % (recipe, type(recipe)))
    status, msg = is_valid_recipe_dict(recipe)
    if not status:
        raise ValueError('The provided recipe is not valid. %s' % msg)

    return vgrid_workflow_json_call(
        vgrid,
        VGRID_CREATE,
        VGRID_RECIPE_OBJECT_TYPE,
        recipe,
        timeout=timeout
    )


def vgrid_workflow_json_call(
        vgrid, operation, workflow_type, attributes, logfile=None,
        ssl=True, timeout=DEFAULT_JSON_TIMEOUT):
    """
    Validates input for a JSON workflow call to VGRID. Raises a TypeError or
    ValueError if an invalid value is found. If no problems are found then a
    JSON message is setup.

    :param vgrid: (str) Vgrid to which workflow will be exported.

    :param operation: (str) The operation type to be performed by the MiG based
    JSON API. Valid operations are 'create', 'read', 'update' and 'delete'.

    :param workflow_type: (str) MiG workflow object type. Valid are
    'workflows', 'workflowpattern', 'workflowrecipe', and 'any',

    :param attributes: (dict) A dictionary of arguments defining the specifics
    of the requested operation.

    :param timeout: (int) [optional] Timeout duration in seconds for Vgrid
    call. Default is 60

    :param logfile: (str)[optional] Path to a logfile. If provided logs are
    recorded in this file. Default is None.

    :param ssl: (boolean)[optional] Toggle to use ssl checks. Default True

    :return: (function call to __vgrid_json_call) If all inputs are valid,
    will call function '__vgrid_json_call'.
    """
    check_input(vgrid, str, 'vgrid')
    check_input(operation, str, 'operation')
    check_input(workflow_type, str, 'workflow_type')
    check_input(attributes, dict, 'attributes', or_none=True)
    check_input(ssl, bool, 'ssl')

    try:
        url = os.environ['WORKFLOWS_URL']
    except KeyError:
        msg = \
            'MiGrid WORKFLOWS_URL was not specified in the local ' \
            'environment. This should be created automatically as part of ' \
            'the Notebook creation if the Notebook was created on IDMC. ' \
            'Currently this is the only supported way to interact with a ' \
            'VGrid. '
        write_to_log(logfile, '__vgrid_json_call', msg)
        raise EnvironmentError(msg)

    write_to_log(
        logfile,
        'vgrid_workflow_json_call',
        'A vgrid call has been requested. vgrid=%s, workflow_type=%s, '
        'attributes=%s' % (vgrid, workflow_type, attributes)
    )

    if operation not in VALID_OPERATIONS:
        msg = \
            'Requested operation %s is not a valid operation. Valid ' \
            'operations are: %s' % (operation, VALID_OPERATIONS)
        write_to_log(logfile, 'vgrid_workflow_json_call', msg)
        raise ValueError(msg)

    if workflow_type not in VALID_WORKFLOW_TYPES:
        msg = \
            'Requested workflow type %s is not a valid workflow type. Valid ' \
            'workflow types are: %s' % (workflow_type, VALID_WORKFLOW_TYPES)
        write_to_log(logfile, 'vgrid_workflow_json_call', msg)
        raise ValueError(msg)

    attributes[VGRID] = vgrid

    return __vgrid_json_call(
        operation,
        workflow_type,
        attributes,
        url,
        logfile=logfile,
        ssl=ssl,
        timeout=timeout
    )


def vgrid_job_json_call(
        vgrid, operation, workflow_type, attributes, logfile=None,
        ssl=True, timeout=DEFAULT_JSON_TIMEOUT):
    """
    Validates input for a JSON job call to VGRID. Raises a TypeError or
    ValueError if an invalid value is found. If no problems are found then a
    JSON message is setup.

    :param vgrid: (str) Vgrid to which recipe will be exported.

    :param operation: (str) The operation type to be performed by the MiG based
    JSON API. Valid operations are 'create', 'read', 'update' and 'delete'.

    :param workflow_type: (str) MiG workflow action type. Valid are
    'queue', 'job', 'cancel_job', and 'resubmit_job',

    :param attributes: (dict) A dictionary of arguments defining the specifics
    of the requested operation.

    :param logfile: (str)[optional] Path to a logfile. If provided logs are
    recorded in this file. Default is None.

    :param ssl: (boolean)[optional] Toggle to skip ssl checks. Default
    False

    :param timeout: (int) [optional] Timeout duration in seconds for Vgrid
    call. Default is 60

    :return: (function call to __vgrid_json_call) If all inputs are valid,
    will call function '__vgrid_json_call'.
    """
    check_input(vgrid, str, 'vgrid')
    check_input(operation, str, 'operation')
    check_input(workflow_type, str, 'workflow_type')
    check_input(attributes, dict, 'attributes', or_none=True)
    check_input(ssl, bool, 'ssl')

    try:
        url = os.environ['JOBS_URL']
    except KeyError:
        msg = \
            'MiGrid JOBS_URL was not specified in the local ' \
            'environment. This should be created automatically as part of ' \
            'the Notebook creation if the Notebook was created on IDMC. ' \
            'Currently this is the only supported way to interact with a ' \
            'VGrid. '
        write_to_log(logfile, '__vgrid_json_call', msg)
        raise EnvironmentError(msg)

    write_to_log(
        logfile,
        'vgrid_job_json_call',
        'A vgrid call has been requested. vgrid=%s, workflow_type=%s, '
        'attributes=%s' % (vgrid, workflow_type, attributes)
    )

    if operation not in VALID_OPERATIONS:
        msg = \
            'Requested operation %s is not a valid operation. Valid ' \
            'operations are: %s' % (operation, VALID_OPERATIONS)
        write_to_log(logfile, 'vgrid_job_json_call',  msg)
        raise ValueError(msg)

    if workflow_type not in VALID_JOB_TYPES:
        msg = \
            'Requested workflow type %s is not a valid workflow type. Valid ' \
            'workflow types are: %s' % (workflow_type, VALID_JOB_TYPES)
        write_to_log(logfile, 'vgrid_job_json_call', msg)
        raise ValueError(msg)

    attributes[VGRID] = vgrid

    return __vgrid_json_call(
        operation,
        workflow_type,
        attributes,
        url,
        logfile=logfile,
        ssl=ssl,
        timeout=timeout
    )


def __vgrid_json_call(
        operation, workflow_type, attributes, url, logfile=None, ssl=True,
        timeout=DEFAULT_JSON_TIMEOUT):
    """
    Makes JSON call to MiG. Will pull url and session_id from local
    environment variables, as setup by MiG notebook spawner. Will raise
    EnvironmentError if these are not present.

    :param operation: (str) The operation type to be performed by the MiG based
    JSON API. Valid operations are 'create', 'read', 'update' and 'delete'.

    :param workflow_type: (str) MiG workflow action type. Valid are
    'workflows', 'workflowpattern', 'workflowrecipe', 'any', 'queue', 'job',
    'cancel_job', and 'resubmit_job'

    :param attributes: (dict) A dictionary of arguments defining the specifics
    of the requested operation.

    :param url: (str) The url to send JSON call to.

    :param logfile: (str)[optional] Path to a logfile. If provided logs are
    recorded in this file. Default is None.

    :param ssl: (boolean)[optional] Toggle to use ssl checks. Default True

    :param timeout: (int) [optional] Timeout duration in seconds for Vgrid
    call. Default is 60

    :return: (Tuple (dict, dict, dict) Returns JSON call results as three
    dicts. First is the header, then the body then the footer. Header contains
    keys 'headers' and 'object_type', Body contains 'workflows' and
    'object_type' and footer contains 'text' and 'object_type'.
    """

    try:
        session_id = os.environ['WORKFLOWS_SESSION_ID']
    except KeyError:
        msg = \
            'MiGrid WORKFLOWS_SESSION_ID was not specified in the local ' \
            'environment. This should be created automatically as part of ' \
            'the Notebook creation if the Notebook was created on IDMC. ' \
            'Currently this is the only supported way to interact with a ' \
            'VGrid. '
        write_to_log(logfile, '__vgrid_json_call', msg)
        raise EnvironmentError(msg)

    data = {
        'workflowsessionid': session_id,
        'operation': operation,
        'type': workflow_type,
        'attributes': attributes
    }

    write_to_log(
        logfile,
        '__vgrid_json_call',
        'sending request to  %s with data: %s' % (url, data)
    )

    try:
        response = requests.post(
            url,
            json=data,
            verify=ssl,
            timeout=timeout
        )

    except requests.Timeout:
        msg = 'Connection to MiG has timed out. '
        write_to_log(logfile, '__vgrid_json_call', msg)
        write_to_log(logfile, '__vgrid_json_call', traceback.format_exc())
        msg += 'Please check that the MiG is still online. If the problem ' \
               'persists contact an admin. '
        raise Exception(msg)
    except requests.ConnectionError:
        msg = 'Connection could not be established. '
        write_to_log(logfile, '__vgrid_json_call', msg)
        write_to_log(logfile, '__vgrid_json_call', traceback.format_exc())
        msg += 'Please check that the MiG is still online. If the problem ' \
               'persists contact an admin. '
        raise Exception(msg)

    try:
        json_response = response.json()

    except json.JSONDecodeError as err:
        msg = 'Unexpected feedback from MiG. %s' % err
        write_to_log(logfile, '__vgrid_json_call', msg)
        raise Exception(msg)

    header = json_response[0]
    body = json_response[1]
    footer = json_response[2]

    return header, body, footer


def read_vgrid(vgrid, ssl=True, timeout=DEFAULT_JSON_TIMEOUT):
    """
    Reads a given vgrid. Returns a dict of Patterns and a dict of Recipes .

    :param vgrid: (str) A vgrid to read

    :param ssl: (boolean)[optional] Toggle to use ssl checks. Default True

    :param timeout: (int) [optional] Timeout duration in seconds for Vgrid
    call. Default is 60

    :return: (dict) A dictionary of responses. Contains separate keys for the
    patterns and the recipes.
    """

    check_input(vgrid, str, VGRID)

    _, response, _ = vgrid_workflow_json_call(
        vgrid,
        VGRID_READ,
        VGRID_ANY_OBJECT_TYPE,
        {},
        ssl=ssl,
        timeout=timeout
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


def write_vgrid(
        patterns, recipes, vgrid, ssl=True, timeout=DEFAULT_JSON_TIMEOUT):
    """
    Writes a collection of patterns and recipes to a given vgrid.

    :param patterns: (dict) A dictionary of pattern objects.

    :param recipes: (recipes) A dictionary of recipes.

    :param vgrid: (str) The vgrid to write to.

    :param ssl: (boolean)[optional] Toggle to use ssl checks. Default True

    :param timeout: (int) [optional] Timeout duration in seconds for Vgrid
    call. Default is 60

    :return: (dict) Dicts of updated patterns and recipes.
    """
    check_input(vgrid, str, VGRID)
    check_input(patterns, dict, 'patterns', or_none=True)
    check_input(recipes, dict, 'recipes', or_none=True)

    updated_patterns = {}
    for pattern in patterns.values():
        new_pattern = write_vgrid_pattern(
            pattern,
            vgrid,
            ssl=ssl,
            timeout=timeout
        )
        updated_patterns[pattern.name] = new_pattern

    updated_recipes = {}
    for recipe in recipes.values():
        new_recipe = write_vgrid_recipe(
            recipe,
            vgrid,
            ssl=ssl,
            timeout=timeout
        )
        updated_recipes[recipe[NAME]] = new_recipe

    return {
        PATTERNS: updated_patterns,
        RECIPES: updated_recipes
    }


def read_vgrid_pattern(pattern, vgrid, ssl=True, timeout=DEFAULT_JSON_TIMEOUT):
    """
    Reads a given pattern from a given vgrid.

    :param pattern: (str) The pattern name to read.

    :param vgrid: (str) The Vgrid to read from

    :param ssl: (boolean)[optional] Toggle to use ssl checks. Default True

    :param timeout: (int) [optional] Timeout duration in seconds for Vgrid
    call. Default is 60

    :return: (Pattern) A pattern object, or None if a Pattern could not be
    found
    """
    check_input(vgrid, str, VGRID)
    valid_pattern_name(pattern)

    attributes = {
        NAME: pattern
    }

    _, response, _ = vgrid_workflow_json_call(
        vgrid,
        VGRID_READ,
        VGRID_PATTERN_OBJECT_TYPE,
        attributes,
        ssl=ssl,
        timeout=timeout
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


def read_vgrid_recipe(recipe, vgrid, ssl=True, timeout=DEFAULT_JSON_TIMEOUT):
    """
    Reads a given recipe from a given vgrid.

    :param recipe: (str) The recipe name to read.

    :param vgrid: (str) The Vgrid to read from

    :param ssl: (boolean)[optional] Toggle to use ssl checks. Default True

    :param timeout: (int) [optional] Timeout duration in seconds for Vgrid
    call. Default is 60

    :return: (dict) A recipe dict, or None if a recipe could not be found
    """
    check_input(vgrid, str, VGRID)
    valid_recipe_name(recipe)

    attributes = {
        NAME: recipe
    }

    _, response, _ = vgrid_workflow_json_call(
        vgrid,
        VGRID_READ,
        VGRID_RECIPE_OBJECT_TYPE,
        attributes,
        ssl=ssl,
        timeout=timeout
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


def write_vgrid_pattern(
        pattern, vgrid, ssl=True, timeout=DEFAULT_JSON_TIMEOUT):
    """
    Creates a new Pattern on a given VGrid, or updates an existing Pattern.

    :param pattern: (Pattern) The pattern object to write to the VGrid.

    :param vgrid: (str) The vgrid to write the pattern to.

    :param ssl: (boolean)[optional] Toggle to use ssl checks. Default True

    :param timeout: (int) [optional] Timeout duration in seconds for Vgrid
    call. Default is 60

    :return: (Pattern) The registered Pattern object.
    """

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
        attributes,
        ssl=ssl,
        timeout=timeout
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


def write_vgrid_recipe(recipe, vgrid, ssl=True, timeout=DEFAULT_JSON_TIMEOUT):
    """
    Creates a new recipe on a given VGrid, or updates an existing recipe.

    :param recipe: (dict) The recipe to write to the VGrid.

    :param vgrid: (str) The vgrid to write the recipe to.

    :param ssl: (boolean)[optional] Toggle to use ssl checks. Default True

    :param timeout: (int) [optional] Timeout duration in seconds for Vgrid
    call. Default is 60

    :return: (dict) The registered Recipe dict.
    """

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
        attributes,
        ssl=ssl,
        timeout=timeout
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


def delete_vgrid_pattern(
        pattern, vgrid, ssl=True, timeout=DEFAULT_JSON_TIMEOUT):
    """
    Attempts to delete a given pattern from a given VGrid.

    :param pattern: (Pattern) A valid workflow Pattern object

    :param vgrid: (str) A MiG Vgrid to connect to

    :param ssl: (boolean)[optional] Toggle to use ssl checks. Default True

    :param timeout: (int) [optional] Timeout duration in seconds for Vgrid
    call. Default is 60

    :return: (dict) Returns a Pattern object. If the deletion is successful
    the persistence_id attribute is removed
    """

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
        attributes,
        ssl=ssl,
        timeout=timeout
    )

    if response['object_type'] != 'error_text':
        delattr(pattern, 'persistence_id')
        print("%s '%s' deleted from VGrid '%s'"
              % (PATTERN_NAME, pattern.name, vgrid))
    else:
        print(response['text'])
    return pattern


def delete_vgrid_recipe(recipe, vgrid, ssl=True, timeout=DEFAULT_JSON_TIMEOUT):
    """
    Attempts to delete a given recipe from a given VGrid.

    :param recipe: (dict) A valid workflow recipe

    :param vgrid: (str) A MiG Vgrid to connect to

    :param ssl: (boolean)[optional] Toggle to use ssl checks. Default True

    :param timeout: (int) [optional] Timeout duration in seconds for Vgrid
    call. Default is 60

    :return: (dict) Returns a recipe dictionary. If the deletion is successful
    the persistence_id attribute is removed
    """

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
        attributes,
        ssl=ssl,
        timeout=timeout
    )

    if response['object_type'] != 'error_text':
        recipe.pop(PERSISTENCE_ID)
        print("%s '%s' deleted from VGrid '%s'"
              % (RECIPE_NAME, recipe[NAME], vgrid))
    else:
        print(response['text'])
    return recipe
