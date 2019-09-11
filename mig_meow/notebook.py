
from .constants import VGRID_MODE
from .workflow_widget import WorkflowWidget


def create_widget(patterns=None, recipes=None, mode=VGRID_MODE, **kwargs):
    # TODO update this
    """Displays a widget for workflow definitions. Can optionally take a
    predefined workflow as input"""

    widget = WorkflowWidget(
        patterns=patterns,
        recipes=recipes,
        mode=mode,
        **kwargs
    )

    return widget.display_widget()

