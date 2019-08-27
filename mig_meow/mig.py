
import requests
from .constants import VGRID_PATTERN_OBJECT_TYPE, VGRID_RECIPE_OBJECT_TYPE, \
    NAME, INPUT_FILE, TRIGGER_PATHS, OUTPUT, RECIPES, VARIABLES
from .notebook import get_containing_vgrid
from .pattern import Pattern
from .recipe import is_valid_recipe_dict


def export_to_vgrid(object, print=True):
    if isinstance(object, Pattern):
        return export_pattern_to_vgrid(object, print=print)
    elif isinstance(object, dict):
        return export_recipe_to_vgrid(object, print=print)


def export_pattern_to_vgrid(pattern, print=True):
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
    return vgrid_json_call('create',
                           VGRID_PATTERN_OBJECT_TYPE,
                           attributes=attributes,
                           print_feedback=print)


def export_recipe_to_vgrid(recipe, print=True):
    if not isinstance(recipe, dict):
        raise TypeError("The provided object '%s' is a %s, not a dict "
                        "as expected" % (recipe, type(recipe)))
    status, msg = is_valid_recipe_dict(recipe)
    if not status:
        raise Exception('The provided recipe is not valid. '
                        '%s' % msg)

    return vgrid_json_call('create',
                           VGRID_RECIPE_OBJECT_TYPE,
                           attributes=recipe,
                           print_feedback=print)


def vgrid_json_call(operation, workflow_type, attributes={}, print_feedback=True):
    # TODO, change these to avoid hard coding
    url = 'https://sid.migrid.test/cgi-sid/workflowjsoninterface.py?output_format=json'
    session_id = '92c2f0735e8cc9dbf693160ad52052fb42d6d8c064876e80b6aae6e6da4cec0e'

    try:
        vgrid = get_containing_vgrid()
    except LookupError as exception:
        if print_feedback:
            print(exception)
        raise LookupError("Cannot identify Vgrid to import from. "
                          "%s" % exception)

    # operation = 'read'
    # workflow_type = 'any'

    # Here the attributes are used as search parameters
    attributes['vgrids'] = vgrid

    data = {
        'workflowsessionid': session_id,
        'operation': operation,
        'type': workflow_type,
        'attributes': attributes
    }

    response = requests.post(url, json=data, verify=False)
    # try:
    json_response = response.json()
    # except json.JSONDecodeError:
    #     self.set_feedback("No response from vgrid. ")

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
