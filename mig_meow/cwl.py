
from .constants import CWL_NAME, CWL_CWL_VERSION, CWL_CLASS, CWL_BASE_COMMAND,\
    CWL_INPUTS, CWL_OUTPUTS, CWL_STEPS, CWL_HINTS, CWL_REQUIREMENTS, \
    CWL_ARGUMENTS, CWL_STDOUT, CWL_WORKFLOW_IN, CWL_WORKFLOW_OUT, \
    CWL_YAML_PATH, CWL_OUTPUT_BINDING, CWL_OUTPUT_TYPE, CWL_OUTPUT_GLOB, \
    CWL_VARIABLES, PLACEHOLDER, WORKFLOW_NAME, STEP_NAME, VARIABLES_NAME, \
    WORKFLOWS, STEPS, SETTINGS, CWL_CLASS_COMMAND_LINE_TOOL, \
    CWL_CLASS_WORKFLOW, CWL_WORKFLOW_RUN
from .inputs import check_input, is_valid_workflow_dict, is_valid_step_dict, \
    is_valid_setting_dict


def make_step_dict(name, base_command):
    """
    Creates a new dict defining a base CWL step.

    :param name: (str) Name of CWL step.

    :param base_command: (str) Base command for CWL step.

    :return: (dict) Dictionary defining CWL step. Format is:
    {
        'name': str,
        'cwlVersion': str,
        'class': str,
        'baseCommand': str,
        'stdout': str,
        'inputs': dict,
        'outputs': dict,
        'arguments': list,
        'requirements': dict,
        'hints': dict
    }
    """
    check_input(name, str, 'name')
    check_input(base_command, str, 'baseCommand')

    return {
        CWL_NAME: name,
        CWL_CWL_VERSION: 'v1.0',
        CWL_CLASS: CWL_CLASS_COMMAND_LINE_TOOL,
        CWL_BASE_COMMAND: base_command,
        CWL_STDOUT: '',
        CWL_INPUTS: {},
        CWL_OUTPUTS: {},
        CWL_ARGUMENTS: [],
        CWL_REQUIREMENTS: {},
        CWL_HINTS: {},
    }


def make_workflow_dict(name):
    """
    Creates a new dict defining a base CWL workflow.

    :param name: (str or dict) Name of CWL workflow.

    :return: (dict) Dictionary defining CWL workflow. Format is:
    {
        'name': str,
        'cwlVersion': str,
        'class': str,
        'inputs': dict,
        'outputs': dict,
        'requirements': dict,
        'steps': dict
    }
    """

    check_input(name, str, 'name')

    return {
        CWL_NAME: name,
        CWL_CWL_VERSION: 'v1.0',
        CWL_CLASS: CWL_CLASS_WORKFLOW,
        CWL_INPUTS: {},
        CWL_OUTPUTS: {},
        CWL_STEPS: {},
        CWL_REQUIREMENTS: {}
    }


def make_settings_dict(name, yaml):
    """
    Creates a new dict defining CWL input variables to be saved as a yaml file.

    :param name: (str) Name of settings dict. This is used to match the dict
    to a workflow or step file.

    :param yaml: (dict) Variables to be saved.

    :return: (dict) Dictionary input arguments. Format is:
    {
        'name': str,
        'arguments': dict
    }
    """

    check_input(name, str, 'name')
    check_input(yaml, dict, 'settings', or_none=True)

    return {
        CWL_NAME: name,
        CWL_VARIABLES: yaml
    }


def get_linked_workflow(workflow, steps, settings):
    """
    Determines static workflow using CWL definitions. This will attempt to get
    all steps defined in the 'workflow' and construct a dict of nodes to be
    displayed.

    :param workflow: (dict) A CWL workflow dictionary.

    :param steps: (dict) A dict of CWL step dictionaries.

    :param settings: (dict) A CWL arguments dictionary.

    :return: Tuple (dict) Returns a dict of workflow nodes. Format is:
    {
        'inputs': dict,
        'outputs': dict,
        'ancestors': dict
    }
    """

    workflow_nodes = {}

    for step_title, step in workflow[CWL_STEPS].items():
        step_name = get_step_name_from_title(step_title, workflow)
        workflow_nodes[step_name] = {
            'inputs': {},
            'outputs': {},
            'ancestors': {},
        }

        for input_key, input_value in step[CWL_WORKFLOW_IN].items():
            if '/' not in input_value:
                if workflow[CWL_INPUTS][input_value] == 'File':
                    workflow_nodes[step_name]['inputs'][input_key] = \
                        settings[input_value][CWL_YAML_PATH]
            else:
                ancestor = input_value[:input_value.index('/')]
                workflow_nodes[step_name]['ancestors'][ancestor] = input_value

        # TODO clean this up. I hate it and its ugly
        outputs_string = step[CWL_WORKFLOW_OUT]

        outputs_list = []
        if isinstance(outputs_string, list):
            outputs_list = outputs_string
        elif isinstance(outputs_string, str):
            if outputs_string.startswith('[') and outputs_string.endswith(']'):
                outputs_string = outputs_string[1:-1]

                outputs_list = outputs_string.split(',')
                for i in range(len(outputs_list)):
                    outputs_list[i] = outputs_list[i].replace(' ', '')

        for output in outputs_list:
            full_output = '%s/%s' % (step_name, output)
            if step_name not in steps:
                break
            if steps[step_name][CWL_OUTPUTS][output][CWL_OUTPUT_TYPE] \
                    == 'File':
                output_value = \
                    steps[step_name][CWL_OUTPUTS][output][CWL_OUTPUT_BINDING]
                if isinstance(output_value, dict):
                    glob = output_value[CWL_OUTPUT_GLOB]
                    if glob.startswith('$(inputs'):
                        glob = glob[glob.index('s')+1:glob.index(')')]

                        if glob.startswith('.'):
                            glob = glob[1:]
                        if glob.startswith('[') and glob.endswith(']'):
                            glob = glob[1:-1]
                        if glob.startswith('\'') and glob.endswith('\''):
                            glob = glob[1:-1]
                        if glob.startswith('"') and glob.endswith('"'):
                            glob = glob[1:-1]
                        if glob in step[CWL_WORKFLOW_IN]:
                            output_key = step[CWL_WORKFLOW_IN][glob]
                            output_value = settings[output_key]
                    else:
                        break
                workflow_nodes[step_name]['outputs'][full_output] = \
                    output_value

    return workflow_nodes


def get_step_name_from_title(title, workflow):
    """
    Gets the specific name of a step according to the longer auto-generated
    but definately unique title.

    :param title: (str)

    :param workflow: (dict) A CWL workflow dict.

    :return: (str) Name derived from title, according to workflow definition.
    """
    name = workflow[CWL_STEPS][title][CWL_WORKFLOW_RUN]
    if '.' in name:
        name = name[:name.index('.')]
    return name


def check_workflow_is_valid(workflow_name, cwl):
    """
    Checks that a given workflow is valid, with a corresponding arguments
    definiton and that no placeholder values are present.

    :param workflow_name: (str)

    :param cwl: (dict) A dict of CWL defitions, including workflows, steps and
    arguments.

    :return: (Tuple (bool, str) If workflow is valid returns a tuple of first
    value True and second value an empty string. Else, returns a tuple of
    first value False, with the second value being an explanatory error
    message.
    """

    if workflow_name not in cwl[WORKFLOWS]:
        msg = "%s \'%s\' does not exist within the current CWL definitions. " \
              % (WORKFLOW_NAME, workflow_name)
        return False, msg
    workflow = cwl[WORKFLOWS][workflow_name]

    if workflow_name not in cwl[SETTINGS]:
        msg = "%s \'%s\' does not have a corresponding YAML %s definition. " \
              "This should share the name of the %s, and in this case " \
              "should be \'%s\'" \
              % (WORKFLOW_NAME, workflow_name, VARIABLES_NAME, WORKFLOW_NAME,
                 workflow_name)
        return False, msg
    settings = cwl[SETTINGS][workflow_name]

    for input_key, input_type in workflow[CWL_INPUTS].items():
        if input_key not in settings[CWL_VARIABLES]:
            msg = '%s \'%s\' expects input \'%s\', but it is not present in ' \
                  'yaml dict \'%s\'. ' \
                  % (WORKFLOW_NAME, workflow[CWL_NAME], input_key,
                     settings[CWL_NAME])
            return False, msg
        if settings[CWL_VARIABLES][input_key] == PLACEHOLDER:
            msg = '%s \'%s\' contains an entry for \'%s\' whose value is ' \
                  'the placeholder value \'%s\'. Please update this to an ' \
                  'actual value before proceeding. ' \
                  % (VARIABLES_NAME, settings[CWL_NAME], input_key,
                     PLACEHOLDER)
            return False, msg
        if isinstance(settings[CWL_VARIABLES][input_key], dict):
            for key, value in settings[CWL_VARIABLES][input_key].items():
                if value == PLACEHOLDER:
                    msg = '%s \'%s\' contains a dict for \'%s\' which ' \
                          'contains the key \'%s\', whose value is the ' \
                          'placeholder value \'%s\'. Please update this to ' \
                          'an actual value before proceeding. ' \
                          % (VARIABLES_NAME, settings[CWL_NAME], input_key,
                             key, PLACEHOLDER)
                    return False, msg
    return True, ''


def check_step_is_valid(step_name, cwl):
    """
    Checks that a given step is valid.

    :param step_name: (str) Name of step to check.

    :param cwl: (dict) Dictionary of CWL steps dictionaries.

    :return: (Tuple (bool, str) If step is valid returns a tuple of first
    value True and second value an empty string. Else, returns a tuple of
    first value False, with the second value being an explanatory error
    message.
    """

    if step_name not in cwl[STEPS]:
        msg = "%s \'%s\' does not exist within the current CWL definitions. " \
              % (STEP_NAME, step_name)
        return False, msg

    return True, ''


def get_glob_value(glob, step_name, workflow_cwl, settings_cwl):
    """
    Attempts to get the value associated with a glob gathering operation given
    the currently defined workflow, steps and arguments.

    :param glob: (str) The glob definition string.

    :param step_name: (str) The name of the step the glob variable is derived
    from.

    :param workflow_cwl: (dict) A CWL workflow dictionary.

    :param settings_cwl: (dict) A CWL arguments dictionary.

    :return: (Tuple(bool, string)) If 'glob' input was not formatted
    correctly or could not be found then a tuple will be returned with the
    first value being False, and the second being an appropriate error
    message. If no problems are encountered then a tuple is returned with the
    first value being True and the appropriate argument in the second value.
    """

    if '$' in glob:
        glob = glob[glob.index('(') + 1:glob.index(')')]
        inputs = glob.split('.')
        if inputs[0] != CWL_INPUTS:
            msg = "Unexpected path. %s did not equal expected path " \
                  "%s" % (inputs[0], CWL_INPUTS)
            return False, msg

        settings_key = ''
        workflow_steps = list(workflow_cwl[CWL_STEPS].keys())
        for step in workflow_steps:
            if step == step_name:
                settings_key = \
                    workflow_cwl[CWL_STEPS][step][CWL_WORKFLOW_IN][inputs[1]]

        if not settings_key:
            msg = "Could not find step %s in %s" \
                  % (step_name, list(workflow_cwl[CWL_STEPS]))
            return False, msg
        setting = settings_cwl[settings_key]

        return True, setting
    else:
        return True, glob


def get_glob_entry_keys(glob, step_name, workflow_cwl):
    """
    Attempts to get a key/value pair from a glob definition. This is the pair
    of lookups within the appropriate arguments dictionary when the CWL is
    imported from MEOW definitions.

    :param glob: (str) The glob definition string.

    :param step_name: (str) The name of the step the glob variable is derived
    from.

    :param workflow_cwl: (dict) A CWL workflow dictionary.

    :return: (Tuple(bool, string or Tuple(string, string)) If 'glob'
    input was not formatted correctly or could not be found then a tuple will
    be returned with the first value being False, and the second being an
    appropriate error message. If no problems are encountered then a tuple is
    returned with the first value being True and a tuple of the key/value
    pairs being the the second value.
    """
    if '$' in glob:
        try:
            glob = glob[glob.index('(') + 1:glob.index(')')]
            inputs = glob.split('.')
            if inputs[0] != CWL_INPUTS:
                msg = "Unexpected path. %s did not equal expected path " \
                      "%s" % (inputs[0], CWL_INPUTS)
                return False, msg
            settings_key = \
                workflow_cwl[CWL_STEPS][step_name][CWL_WORKFLOW_IN][inputs[1]]

            if settings_key.endswith('_key'):
                entry = settings_key[:settings_key.rfind('_')]
                value_key = "%s_value" % entry
                return True, (settings_key, value_key)

            elif settings_key.endswith('_value'):
                entry = settings_key[:settings_key.rfind('_')]
                key_key = "%s_key" % entry
                return True, (key_key, settings_key)

        except Exception as exception:
            return False, str(exception)
    msg = 'Could not identify matching key pairs for glob %s. ' % glob
    return False, msg


def get_output_lookup(target_step_key, target_value, workflow, steps):
    """
    Retrieves the output value for a given step with a given value.

    :param target_step_key: (str) Name of the CWL step.

    :param target_value: (str) Name of the CWL step output.

    :param workflow: (dict) CWL Workflow dict containing the step.

    :param steps: (dict) CWL steps dict.

    :return: (Tuple(bool, string)) If output was not found then a tuple will
    be returned with the first value being False, and the second being an
    appropriate error message. If no problems are encountered then a tuple is
    returned with the first value being True and the output argument in the
    second value.
    """
    if target_step_key in workflow[CWL_STEPS]:
        target_step_key = get_step_name_from_title(
            target_step_key,
            workflow
        )
    if target_step_key not in steps:
        msg = "%s isn't in steps" % target_step_key
        return False, msg
    target_step = steps[target_step_key]
    if target_value not in target_step[CWL_OUTPUTS]:
        msg = '%s not in outputs' % target_value
        return False, msg
    target_output = target_step[CWL_OUTPUTS][target_value]

    if CWL_OUTPUT_TYPE not in target_output \
            or target_output[CWL_OUTPUT_TYPE] != 'File' \
            or CWL_OUTPUT_BINDING not in target_output \
            or not isinstance(target_output[CWL_OUTPUT_BINDING], dict) \
            or 'glob' not in \
            target_output[CWL_OUTPUT_BINDING]:
        msg = 'Output type is not a correctly formatted file entry'
        return False, msg
    glob = target_output[CWL_OUTPUT_BINDING]['glob']
    return True, glob


def check_workflows_dict(workflows):
    """
    Validate that the given object is a dictionary of cwl workflows.

    :param workflows: (dict) A dictionary of cwl workflow dictionaries.

    :return: (Tuple (bool, string) Returns a tuple where if the provided
    object is not a dict of cwl workflows dictionaries the first value will be
    False. Otherwise it will be True. If the first value is False then an
    explanatory error message is provided in the second value which will
    otherwise be an empty string.
    """
    if not isinstance(workflows, dict):
        return False, 'The provided %s(s) were not in a dict' % WORKFLOW_NAME
    else:
        for name, workflow in workflows.items():
            valid, feedback = is_valid_workflow_dict(workflow)
            if not valid:
                return False, \
                       '%s %s was not valid. %s' \
                       % (WORKFLOW_NAME, workflow, feedback)
            if name != workflow[CWL_NAME]:
                return False, \
                       '%s %s is not stored correctly as it does not share ' \
                       'a name with its key %s.' \
                       % (WORKFLOW_NAME, workflow[CWL_NAME], name)
    return True, ''


def check_steps_dict(steps):
    """
    Validate that the given object is a dictionary of cwl steps.

    :param workflows: (dict) A dictionary of cwl step dictionaries.

    :return: (Tuple (bool, string) Returns a tuple where if the provided
    object is not a dict of cwl steps dictionaries the first value will be
    False. Otherwise it will be True. If the first value is False then an
    explanatory error message is provided in the second value which will
    otherwise be an empty string.
    """
    if not isinstance(steps, dict):
        return False, 'The provided %s(s) were not in a dict' % STEP_NAME
    else:
        for name, step in steps.items():
            valid, feedback = is_valid_step_dict(step)
            if not valid:
                return False, \
                       '%s %s was not valid. %s' \
                       % (STEP_NAME, step, feedback)
            if name != step[CWL_NAME]:
                return False, \
                       '%s %s is not stored correctly as it does not share ' \
                       'a name with its key %s.' \
                       % (WORKFLOW_NAME, step[CWL_NAME], name)
    return True, ''


def check_settings_dict(settings):
    """
    Validate that the given object is a dictionary of cwl settings.

    :param settings: (dict) A dictionary of cwl argument dictionaries.

    :return: (Tuple (bool, string) Returns a tuple where if the provided
    object is not a dict of cwl arguments dictionaries the first value will be
    False. Otherwise it will be True. If the first value is False then an
    explanatory error message is provided in the second value which will
    otherwise be an empty string.
    """
    if not isinstance(settings, dict):
        return False, 'The provided %s(s) were not in a dict' % VARIABLES_NAME
    else:
        for name, setting in settings.items():
            valid, feedback = is_valid_setting_dict(setting)
            if not valid:
                return False, \
                       '%s %s was not valid. %s' \
                       % (VARIABLES_NAME, setting, feedback)
            if name != setting[CWL_NAME]:
                return False, \
                       '%s %s is not stored correctly as it does not share ' \
                       'a name with its key %s.' \
                       % (WORKFLOW_NAME, setting[CWL_NAME], name)
    return True, ''
