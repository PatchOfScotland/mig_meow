
import ipywidgets as widgets
import ipydatetime

from IPython.display import display
from graphviz import Digraph

from .constants import VGRID_READ, VGRID_REPORT_OBJECT_TYPE
from .logging import create_report_logfile, write_to_log
from .mig import vgrid_report_json_call
from .validation import check_input

DEFAULT_FILENAME = 'workflow_report'
DEFAULT_EXTENSION = 'png'

SUPPORTED_EXTENSIONS = [
    DEFAULT_EXTENSION,
    'pdf'
]


class ReportWidget:
    """

    """
    def __init__(self, vgrid, debug=False, filename=DEFAULT_FILENAME,
                 extension=DEFAULT_EXTENSION, horizontal=False):
        """

        """
        self.logfile = create_report_logfile(debug)

        check_input(vgrid, str, 'vgrid')
        self.vgrid = vgrid

        check_input(filename, str, 'filename')
        self.filename = filename

        check_input(extension, str, 'format')
        if extension not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                "Invalid report extension '%s' given. Supported extensions "
                "are: %s" % (extension, SUPPORTED_EXTENSIONS)
            )
        self.extension = extension

        check_input(horizontal, bool, 'horizontal')
        self.horizontal = horizontal

        self.report = None
        self.jobs = []
        self.paths = []
        self.patterns = []
        self.recipes = []
        self.pattern_filter = None
        self.recipe_filter = None
        self.path_filter = None
        self.job_filter = None
        self.greedy_filter = None
        self.before_filter = None
        self.after_filter = None

        self.header_display_area = widgets.Output()
        self.report_display_area = widgets.Output()

        self.__get_workflow_report()

    def __get_workflow_report(self):
        """

        :return:
        """
        if not self.report:
            valid, result = self.get_vgrid_report()

            if valid:
                self.report = result
                for job_id, job_hist in result.items():
                    self.jobs.append(job_id)
                    pattern = job_hist['pattern_name']
                    if pattern not in self.patterns:
                        self.patterns.append(pattern)
                    recipes = [name for name, _ in job_hist['recipes']]
                    for recipe in recipes:
                        if recipe not in self.recipes:
                            self.recipes.append(recipe)
                    trigger_path = job_hist['trigger_path']
                    if trigger_path not in self.paths:
                        self.paths.append(trigger_path)

                self.jobs.sort()
                self.paths.sort()
                self.patterns.sort()
                self.recipes.sort()

                self.__construct_image()
            else:
                self.__display_error(result)

    def get_vgrid_report(self):
        """

        :return:
        """
        attributes = {}
        _, response, _ = vgrid_report_json_call(
            self.vgrid,
            VGRID_READ,
            VGRID_REPORT_OBJECT_TYPE,
            attributes,
            logfile=self.logfile
        )

        if response['object_type'] == VGRID_REPORT_OBJECT_TYPE:
            report = response['report']
            write_to_log(
                self.logfile,
                'get_vgrid_report',
                'Got report with jobs: %s' % report.keys()
            )
            return True, report
        else:
            msg = 'Something went wrong with retrieving the report. '
            write_to_log(
                self.logfile,
                'get_vgrid_report',
                '%s:%s' % (msg, response)
            )
            if self.logfile:
                msg += "You can check the logfile '%s' for details" \
                       % self.logfile
            return False, msg

    def __display_report(self):
        """

        :return:
        """
        self.__construct_header()
        self.__construct_image()
        self.__load_image()

        widget = widgets.VBox(
            [
                self.header_display_area,
                self.report_display_area
            ],
            layout=widgets.Layout(width='100%')
        )

        return widget

    def __construct_header(self):
        """

        :return:
        """
        contents = []

        self.job_filter = widgets.SelectMultiple(
            options=self.jobs,
            disabled=False,
            layout=widgets.Layout(width='25%')
        )

        self.path_filter = widgets.SelectMultiple(
            options=self.paths,
            disabled=False,
            layout=widgets.Layout(width='25%')
        )

        self.pattern_filter = widgets.SelectMultiple(
            options=self.patterns,
            disabled=False,
            layout=widgets.Layout(width='25%')
        )

        self.recipe_filter = widgets.SelectMultiple(
            options=self.recipes,
            disabled=False,
            layout=widgets.Layout(width='25%')
        )

        contents.append(
            widgets.HBox(
                [
                    widgets.Label(
                        value="Jobs:",
                        layout=widgets.Layout(width='25%')
                    ),
                    widgets.Label(
                        value="Paths:",
                        layout=widgets.Layout(width='25%')
                    ),
                    widgets.Label(
                        value="Patterns:",
                        layout=widgets.Layout(width='25%')
                    ),
                    widgets.Label(
                        value="Recipes:",
                        layout=widgets.Layout(width='25%')
                    )
                ]
            )
        )

        contents.append(
            widgets.HBox(
                [
                    self.job_filter,
                    self.path_filter,
                    self.pattern_filter,
                    self.recipe_filter
                ]
            )
        )

        refresh_button = widgets.Button(
            value=False,
            description='Refresh',
            disabled=False,
            button_style='',
            tooltip='Refresh displayed report',
            layout=widgets.Layout(width='15%', min_width='12ex')
        )
        refresh_button.on_click(self.__refresh_image)

        # greedy_selector = widgets.Checkbox(
        #     value=False,
        #     description='Only direct matches',
        #     disabled=False,
        #     indent=False
        # )

        self.before_filter = ipydatetime.DatetimePicker(
            description='Before:'
        )

        self.after_filter = ipydatetime.DatetimePicker(
            description='After:'
        )

        # first_time = None
        # last_time = None
        # if self.report:
        #     for job_id, job_hist in self.report.items():
        #         copenhagen = pytz.timezone('Europe/Copenhagen')
        #         job_start = parser.parse(job_hist['start'], tzinfo=copenhagen)
        #         if not first_time or first_time < job_start:
        #             first_time = job_start
        #         if not last_time or last_time > job_start:
        #             last_time = job_start
        #
        # if first_time:
        #     self.before_filter.value = first_time
        # if last_time:
        #     self.after_filter.value = last_time

        bottom_row = widgets.HBox([
            self.after_filter,
            self.before_filter,
            # greedy_selector,
            refresh_button
        ])

        contents.append(
             bottom_row
        )

        v_box = widgets.VBox(
            contents
        )

        self.header_display_area.clear_output(wait=True)
        with self.header_display_area:
            display(v_box)

    def __refresh_image(self, *args):
        write_to_log(
            self.logfile,
            '__refresh_image',
            'Refreshing workflow image'
        )

        self.__construct_image()

        write_to_log(
            self.logfile,
            '__refresh_image',
            'Construction complete'
        )

        self.__load_image()

        write_to_log(
            self.logfile,
            '__refresh_image',
            'Completed refresh'
        )

    def __construct_image(self):
        dot = Digraph(comment=self.filename,
                      format=self.extension,
                      node_attr={'shape': 'plaintext'})

        if self.logfile:
            msg = 'filters are:'
            if self.job_filter and self.job_filter.value:
                msg += '\n\tjobs: %s' % str(self.job_filter.value)
            if self.path_filter and self.path_filter.value:
                msg += '\n\tpaths: %s' % str(self.path_filter.value)
            if self.pattern_filter and self.pattern_filter.value:
                msg += '\n\tpatterns: %s' % str(self.pattern_filter.value)
            if self.recipe_filter and self.recipe_filter.value:
                msg += '\n\trecipes: %s' % str(self.recipe_filter.value)
            if self.after_filter and self.after_filter.value:
                msg += '\n\tafter: %s' % str(self.after_filter.value)
            if self.before_filter and self.before_filter.value:
                msg += '\n\tbefore: %s' % str(self.before_filter.value)
            if msg == 'filters are:':
                msg += '\n\t(None)'
            write_to_log(
                self.logfile,
                '__construct_image',
                msg
            )

        if self.report:
            for job_id, job_hist in self.report.items():
                if self.pattern_filter \
                        and self.pattern_filter.value \
                        and job_hist['pattern_name'] \
                        not in self.pattern_filter.value:
                    continue
                if self.recipe_filter \
                        and self.recipe_filter.value\
                        and set(r for r, _ in job_hist['recipes'])\
                        .isdisjoint(self.recipe_filter.value):
                    continue
                if self.path_filter \
                        and self.path_filter.value \
                        and job_hist['trigger_path'] \
                        not in self.path_filter.value:
                    continue
                if self.job_filter \
                        and self.job_filter.value \
                        and job_id not in self.job_filter.value:
                    continue
                if self.before_filter \
                        and self.before_filter.value \
                        and job_hist['start'] > str(self.before_filter.value):
                    continue
                if self.after_filter \
                        and self.after_filter.value \
                        and job_hist['start'] < str(self.after_filter.value):
                    continue

                write_to_log(
                    self.logfile,
                    '__construct_image',
                    'job %s will be displayed' % job_id
                )

                unique_write = []
                for write, _ in job_hist['write']:
                    if write not in unique_write:
                        unique_write.append(write)

                display_string = \
                    "Job: %s" % job_id + \
                    "\nTrigger: %s" % (job_hist['trigger_path']) + \
                    "\nOutput: %s" % unique_write + \
                    "\nPattern: %s" % (job_hist['pattern_name']) + \
                    "\nRecipe: %s" % (
                        [name for name, _ in job_hist['recipes']])
                dot.node(job_id, display_string)

                for child in job_hist['children']:
                    tail_name = dot._quote_edge(job_id)
                    head_name = dot._quote_edge(child)
                    edge = dot._edge % (tail_name, head_name, '')

                    if edge not in dot.body:
                        dot.edge(job_id, child)

                for parent in job_hist['parents']:
                    tail_name = dot._quote_edge(parent)
                    head_name = dot._quote_edge(job_id)
                    edge = dot._edge % (tail_name, head_name, '')

                    if edge not in dot.body:
                        dot.edge(parent, job_id)

        if self.horizontal:
            dot.graph_attr['rankdir'] = 'LR'

        write_to_log(
            self.logfile,
            '__refresh_image',
            'Rendering....'
        )

        dot.render(self.filename)

        write_to_log(
            self.logfile,
            '__refresh_image',
            'Render complete'
        )

    def __load_image(self):
        file = open(self.filename + '.' + self.extension, 'rb')
        image = file.read()
        report = widgets.Image(
                value=image,
                format='.' + self.extension,
        )

        self.report_display_area.clear_output(wait=True)
        with self.report_display_area:
            display(report)

    def __display_error(self, error):
        """

        :param error:
        :return:
        """
        labels = [
            widgets.Label('Could not retrieve workflow job report. %s' % error)
        ]

        label_display = widgets.VBox(labels)

        self.report_display_area.clear_output(wait=True)
        with self.report_display_area:
            display(label_display)

    def display_widget(self):
        """
        Returns the widget in a display ready state.

        :return: (widgets.Output) The output are to be displayed in a notebook.
        """
        return self.__display_report()
