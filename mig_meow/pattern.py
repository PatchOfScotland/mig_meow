
from .constants import DEFAULT_JOB_NAME, VALID_PATTERN, NAME, INPUT_FILE, \
    TRIGGER_PATHS, OUTPUT, RECIPES, VARIABLES, CHAR_UPPERCASE, \
    CHAR_LOWERCASE, CHAR_NUMERIC, CHAR_LINES, PERSISTENCE_ID, \
    TRIGGER_OUTPUT, NOTEBOOK_OUTPUT, PLACEHOLDER
from .input import valid_string, check_input


class Pattern:
    def __init__(self, parameters):
        """Constructor for new pattern object. Used within MEOW as a more
        user friendly and controllable way of creating and manipulating
        patterns, as opposed to a raw dict

        Takes a single input. This can be either a string, which is used as
        the patterns name when defining a new pattern, or can be a dict which
        already expresses a complete pattern. The dict option is used during
        the importing of data from the mig and should only be used by expert
        users."""
        # if given only a string use this as a name, it is the basis of a
        # completely new pattern
        if isinstance(parameters, str):
            valid_string(parameters,
                         'pattern_name',
                         CHAR_UPPERCASE
                         + CHAR_LOWERCASE
                         + CHAR_NUMERIC
                         + CHAR_LINES)
            self.name = parameters
            self.trigger_file = None
            self.trigger_paths = []
            self.recipes = []
            self.outputs = {}
            self.variables = {}
            return
        # if given dict we are importing from a stored pattern object
        if isinstance(parameters, dict):
            is_valid_pattern_dict(parameters)
            if PERSISTENCE_ID in parameters:
                self.persistence_id = parameters[PERSISTENCE_ID]
            self.name = parameters[NAME]
            self.trigger_file = parameters[INPUT_FILE]
            self.outputs = parameters[OUTPUT]
            self.variables = parameters[VARIABLES]
            self.trigger_paths = parameters[TRIGGER_PATHS]

            # TODO update propperly
            recipes = []
            for k1, v1 in parameters['trigger_recipes'].items():
                for k2, v2 in v1.items():
                    if 'name' in v2:
                        recipes.append(v2['name'])
            self.recipes = recipes
            return
        raise Exception('Pattern requires either a str input as a name for a '
                        'new pattern, or a dict defining a complete pattern')

    def __str__(self):
        string = 'Name: %s, ' \
                 'Input(s): %s, ' \
                 'Trigger(s): %s, ' \
                 'Output(s): %s, ' \
                 'Recipe(s): %s, ' \
                 'Variable(s): %s' \
                 % (self.name,
                    self.trigger_file,
                    self.trigger_paths,
                    self.outputs,
                    self.recipes,
                    self.variables)
        return string

    def __eq__(self, other):
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

    def display_str(self):
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
        """Performs some basic checks on the data within a pattern to check
        that all required fields have been filled out as it is currently very
        possible to create incomplete patterns.

        This takes no input and only raises warnings rather than Exceptions
        so that multiple problems may easily be identified at once"""
        warning = ''
        if self.name is None:
            return False, "A pattern name must be defined. "
        if self.trigger_file is None \
                or self.trigger_file == PLACEHOLDER:
            return (False, "An input file must be defined. This is the file "
                           "that is used to trigger any processing and can be "
                           "defined using the methods '.add_single_input' or "
                           "'add_gathering_input. ")
        if len(self.trigger_paths) == 0 \
                or PLACEHOLDER in self.trigger_paths:
            return (False, "At least one input path must be defined. This is "
                           "the path to the file that is used to trigger any "
                           "processing and can be defined using the methods "
                           "'.add_single_input' or 'add_gathering_input. ")
        if len(self.outputs) == 0 \
                or PLACEHOLDER in self.outputs.keys()\
                or PLACEHOLDER in self.outputs.values():
            warning += 'No output has been set, meaning no resulting ' \
                       'data will be copied back into the vgrid. ANY OUTPUT ' \
                       'WILL BE LOST. '
        if len(self.recipes) == 0 \
                or PLACEHOLDER in self.recipes:
            return False, "No recipes have been defined. "
        if PLACEHOLDER in self.variables.keys() \
                or PLACEHOLDER in self.variables.values():
            return False, "A variable uses a placeholder value. "
        if self.trigger_file not in self.variables.keys():
            return (False, "Trigger file has been defined but is not "
                           "accessible as a variable within the job. If you "
                           "manually set the trigger file you should also "
                           "add it to the variables dict")
        for output in self.outputs.keys():
            if output not in  self.variables.keys():
                return (False, "Output %s has been defined but is not "
                               "accessible as a variable within the job. If "
                               "you manually set the trigger file you should "
                               "also add it to the variables dict" % output)
        return True, warning

    def add_single_input(self, input_file, regex_path, output_path=None):
        """
        Defines a single input for a pattern. That is, a path that when a
        single file is either created or modified and matches said path, the
        recipe will be triggered taking that file as input.

        Takes 2 mandatory inputs. 'input_file' is the variable name used to
        refer to the triggering file within the recipe. 'regex_path' is path
        within the mig against which any file creation or modification events
        are compared. The path should be given relative to the vgrid home
        directory so the path 'dir/file.txt' would match the file 'file.txt'
        within the directory 'dir' that is contained within the vgrid folder
        itself. Paths can, and should be expressed using regular expressions
        in order to match multiple files and so create a dynamic workflow.
        For example:

        initial_data/.*\\.hdf5

        This would match any hdf5 files contained within the directory initial
        data. Note that as string expression of regular expression normal use
        of escape characters and the like apply.

        'output_path' may also be defined. If done so, this will be the path
        where the input file will be copied. This is useful if some data
        processing is taking place on the input and you require that data, as
        the triggering file itself will remain unchanged. Note that this is a
        regular string path and can be hard coded such as 'dir/file.txt'
        which will always write to the same location. Alternatively the '*'
        character can be used to take the name of the triggering file.
        For example:

        'output_dir/*.hdf5'

        When triggered by a file called 'filename.txt' this would copy the
        output to output_dir/filename.hdf5
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
                self.add_variable(input_file, input_file)
        else:
            raise Exception('Could not create single input %s, as input '
                            'already defined' % input_file)

    def add_gathering_input(self, input_file, path_list, output_path=None):
        """
        Defines a gathering input for a pattern. That is, a collection of
        paths that when each individual path is either created or modified,
        a buffer file containing all the specified paths is updated. Once all
        files are present in the buffer then the recipe is triggered by it
        according to the single input trigger, with the buffer as the trigger.

        Takes 2 mandatory inputs. 'input_file' is the variable name used to
        refer to the triggering file within the recipe. 'path_list' is a list
        of paths which will be combined into a single buffer file as so used
        to trigger a job. Note that these paths are hard coded as paths and
        are not evaluated as regular expressions

        'output_path' may also be defined. If done so, this will be the path
        where the input file will be copied. This is useful if some data
        processing is taking place on the input and you require that data, as
        the triggering file itself will remain unchanged. Note that this is a
        regular string path and can be hard coded such as 'dir/file.txt'
        which will always write to the same location. Alternatively the '*'
        character can be used to take the name of the triggering file.
        For example:

        'output_dir/*.hdf5'

        When triggered by a file called 'filename.txt' this would copy the
        output to output_dir/filename.hdf5
        """
        check_input(input_file, str, 'input_file')
        check_input(path_list, list, 'path_list')
        for entry in path_list:
            check_input(entry, str, 'path_list entry')
        check_input(output_path, str, 'output_path', or_none=True)

        if len(self.trigger_paths) == 0:
            if output_path:
                self.add_output(input_file, output_path)
            else:
                self.add_variable(input_file, input_file)
            for path in path_list:
                self.trigger_paths.append(path)
        else:
            raise Exception('Could not create gathering input %s, as input '
                            'already defined' % input_file)

    def add_output(self, output_name, output_location):
        """
        Adds output to the pattern. That is, defines some file that is copied
        as output from the job processing. If any file is created by the
        recipe at runtime is should be added as output using this method or
        else it may be lost.

        Takes two inputs, 'output_name' is the variable name used within the
        recipe to refer to the output file, whilst 'output_location' is the
        path where the file will be copied on job completion. Note that this
        is a string path and can be hard coded such as 'dir/file.txt'
        which will always write to the same location. Alternatively the '*'
        character can be used to take the name of the triggering file.
        For example:

        'output_dir/*.hdf5'

        When triggered by a file called 'filename.txt' this would copy the
        output to output_dir/filename.hdf5
        """
        check_input(output_name, str, 'output_name')
        check_input(output_location, str, 'output_location')

        if output_name not in self.outputs.keys():
            self.outputs[output_name] = output_location
            self.add_variable(output_name, output_name)
        else:
            raise Exception('Could not create output %s as already defined'
                            % output_name)

    def return_notebook(self, output_location):
        """
        Adds the notebook used to run the job as output. 'output_location' is
        the path where the file will be copied on job completion. Note that
        this is a string path and can be hard coded such as 'dir/file.txt'
        which will always write to the same location. Alternatively the '*'
        character can be used to take the name of the triggering file.
        For example:

        'output_dir/*.hdf5'

        When triggered by a file called 'filename.txt' this would copy the
        output to output_dir/filename.hdf5
        """
        check_input(output_location, str, 'output_location')
        self.add_output(DEFAULT_JOB_NAME, output_location)

    def add_recipe(self, recipe):
        """
        Adds a recipe to the pattern. This is the code that runs as part of a
        workflow job, and is triggered by the patterns specified trigger.
        """
        check_input(recipe, str, 'recipe')
        self.recipes.append(recipe)

    def add_variable(self, variable_name, variable_value):
        """
        Adds a variable to the pattern, which will be passed to the recipe
        notebook using papermill as parameters.

        Takes two arguments. 'variable_name' is the name of the variable and
        must be a string, 'variable_value' can be any valid python variable
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
            if variable_name == self.trigger_file:
                raise Exception('Could not create variable %s as this name '
                                'is already used by the input file. '
                                % variable_name)
            else:
                raise Exception('Could not create variable %s as a variable '
                                'with this name is already defined. '
                                % variable_name)

    def to_display_dict(self):
        # TODO description
        dict = {
            NAME: self.name,
            INPUT_FILE: self.trigger_file,
            TRIGGER_PATHS: self.trigger_paths,
            RECIPES: self.recipes,
            OUTPUT: {},
            VARIABLES: {},
            TRIGGER_OUTPUT: '',
            NOTEBOOK_OUTPUT: ''
        }

        for key, value in self.variables.items():
            if key not in self.outputs \
                    and key != self.trigger_file:
                dict[VARIABLES][key] = value

        for key, value in self.outputs.items():
            if key != self.trigger_file and key != DEFAULT_JOB_NAME:
                dict[OUTPUT][key] = value

        if self.trigger_file in self.outputs:
            dict[TRIGGER_OUTPUT] = self.outputs[self.trigger_file]
        if DEFAULT_JOB_NAME in self.outputs:
            dict[NOTEBOOK_OUTPUT] = self.outputs[DEFAULT_JOB_NAME]
        return dict


def is_valid_pattern_object(to_test):
    """Validates that the passed object is a Pattern

    :param: to_test: object to be tested.
    :return: returns tuple. First value is boolean. True = to_test is Pattern,
    False = to_test is not Pattern. Second value is feedback string.
    """

    if not to_test:
        return False, 'A workflow pattern was not provided'

    if not isinstance(to_test, Pattern):
        return False, 'The workflow pattern was incorrectly formatted'

    return True, ''


def is_valid_pattern_dict(to_test):
    """Validates that the passed dictionary can be used to create a new
    Pattern object.

    :param: to_test: object to be tested. Must be dict.
    :return: returns tuple. First value is boolean. True = to_test is Pattern,
    False = to_test is not Pattern. Second value is feedback string.
    """

    if not to_test:
        return False, 'A workflow pattern was not provided'

    if not isinstance(to_test, dict):
        return False, 'The workflow pattern was incorrectly formatted'

    message = 'The workflow pattern had an incorrect structure'
    for key, value in to_test.items():
        if key not in VALID_PATTERN:
            message += ' Is missing key %s' % key
            return False, message
        if not isinstance(value, VALID_PATTERN[key]):
            message += ' %s is expected to have type %s but actually has %s' \
                       % (value, VALID_PATTERN[key], type(value))
            return False, message
    return True, ''
