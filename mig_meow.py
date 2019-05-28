import os
import json
import re


PATTERNS_DIR = '.workflow_patterns_home'

OBJECT_TYPE = 'object_type'
PERSISTENCE_ID = 'persistence_id'
TRIGGER = 'trigger'
OWNER = 'owner'
NAME = 'name'
INPUT_FILE = 'input_file'
TRIGGER_PATHS = 'trigger_paths'
OUTPUT = 'output'
RECIPES = 'recipes'
VARIABLES = 'variables'
VGRIDS = 'vgrids'
ANCESTORS = 'ancestors'
DESCENDETS = 'descendets'

VALID_PATTERN = {
    OBJECT_TYPE: str,
    PERSISTENCE_ID: str,
    TRIGGER: dict,
    OWNER: str,
    NAME: str,
    INPUT_FILE: str,
    TRIGGER_PATHS: list,
    OUTPUT: dict,
    RECIPES: list,
    VARIABLES: dict,
    VGRIDS: str
}


def help():
    print('Managing Event-Oriented Workflows has been installed correctly. '
          '\nMEOW is a package used for defining event based workflows. It is designed to work with the MiG system.')


def build_workflow(patterns):
    workflow = []
    message = ''
    # TODO validation on input

    # TODO sort out what is going on here
    nodes = {}
    for pattern in patterns:
        workflowNode = {
            NAME: pattern[NAME],
            ANCESTORS: [],
            DESCENDETS: []
        }
        input_regex_list = pattern[TRIGGER_PATHS]
        output_dict = pattern[OUTPUT]
        for other_pattern in patterns:
            other_input_regex_list = other_pattern[TRIGGER_PATHS]
            other_output_dict = other_pattern[OUTPUT]
            for input in input_regex_list:
                for key, value in other_output_dict.items():
                    if re.match(input, value):
                        print('%s leads into %s' % (other_pattern[NAME], pattern[NAME]))
                pass


    return (True, workflow, message)


def __is_valid_pattern(to_test):
    """Validates that the workflow pattern object is correctly formatted"""
    contact_msg = "please contact support so that we can help resolve this " \
                  "issue"

    if not to_test:
        msg = "A workflow pattern was not provided, " + contact_msg
        return (False, msg)

    if not isinstance(to_test, dict):
        msg = "The workflow pattern was incorrectly formatted, " + contact_msg
        return (False, msg)

    msg = "The workflow pattern had an incorrect structure, " + contact_msg
    for k, v in to_test.items():
        if k not in VALID_PATTERN:
            return (False, msg)
        # TODO alter this so is not producing error
        if not isinstance(v, VALID_PATTERN[k]):
            return (False, msg)
    return (True, '')


def retrieve_current_patterns():
    all_patterns = []
    message = ''
    if os.path.isdir(PATTERNS_DIR):
        for path in os.listdir(PATTERNS_DIR):
            file_path = os.path.join(PATTERNS_DIR, path)
            if os.path.isfile(file_path):
                try:
                    with open(file_path) as file:
                        input_dict = json.load(file)
                        if __is_valid_pattern(input_dict):
                            all_patterns.append(input_dict)
                        else:
                            message += '%s did not contain a valid pattern definition.' % path
                except:
                    message += '%s is unreadable, possibly corrupt.' % path
    else:
        return (False, None, 'No patterns found to import.')
    return (True, all_patterns, message)


class Pattern:
    # Could make name optional, but I think its clearer to make it mandatory
    def __init__(self, name):
        self.name = name
        self.input_file = None
        self.trigger_paths = []
        self.outputs = {}
        self.recipes = []
        self.variables = {}

    def integrity_check(self):
        warning = ''
        if self.input_file is None:
            return (False, "An input file must be defined. This is the file "
                           "that is used to trigger any processing and can be "
                           "defined using the methods '.add_single_input' or "
                           "'add_multiple_input")
        if len(self.trigger_paths) == 0:
            return (False, "At least one input path must be defined. This is "
                           "the path to the file that is used to trigger any "
                           "processing and can be defined using the methods "
                           "'.add_single_input' or 'add_multiple_input")
        if len(self.outputs) == 0:
            warning += '\n No output has been set, meaning no resulting ' \
                       'data will be copied back into the vgrid. ANY OUTPUT ' \
                       'WILL BE LOST.'
        if len(self.recipes) == 0:
            return (False, "No recipes have been defined")
        return (True, warning)

    def add_single_input(self, input_file, regex_path):
        # print('%s is adding single input with file: %s and path: %s' %
        #       (self.name, input_file, regex_path))
        if len(self.trigger_paths) == 0:
            self.input_file = input_file
            self.trigger_paths = [regex_path]
            self.add_variable(input_file, input_file)
        else:
            raise Exception('Could not create single input %s, as input '
                            'already defined' % input_file)

    def add_gathering_input(self, input_file, common_path, starting_index, number_of_files):
        # print('%s is adding gathing inputs with file: %s, common_path: %s, stating_index %d, and number_of_files: %d' %
        #       (self.name, input_file, common_path, starting_index, number_of_files))
        if len(self.trigger_paths) == 0:
            # common path must have '*' in it to act as wildcard for diffrenet indexed files
            star_count = common_path.count('*')
            if star_count == 0:
                raise Exception("common_path must contain a '*' character.")
            if star_count > 1:
                raise Exception("common_path should only contain one '*' character.")
            self.input_file = input_file
            self.add_variable(input_file, input_file)
            for index in range(0, number_of_files):
                path = common_path.replace('*', str(index + starting_index))
                self.trigger_paths.append(path)
        else:
            raise Exception('Could not create gathering input %s, as input '
                            'already defined' % input_file)

    def add_output(self, output_name, output_location):
        # print('%s is adding output with name: %s and path: %s' %
        #       (self.name, output_name, output_location))
        if output_name not in self.outputs.keys():
            self.outputs[output_name] = output_location
            self.add_variable(output_name, output_name)
        else:
            raise Exception('Could not create output %s as already defined'
                            % output_name)

    def add_recipe(self, recipe):
        # print('%s is adding recipe: %s' % (self.name, recipe))
        self.recipes.append(recipe)

    def add_variable(self, variable_name, variable_value):
        # print('%s is adding variable with name: %s and value: %s' %
        #       (self.name, variable_name, variable_value))
        # put variable as a string. Should allow any declared variable type to
        # be stored
        if variable_name not in self.variables.keys():
            self.variables[variable_name] = variable_value
        else:
            raise Exception('Could not create variable %s as it is already '
                            'defined' % variable_name)
