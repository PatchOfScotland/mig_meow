import requests
import json
import traceback
import os

from .constants import VGRID_PATTERN_OBJECT_TYPE, VGRID_RECIPE_OBJECT_TYPE, \
    NAME, INPUT_FILE, TRIGGER_PATHS, OUTPUT, RECIPES, VARIABLES, \
    VGRID_CREATE, VGRID, \
    VALID_OPERATIONS, VALID_WORKFLOW_TYPES, VALID_JOB_TYPES, \
    DEFAULT_JSON_TIMEOUT
from .inputs import check_input
from .logging import write_to_log
from .meow import Pattern, is_valid_recipe_dict


MRSL_VGRID = 'VGRID'


def export_pattern_to_vgrid(vgrid, pattern):
    """
    Exports a given pattern to a MiG based Vgrid. Raises a TypeError or
    ValueError if the pattern is not valid. Note this function is not used
    within mig_meow and is intended for users who want to programmatically
    alter vgrid workflows.

    :param vgrid: (str) Vgrid to which pattern will be exported.

    :param pattern: (Pattern) Pattern object to export.

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
        attributes
    )


def export_recipe_to_vgrid(vgrid, recipe):
    """
    Exports a given recipe to a MiG based Vgrid. Raises a TypeError or
    ValueError if the recipe is not valid. Note this function is not used
    within mig_meow and is intended for users who want to programmatically
    alter vgrid workflows.

    :param vgrid: (str) Vgrid to which recipe will be exported.

    :param recipe: (dict) Recipe object to export.

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
        recipe
    )


def vgrid_workflow_json_call(
        vgrid, operation, workflow_type, attributes, logfile=None):
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

    :param logfile: (str)[optional] Path to a logfile. If provided logs are
    recorded in this file. Default is None.

    :return: (function call to __vgrid_json_call) If all inputs are valid,
    will call function '__vgrid_json_call'.
    """
    check_input(vgrid, str, 'vgrid')
    check_input(operation, str, 'operation')
    check_input(workflow_type, str, 'workflow_type')
    check_input(attributes, dict, 'attributes', or_none=True)

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
        logfile=logfile
    )


def vgrid_job_json_call(
        vgrid, operation, workflow_type, attributes, logfile=None):
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

    :return: (function call to __vgrid_json_call) If all inputs are valid,
    will call function '__vgrid_json_call'.
    """
    check_input(vgrid, str, 'vgrid')
    check_input(operation, str, 'operation')
    check_input(workflow_type, str, 'workflow_type')
    check_input(attributes, dict, 'attributes', or_none=True)

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
        logfile=logfile
    )


def __vgrid_json_call(operation, workflow_type, attributes, url, logfile=None):
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
            verify=False,
            timeout=DEFAULT_JSON_TIMEOUT
        )

    except requests.Timeout:
        msg = 'Connection to MiG has timed out. '
        write_to_log(logfile, '__vgrid_json_call', msg)
        write_to_log(logfile, '__vgrid_json_call', traceback.format_exc())
        msg += 'Please check that the MiG is still online. If the problem ' \
               'persists contact an admin. '
        raise Exception(msg)
    except requests.ConnectionError :
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
