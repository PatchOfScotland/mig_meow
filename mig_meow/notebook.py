
import os
import json

from .input import check_input
from .constants import PATTERNS_DIR, RECIPES_DIR, FILES_DIR, NAME
from .pattern import Pattern
from .recipe import is_valid_recipe_dict


def is_in_vgrid():
    """
    Throws an exception if the current notebook is not in an expected vgrid
    structure.
    """
    # TODO implement this in a more robust way
    message = 'Notebook is not currently in a recognised vgrid. Notebook ' \
              'should be in the top vgrid directory for correct functionality.'

    path = os.getcwd().split(os.sep)

    if len(path) < 2:
        raise Exception(message + ' Current working path is not long enough '
                                  'to be correct.')

    possible_vgrid_files_home = path[len(path)-2]

    if possible_vgrid_files_home != FILES_DIR:
        raise Exception(message + ' Notebook is not contained in correct '
                                  'directory')

    return True


def get_containing_vgrid():
    # TODO implement this in a more robust way

    message = 'Notebook is not currently in a recognised vgrid. Notebook ' \
              'should be stored within a vgrid to interact with it. '

    path = os.getcwd().split(os.sep)

    if FILES_DIR in path:
        index = path.index(FILES_DIR)
        vgrid_index = index + 1
        if vgrid_index >= len(path):
            raise LookupError(message)
        return path[vgrid_index]
    else:
        raise LookupError(message)

# def __check_export_location(location, source, export_type):
#     if os.path.exists(location):
#         file_name = location.replace(EXPORT_DIR + os.path.sep, '')
#         raise Exception('Another export sharing the same name %s currently is '
#                         'waiting to be imported into the MiG. Either rename '
#                         'the %s to create a different %s, or wait '
#                         'for the existing import to complete. If the problem '
#                         'persists, please check the MiG is still running '
#                         'correctly' % (file_name, source, export_type))
#
#
# def __prepare_recipe_export(notebook):
#     """
#     Checks that a recipe note book exists and is not already staged for
#     import into the mig.
#
#     Takes 1 argument, 'notebook' being the path to a jupyter notebook. File
#     extension does not need to be included.
#
#     Returns the filename of the notebook and the destination for the notebook
#     to be copied to.
#     """
#     if NOTEBOOK_EXTENSION not in notebook:
#         if '.' in notebook:
#             extension = notebook[notebook.rfind('.'):]
#             raise Exception('%s is not a supported format. Only jupyter '
#                             'notebooks may be exported as recipes.'
#                             % extension)
#         notebook += NOTEBOOK_EXTENSION
#
#     if not os.path.exists(notebook):
#         raise Exception('Notebook was identified as %s, but this '
#                         'appears to not exist' % notebook)
#
#     if not os.path.exists(EXPORT_DIR):
#         os.mkdir(EXPORT_DIR)
#
#     recipe_name = notebook
#     if os.path.sep in notebook:
#         recipe_name = notebook[notebook.rfind(os.path.sep)+1:]
#
#     destination = os.path.join(EXPORT_DIR, recipe_name)
#     __check_export_location(destination, 'notebook', 'recipe')
#
#     return recipe_name, destination
#
#
# def export_recipe(notebook):
#     """
#     Sends a copy of the given notebook to the MiG. This will only run
#     if there is not already a file awaiting import of the same name.
#
#     Takes 1 argument, 'notebook' which is the path to a jupyter notebook.
#     File extension does not need to be included.
#     """
#     is_in_vgrid()
#     check_input(notebook, str)
#     name, destination = __prepare_recipe_export(notebook)
#     copyfile(notebook, destination)
#
#
# def export_recipes(notebooks):
#     """
#     Sends a copy of the given notebooks to the MiG. This will only run
#     if there is not already a file awaiting import of the same name.
#
#     Takes 1 argument, 'notebooks' which is a list of paths to jupyter
#     notebooks. File extensions do not need to be included.
#     """
#     is_in_vgrid()
#     check_input(notebooks, list)
#     valid_notebooks = []
#     for notebook in notebooks:
#         check_input(notebook, str)
#         name, destination = __prepare_recipe_export(notebook)
#         for valid_name, _ in valid_notebooks:
#             if valid_name == name:
#                 raise Exception('Attempting to copy multiple recipes of the '
#                                 'same name :%s' % name)
#         valid_notebooks.append((notebook, destination))
#
#     for notebook, destination in valid_notebooks:
#         copyfile(notebook, destination)
#
#
# def export_pattern(pattern):
#     """
#     Sends a patterns to the MiG. This will only run if the MiG
#     is not currently waiting to process an existing pattern definition.
#
#     Takes 1 argument, 'pattern' which is a pattern object.
#     """
#     is_in_vgrid()
#     check_input(pattern, Pattern)
#     status, message = pattern.integrity_check()
#
#     if not status:
#         raise Exception('Pattern %s is incomplete. %s' % (pattern, message))
#     if message:
#         print(message)
#
#     if not os.path.exists(EXPORT_DIR):
#         os.mkdir(EXPORT_DIR)
#
#     destination = os.path.join(EXPORT_DIR, pattern.name + PATTERN_EXTENSION)
#     __check_export_location(destination, 'pattern', 'pattern')
#
#     pattern_as_json = json.dumps(pattern.__dict__)
#     with open(destination, 'w') as json_file:
#         json_file.write(pattern_as_json)
#
#
# def export_patterns(patterns):
#     """
#     Sends multiple patterns to the MiG.
#
#     Takes 1 argument, 'patterns', that being a dict of patterns.
#     """
#     is_in_vgrid()
#     check_input(patterns, dict)
#     for pattern in patterns.values():
#         export_pattern(pattern)


# def retrieve_current_patterns(debug=False):
#     """
#     Will look within the expected workflow pattern directory and return a
#     dict of all found patterns. If debug is set to true will also output
#     warning messages.
#     """
#     is_in_vgrid()
#     check_input(debug, bool, 'debug')
#
#     all_patterns = {}
#     message = ''
#     if os.path.isdir(PATTERNS_DIR):
#         for path in os.listdir(PATTERNS_DIR):
#             file_path = os.path.join(PATTERNS_DIR, path)
#             if os.path.isfile(file_path):
#                 try:
#                     with open(file_path) as file:
#                         input_dict = json.load(file)
#                         pattern = Pattern(input_dict)
#                         all_patterns[pattern.name] = pattern
#                 except Exception:
#                     message += '%s is unreadable, possibly corrupt.' % path
#     else:
#         if debug:
#             return ({}, 'No patterns found to import. Is the notebook in the '
#                         'top vgrid directory?')
#         return {}
#     if debug:
#         return all_patterns, message
#     return all_patterns


# def list_current_recipes():
#     """
#     Returns a list of the names of all currently registered recipes in a vgrid
#     """
#     all_recipes = retrieve_current_recipes()
#     output = ""
#     for key in all_recipes.keys():
#         if output is not "":
#             output += ", "
#         output += key
#     return output
#
#
# def list_current_patterns():
#     """
#     Returns a list of the names of all currently registered patterns in a vgrid
#     """
#     all_patterns = retrieve_current_patterns()
#     output = ""
#     for key in all_patterns.keys():
#         if output is not "":
#             output += ", "
#         output += key
#     return output
