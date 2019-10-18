
from .constants import MEOW_MODE
from .workflow_widget import WorkflowWidget
from .monitor_widget import MonitorWidget


def create_workflow_widget(**kwargs):
    # TODO update this
    """Displays a widget for workflow definitions. Can optionally take a
    predefined workflow as input"""

    widget = WorkflowWidget(**kwargs)

    return widget.display_widget()


def create_monitor_widget(**kwargs):
    # TODO update this
    """"""

    widget = MonitorWidget(**kwargs)

    return widget.display_widget()

