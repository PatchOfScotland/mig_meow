
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
