
import ipywidgets as widgets
import threading
import time

from IPython.display import display

from .input import check_input
from .constants import VGRID, MRSL_VGRID, VGRID_READ, VGRID_QUEUE_OBJECT_TYPE,\
    CANCEL_JOB, RESUBMIT_JOB, VGRID_CREATE
from .mig import vgrid_job_json_call


MRSL_JOB_ID = 'JOB_ID'
MRSL_JOB_STATUS = 'STATUS'
MRSL_JOB_RECEIVED_TIME = 'RECEIVED_TIMESTAMP'
MRSL_JOB_VGRID = 'VGRID'
MRSL_JOB_EXECUTE = 'EXECUTE'
MRSL_JOB_EXECUTABLES = 'EXECUTABLES'
MRSL_JOB_INPUTFILES = 'INPUTFILES'
MRSL_JOB_OUTPUTFILES = 'OUTPUTFILES'
# MRSL_JOB_NAME = 'JOBNAME'
# MRSL_JOB_RETRIES = 'RETRIES'
# MRSL_JOB_RUNTIMEENVIROMENT = 'RUNTIMEENVIRONMENT'
# MRSL_JOB_ENVIROMENT = 'ENVIRONMENT'
# MRSL_JOB_VERIFYFILES = 'VERIFYFILES'
# MRSL_JOB_DISK = 'DISK'
# MRSL_JOB_JOBTYPE = 'JOBTYPE'
# MRSL_JOB_RESOURCE = 'RESOURCE'
# MRSL_JOB_CPUTIME = 'CPUTIME'
# MRSL_JOB_PLATFORM = 'PLATFORM'
# MRSL_JOB_USERCERT = 'USER_CERT'
# MRSL_JOB_MAXFILL = 'MAXFILL'
# MRSL_JOB_MOUNT = 'MOUNT'
# MRSL_JOB_MAXPRICE = 'MAXPRICE'
# MRSL_JOB_PROJECT = 'PROJECT'
# MRSL_JOB_SANDBOX = 'SANDBOX'
# MRSL_JOB_CPUCOUNT = 'CPUCOUNT'
# MRSL_JOB_NOTIFY = 'NOTIFY'
# MRSL_JOB_NODECOUNT = 'NODECOUNT'
# MRSL_JOB_ARCHITECTURE = 'ARCHITECTURE'
# MRSL_JOB_MEMORY = 'MEMORY'
# MRSL_JOB_QUEUED_TIME = 'QUEUED_TIMESTAMP'
# MRSL_JOB_CANCELED_TIME = 'CANCELED_TIMESTAMP'

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


SELECTION_START = 'START'
SELECTION_END = 'END'
SELECTION_MAX = 'MAX'
LOWER = 'lower'
UPPER = 'upper'
TOP_BAR = 'top_bar'


class PollingThread(threading.Thread):
    def __init__(self, monitor_widget, stop_flag, timer):
        threading.Thread.__init__(self)
        self.monitor_widget = monitor_widget
        self.stop_flag = stop_flag
        self.timer = timer

    def run(self):
        while not self.stop_flag.wait(self.timer):
            self.monitor_widget.update_queue_display()


class MonitorWidget:
    # TODO extend this timer before deployment
    def __init__(self, vgrid, timer=60, displayed_jobs=30):

        check_input(vgrid, str, 'vgrid')
        self.vgrid = vgrid
        check_input(timer, int, 'timer')

        self.monitor_display_area = widgets.Output()
        self.current_queue_selection = {}
        self.displayed_jobs = displayed_jobs
        self.job_count = 0
        self.jobs = {}
        self.widgets = {}

        self.__stop_polling = threading.Event()
        self.timer = timer
        self.__start_queue_display()

    def __start_queue_display(self, *args):
        self.update_queue_display()
        polling_thread = PollingThread(self, self.__stop_polling, self.timer)
        polling_thread.daemon = True
        polling_thread.start()

    def __stop_queue_display(self):
        self.__stop_polling.set()

    def update_queue_display(self):
        self.jobs = self.get_vgrid_queue()
        self.__display_job_queue()

    def get_vgrid_queue(self):
        attributes = {}
        _, response, _ = vgrid_job_json_call(
            self.vgrid,
            VGRID_READ,
            VGRID_QUEUE_OBJECT_TYPE,
            attributes,
            print_feedback=False
        )

        if 'workflows' in response:
            jobs = response['workflows']

            return jobs
        else:
            raise Exception('something went wrong with retrieving the queue')

    def __display_job_queue(self, *args):

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
                # TODO update this so is not static
                layout=widgets.Layout(width='60px')
            )
            lower.observe(self.__display_job_queue, names='value')
            upper = widgets.BoundedIntText(
                value=self.current_queue_selection[SELECTION_END],
                min=self.current_queue_selection[SELECTION_START],
                max=self.current_queue_selection[SELECTION_MAX],
                step=1,
                disabled=False,
                # TODO update this so is not static
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

        disable_cancel = False
        cancel_tooltip = 'Cancel job'
        if job[MRSL_JOB_STATUS] in ['CANCELED', 'FINISHED']:
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
        self.__stop_queue_display()

        job = self.jobs[job_id]

        detail_items = []

        detail_items.append(self.__back_to_queue_button())
        for key, value in JOB_CORE_DISPLAY_KEYS.items():
            detail_items.append(
                widgets.Label("-- %s --" % value)
            )
            msg = ''
            if key in job:
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
        button = widgets.Button(
            value=False,
            description='',
            button_style='',
            tooltip='Go back to job queue',
            icon='backward'
        )
        button.on_click(self.__start_queue_display)
        return button

    def __resubmit_func(self, button, job_id):
        # TODO implement
        print('resubmit func for %s' % job_id)

    def __cancel_func(self, button, job_id):
        attributes = {
            MRSL_JOB_ID: job_id,
            VGRID: self.vgrid
        }
        _, response, _ = vgrid_job_json_call(
            self.vgrid,
            VGRID_CREATE,
            CANCEL_JOB,
            attributes,
            print_feedback=False
        )

        print(response)

    def display_widget(self):
        # TODO update this
        """"""
        return self.monitor_display_area
