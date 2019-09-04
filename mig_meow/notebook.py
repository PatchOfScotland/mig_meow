
import os

from .constants import FILES_DIR


# TODO implement this in a more robust way
def get_containing_vgrid():
    """
    Gets the name of a VGrid, if the notebook is stored within it. If no
    VGrid can be identified then a LookupError is raised.

    :return: returns name of vgrid.
    """
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
