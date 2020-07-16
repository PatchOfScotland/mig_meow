import copy
import json
import re
import os
import nbformat

from .constants import NOTEBOOK_EXTENSIONS
from .inputs import valid_string, is_valid_pattern_dict, check_input, \
    valid_file_path, is_valid_recipe_dict, valid_param_sweep, \
    valid_recipe_name, valid_pattern_name
from .constants import DESCENDANTS, WORKFLOW_INPUTS, \
    WORKFLOW_OUTPUTS, ANCESTORS, DEFAULT_JOB_NAME, NAME, INPUT_FILE, \
    TRIGGER_PATHS, OUTPUT, RECIPES, VARIABLES, CHAR_UPPERCASE, \
    CHAR_LOWERCASE, CHAR_NUMERIC, CHAR_LINES, PERSISTENCE_ID, \
    PLACEHOLDER, TRIGGER_RECIPES, SOURCE, RECIPE, PATTERN_NAME, RECIPE_NAME, \
    NO_OUTPUT_SET_WARNING, NO_INPUT_FILE_SET_ERROR, NO_INPUT_PATH_SET_ERROR, \
    NO_NAME_SET_ERROR, NO_RECIPES_SET_ERROR, PLACEHOLDER_ERROR, \
    INVALID_INPUT_PATH_ERROR, SWEEP, SWEEP_START, SWEEP_STOP, \
    SWEEP_JUMP, MIG_TRIGGER_KEYWORDS


OUTPUT_MAGIC_CHARS = MIG_TRIGGER_KEYWORDS + ['*']


def is_valid_pattern_object(to_test, integrity=False):
    """
    Validates that the passed object is a meow Pattern

    :param: to_test: (dict) object, hopefully is a Pattern class object..

    :param: integrity: (boolean) toggle for if to perform integrity check on
    pattern object. Default is false.

    :return: (Tuple (bool, string) Returns a tuple where if the provided
    object is not a Pattern the first value will be False. Otherwise it will
    be True. If the first value is False then an explanatory error message is
    provided in the second value which will otherwise be an empty string.
    """

    if not to_test:
        return False, 'A workflow %s was not provided' % PATTERN_NAME

    if not isinstance(to_test, Pattern):
        return False, \
               'The workflow %s was incorrectly formatted' % PATTERN_NAME

    if integrity:
        return to_test.integrity_check()
    else:
        return True, ''


def check_patterns_dict(patterns, integrity=False):
    """
    Validates that the given object is a dictionary of valid patterns.

    :param patterns: (dict) A dictionary of Pattern class objects.

    :param: integrity: (boolean) toggle for if to perform integrity check on
    pattern object. Default is false.

    :return: (Tuple (bool, string) Returns a tuple where if the provided
    object is not a dict of valid Pattern objects the first value will be
    False. Otherwise it will be True. If the first value is False then an
    explanatory error message is provided in the second value which will
    otherwise be an empty string.
    """
    if not isinstance(patterns, dict):
        return False, 'The provided %s(s) were not in a dict' % PATTERN_NAME
    for name, pattern in patterns.items():
        if not isinstance(pattern, Pattern):
            return False, \
                   'Object %s is a  %s, not the expected %s. '\
                   % (pattern, type(pattern), type(Pattern))

        if name != pattern.name:
            return False, \
                   '%s %s is not stored correctly as it does not share a ' \
                   'name with its key %s.' \
                   % (PATTERN_NAME, pattern.name, name)

        valid, feedback = is_valid_pattern_object(pattern, integrity=integrity)
        if not valid:
            return False, \
                   '%s %s was not valid. %s' \
                   % (PATTERN_NAME, pattern, feedback)
    return True, ''


def check_recipes_dict(recipes):
    """
    Validate that the given object is a dictionary of meow recipes.

    :param recipes: (dict) A dictionary of meow recipe dictionaries.

    :return: (Tuple (bool, string) Returns a tuple where if the provided
    object is not a dict of meow recipe dictionaries the first value will be
    False. Otherwise it will be True. If the first value is False then an
    explanatory error message is provided in the second value which will
    otherwise be an empty string.
    """
    if not isinstance(recipes, dict):
        return False, 'The provided %s(s) were not in a dict' % RECIPE_NAME
    else:
        for name, recipe in recipes.items():
            valid, feedback = is_valid_recipe_dict(recipe)
            if not valid:
                return False, \
                       '%s %s was not valid. %s' \
                       % (RECIPE_NAME, recipe, feedback)

            if name != recipe[NAME]:
                return False, \
                       '%s %s is not stored correctly as it does not share ' \
                       'a name with its key %s.' \
                       % (RECIPE_NAME, recipe[NAME], name)

    return True, ''


def parameter_sweep_entry(name, start, stop, increment):
    """
    Helper function to create parameter sweep entry

    :return: (dict) A dictionary expressing a parameter sweep
    """
    check_input(name, str, 'name')

    return {
        SWEEP_START: start,
        SWEEP_STOP: stop,
        SWEEP_JUMP: increment
    }


class Pattern:
    def __init__(self, parameters):
        """
        Constructor for new pattern object. Used within MEOW as a more user
        friendly and controllable way of creating and manipulating meow
        patterns, as opposed to a raw dict. Will raise a TypeError if
        incorrect parameters given.

        :param parameters: (string or dict) Takes a single input. This can be
        either a string, which is used as the patterns name when defining a
        new pattern, or can be a dict which already expresses a complete
        pattern. The dict option is used during the importing of data from
        the mig and should only be used by expert users.
        """
        # if given only a string use this as a name, it is the basis of a
        # completely new pattern
        if isinstance(parameters, str):
            valid_pattern_name(parameters)
            self.name = parameters
            self.trigger_file = None
            self.trigger_paths = []
            self.recipes = []
            self.outputs = {}
            self.variables = {}
            self.sweep = {}
            return
        # if given dict we are importing from a stored pattern object
        if isinstance(parameters, dict):
            valid, msg = is_valid_pattern_dict(parameters)

            if not valid:
                raise Exception("%s object is incorrectly formatted. %s"
                                % (PATTERN_NAME, msg))
            self.name = copy.deepcopy(parameters[NAME])

            if PERSISTENCE_ID in parameters:
                self.persistence_id = copy.deepcopy(parameters[PERSISTENCE_ID])

            self.trigger_paths = copy.deepcopy(parameters[TRIGGER_PATHS])
            self.recipes = []
            self.outputs = {}
            self.variables = {}
            self.sweep = {}

            self.trigger_file = copy.deepcopy(parameters[INPUT_FILE])

            # MiG has fun formatting recipe entries.
            if TRIGGER_RECIPES in parameters:
                for trigger_id, trigger in parameters[TRIGGER_RECIPES].items():
                    for recipe_key, recipe in trigger.items():
                        # A MiG recipe by this name has already been registered
                        if 'name' in recipe:
                            self.add_recipe(recipe['name'])
                        # If not already registered
                        else:
                            self.add_recipe(recipe_key)
            elif RECIPES in parameters:
                for recipe in parameters[RECIPES]:
                    self.add_recipe(recipe)

            if OUTPUT in parameters:
                for name, path in parameters[OUTPUT].items():
                    self.add_output(name, path)

            if VARIABLES in parameters:
                for name, value in parameters[VARIABLES].items():
                    self.add_variable(name, value)

            if SWEEP in parameters:
                for name, value in parameters[SWEEP].items():
                    self.add_param_sweep(name, value)
            return
        raise TypeError(
            'Pattern requires either a str input as a name for a new pattern, '
            'or a dict defining a complete pattern. Was instead given a %s. '
            % type(parameters)
        )

    def __str__(self):
        """
        Creates a string that expressed the current state of the Pattern
        object. Only displays parameters that should be directly editable by
        users.

        :return: (str) String expressing current Pattern object state.
        """
        string = 'Name: %s, ' \
                 'Input(s): %s, ' \
                 'Trigger(s): %s, ' \
                 'Output(s): %s, ' \
                 'Recipe(s): %s, ' \
                 'Variable(s): %s, ' \
                 'Sweeping(s): %s' \
                 % (self.name,
                    self.trigger_file,
                    self.trigger_paths,
                    self.outputs,
                    self.recipes,
                    self.variables,
                    self.sweep)
        return string

    def __eq__(self, other):
        """
        Tests if a given object is equal to this Pattern object.

        :param other: (Object) Object to test for equality.

        :return: (bool) True/False, with True denoting that the two Pattern
        objects are equal.
        """

        if not other:
            return False
        if not isinstance(other, Pattern):
            return False
        if self.name != other.name:
            return False
        if self.trigger_file != other.trigger_file:
            return False
        if self.trigger_paths != other.trigger_paths:
            return False
        if self.outputs != other.outputs:
            return False
        if self.recipes != other.recipes:
            return False
        if self.variables != other.variables:
            return False
        if self.sweep != other.sweep:
            return False
        count = 0
        try:
            self.persistence_id
            count += 1
        except AttributeError:
            pass
        try:
            other.persistence_id
            count += 1
        except AttributeError:
            pass
        if count == 1:
            return False
        if count == 2:
            if self.persistence_id != other.persistence_id:
                return False
        return True

    def display_dag_str(self):
        """
        Creates and display ready string, expressing the current Pattern
        state for a dag graph. Only displays the Pattern name, trigger file,
        trigger paths, outputs and recipes as any other characteristics are
        internal system parameters, or unnecessary for the dag.

        :return: (str) String expressing current Pattern object state.
        """
        string = 'Name: %s\n' \
                 'Input(s): %s\n' \
                 'Trigger(s): %s\n' \
                 'Output(s): %s\n' \
                 'Recipe(s): %s' \
                 % (self.name,
                    self.trigger_file,
                    self.trigger_paths,
                    self.outputs,
                    self.recipes)
        return string

    def integrity_check(self):
        """
        Performs some basic checks on the data within a pattern to check
        that all required fields have been filled out as it is currently very
        possible to create incomplete patterns.

        :return: (Tuple (bool, str)). Bool is a marker of if the pattern has
        passed the integrity check whilst str is a reason for a fail, or
        warnings of possible issues in the event of a pass.
        """
        warning = ''
        if self.name is None or not self.name:
            return False, NO_NAME_SET_ERROR
        if self.trigger_file is None or not self.trigger_file:
            return False, NO_INPUT_FILE_SET_ERROR
        if len(self.trigger_paths) == 0:
            return False, NO_INPUT_PATH_SET_ERROR
        for trigger_path in self.trigger_paths:
            if trigger_path is None or not trigger_path:
                return False, ("Error for input path '%s' " % trigger_path) \
                       + INVALID_INPUT_PATH_ERROR
        if len(self.outputs) == 0:
            warning += NO_OUTPUT_SET_WARNING
        if len(self.recipes) == 0:
            return False, NO_RECIPES_SET_ERROR

        if self.name == PLACEHOLDER \
                or self.trigger_file == PLACEHOLDER \
                or self.trigger_paths == PLACEHOLDER \
                or self.recipes == PLACEHOLDER \
                or PLACEHOLDER in self.trigger_paths \
                or PLACEHOLDER in self.outputs.keys() \
                or PLACEHOLDER in self.outputs.values() \
                or PLACEHOLDER in self.recipes \
                or PLACEHOLDER in self.variables.keys() \
                or PLACEHOLDER in self.variables.values():
            return False, PLACEHOLDER_ERROR

        return True, warning

    def add_single_input(self, input_file, regex_path, output_path=None):
        """
        Defines a single input for a pattern. That is, a path that when a
        single file is either created or modified and matches said path, the
        recipe will be triggered taking that file as input. Raises
        AttributeError if an input is already defined.

        :param input_file: (str) 'input_file' is the variable name used to
        refer to the triggering file within the recipe.

        :param regex_path: (str) 'regex_path' is path against which any file
        creation or modification events are compared. The path should be given
        relative to the vgrid home directory so the path 'dir/file.txt' would
        match the file 'file.txt' within the directory 'dir' that is contained
        within the vgrid folder itself. Paths can, and should be expressed
        using regular expressions in order to match multiple files and so
        create a dynamic workflow.
        For example:

        initial_data/.*\\.hdf5

        This would match any hdf5 files contained within the directory initial
        data. Note that as string expression of regular expression normal use
        of escape characters and the like apply.

        :param output_path: (str)[optional] 'output_path' may also be defined.
        If done so, this will be the path where the input file will be copied
        after job completion. This is useful if some data processing is taking
        place on the input and you require that data, as the triggering file
        itself will remain unchanged. Note that this is a regular string path
        and can be hard coded such as 'dir/file.txt' which will always write
        to the same location. Alternatively the '*' character can be used to
        take the name of the triggering file.
        For example:

        'output_dir/*.hdf5'

        When triggered by a file called 'filename.txt' this would copy the
        output to output_dir/filename.hdf5. Default is None.

        :return: No return.
        """

        check_input(input_file, str, 'input_file')
        check_input(regex_path, str, 'regex_path')
        check_input(output_path, str, 'output_path', or_none=True)

        if len(self.trigger_paths) == 0:
            self.trigger_file = input_file
            self.trigger_paths = [regex_path]
            if output_path:
                self.add_output(input_file, output_path)
        else:
            raise AttributeError(
                'Could not create single input %s, as input already defined'
                % input_file
            )

    def add_output(self, output_name, output_location):
        """
        Adds output to the pattern. That is, defines some file that is copied
        as output from the job processing. If any file is created by the
        recipe at runtime is should be added as output using this method or
        else it may be lost.

        :param output_name: (str) variable name used within the recipe to
        refer to the output file.

        :param output_location: (str) path where the file will be copied on
        job completion. Note that this is a string path and can be hard coded
        such as 'dir/file.txt' which will always write to the same location.
        Alternatively the '*' character can be used to take the name of the
        triggering file.
        For example:

        'output_dir/*.hdf5'

        When triggered by a file called 'filename.txt' this would copy the
        output to output_dir/filename.hdf5.

        :return: No return.
        """
        check_input(output_name, str, 'output_name')
        check_input(output_location, str, 'output_location')

        if output_name not in self.outputs.keys():
            self.outputs[output_name] = output_location
        else:
            raise Exception('Could not create output %s as already defined'
                            % output_name)

    def return_notebook(self, output_location):
        """
        Adds the notebook used to run the job as output.

        :param output_location: (str) The path where the file will be copied
        on job completion. Note that this is a string path and can be hard
        coded such as 'dir/file.txt' which will always write to the same
        location. Alternatively the '*' character can be used to take the name
        of the triggering file.
        For example:

        'output_dir/*.hdf5'

        When triggered by a file called 'filename.txt' this would copy the
        output to output_dir/filename.hdf5.

        :return: No return.
        """
        check_input(output_location, str, 'output_location')
        self.add_output(DEFAULT_JOB_NAME, output_location)

    def add_recipe(self, recipe):
        """
        Adds a recipe to the pattern. This is the code that runs as part of a
        workflow job, and is triggered by the patterns specified trigger.

        :param recipe: (str) Name of recipe to be added.

        :return: No return.
        """
        check_input(recipe, str, 'recipe')
        self.recipes.append(recipe)

    def add_variable(self, variable_name, variable_value):
        """
        Adds a variable to the pattern, which will be passed to the recipe
        notebook using papermill as parameters. Raises ValueError if variable
        name is already in use.

        :param variable_name: (str) name of the variable.

        :param variable_value: (any) any valid base python variable value.

        :return: No return.
        """
        valid_string(variable_name,
                     'variable name',
                     CHAR_UPPERCASE
                     + CHAR_LOWERCASE
                     + CHAR_NUMERIC
                     + CHAR_LINES)
        if variable_name not in self.variables.keys():
            self.variables[variable_name] = variable_value
        else:
            raise ValueError(
                'Could not create variable %s as a variable with this '
                'name is already defined. ' % variable_name
            )

    def add_param_sweep(self, name, sweep_dict):
        """
        Adds a parameter sweeping variable to the Pattern, which will be
        passed to the Recipe notebook using papermill as parameters. Raises
        ValueError if parameter sweeping variable name is already in use.

        :param name: (str) name of the variable.

        :param sweep_dict: (dict) dictionary defining the parameter sweep.
        Should be of the form:
        {
            'start': (int) or (float),
            'stop': (int) or (float),
            'jump': (int) or (float)
        }

        :return: No return.
        """
        valid_string(name,
                     'name',
                     CHAR_UPPERCASE
                     + CHAR_LOWERCASE
                     + CHAR_NUMERIC
                     + CHAR_LINES)
        valid_param_sweep(sweep_dict, name)

        if name not in self.sweep.keys():
            self.sweep[name] = sweep_dict
        else:
            raise ValueError(
                'Could not create parameter sweeping variable %s as a '
                'parameter sweeping variable with this name is already '
                'defined. ' % name
            )

    def to_display_dict(self):
        """
        Creates a dictionary of the current pattern state to be displayed as
        part of the WorkflowWidget visualisation.

        :return: (dict) Dictionary expressing current state of the Pattern
        object.
        """
        display_dict = {
            NAME: self.name,
            INPUT_FILE: self.trigger_file,
            TRIGGER_PATHS: self.trigger_paths,
            RECIPES: self.recipes,
            SWEEP: self.sweep,
            OUTPUT: {},
            VARIABLES: {}
        }

        for key, value in self.variables.items():
            if key not in self.outputs \
                    and key != self.trigger_file:
                display_dict[VARIABLES][key] = value

        for key, value in self.outputs.items():
            if key != self.trigger_file and key != DEFAULT_JOB_NAME:
                display_dict[OUTPUT][key] = value

        return display_dict


def register_recipe(source, name=None):
    """
    Registers a new Recipe dict.

    :param source: (str) The source notebook of the Recipe.

    :param name: (str)[optional] The name the Recipe is to be registered under.
    If not provided then the source filename will be used instead.

    :return: (dict) A dict object expressing the Recipe notebook at the given
    source
    """
    valid_file_path(source, 'source', extensions=NOTEBOOK_EXTENSIONS)
    check_input(name, str, 'name', or_none=True)

    if not name:
        if os.path.sep in source:
            name = source[source.rfind('/') + 1:source.index('.')]
        else:
            name = source[:source.index('.')]
    if not os.path.isfile(source):
        raise FileNotFoundError("Source %s was not found. " % source)

    with open(source, "r") as read_file:
        notebook = json.load(read_file)
        return create_recipe_dict(notebook, name, source)


def create_recipe_dict(notebook, name, source):
    """
    Creates a recipe dictionary from the given parameters.

    :param notebook: (dict) notebook source code.

    :param name: (str) name of recipe.

    :param source: (str) original notebook source code was extracted from.

    :return: (dict) Meow recipe dictionary. Format is {'name': str,
    'source': str, 'recipe': dict}
    """

    valid_recipe_name(name)
    valid_file_path(
        source,
       'recipe source'
    )
    nbformat.validate(notebook)

    recipe = {
        NAME: name,
        SOURCE: source,
        RECIPE: notebook
    }
    return recipe


def build_workflow_object(patterns):
    """
    Builds the emergent workflow from defined patterns.

    :param patterns: (dict) A dictionary of valid Pattern objects.

    :return: (Tuple (bool, string or dict) Returns a tuple with the first value
    being a boolean, with True showing that a workflow was built without
    errors, and False showing that a problem was encountered. If False the
    second value is an explanatory error message. If True the second value is
    the produced workflow, which may be empty if no workflow can be built from
    the pattern definitions. The workflow is a dict of nodes with each node
    being a dict with Format {'descendants': dict, 'ancestors': dict,
    'workflow inputs': dict, 'workflow outputs': dict}.
    """

    valid, msg = check_patterns_dict(patterns)
    if not valid:
        return False, msg

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
                    check = [mc for mc in OUTPUT_MAGIC_CHARS if mc in value]
                    if check:
                        magic_value = value
                        for magic_char in check:
                            magic_value = magic_value.replace(magic_char, '.*')
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
    return True, workflow


def pattern_has_recipes(pattern, recipes):
    """
    Checks that a pattern has all required recipes in the workflow for it
    to be triggerable

    :param pattern: (Pattern) A pattern object.

    :param recipes: (dict) A dictionary of recipes.

    :return: (Tuple (bool, string) Returns a tuple with the first value
    being a boolean, with True showing that all pattern recipes are already
    registered, and False showing that a problem was encountered. If False the
    second value is an explanatory error message. If True the second value is
    an empty string.
    """

    valid, feedback = is_valid_pattern_object(pattern)

    if not valid:
        return False, "Pattern %s is not valid. %s" % (pattern, feedback)

    if not recipes:
        return False, 'Recipes were not provided.'

    if not isinstance(recipes, dict):
        return False, \
               'Recipes was not formatted correctly. Expected dict but got ' \
               '%s. ' % type(recipes)

    for recipe in recipes.values():
        if not isinstance(recipe, dict):
            return False, \
                   'Recipe %s was incorrectly formatted. Expected %s but ' \
                   'got %s. ' % (recipe, dict, type(recipe))
        valid, feedback = is_valid_recipe_dict(recipe)
        if not valid:
            return False, "Recipe %s is not valid. %s" % (recipe, feedback)

    for recipe in pattern.recipes:
        if recipe not in recipes:
            return False, 'Recipe %s was not present in recipes. '
    return True, ''

