
import os
import unicodedata

from .constants import CHAR_LOWERCASE, CHAR_NUMERIC, CHAR_UPPERCASE, \
    VALID_PATTERN_MIN, RECIPE_NAME, VALID_RECIPE_MIN, PATTERN_NAME, \
    WORKFLOW_NAME, STEP_NAME, VARIABLES_NAME, MEOW_MODE, CWL_MODE, \
    VALID_WORKFLOW_MIN, VALID_STEP_MIN, VALID_SETTING_MIN, \
    VALID_PATTERN_OPTIONAL, VALID_RECIPE_OPTIONAL, VALID_SETTING_OPTIONAL, \
    VALID_STEP_OPTIONAL, VALID_WORKFLOW_OPTIONAL, CWL_CLASS_WORKFLOW, \
    CWL_CLASS_COMMAND_LINE_TOOL, CWL_CLASS, TRIGGER_PATHS, TRIGGER_RECIPES, \
    INPUT_FILE, VALID_SWEEP_MIN, VALID_SWEEP_OPTIONAL, SWEEP_START, \
    SWEEP_STOP, SWEEP_JUMP, CHAR_LINES


def is_a_number(string):
    """
    Helper function to determine if a given string expresses a number

    :param string: (str) The string to check

    :return: (bool) Will return True if given string expresses a number, and
    False otherwise
    """
    check_input(string, 'str', 'string')

    try:
        float(string)
        return True
    except ValueError:
        pass

    try:
        unicodedata.numeric(string)
        return True
    except (TypeError, ValueError):
        pass

    return False


def check_input(variable, expected_type, name, or_none=False):
    """
    Checks if a given variable is of the expected type. Raises TypeError or
    ValueError as appropriate if any issues are encountered.

    :param variable: (any) variable to check type of

    :param expected_type: (type) expected type of the provided variable

    :param name: (str) name of the variable, used to make clearer debug
    messages.

    :param or_none: (optional) boolean of if the variable can be unset.
    Default value is False.

    :return: No return.
    """

    if not variable and expected_type is not bool and or_none is False:
        raise ValueError('variable %s was not given' % name)

    if not expected_type:
        raise ValueError('\'expected_type\' %s was not given' % expected_type)

    if not or_none:
        if not isinstance(variable, expected_type):
            raise TypeError(
                'Expected %s type was %s, got %s'
                % (name, expected_type, prep_html(type(variable)))
            )
    else:
        if not isinstance(variable, expected_type) \
                and not isinstance(variable, type(None)):
            raise TypeError(
                'Expected %s type was %s or None, got %s'
                % (name, expected_type, prep_html(type(variable)))
            )


def check_input_args(args, valid_args):
    """
    Checks that given args are allowed. Raises ValueError or TypeError as
    appropriate if provided arguments are not valid.

    :param args: (dict) arguments to check.

    :param valid_args: (dict) arguments that are expected and their type.

    :return: No return
    """
    if not isinstance(args, dict):
        raise TypeError("Arguments provided in invalid format")

    for key, arg in args.items():
        if key not in valid_args:
            raise ValueError(
                "Unsupported argument %s. Valid are: %s. "
                % (key, list(valid_args.keys()))
            )
        if not isinstance(arg, valid_args[key]):
            raise TypeError(
                'Argument %s is in an unexpected format. Expected %s but got '
                '%s' % (key, valid_args[key], prep_html(type(arg)))
            )


def valid_string(variable, name, valid_chars):
    """
    Checks that all characters in a given string are present in a provided
    list of characters. Will raise an ValueError if unexpected character is
    encountered.

    :param variable: (str) variable to check.

    :param name: (str) name of variable to check. Only used to clarify debug
    messages.

    :param valid_chars: (str) collection of valid characters.

    :return: No return.
    """
    check_input(variable, str, name)
    check_input(valid_chars, str, 'valid_chars')

    for char in variable:
        if char not in valid_chars:
            raise ValueError(
                "Invalid character %s in %s '%s'. Only valid characters are: "
                "%s" % (char, name, variable, valid_chars)
            )


def valid_dir_path(path, name):
    """
    Checks that a given string is a valid path. Raises ValueError if not a
    valid path.

    :param path: (str) path to check.

    :param name: (str) name of variable to check. Only used to clarify debug
    messages.

    :return: No return.
    """
    check_input(path, str, name)

    valid_chars = \
        CHAR_NUMERIC + CHAR_UPPERCASE + CHAR_LOWERCASE + '-_' + os.path.sep

    for char in path:
        if char not in valid_chars:
            raise ValueError(
                'Invalid character %s in string %s for variable %s. Only '
                'valid characters are %s' % (char, path, name, valid_chars)
            )


def dir_exists(path, create=False):
    '''
    Checks a given path exists and is a directory. Raises a ValueError if the
    path either does not exist or is not a directory.

    :param path: (str) the path to check

    :param create: (bool) toggle to create dir if it does not exist. Default
    is false

    :return: (no return)
    '''
    if not os.path.exists(path):
        if create:
            os.mkdir(path)
        else:
            raise ValueError("Directory '%s' does not exist. " % path)
    if not os.path.isdir(path):
        raise ValueError("Path '%s' is not a directory. " % path)


def valid_file_path(path, name, extensions=None):
    """
    Checks that a given string is a valid file path. Raises ValueError if not
    a valid path.

    :param path: (str) path to check.

    :param name: (str) name of variable to check. Only used to clarify debug
    messages.

    :param extensions: (list)[optional]. List of possible extensions to
    check in path. Defaults to None. Extensions should be of the form '.txt'.

    :return: No return.
    """
    check_input(path, str, name)
    check_input(extensions, list, 'extensions', or_none=True)

    valid_chars = \
        CHAR_NUMERIC + CHAR_UPPERCASE + CHAR_LOWERCASE + '-_.' + os.path.sep

    if path.count('.') > 1:
        raise ValueError(
            "Too many '.' characters in %s path. Should only be one. " % name
        )
    if path.count('.') == 0:
        raise ValueError(
            "No file extension found in %s path. Please define one. " % name
        )

    if extensions:
        extension = path[path.index('.'):]
        if extension not in extensions:
            raise ValueError(
                '%s is not a supported format for variable %s. Please only '
                'use one of the following: %s. '
                % (extension, name, extensions)
            )

    for char in path:
        if char not in valid_chars:
            raise ValueError(
                'Invalid character %s in string %s for variable %s. Only '
                'valid characters are %s' % (char, path, name, valid_chars)
            )


def valid_param_sweep(to_test, name):
    """
    Checks that a given dict is a valid Pattern parameter sweep definition.
    Raises ValueError if a problem is encountered.

    :param to_test: (dict) The dictionary to test.

    :param name: (str) The name of the given dictionary. Used for ease of
    debugging.

    :return: No return.
    """
    check_input(to_test, dict, 'parameter sweep')
    check_input(name, str, 'parameter sweep name')
    valid, msg = is_valid_dict(
        to_test,
        VALID_SWEEP_MIN,
        VALID_SWEEP_OPTIONAL,
        'parameter sweep',
        MEOW_MODE,
        strict=True
    )

    if not valid:
        raise ValueError(msg)

    if not isinstance(to_test[SWEEP_START], type(to_test[SWEEP_STOP])) or \
            not isinstance(to_test[SWEEP_START], type(to_test[SWEEP_JUMP])):
        raise ValueError(
            'All parameter sweep values should be of the same type. Found '
            'types were start: %s, stop: %s, and jump: %s'
            % (prep_html(type(to_test[SWEEP_START])),
               prep_html(type(to_test[SWEEP_STOP])),
               prep_html(type(to_test[SWEEP_JUMP])))
        )

    # Try to check that this loop is not infinite
    if to_test[SWEEP_JUMP] == 0:
        raise ValueError(
            'Cannot create parameter sweep with a jump value of zero, as '
            'this would create an infinite loop'
        )
    elif to_test[SWEEP_JUMP] > 0:
        if not to_test[SWEEP_STOP] > to_test[SWEEP_START]:
            raise ValueError(
                'Cannot create parameter sweep with a positive jump value '
                'where the end point is smaller than the start. '
            )
    elif to_test[SWEEP_JUMP] < 0:
        if not to_test[SWEEP_STOP] < to_test[SWEEP_START]:
            raise ValueError(
                'Cannot create parameter sweep with a negative jump value '
                'where the end point is larger than the start. '
            )


def valid_recipe_name(name):
    '''
    Validates that a given name is a valid recipe name.

    :param name: (str) The name to test.

    :return: No return
    '''
    valid_string(
        name,
        'recipe name',
        CHAR_UPPERCASE
        + CHAR_LOWERCASE
        + CHAR_NUMERIC
        + CHAR_LINES
    )


def valid_pattern_name(name):
    '''
    Validates that a given name is a valid pattern name.

    :param name: (str) The name to test.

    :return: No return
    '''
    valid_string(
        name,
        'pattern name',
        CHAR_UPPERCASE
        + CHAR_LOWERCASE
        + CHAR_NUMERIC
        + CHAR_LINES
    )


def is_valid_dict(to_test, required_args, optional_args, name, paradigm,
                  strict=False):
    """
    Validates that a given dict has the expected arguments.

    :param to_test: (dict) the dictionary whose arguments are to be checked.

    :param required_args: (dict) A dictionary of expected arguments and the
    types of those arguments. Check will fail if all of these are not provided.

    :param optional_args: (dict) A dictionary of possible arguments and the
    types of those arguments. These will be type checked if provided, but are
    not necessary for a 'to_test' dict to be valid.

    :param name: (str) The name of this dict type. Used for debugging messages.

    :param paradigm: (str) The paradigm the tested dict is operating within.
    Only used for debugging messages.

    :param strict: (bool)[optional] Option to be strict about arguments. If
    True then any extra arguments that have been provided will fail. Default
    is False.

    :return: (Tuple(bool, str)) First value is boolean. True = to_test
    is valid, False = to_test is not valid. Second value is feedback
    string and will be empty if first value is True.
    """

    if not to_test:
        return False, 'A %s %s was not provided. ' % (paradigm, name)

    if not isinstance(to_test, dict):
        return False, \
               'The %s %s was incorrectly formatted. Should be a dict, but ' \
               '%s is a %s' \
               % (paradigm, name, to_test, prep_html(type(to_test)))

    message = 'The %s %s %s had an incorrect structure, ' \
              % (paradigm, name, to_test)
    for key, value in required_args.items():
        if key not in to_test:
            message += 'it is missing key %s. ' % key
            return False, message
        if isinstance(value, list):
            if type(to_test[key]) not in value:
                message += \
                    ' %s is expected to have types %s but actually has %s. ' \
                    % (key, prep_html(value), prep_html(type(to_test[key])))
                return False, message
        else:
            if not isinstance(to_test[key], value):
                message += \
                    ' %s is expected to have type %s but actually has %s. ' \
                    % (key, prep_html(value), prep_html(type(to_test[key])))
                return False, message

    for key, value in optional_args.items():
        if key in to_test:
            if isinstance(value, list):
                if type(to_test[key] not in value):
                    message += \
                        ' %s is expected to have types %s but actually has ' \
                        '%s. ' \
                        % (to_test[key], prep_html(value),
                           prep_html(type(to_test[key])))
                    return False, message
            else:
                if not isinstance(to_test[key], value):
                    message += \
                        ' %s is expected to have type %s but actually has ' \
                        '%s. ' \
                        % (to_test[key], prep_html(value),
                           prep_html(type(to_test[key])))
                    return False, message

    if strict:
        for key in to_test.keys():
            if key not in required_args and key not in optional_args:
                message += ' contains extra key %s' % key
                return False, message
    return True, ''


def is_valid_pattern_dict(to_test, strict=False):
    """
    Validates that the passed dictionary can be used to create a new Pattern
    object.

    :param: to_test: (dict) object to be tested.

    :param strict: (bool)[optional] Option to be strict about arguments. If
    True then any extra arguments that have been provided will fail. Default
    is False.

    :return: (Tuple(bool, str)) First value is boolean. True = to_test
    is Pattern, False = to_test is not Pattern. Second value is feedback
    string and will be empty if first value is True.
    """

    valid, msg = is_valid_dict(
        to_test,
        VALID_PATTERN_MIN,
        VALID_PATTERN_OPTIONAL,
        PATTERN_NAME,
        MEOW_MODE,
        strict=strict
    )

    if not valid:
        return False, msg

    if not to_test[TRIGGER_PATHS]:
        return False, "%s invalid: %s. Must be defined" \
               % (TRIGGER_PATHS, to_test[TRIGGER_PATHS])

    if not to_test[INPUT_FILE]:
        return False, "%s invalid: %s. Must be defined" \
               % (INPUT_FILE, to_test[INPUT_FILE])

    if TRIGGER_RECIPES not in to_test:
        return False, "'trigger_recipes' key was not in %s. " \
               % str(list(to_test.keys()))
    if not isinstance(to_test[TRIGGER_RECIPES], dict):
        return False, \
               "Trigger id's have not be stored in the correct format. " \
               "Expected dict but got %s." \
               % prep_html(type(to_test['trigger_recipes']))

    for trigger_id, trigger in to_test[TRIGGER_RECIPES].items():
        if not isinstance(trigger_id, str):
            return False, "Trigger id %s is a %s, not the expected str." \
                   % (str(trigger_id), prep_html(type(trigger_id)))
        if not isinstance(trigger, dict):
            return False, "Trigger %s is a %s, not the expected dict." \
                   % (str(trigger), prep_html(type(trigger)))

        if not trigger:
            return False, "Trigger is empty. Should contain at least a " \
                          "single recipe"

        for id, recipe in trigger.items():
            if not isinstance(id, str):
                return False, "Recipe id %s is a %s, not the expected str." \
                       % (str(id), prep_html(type(id)))
            valid, msg = is_valid_recipe_dict(recipe)
            if not valid:
                return False, msg

    return True, ''


def is_valid_recipe_dict(to_test, strict=False):
    """
    Validates that the passed dictionary expresses a meow recipe.

    :param to_test: (dict) A dictionary, hopefully expressing a meow recipe

    :param strict: (bool)[optional] Option to be strict about arguments. If
    True then any extra arguments that have been provided will fail. Default
    is False.

    :return: (function call to 'is_valid_dict'). Returns a function call to
    'is_valid_dict'.
    """

    # Note that recipe may be an empty dict if a recipe has not yet been
    # registered on the mig
    if isinstance(to_test, dict) and not to_test:
        return True, ''

    return is_valid_dict(
        to_test,
        VALID_RECIPE_MIN,
        VALID_RECIPE_OPTIONAL,
        RECIPE_NAME,
        MEOW_MODE,
        strict=strict
    )


def is_valid_workflow_dict(to_test, strict=False):
    """
    Validates that the passed dictionary expresses a cwl workflow.

    :param to_test: (dict) A dictionary, hopefully expressing a cwl workflow

    :param strict: (bool)[optional] Option to be strict about arguments. If
    True then any extra arguments that have been provided will fail. Default
    is False.

    :return: (Tuple(bool, str)) First value is boolean. True = to_test
    is workflow, False = to_test is not workflow. Second value is feedback
    string and will be empty if first value is True.
    """
    valid, msg = is_valid_dict(
        to_test,
        VALID_WORKFLOW_MIN,
        VALID_WORKFLOW_OPTIONAL,
        WORKFLOW_NAME,
        CWL_MODE,
        strict=strict
    )

    if not valid:
        return False, msg

    if to_test[CWL_CLASS] != CWL_CLASS_WORKFLOW:
        msg = "%s class is '%s' not %s" \
              % (WORKFLOW_NAME, to_test[CWL_CLASS], CWL_CLASS_WORKFLOW)
        return False, msg

    return True, ''


def is_valid_step_dict(to_test, strict=False):
    """
    Validates that the passed dictionary expresses a cwl step.

    :param to_test: (dict) A dictionary, hopefully expressing a cwl step

    :param strict: (bool)[optional] Option to be strict about arguments. If
    True then any extra arguments that have been provided will fail. Default
    is False.

    :return: (Tuple(bool, str)) First value is boolean. True = to_test
    is step, False = to_test is not step. Second value is feedback
    string and will be empty if first value is True.
    """
    valid, msg = is_valid_dict(
        to_test,
        VALID_STEP_MIN,
        VALID_STEP_OPTIONAL,
        STEP_NAME,
        CWL_MODE,
        strict=strict
    )

    if not valid:
        return False, msg

    if to_test[CWL_CLASS] != CWL_CLASS_COMMAND_LINE_TOOL:
        return False, "%s class is '%s' not %s" \
               % (STEP_NAME, to_test[CWL_CLASS], CWL_CLASS_COMMAND_LINE_TOOL)

    return True, ''


def is_valid_setting_dict(to_test, strict=False):
    """
    Validates that the passed dictionary expresses cwl arguments.

    :param to_test: (dict) A dictionary, hopefully expressing cwl arguments

    :param strict: (bool)[optional] Option to be strict about arguments. If
    True then any extra arguments that have been provided will fail. Default
    is False.

    :return: (function call to 'is_valid_dict'). Returns a function call to
    'is_valid_dict'.
    """
    return is_valid_dict(
        to_test,
        VALID_SETTING_MIN,
        VALID_SETTING_OPTIONAL,
        VARIABLES_NAME,
        CWL_MODE,
        strict=strict
    )


def prep_html(prep):
    """
    Helper function to strip the pointy brackets out of type strings so that
    their contents appears in html

    :param prep: (type) or (list) An object type, or a list of object types

    :return: (str) The finalised string
    """
    if isinstance(prep, list):
        for elem in prep:
            if not isinstance(elem, type):
                raise TypeError(
                    "'prep_html given incorrect format %s when expected 'type'"
                    % prep_html(type(elem))
                )
    else:
        if not isinstance(prep, type):
            raise TypeError(
                "'prep_html given incorrect format %s when expected 'type'"
                % prep_html(type(prep))
            )

    string = str(prep)
    string = string.replace('>', '')
    string = string.replace('<', '')

    return string
