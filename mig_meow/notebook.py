
from .workflow_widget import WorkflowWidget
from .monitor_widget import MonitorWidget


# TODO update description
def create_workflow_widget(**kwargs):
    """
    Creates and displays a widget for workflow definitions. Passes any given
    arguments to the WorkflowWidget constructor
    """

    widget = WorkflowWidget(**kwargs)

    return widget.display_widget()


# TODO update description
def create_monitor_widget(**kwargs):
    """
    Creates and displays a widget for monitoring Vgrid job queues. Passes
    any given arguments to the MonitorWidget constructor
    """

    widget = MonitorWidget(**kwargs)

    return widget.display_widget()
