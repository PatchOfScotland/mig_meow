
import ipywidgets as widgets
import time

from IPython.display import display

from .validation import check_input
from .constants import VGRID_READ, VGRID_QUEUE_OBJECT_TYPE,\
    VGRID_CREATE, VGRID_UPDATE, VGRID_JOB_OBJECT_TYPE, \
    OBJECT_TYPE
from .logging import create_monitor_logfile, write_to_log
from .mig import vgrid_job_json_call


MRSL_VGRID = 'VGRID'
MRSL_JOB_ID = 'JOB_ID'
MRSL_JOB_STATUS = 'STATUS'
MRSL_JOB_RECEIVED_TIME = 'RECEIVED_TIMESTAMP'
MRSL_JOB_VGRID = 'VGRID'
MRSL_JOB_EXECUTE = 'EXECUTE'
MRSL_JOB_EXECUTABLES = 'EXECUTABLES'
MRSL_JOB_INPUTFILES = 'INPUTFILES'
MRSL_JOB_OUTPUTFILES = 'OUTPUTFILES'
MRSL_JOB_NAME = 'JOBNAME'
MRSL_JOB_RETRIES = 'RETRIES'
MRSL_JOB_RUNTIMEENVIROMENT = 'RUNTIMEENVIRONMENT'
MRSL_JOB_ENVIROMENT = 'ENVIRONMENT'
MRSL_JOB_VERIFYFILES = 'VERIFYFILES'
MRSL_JOB_DISK = 'DISK'
MRSL_JOB_JOBTYPE = 'JOBTYPE'
MRSL_JOB_RESOURCE = 'RESOURCE'
MRSL_JOB_CPUTIME = 'CPUTIME'
MRSL_JOB_PLATFORM = 'PLATFORM'
MRSL_JOB_USERCERT = 'USER_CERT'
MRSL_JOB_MAXFILL = 'MAXFILL'
MRSL_JOB_MOUNT = 'MOUNT'
MRSL_JOB_MAXPRICE = 'MAXPRICE'
MRSL_JOB_PROJECT = 'PROJECT'
MRSL_JOB_SANDBOX = 'SANDBOX'
MRSL_JOB_CPUCOUNT = 'CPUCOUNT'
MRSL_JOB_NOTIFY = 'NOTIFY'
MRSL_JOB_NODECOUNT = 'NODECOUNT'
MRSL_JOB_ARCHITECTURE = 'ARCHITECTURE'
MRSL_JOB_MEMORY = 'MEMORY'
MRSL_JOB_QUEUED_TIME = 'QUEUED_TIMESTAMP'
MRSL_JOB_CANCELED_TIME = 'CANCELED_TIMESTAMP'

JOB_QUEUE_KEYS = {
    MRSL_JOB_ID: 'Job ID',
    MRSL_JOB_STATUS: 'Status',
    MRSL_JOB_RECEIVED_TIME: 'Created at'
}

JOB_CORE_DISPLAY_KEYS = {
    MRSL_JOB_ID: 'Job ID',
    MRSL_JOB_STATUS: 'Status',
    MRSL_JOB_RECEIVED_TIME: 'Created at',
    MRSL_JOB_VGRID: 'Vgrid',
    MRSL_JOB_EXECUTE: 'Execute',
    MRSL_JOB_INPUTFILES: 'Input files',
    MRSL_JOB_EXECUTABLES: 'Executable files',
    MRSL_JOB_OUTPUTFILES: 'Output files',
}

JOB_KEYS = [
    MRSL_JOB_ID,
    MRSL_JOB_STATUS,
    MRSL_JOB_RECEIVED_TIME,
    MRSL_JOB_VGRID,
    MRSL_JOB_EXECUTE,
    MRSL_JOB_EXECUTABLES,
    MRSL_JOB_INPUTFILES,
    MRSL_JOB_OUTPUTFILES,
    MRSL_JOB_NAME,
    MRSL_JOB_RETRIES,
    MRSL_JOB_RUNTIMEENVIROMENT,
    MRSL_JOB_ENVIROMENT,
    MRSL_JOB_VERIFYFILES,
    MRSL_JOB_DISK,
    MRSL_JOB_JOBTYPE,
    MRSL_JOB_RESOURCE,
    MRSL_JOB_CPUTIME,
    MRSL_JOB_PLATFORM,
    MRSL_JOB_USERCERT,
    MRSL_JOB_MAXFILL,
    MRSL_JOB_MOUNT,
    MRSL_JOB_MAXPRICE,
    MRSL_JOB_PROJECT,
    MRSL_JOB_SANDBOX,
    MRSL_JOB_CPUCOUNT,
    MRSL_JOB_NOTIFY,
    MRSL_JOB_NODECOUNT,
    MRSL_JOB_ARCHITECTURE,
    MRSL_JOB_MEMORY,
    MRSL_JOB_QUEUED_TIME,
    MRSL_JOB_CANCELED_TIME
]

SUBMISSION_JOB_KEYS = [
    MRSL_JOB_VGRID,
    MRSL_JOB_EXECUTE,
    MRSL_JOB_EXECUTABLES,
    MRSL_JOB_INPUTFILES,
    MRSL_JOB_OUTPUTFILES,
    MRSL_JOB_NAME,
    MRSL_JOB_RETRIES,
    MRSL_JOB_RUNTIMEENVIROMENT,
    MRSL_JOB_ENVIROMENT,
    MRSL_JOB_VERIFYFILES,
    MRSL_JOB_DISK,
    MRSL_JOB_JOBTYPE,
    MRSL_JOB_RESOURCE,
    MRSL_JOB_CPUTIME,
    MRSL_JOB_PLATFORM,
    MRSL_JOB_USERCERT,
    MRSL_JOB_MAXFILL,
    MRSL_JOB_MOUNT,
    MRSL_JOB_MAXPRICE,
    MRSL_JOB_PROJECT,
    MRSL_JOB_SANDBOX,
    MRSL_JOB_CPUCOUNT,
    MRSL_JOB_NOTIFY,
    MRSL_JOB_NODECOUNT,
    MRSL_JOB_ARCHITECTURE,
    MRSL_JOB_MEMORY
]

SELECTION_START = 'START'
SELECTION_END = 'END'
SELECTION_MAX = 'MAX'
LOWER = 'lower'
UPPER = 'upper'
TOP_BAR = 'top_bar'


# class PollingThread(threading.Thread):
#     """
#     Separate thread used to update the monitor widget by polling data from
#     MiG job queue.
#     """
#     # TODO replace this methodology.
#     def __init__(self, monitor_widget, stop_flag, timer):
#         """
#         Constructor for PollingThread.
#
#         :param monitor_widget: (MonitorWidget) The widget to poll for.
#
#         :param stop_flag: (Event) A flag denoting if the polling should
#         continue or not.
#
#         :param timer: (int) How often to poll, in seconds.
#         """
#         threading.Thread.__init__(self)
#         self.monitor_widget = monitor_widget
#         self.stop_flag = stop_flag
#         self.timer = timer
#
#     def run(self):
#         """
#         Run function for PollingThread, which will start the thread. Until it
#         is flagged to stop this will continue forever, and ask the monitor
#         widget to update periodically, according to the timer given.
#
#         :return: No return.
#         """
#         while not self.stop_flag.wait(3):
#             self.monitor_widget.update_queue_display()


class MonitorWidget:
    """
    Jupyter widget for displaying a MiG job queue. Some basic interactions
    such as cancelling or resubmitting can also be performed. Will update
    periodically.
    """
    def __init__(self, vgrid, timer=60, displayed_jobs=30, debug=True):
        """
        Constructor for MonitorWidget.

        :param vgrid: (str) The VGrid to connect to.

        :param timer: (int)[optional] How often the widget should update. If
        lower than 60, will be changed to 60. Default is 60.

        :param displayed_jobs: (int)[optional] How many jobs to display per
        page. Default is 30.

        :param debug: (bool)[optional] Flag for if the widget is running in
        debug mode. Default value is True.
        """

        self.logfile = create_monitor_logfile(debug)

        check_input(vgrid, str, 'vgrid')
        self.vgrid = vgrid
        check_input(timer, int, 'timer')
        if timer < 60:
            timer = 60
        self.timer = timer

        self.monitor_display_area = widgets.Output()
        self.current_queue_selection = {}
        self.displayed_jobs = displayed_jobs
        self.job_count = 0
        self.jobs = {}
        self.widgets = {}

        # self.__stop_polling = threading.Event()
        self.__start_queue_display(None)

    def __start_queue_display(self, button):
        """
        Starts displaying queue information. Creates and starts a
        PollingThread to keep the display updating automatically.

        :return: No return.
        """
        self.update_queue_display()
        # polling_thread = PollingThread(self, self.__stop_polling, self.timer)
        # polling_thread.daemon = True
        # polling_thread.start()

    def __stop_queue_display(self):
        """
        Sets a flag to stop the PollingThread and prevent an automatic
        update.

        :return: No return.
        """
        # self.__stop_polling.set()

    def update_queue_display(self):
        """
        Sends a request for an up to date job_queue from the vgrid. If a valid
        response is returned then the job display is updated.

        :return: No return.
        """
        #  TODO accommodate this call not working
        valid, result = self.get_vgrid_queue()

        if valid:
            self.jobs = result
            self.__display_job_queue()

    def get_vgrid_queue(self):
        """
        Retrieves a dictionary of jobs from the MiG Vgrid via JSON request.

        :return: (Tuple (bool, str or dict)) If a invalid JSON response is
        received then an tuple of first value False, with a explanatory error
        message as second value is returned. Otherwise, a tuple is returned
        with a first value of True, and with the dictionary of jobs as the
        second value.
        """
        attributes = {}
        _, response, _ = vgrid_job_json_call(
            self.vgrid,
            VGRID_READ,
            VGRID_QUEUE_OBJECT_TYPE,
            attributes,
            logfile=self.logfile
        )

        if response['object_type'] == 'job_dict':
            jobs = response['jobs']
            write_to_log(
                self.logfile,
                'get_vgrid_queue',
                'Got jobs: %s' % jobs.keys())
            return True, jobs
        else:
            msg = 'something went wrong with retrieving the queue. '
            write_to_log(
                self.logfile,
                'get_vgrid_queue',
                '%s: %s' % (msg, response)
            )
            if self.logfile:
                msg += \
                    "You can check the logfile '%s' for details" % self.logfile
            return False, msg

    def __display_job_queue(self, *args):
        """
        Creates a job queue display within the widget. This will display all
        jobs in the queue in the defined range. A top bar of buttons is also
        created.

        :return: No return.
        """
        # first time run through
        if not self.current_queue_selection:
            self.current_queue_selection[SELECTION_MAX] = len(self.jobs)
            self.current_queue_selection[SELECTION_START] = 1

            self.current_queue_selection[SELECTION_END] = self.displayed_jobs
            if len(self.jobs) < self.displayed_jobs:
                self.current_queue_selection[SELECTION_END] = len(self.jobs)
        # got new job selection
        elif self.job_count != len(self.jobs):
            self.current_queue_selection[SELECTION_MAX] = len(self.jobs)
            self.current_queue_selection[SELECTION_START] = \
                self.widgets[LOWER].value
            self.current_queue_selection[SELECTION_END] = \
                self.widgets[UPPER].value
            if len(self.jobs) < self.widgets[UPPER].value:
                self.current_queue_selection[SELECTION_END] = len(self.jobs)
        # any other time
        else:
            self.current_queue_selection[SELECTION_MAX] = len(self.jobs)
            self.current_queue_selection[SELECTION_START] = \
                self.widgets[LOWER].value
            self.current_queue_selection[SELECTION_END] = \
                self.widgets[UPPER].value

        if TOP_BAR not in self.widgets or self.job_count != len(self.jobs):
            lower = widgets.BoundedIntText(
                value=self.current_queue_selection[SELECTION_START],
                min=1,
                max=self.current_queue_selection[SELECTION_END],
                step=1,
                disabled=False,
                layout=widgets.Layout(width='60px')
            )
            lower.observe(self.__display_job_queue, names='value')
            upper = widgets.BoundedIntText(
                value=self.current_queue_selection[SELECTION_END],
                min=self.current_queue_selection[SELECTION_START],
                max=self.current_queue_selection[SELECTION_MAX],
                step=1,
                disabled=False,
                layout=widgets.Layout(width='60px')
            )
            upper.observe(self.__display_job_queue, names='value')

            self.widgets[UPPER] = upper
            self.widgets[LOWER] = lower
            widgets.link((lower, 'value'), (upper, 'min'))
            widgets.link((upper, 'value'), (lower, 'max'))

            top_bar_items = [
                widgets.Label('Displaying '),
                lower,
                widgets.Label(' to '),
                upper,
                widgets.Label(' of %s total jobs for VGrid %s'
                              % (len(self.jobs), self.vgrid))
            ]
            top_bar = widgets.HBox(
                top_bar_items
            )
            self.widgets[TOP_BAR] = top_bar

        grid_items = []
        for _, v in JOB_QUEUE_KEYS.items():
            grid_items.append(
                widgets.Label(
                    value=v,
                    layout=widgets.Layout(width='100%')
                )
            )
        grid_items.append(widgets.Label(''))

        sorted_jobs = sorted(
            self.jobs.items(),
            key=lambda k_v: k_v[1][MRSL_JOB_RECEIVED_TIME],
            reverse=True
        )

        lower_limit = int(self.widgets[LOWER].value) - 1
        if lower_limit < 0:
            lower_limit = 0
        cut_list = sorted_jobs[lower_limit:self.widgets[UPPER].value]
        for job in cut_list:
            grid_items += self.__get_job_display_row(job[1])

        grid = widgets.GridBox(
            grid_items,
            layout=widgets.Layout(
                grid_template_columns="repeat(%s, 25%%)"
                                      % str(len(JOB_QUEUE_KEYS) + 1)
            )
        )
        queue_display = widgets.VBox(
            [
                self.widgets[TOP_BAR],
                grid
            ]
        )

        self.monitor_display_area.clear_output(wait=True)
        with self.monitor_display_area:
            display(queue_display)
        self.job_count = len(self.jobs)

    def __get_job_display_row(self, job):
        """
        Creates a table row displaying a job and its most important details,
        along with buttons to interact with the job directly.

        :param job: (str) The job id for the row.

        :return: (list) A list of all widget elements created for the row.
        """
        row_items = []
        job_id = job[MRSL_JOB_ID]
        for key in JOB_QUEUE_KEYS.keys():
            row_items.append(
                widgets.Label(
                    value=job[key],
                    layout=widgets.Layout(width='100%')
                )
            )
        button_items = []
        for button_dict in self.__get_job_interaction_buttons(job):
            button_args = button_dict['args']
            button_func = button_dict['func']
            button = widgets.Button(
                value=button_args['value'],
                description=button_args['description'],
                button_style=button_args['button_style'],
                tooltip=button_args['tooltip'],
                icon=button_args['icon'],
                disabled=button_args['disabled']
            )

            button.on_click(lambda b, f=button_func: f(b, job_id))
            button_items.append(button)

        buttons = widgets.HBox(button_items)
        row_items.append(buttons)
        return row_items

    def __get_job_interaction_buttons(self, job):
        """
        Creates buttons for interacting with individual jobs. A details,
        resubmit and cancel button are provided. If the job is already
        complete the cancel button is disabled.

        :param job: (str) The job id for these buttons.

        :return: (list) A list of dictionaries defining the three buttons.
        """

        disable_cancel = False
        cancel_tooltip = 'Cancel job'
        if job[MRSL_JOB_STATUS] in ['CANCELED', 'FINISHED', 'FAILED']:
            disable_cancel = True
            cancel_tooltip = 'Cannot cancel job with status  %s' % \
                             job[MRSL_JOB_STATUS].lower()

        return [
            {
                'func': self.__display_func,
                'args': {
                    'value': False,
                    'description': '',
                    'disabled': False,
                    'button_style': '',
                    'tooltip': 'Display job details',
                    'icon': 'plus'
                }
            },
            {
                'func': self.__resubmit_func,
                'args': {
                    'value': False,
                    'description': '',
                    'disabled': False,
                    'button_style': '',
                    'tooltip': 'Resubmit job',
                    'icon': 'refresh'
                }
            },
            {
                'func': self.__cancel_func,
                'args': {
                    'value': False,
                    'description': '',
                    'disabled': disable_cancel,
                    'button_style': '',
                    'tooltip': cancel_tooltip,
                    'icon': 'times'
                }
            },
        ]

    def __display_func(self, button, job_id):
        """
        'Display Job' button clicked event handler. Displays the given jobs
        details in the widget.

        :param button: (widgets.Button) The button object.

        :param job_id: (str) Id of the job to display.

        :return: No return.
        """
        self.__stop_queue_display()

        job = self.jobs[job_id]

        detail_items = [self.__back_to_queue_button()]

        for key, value in JOB_CORE_DISPLAY_KEYS.items():
            detail_items.append(
                widgets.Label("-- %s --" % value)
            )
            msg = ''
            if key in job:
                if isinstance(job[key], list):
                    for elem in job[key]:
                        msg += str(elem)
                else:
                    msg = str(job[key])
            detail_items.append(
                widgets.Label(msg)
            )
        detail_items.append(self.__back_to_queue_button())

        job_details = widgets.VBox(detail_items)

        self.monitor_display_area.clear_output(wait=True)
        with self.monitor_display_area:
            display(job_details)
        self.job_count = len(self.jobs)

    def __back_to_queue_button(self):
        """
        Creates a button to revert view to job queue.

        :return: (widgets.Button) The cancel button.
        """
        button = widgets.Button(
            value=False,
            description='',
            button_style='',
            tooltip='Go back to job queue',
            icon='backward'
        )
        # button.on_click(self.__start_queue_display)
        button.on_click(self.__display_job_queue)
        return button

    def __resubmit_func(self, button, job_id):
        """
        'Resubmit Job' button clicked event handler. Sends a JSON request to
        the MiG VGrid for the job to be ressubmitted.

        :param button: (widgets.Button) The button object.

        :param job_id: (str) The resubmitted job id.

        :return: No return.
        """

        job = self.jobs[job_id]

        attributes = {}
        for key, value in job.items():
            if key in SUBMISSION_JOB_KEYS and value:
                updated_values = []
                if isinstance(value, list):
                    for element in value:
                        if isinstance(element, list):
                            updated_values.append("%s=%s"
                                                  % (element[0], element[1]))
                if updated_values:
                    attributes[key] = updated_values
                else:
                    attributes[key] = value

        _, response, _ = vgrid_job_json_call(
            self.vgrid,
            VGRID_CREATE,
            VGRID_JOB_OBJECT_TYPE,
            attributes
        )

    def __cancel_func(self, button, job_id):
        """
        'Cancel Job' button clicked event handler. Sends a JSON request to
        the MiG VGrid for the job to be cancelled.

        :param button: (widgets.Button) The button object.

        :param job_id: (str) The cancelled job id.

        :return: No return.
        """
        attributes = {
            MRSL_JOB_ID: job_id,
            MRSL_JOB_STATUS: 'CANCELED'
        }
        _, response, _ = vgrid_job_json_call(
            self.vgrid,
            VGRID_UPDATE,
            VGRID_JOB_OBJECT_TYPE,
            attributes
        )

        if OBJECT_TYPE in response and response[OBJECT_TYPE] == 'text':
            self.jobs[job_id][MRSL_JOB_STATUS] = 'CANCELED'

    def display_widget(self):
        """
        Returns the widget in a display ready state.

        :return: (widgets.Output) The output are to be displayed ina  notebook.
        """
        return self.monitor_display_area


def update_monitor(monitor):
    while(True):
        monitor.update_queue_display()
        time.sleep(15)
