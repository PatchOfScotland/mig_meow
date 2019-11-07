
import os

from .constants import CHAR_LOWERCASE, CHAR_NUMERIC, CHAR_UPPERCASE, \
    VALID_PATTERN


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
            raise TypeError('Expected %s type was %s, got %s'
                            % (name, expected_type, type(variable)))
    else:
        if not isinstance(variable, expected_type) \
                and not isinstance(variable, type(None)):
            raise TypeError('Expected %s type was %s or None, got %s'
                            % (name, expected_type, type(variable)))


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
            raise ValueError("Unsupported argument %s. Valid are: %s. "
                            % (key, list(valid_args.keys())))
        if not isinstance(arg, valid_args[key]):
            raise TypeError(
                'Argument %s is in an unexpected format. Expected %s but got '
                '%s' % (key, valid_args[key], type(arg)))


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


def valid_path(path, name, extensions=None):
    """
    Checks that a given string is a valid path. Will raise an exception if it
    is not a valid path. Raises ValueError if not a valid path.

    :param path: (str) path to check.

    :param name: (str) name of variable to check. Only used to clarify debug
    messages.

    :param extensions: (list)[optional]. List of possible extensions to
    check in path. Defaults to None.

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


def is_valid_pattern_dict(to_test):
    """
    Validates that the passed dictionary can be used to create a new Pattern
    object.

    :param: to_test: (dict) object to be tested.

    :return: (Tuple(bool, str))tuple. First value is boolean. True = to_test
    is Pattern, False = to_test is not Pattern. Second value is feedback
    string and will be empty if first value is True.
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
