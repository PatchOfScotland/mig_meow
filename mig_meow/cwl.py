
from .constants import CWL_NAME, CWL_CWL_VERSION, CWL_CLASS, CWL_BASE_COMMAND,\
    CWL_INPUTS, CWL_OUTPUTS, CWL_STEPS, CWL_HINTS, CWL_REQUIREMENTS, \
    CWL_ARGUMENTS, CWL_STDOUT, CWL_WORKFLOW_IN, CWL_WORKFLOW_OUT, \
    CWL_YAML_PATH, CWL_OUTPUT_BINDING, CWL_OUTPUT_TYPE, CWL_OUTPUT_GLOB, \
    CWL_VARIABLES, PLACEHOLDER, WORKFLOW_NAME, STEP_NAME, VARIABLES_NAME, \
    WORKFLOWS, STEPS, SETTINGS, CWL_CLASS_COMMAND_LINE_TOOL, \
    CWL_CLASS_WORKFLOW, CWL_WORKFLOW_RUN


def make_step_dict(name, base_command):
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
    return {
        CWL_NAME: name,
        CWL_VARIABLES: yaml
    }


def get_linked_workflow(workflow, steps, settings):
    workflow_nodes = {}
    # settings = combine_settings(settings)

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
            if steps[step_name][CWL_OUTPUTS][output][CWL_OUTPUT_TYPE] == 'File':
                output_value = steps[step_name][CWL_OUTPUTS][output][CWL_OUTPUT_BINDING]
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
                        msg = 'Unsupported format. Glob command "%s" does ' \
                              'not take parameters from inputs. ' % glob
                        return False, msg
                workflow_nodes[step_name]['outputs'][full_output] = \
                    output_value

    return True, workflow_nodes


def get_step_name_from_title(title, workflow):
    name = workflow[CWL_STEPS][title][CWL_WORKFLOW_RUN]
    if '.' in name:
        name = name[:name.index('.')]
    return name


def check_workflow_is_valid(workflow_name, cwl):
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
    if step_name not in cwl[STEPS]:
        msg = "%s \'%s\' does not exist within the current CWL definitions. " \
              % (STEP_NAME, step_name)
        return False, msg
    step = cwl[STEPS][step_name]

    return True, ''


def get_glob_value(glob, step_name, workflow_cwl, settings_cwl):
    if '$' in glob:
        # try:
        glob = glob[glob.index('(') + 1:glob.index(')')]
        inputs = glob.split('.')
        if inputs[0] != CWL_INPUTS:
            msg = "Unexpected path. %s did not equal expected path " \
                  "%s" % (inputs[0], CWL_INPUTS)
            return False, msg

        settings_key = ''
        workflow_steps = list(workflow_cwl[CWL_STEPS].keys())
        for step in workflow_steps:
            run = workflow_cwl[CWL_STEPS][step][CWL_WORKFLOW_RUN]
            if '.' in run:
                run = run[:run.index('.')]
            if step == step_name:
                settings_key = \
                    workflow_cwl[CWL_STEPS][step][CWL_WORKFLOW_IN][inputs[1]]

        if not settings_key:
            msg = "Could not find step %s in %s" \
                  % (step_name, list(workflow_cwl[CWL_STEPS]))
            return False, msg
        setting = settings_cwl[settings_key]

        return True, setting
        # except Exception as exception:
        #     return False, str(exception)
    else:
        return True, glob


def get_glob_entry_keys(glob, step_name, workflow_cwl):
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
