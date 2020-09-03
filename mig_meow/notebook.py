
import threading

from .localrunner import WorkflowRunner
from .workflow_widget import WorkflowWidget
from .monitor_widget import MonitorWidget, update_monitor


def workflow_widget(**kwargs):
    """
    Creates and displays a widget for workflow definitions. Passes any given
    keyword arguments to the WorkflowWidget constructor.

    :return: (function call to 'WorkflowWidget.display_widget)
    """

    widget = WorkflowWidget(**kwargs)

    return widget.display_widget()


def monitor_widget(**kwargs):
    """
    Creates and displays a widget for monitoring Vgrid job queues. Passes
    any given keyword arguments to the MonitorWidget constructor.

    :return: (function call to 'MonitorWidget.display_widget)
    """

    widget = MonitorWidget(**kwargs)

    monitor_thread = threading.Thread(
        target=update_monitor,
        args=(widget,),
        daemon=True
    )

    monitor_thread.start()

    return widget.display_widget()


def start_local_workflow(
        vgrid_name, patterns, recipes, workers, warning=True,
        print_logging=True, start_workers=True, daemon=False):
    if warning:
        print("This function is intended only as an illustration of MEOW "
              "functionality, and should therefore be used with caution. It "
              "may behave unexpectedly, is not thread safe, has no protection "
              "for data being overridden, and very little error handling. For "
              "proper workflow functionality please use the MiG integration")

    runner = WorkflowRunner(
        vgrid_name,
        workers,
        patterns=patterns,
        recipes=recipes,
        start_workers=start_workers,
        print_logging=print_logging,
        daemon=daemon
    )

    return runner
