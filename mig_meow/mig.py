import requests
from .constants import VGRID_PATTERN_OBJECT_TYPE, VGRID_RECIPE_OBJECT_TYPE, \
    NAME, INPUT_FILE, TRIGGER_PATHS, OUTPUT, RECIPES, VARIABLES
from .notebook import get_containing_vgrid
from .pattern import Pattern
from .recipe import is_valid_recipe_dict


def export_to_vgrid(object, print=True):
    """
    Sets up exporting an object to a MiG base Vgrid. Will raise an exception
    if the object provided is not supported.

    :param object: object to be exported. Should be either a Pattern or
    dict(recipe).
    :param print: (optional) In the event of feedback sets if it is printed
    to console or not. Default value is True.
    :return: returns output form relevant export function.
    """
    if isinstance(object, Pattern):
        return export_pattern_to_vgrid(object, print=print)
    elif isinstance(object, dict):
        return export_recipe_to_vgrid(object, print=print)
    raise TypeError('Object %s is not a recognised object. Must be %s or '
                    'dict' % (object, type(Pattern)))


def export_pattern_to_vgrid(pattern, print=True):
    """
    Exports a given pattern to a MiG based Vgrid. Raises an exception if
    the pattern object does not pass an integrity check before export.

    :param pattern: Pattern object to export. Must a Pattern
    :param print: (optional) In the event of feedback sets if it is printed
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
        INPUT_FILE: pattern.input_file,
        TRIGGER_PATHS: pattern.trigger_paths,
        OUTPUT: pattern.outputs,
        RECIPES: pattern.recipes,
        VARIABLES: pattern.variables
    }
    return _vgrid_json_call('create',
                            VGRID_PATTERN_OBJECT_TYPE,
                            attributes=attributes,
                            print_feedback=print)


def export_recipe_to_vgrid(recipe, print=True):
    """
    Exports a given recipe to a MiG based Vgrid. Raises an exception if
    the recipe object does not a valid recipe.

    :param recipe: Recipe object to export. Must a dict
    :param print: (optional) In the event of feedback sets if it is printed
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

    return _vgrid_json_call('create',
                            VGRID_RECIPE_OBJECT_TYPE,
                            attributes=recipe,
                            print_feedback=print)


def _vgrid_json_call(operation, workflow_type, attributes={},
                     print_feedback=True):
    """
    Sends a message to a MiG based VGrid using the JSON format.


    # TODO clarify this, curently also inludes 'delete' and 'update'.
    :param operation: operation to perform. Can be 'create' or 'read'
    # TODO check these
    :param workflow_type: type of object being sent or requested. Must be
    'workflows'
    :param attributes: (optional) attributes of object being passed. Must be
    a dict. Default is {}
    :param print_feedback: (optional) If feedback is generated, print it to
    command line. Default value is True.
    :return: returns 4 part tuple. First value is vgrid communicated with.
    Second is response message header. Third is response message body and
    fourth is response message footer.
    """

    # TODO introduce more type checks

    # TODO, change these to avoid hard coding
    url = 'https://sid.migrid.test/cgi-sid/workflowjsoninterface.py?output_format=json'
    session_id = 'd04c1047eb91a55836dd05fec08dbb1ad693090aca9983904acf7fd10f6bdb6e'

    try:
        vgrid = get_containing_vgrid()
    except LookupError as exception:
        if print_feedback:
            print(exception)
        raise LookupError("Cannot identify Vgrid to import from. "
                          "%s" % exception)

    # Here the attributes are used as search parameters
    attributes['vgrids'] = vgrid

    data = {
        'workflowsessionid': session_id,
        'operation': operation,
        'type': workflow_type,
        'attributes': attributes
    }

    response = requests.post(url, json=data, verify=False)
    json_response = response.json()

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

    return vgrid, header, body, footer
