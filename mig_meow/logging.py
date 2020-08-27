
import os
import threading

from datetime import datetime

from .constants import LOGGING_DIR, WORKFLOW_LOGFILE_NAME, \
    MONITOR_LOGFILE_NAME, RUNNER_LOGFILE_NAME

lock = threading.Lock()


def __create_logfile(mode, title):
    """
    Creates a new logfile within the logging directory.

    :param mode: (boolean) Flag for if logfile is required. If false then a
    log is not created and None is returned.

    :param title: (str) The logfile to be created.

    :return: (str or None) If the logfile is created the path of said file is
    returned. If it could not be created then None is returned.
    """
    # TODO improve this

    if not mode:
        return False

    try:
        time = str(datetime.now())
        if not os.path.exists(LOGGING_DIR):
            os.mkdir(LOGGING_DIR)
        log_filename = \
            os.path.join(LOGGING_DIR, "%s_%s.log" % (time, title))
        with open(log_filename, 'w') as logfile:
            logfile.write('Start of %s log at %s\n' % (title, time))
        return log_filename
    except Exception:
        return None


def create_workflow_logfile(debug_mode=None):
    """
    Creates a new logfile for a workflow widget.

    :param debug_mode: (boolean)[optional] flag for widget debug mode. If True
    then a log is created. If false it is not. Default is None.

    :return: (function call to __create_logfile)
    """
    return __create_logfile(debug_mode, WORKFLOW_LOGFILE_NAME)


def create_monitor_logfile(debug_mode=None):
    """
    Creates a new logfile for a monitor widget.

    :param debug_mode: (boolean)[optional] flag for widget debug mode. If True
    then a log is created. If false it is not. Default is None.

    :return: (function call to __create_logfile)
    """
    return __create_logfile(debug_mode, MONITOR_LOGFILE_NAME)


def create_localrunner_logfile(debug_mode=None):
    """
    Creates a new logfile for a local runner.

    :param debug_mode: (boolean)[optional] flag for runner debug mode. If True
    then a log is created. If false it is not. Default is None.

    :return: (function call to __create_logfile)
    """
    return __create_logfile(debug_mode, RUNNER_LOGFILE_NAME)


def write_to_log(log, anchor, entry, to_print=False):
    """
    Writes a new entry to a logfile.

    :param log: (str or None) Path to a logfile to write in. If no log is
    provided because the widget is not in debug mode then the entry is not
    written.

    :param anchor: (str) A string to help locate where this log message
    originated from. Should usually be the name of the function calling this
    function.

    :param entry: (str) Line to write to logfile.

    :param to_print: (boolean) Also print entry. Default is False

    :return: No return.
    """
    if log:
        lock.acquire()
        time = str(datetime.now())
        with open(log, 'a') as logfile:
            logfile.write("%s: %s - %s\n" % (time, anchor, entry))
        lock.release()
    if to_print:
        print("%s - %s" % (anchor, entry))
