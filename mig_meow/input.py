
import os

from .constants import CHAR_LOWERCASE, CHAR_NUMERIC, CHAR_UPPERCASE


def check_input(variable, expected_type, name, or_none=False):
    """
    Checks if a given variable is of the expected type. May also be
    NoneType is or_none is True. Raises an exception if any issues are
    encountered.

    :param variable: variable to check type of
    :param expected_type: expected type of the provided variable
    :param name: name of the variable, used to make clearer debug messages
    :param or_none: (optional) boolean of if the variable can be unset.
    Default value is False
    :return: returns nothing
    """

    if not variable and expected_type is not bool and or_none is False:
        raise Exception('variable %s was not given' % name)

    if not expected_type:
        raise Exception('\'expected_type\' %s was not given' % expected_type)

    if not or_none:
        if not isinstance(variable, expected_type):
            raise Exception('Expected %s type was %s, got %s'
                            % (name, expected_type, type(variable)))
    else:
        if not isinstance(variable, expected_type) \
                and not isinstance(variable, type(None)):
            raise Exception('Expected %s type was %s or None, got %s'
                            % (name, expected_type, type(variable)))


def valid_string(variable, name, valid_chars):
    """
    Checks that all characters in a given string are present in a provided
    list of characters. Will raise an exception if unexpected character is
    encountered.

    :param variable: variable to check. Must be a str
    :param name: name of variable to check. Only used to clarify debug
    messages.
    :param valid_chars: collection of valid characters. Must be a str.
    :return: returns nothing
    """
    check_input(variable, str, name)
    check_input(valid_chars, str, 'valid_chars')

    # valid_chars = CHAR_NUMERIC + CHAR_UPPERCASE + CHAR_LOWERCASE + '-_'

    for char in variable:
        if char not in valid_chars:
            raise Exception("Invalid character %s in %s '%s'. "
                            "Only valid characters are: %s"
                            % (char, name, variable, valid_chars))


def valid_path(path, name, extensions=None):
    """
    Checks that a given string is a valid path Will raise an exception if it
    is not a valid path. Raises an exception if not a valid path.

    :param path: path to check. Must be a str
    :param name: name of variable to check. Only used to clarify debug
    messages.
    :param extensions: (optional). List of possible extensions to check in
    path. Defaults to None
    :return: returns nothing
    """
    check_input(path, str, name)
    check_input(extensions, list, 'extensions', or_none=True)

    valid_chars = \
        CHAR_NUMERIC + CHAR_UPPERCASE + CHAR_LOWERCASE + '-_.' + os.path.sep

    if path.count('.') > 1:
        raise Exception("Too many '.' characters in %s path. "
                        "Should only be one. " % name)
    if path.count('.') == 0:
        raise Exception("No file extension found in %s path. "
                        "Please define one. " % name)

    if extensions:
        extension = path[path.index('.'):]
        if extension not in extensions:
            raise Exception('%s is not a supported format for variable %s. '
                            'Please only use one of the following: %s. '
                            % (extension, name, extensions))

    for char in path:
        if char not in valid_chars:
            raise Exception('Invalid character %s in string %s for variable '
                            '%s. Only valid characters are %s'
                            % (char, path, name, valid_chars))
