
import requests
from .notebook import get_containing_vgrid

def prepare_patterns_for_export(pattern_dict):

    if not isinstance(pattern_dict, dict):
        pass

def vgrid_json_call(operation, workflow_type, attributes={}):
    # TODO, change these to avoid hard coding
    url = 'https://sid.migrid.test/cgi-sid/workflowjsoninterface.py?output_format=json'
    session_id = '92c2f0735e8cc9dbf693160ad52052fb42d6d8c064876e80b6aae6e6da4cec0e'

    try:
        vgrid = get_containing_vgrid()
    except LookupError as exception:
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

    return vgrid, header, body, footer
