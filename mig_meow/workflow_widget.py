
import ast
import yaml

from bqplot import *
from bqplot.marks import Graph
from copy import deepcopy
from shutil import copyfile

from IPython.display import display

from .input import valid_path, valid_string
from .constants import GREEN, RED, \
    NOTEBOOK_EXTENSIONS, NAME, DEFAULT_JOB_NAME, \
    SOURCE, PATTERN_NAME, RECIPE_NAME, OBJECT_TYPE, \
    VGRID_PATTERN_OBJECT_TYPE, VGRID_RECIPE_OBJECT_TYPE, \
    VGRID_WORKFLOWS_OBJECT, INPUT_FILE, TRIGGER_PATHS, OUTPUT, RECIPES, \
    VARIABLES, CHAR_UPPERCASE, CHAR_LOWERCASE, CHAR_NUMERIC, CHAR_LINES, \
    VGRID_ERROR_TYPE, VGRID_TEXT_TYPE, PERSISTENCE_ID, VGRID_CREATE, \
    VGRID_UPDATE, PATTERNS, RECIPE, VGRID_DELETE, WIDGET_MODES, MEOW_MODE, \
    VGRID, MOUNT_USER_DIR, VGRID_READ, DESCENDANTS, BLUE, \
    WORKFLOW_INPUTS, WORKFLOW_OUTPUTS, WHITE, ANCESTORS, CWL_MODE, \
    TRIGGER_OUTPUT, NOTEBOOK_OUTPUT, TRIGGER_PATHS, CWL_INPUTS, \
    CWL_NAME, CWL_OUTPUTS, CWL_BASE_COMMAND, CWL_ARGUMENTS, CWL_REQUIREMENTS, \
    CWL_STDOUT, CWL_HINTS, CWL_STEPS, CWL_INPUT_TYPE, CWL_INPUT_BINDING, \
    CWL_INPUT_POSITION, CWL_INPUT_PREFIX, CWL_OUTPUT_TYPE, CWL_OUTPUT_BINDING,\
    CWL_OUTPUT_SOURCE, CWL_OUTPUT_GLOB, CWL_YAML_CLASS, CWL_YAML_PATH, \
    CWL_WORKFLOW_RUN, CWL_WORKFLOW_IN, CWL_WORKFLOW_OUT, CWL_VARIABLES, \
    PLACEHOLDER, WORKFLOW_NAME, STEP_NAME, VARIABLES_NAME, WORKFLOWS, STEPS, \
    SETTINGS, YAML_EXTENSIONS, CWL_EXTENSIONS, CWL_CLASS, CWL_CLASS_WORKFLOW, \
    CWL_CLASS_COMMAND_LINE_TOOL
from .cwl import make_step_dict, make_workflow_dict, get_linked_workflow, \
    make_settings_dict, check_workflow_is_valid, check_step_is_valid, \
    get_glob_value, get_glob_entry_keys, get_step_name_from_title, \
    get_output_lookup
from .mig import vgrid_workflow_json_call
from .pattern import Pattern, is_valid_pattern_object
from .recipe import is_valid_recipe_dict, create_recipe_dict
from .meow import build_workflow_object, pattern_has_recipes, \
    get_workflow_tops, get_linear_workflow

MEOW_NEW_PATTERN_BUTTON = 'meow_new_pattern_button'
MEOW_EDIT_PATTERN_BUTTON = 'meow_edit_pattern_button'
MEOW_NEW_RECIPE_BUTTON = 'meow_new_recipe_button'
MEOW_EDIT_RECIPE_BUTTON = 'meow_edit_recipe_button'
MEOW_IMPORT_CWL_BUTTON = 'meow_import_cwl_button'
MEOW_IMPORT_VGRID_BUTTON = 'meow_import_vgrid_button'
MEOW_EXPORT_VGRID_BUTTON = 'meow_export_vgrid_button'

CWL_NEW_WORKFLOW_BUTTON = 'cwl_new_workflow_button'
CWL_EDIT_WORKFLOW_BUTTON = 'cwl_edit_workflow_button'
CWL_NEW_STEP_BUTTON = 'cwl_new_step_button'
CWL_EDIT_STEP_BUTTON = 'cwl_edit_step_button'
CWL_NEW_VARIABLES_BUTTON = 'cwl_new_variables_button'
CWL_EDIT_VARIABLES_BUTTON = 'cwl_edit_variables_button'
CWL_IMPORT_MEOW_BUTTON = 'cwl_import_meow_button'
CWL_IMPORT_DIR_BUTTON = 'cwl_import_dir_button'
CWL_EXPORT_DIR_BUTTON = 'cwl_export_dir_button'

DEFAULT_RESULT_NOTEBOOKS = [
    DEFAULT_JOB_NAME,
    'Result',
    'result'
]

DEFAULT_WORKFLOW_TITLE = 'workflow'
WORKFLOW_TITLE_ARG = "export_name"
DEFAULT_CWL_IMPORT_EXPORT_DIR = 'cwl_directory'
CWL_IMPORT_EXPORT_DIR_ARG = 'cwl_dir'

MODE = 'mode'
AUTO_IMPORT = 'auto_import'
SUPPORTED_ARGS = {
    MODE: str,
    PATTERNS: dict,
    RECIPES: dict,
    VGRID: str,
    AUTO_IMPORT: bool,
    CWL_IMPORT_EXPORT_DIR_ARG: str
}

FORM_RECIPE_SOURCE = 'Source'
FORM_RECIPE_NAME = 'Name'

FORM_PATTERN_NAME = 'Name'
FORM_PATTERN_TRIGGER_PATH = 'Trigger path'
FORM_PATTERN_RECIPES = 'Recipes'
FORM_PATTERN_TRIGGER_FILE = 'Input file'
FORM_PATTERN_TRIGGER_OUTPUT = 'Trigger output'
FORM_PATTERN_NOTEBOOK_OUTPUT = 'Notebook output'
FORM_PATTERN_OUTPUT = 'Output'
FORM_PATTERN_VARIABLES = 'Variables'

NAME_KEY = 'Name'
VALUE_KEY = 'Value'

INPUT_KEY = 'key'
INPUT_NAME = 'name'
INPUT_TYPE = 'type'
INPUT_HELP = 'help'
INPUT_OPTIONAL = 'optional'

FORM_SINGLE_INPUT = 'single'
FORM_MULTI_INPUT = 'multi'
FORM_DICT_INPUT = 'dict'
FORM_SELECTOR_INPUT = 'selector'

FORM_BUTTONS_KEY = 'buttons'
FORM_SELECTOR_KEY = 'selector'

BUTTON_ON_CLICK = 'on_click'
BUTTON_DESC = 'description'
BUTTON_TOOLTIP = 'tooltip'

RECIPE_FORM_INPUTS = {
    FORM_RECIPE_SOURCE: {
        INPUT_KEY: SOURCE,
        INPUT_TYPE: FORM_SINGLE_INPUT,
        INPUT_NAME: FORM_RECIPE_SOURCE,
        INPUT_HELP:
            "The Jupyter Notebook to be used as a source for the recipe. This "
            "should be expressed as a path to the notebook. Note that if a "
            "name is not provided below then the notebook filename will be "
            "used as the recipe name"
            "<br/>"
            "Example: <b>dir/notebook_1.ipynb</b>"
            "<br/>"
            "In this example this notebook 'notebook_1' in the 'dir' ."
            "directory is imported as a recipe. ",
        INPUT_OPTIONAL: False
    },
    FORM_RECIPE_NAME: {
        INPUT_KEY: NAME,
        INPUT_TYPE: FORM_SINGLE_INPUT,
        INPUT_NAME: FORM_RECIPE_NAME,
        INPUT_HELP:
            "Optional recipe name. This is used to identify the recipe and so "
            "must be unique. If not provided then the notebook filename is "
            "taken as the name. "
            "<br/>"
            "Example: <b>recipe_1</b>"
            "<br/>"
            "In this example this recipe is given the name 'recipe_1', "
            "regardless of the name of the source notebook.",
        INPUT_OPTIONAL: True
    }
}

PATTERN_FORM_INPUTS = {
    FORM_PATTERN_NAME: {
        INPUT_KEY: NAME,
        INPUT_TYPE: FORM_SINGLE_INPUT,
        INPUT_NAME: FORM_PATTERN_NAME,
        INPUT_HELP:
            "%s Name. This is used to identify the %s and so "
            "should be a unique string."
            "<br/>"
            "Example: <b>pattern_1</b>"
            "<br/>"
            "In this example this %s is given the name 'pattern_1'."
            % (PATTERN_NAME, PATTERN_NAME, PATTERN_NAME),
        INPUT_OPTIONAL: False
    },
    FORM_PATTERN_TRIGGER_PATH: {
        INPUT_KEY: TRIGGER_PATHS,
        INPUT_TYPE: FORM_MULTI_INPUT,
        INPUT_NAME: FORM_PATTERN_TRIGGER_PATH,
        INPUT_HELP:
            "Triggering path for file events which are used to schedule "
            "jobs. This is expressed as a regular expression against which "
            "file events are matched. It can be as broad or specific as "
            "required. Any matches between file events and the path given "
            "will cause a scheduled job. File paths are taken relative to the "
            "vgrid home directory. "
            "<br/>"
            "Example: <b>dir/input_file_.*\\.txt</b>"
            "<br/>"
            "In this example %s jobs will trigger on an '.txt' files "
            "whose file name starts with 'input_file_' and is located in "
            "the 'dir' directory. The 'dir' directory in this case should be "
            "located in he vgrid home directory. So if you are operating in "
            "the 'test' vgrid, the structure should be 'test/dir'."
            % PATTERN_NAME,
        INPUT_OPTIONAL: False
    },
    FORM_PATTERN_RECIPES: {
        INPUT_KEY: RECIPES,
        INPUT_TYPE: FORM_MULTI_INPUT,
        INPUT_NAME: FORM_PATTERN_RECIPES,
        INPUT_HELP:
            "Recipe(s) to be used for job definition. These should be recipe "
            "names and may be recipes already defined in the system or "
            "additional ones yet to be added. Each recipe should be defined "
            "in its own text box, and the 'Add recipe' button can be used to "
            "create additional text boxes as needed."
            "<br/>"
            "Example: <b>recipe_1</b>"
            "<br/>"
            "In this example, the recipe 'recipe_1' is used as the definition "
            "of any job processing.",
        INPUT_OPTIONAL: False
    },
    FORM_PATTERN_TRIGGER_FILE: {
        INPUT_KEY: INPUT_FILE,
        INPUT_TYPE: FORM_SINGLE_INPUT,
        INPUT_NAME: FORM_PATTERN_TRIGGER_FILE,
        INPUT_HELP:
            "This is the variable name used to identify the triggering file "
            "within the job processing."
            "<br/>"
            "Example: <b>input_file</b>"
            "<br/>"
            "In this the triggering file will be copied into the job as "
            "'input_file'. This can then be opened or manipulated as "
            "necessary by the job processing.",
        INPUT_OPTIONAL: False
    },
    FORM_PATTERN_TRIGGER_OUTPUT: {
        INPUT_KEY: TRIGGER_OUTPUT,
        INPUT_TYPE: FORM_SINGLE_INPUT,
        INPUT_NAME: FORM_PATTERN_TRIGGER_OUTPUT,
        INPUT_HELP:
            "Trigger output is an optional parameter used to define if the "
            "triggering file is returned. This is defined by the path for the "
            "file to be copied to at job completion. If it is not provided "
            "then any changes made to it are lost, but other output may still "
            "be saved if defined in the output parameter."
            "<br/>"
            "Example: <b>dir/*_output.txt</b>"
            "<br/>"
            "In this example data file is saved within the 'dir' directory. "
            "If the job was triggered on 'test.txt' then the output file "
            "would be called 'test_output.txt",
        INPUT_OPTIONAL: True
    },
    FORM_PATTERN_NOTEBOOK_OUTPUT: {
        INPUT_KEY: NOTEBOOK_OUTPUT,
        INPUT_TYPE: FORM_SINGLE_INPUT,
        INPUT_NAME: FORM_PATTERN_NOTEBOOK_OUTPUT,
        INPUT_HELP:
            "Notebook output is an optional parameter used to define if the "
            "notebook used for job processing is returned. This is defined as "
            "a path for the notebook to be copied to at job completion. If it "
            "is not provided then the notebook is destroyed, but other output "
            "may still be saved if defined in the output parameter."
            "<br/>"
            "Example: <b>dir/*_output.ipynb</b>"
            "<br/>"
            "In this example the job notebook is saved within the 'dir' "
            "directory. If the job was triggered on 'test.txt' then the "
            "output notebook would be called 'test_output.ipynb",
        INPUT_OPTIONAL: True
    },
    FORM_PATTERN_OUTPUT: {
        INPUT_KEY: OUTPUT,
        INPUT_TYPE: FORM_DICT_INPUT,
        INPUT_NAME: FORM_PATTERN_OUTPUT,
        INPUT_HELP:
            "TODO",
        INPUT_OPTIONAL: True
    },
    FORM_PATTERN_VARIABLES: {
        INPUT_KEY: VARIABLES,
        INPUT_TYPE: FORM_DICT_INPUT,
        INPUT_NAME: FORM_PATTERN_VARIABLES,
        INPUT_HELP:
            "TODO",
        INPUT_OPTIONAL: True
    },
}

FORM_WORKFLOW_NAME = 'Name'
FORM_WORKFLOW_INPUTS = "Input(s)"
FORM_WORKFLOW_OUTPUTS = "Output(s)"
FORM_WORKFLOW_STEPS = 'Step(s)'
FORM_WORKFLOW_REQUIREMENTS = 'Requirement(s)'

WORKFLOW_FORM_INPUTS = {
    FORM_WORKFLOW_NAME: {
        INPUT_KEY: CWL_NAME,
        INPUT_TYPE: FORM_SINGLE_INPUT,
        INPUT_NAME: FORM_WORKFLOW_NAME,
        INPUT_HELP:
            "TODO",
        INPUT_OPTIONAL: False
    },
    FORM_WORKFLOW_INPUTS: {
        INPUT_KEY: CWL_INPUTS,
        INPUT_TYPE: FORM_DICT_INPUT,
        INPUT_NAME: FORM_WORKFLOW_INPUTS,
        INPUT_HELP:
            "TODO",
        INPUT_OPTIONAL: False
    },
    FORM_WORKFLOW_OUTPUTS: {
        INPUT_KEY: CWL_OUTPUTS,
        INPUT_TYPE: FORM_DICT_INPUT,
        INPUT_NAME: FORM_WORKFLOW_OUTPUTS,
        INPUT_HELP:
            "TODO",
        INPUT_OPTIONAL: True
    },
    FORM_WORKFLOW_STEPS: {
        INPUT_KEY: CWL_STEPS,
        INPUT_TYPE: FORM_DICT_INPUT,
        INPUT_NAME: FORM_WORKFLOW_STEPS,
        INPUT_HELP:
            "TODO",
        INPUT_OPTIONAL: False
    },
    FORM_WORKFLOW_REQUIREMENTS: {
        INPUT_KEY: CWL_REQUIREMENTS,
        INPUT_TYPE: FORM_DICT_INPUT,
        INPUT_NAME: FORM_WORKFLOW_REQUIREMENTS,
        INPUT_HELP:
            "TODO",
        INPUT_OPTIONAL: True
    }
}

FORM_STEP_NAME = 'Name'
FORM_STEP_BASE_COMMAND = 'Base Command'
FORM_STEP_STDOUT = "Stdout"
FORM_STEP_INPUTS = "Input(s)"
FORM_STEP_OUTPUTS = "Output(s)"
FORM_STEP_HINTS = 'Hint(s)'
FORM_STEP_REQUIREMENTS = 'Requirement(s)'
FORM_STEP_ARGUMENTS = 'Argument(s)'

STEP_FORM_INPUTS = {
    FORM_STEP_NAME: {
        INPUT_KEY: CWL_NAME,
        INPUT_TYPE: FORM_SINGLE_INPUT,
        INPUT_NAME: FORM_STEP_NAME,
        INPUT_HELP:
            "TODO",
        INPUT_OPTIONAL: False
    },
    FORM_STEP_BASE_COMMAND: {
        INPUT_KEY: CWL_BASE_COMMAND,
        INPUT_TYPE: FORM_SINGLE_INPUT,
        INPUT_NAME: FORM_STEP_BASE_COMMAND,
        INPUT_HELP:
            "TODO",
        INPUT_OPTIONAL: False
    },
    FORM_STEP_STDOUT: {
        INPUT_KEY: CWL_STDOUT,
        INPUT_TYPE: FORM_SINGLE_INPUT,
        INPUT_NAME: FORM_STEP_STDOUT,
        INPUT_HELP:
            "TODO",
        INPUT_OPTIONAL: True
    },
    FORM_STEP_INPUTS: {
        INPUT_KEY: CWL_INPUTS,
        INPUT_TYPE: FORM_DICT_INPUT,
        INPUT_NAME: FORM_STEP_INPUTS,
        INPUT_HELP:
            "TODO",
        INPUT_OPTIONAL: False
    },
    FORM_STEP_OUTPUTS: {
        INPUT_KEY: CWL_OUTPUTS,
        INPUT_TYPE: FORM_DICT_INPUT,
        INPUT_NAME: FORM_STEP_OUTPUTS,
        INPUT_HELP:
            "TODO",
        INPUT_OPTIONAL: True
    },
    FORM_STEP_REQUIREMENTS: {
        INPUT_KEY: CWL_REQUIREMENTS,
        INPUT_TYPE: FORM_DICT_INPUT,
        INPUT_NAME: FORM_STEP_REQUIREMENTS,
        INPUT_HELP:
            "TODO",
        INPUT_OPTIONAL: True
    },
    FORM_STEP_ARGUMENTS: {
        INPUT_KEY: CWL_ARGUMENTS,
        INPUT_TYPE: FORM_MULTI_INPUT,
        INPUT_NAME: FORM_STEP_ARGUMENTS,
        INPUT_HELP:
            "TODO",
        INPUT_OPTIONAL: True
    },
    FORM_STEP_HINTS: {
        INPUT_KEY: CWL_HINTS,
        INPUT_TYPE: FORM_DICT_INPUT,
        INPUT_NAME: FORM_STEP_HINTS,
        INPUT_HELP:
            "TODO",
        INPUT_OPTIONAL: True
    }
}

FORM_VARIABLES_NAME = 'Name'
FORM_VARIABLES_VARIABLES = 'Variables'

VARIABLES_FORM_INPUTS = {
    FORM_VARIABLES_NAME: {
        INPUT_KEY: CWL_NAME,
        INPUT_TYPE: FORM_SINGLE_INPUT,
        INPUT_NAME: FORM_VARIABLES_NAME,
        INPUT_HELP:
            "TODO",
        INPUT_OPTIONAL: False
    },
    FORM_VARIABLES_VARIABLES: {
        INPUT_KEY: CWL_VARIABLES,
        INPUT_TYPE: FORM_DICT_INPUT,
        INPUT_NAME: FORM_VARIABLES_VARIABLES,
        INPUT_HELP:
            "TODO",
        INPUT_OPTIONAL: False
    }
}

MEOW_TOOLTIP = Tooltip(
    fields=[
        'Name',
        'Recipe(s)',
        'Trigger Path(s)',
        'Outputs(s)',
        'Static Inputs(s)',
        'Input File',
        'Variable(s)'
    ],
)

CWL_TOOLTIP = Tooltip(
    fields=[
        'Name',
        'Base Command',
        'Inputs(s)',
        'Outputs(s)',
        'Argument(s)',
        'Requirement(s)',
        'Hint(s)',
        'Stdout'
    ],
)

NO_VGRID_MSG = "No VGrid has been specified so MEOW importing/exporting " \
               "will not be possible. If this is required then specify a " \
               "VGrid in the create_workflow_widget arguments by stating " \
               "'create_workflow_widget(vgrid='name_of_vgrid')'. "




# Move this to input file
def check_input_args(args):
    if not isinstance(args, dict):
        raise Exception("Arguments provided in invalid format")

    for arg in args.keys():
        if arg not in SUPPORTED_ARGS:
            raise Exception("Unsupported argument %s. Valid are: %s. "
                            % (arg, list(SUPPORTED_ARGS.keys())))


def strip_dirs(path):
    if os.path.sep in path:
        path = path[path.rfind(os.path.sep) + 1:]
    return path


def count_calls(calls, operation, type):
    count = [i[2][NAME] for i in calls
             if i[0] == operation and i[1] == type]
    return count


def list_to_dict(to_convert):
    variables_dict = {}
    for variables in to_convert:
        try:
            variables[VALUE_KEY] = ast.literal_eval(
                variables[VALUE_KEY])
        except (SyntaxError, ValueError):
            pass
        if variables[NAME_KEY] and variables[VALUE_KEY]:
            variables_dict[variables[NAME_KEY]] = variables[VALUE_KEY]
    return variables_dict


def prepare_to_dump(to_export):
    new_dict = {}
    for key, value in to_export.items():
        if key != CWL_NAME:
            if value:
                new_dict[key] = value
    return new_dict


class WorkflowWidget:
    def __init__(self, **kwargs):

        check_input_args(kwargs)

        self.mode = kwargs.get(MODE, None)
        if not self.mode:
            self.mode = MEOW_MODE
        if self.mode not in WIDGET_MODES:
            raise Exception("Unsupported mode %s specified. Valid are %s. "
                            % (self.mode, WIDGET_MODES))

        cwl_dir = kwargs.get(CWL_IMPORT_EXPORT_DIR_ARG, None)
        if cwl_dir:
            self.cwl_import_export_dir = cwl_dir
        else:
            self.cwl_import_export_dir = DEFAULT_CWL_IMPORT_EXPORT_DIR

        workflow_title = kwargs.get(WORKFLOW_TITLE_ARG, None)
        if workflow_title:
            self.workflow_title = workflow_title
        else:
            self.workflow_title = DEFAULT_WORKFLOW_TITLE

        self.vgrid = kwargs.get(VGRID, None)
        self.auto_import = kwargs.get(AUTO_IMPORT, False)

        self.mode_toggle = widgets.ToggleButtons(
            options=[i for i in WIDGET_MODES if isinstance(i, str)],
            description='Mode:',
            disabled=False,
            button_style='',
            tooltips= [
                "Construct workflows as defined by %s. Attempts will be made "
                "to convert any existing objects to the %s paradigm. " % (i, i)
                for i in WIDGET_MODES if isinstance(i, str)
            ],
            value=self.mode
        )
        self.mode_toggle.observe(self.__on_mode_selection_changed)

        self.visualisation_area = widgets.Output()
        self.button_area = widgets.Output()
        self.form_area = widgets.Output()
        self.feedback_area = widgets.HTML()

        self.meow = {
            PATTERNS: {},
            RECIPES: {}
        }
        self.cwl = {
            WORKFLOWS: {},
            STEPS: {},
            SETTINGS: {}
        }

        self.mig_imports = {
            PATTERNS: {},
            RECIPES: {}
        }

        self.button_elements = {}
        self.form_inputs = {}
        self.form_sections = {}

        self.BUTTONS = {
            MEOW_MODE: {
                MEOW_NEW_PATTERN_BUTTON: {
                    BUTTON_ON_CLICK: self.new_pattern_clicked,
                    BUTTON_DESC: "New %s" % PATTERN_NAME,
                    BUTTON_TOOLTIP: 'Define a new %s. ' % PATTERN_NAME
                },
                MEOW_EDIT_PATTERN_BUTTON: {
                    BUTTON_ON_CLICK: self.edit_pattern_clicked,
                    BUTTON_DESC: "Edit %s" % PATTERN_NAME,
                    BUTTON_TOOLTIP: 'Edit an existing %s. ' % PATTERN_NAME
                },
                MEOW_NEW_RECIPE_BUTTON: {
                    BUTTON_ON_CLICK: self.new_recipe_clicked,
                    BUTTON_DESC: "Add %s" % RECIPE_NAME,
                    BUTTON_TOOLTIP: 'Import a new %s. ' % RECIPE_NAME
                },
                MEOW_EDIT_RECIPE_BUTTON: {
                    BUTTON_ON_CLICK: self.edit_recipe_clicked,
                    BUTTON_DESC: "Edit %s" % RECIPE_NAME,
                    BUTTON_TOOLTIP: 'Edit an existing %s. ' % RECIPE_NAME
                },
                MEOW_IMPORT_CWL_BUTTON: {
                    BUTTON_ON_CLICK: self.import_from_cwl_clicked,
                    BUTTON_DESC: "Convert CWL",
                    BUTTON_TOOLTIP:
                        'Attempt to convert existing CWl definitions into '
                        'MEOW format. '
                },
                MEOW_IMPORT_VGRID_BUTTON: {
                    BUTTON_ON_CLICK: self.import_from_vgrid_clicked,
                    BUTTON_DESC: "Read VGrid",
                    BUTTON_TOOLTIP: 'Import data from Vgrid. '
                },
                MEOW_EXPORT_VGRID_BUTTON: {
                    BUTTON_ON_CLICK: self.export_to_vgrid_clicked,
                    BUTTON_DESC: "Export to Vgrid",
                    BUTTON_TOOLTIP: 'Exports data to Vgrid. '
                }
            },
            CWL_MODE: {
                CWL_NEW_WORKFLOW_BUTTON: {
                    BUTTON_ON_CLICK: self.new_workflow_clicked,
                    BUTTON_DESC: "New %s" % WORKFLOW_NAME,
                    BUTTON_TOOLTIP: 'Define a new %s. ' % WORKFLOW_NAME
                },
                CWL_EDIT_WORKFLOW_BUTTON: {
                    BUTTON_ON_CLICK: self.edit_workflow_clicked,
                    BUTTON_DESC: "Edit %s" % WORKFLOW_NAME,
                    BUTTON_TOOLTIP: 'Edit an existing %s. ' % WORKFLOW_NAME
                },
                CWL_NEW_STEP_BUTTON: {
                    BUTTON_ON_CLICK: self.new_step_clicked,
                    BUTTON_DESC: "New %s" % STEP_NAME,
                    BUTTON_TOOLTIP: 'Define a new %s. ' % STEP_NAME
                },
                CWL_EDIT_STEP_BUTTON: {
                    BUTTON_ON_CLICK: self.edit_step_clicked,
                    BUTTON_DESC: "Edit %s" % STEP_NAME,
                    BUTTON_TOOLTIP: 'Edit an existing %s. ' % STEP_NAME
                },
                CWL_NEW_VARIABLES_BUTTON: {
                    BUTTON_ON_CLICK: self.new_variables_clicked,
                    BUTTON_DESC: "Add %s" % VARIABLES_NAME,
                    BUTTON_TOOLTIP: 'Define new %s. ' % VARIABLES_NAME
                },
                CWL_EDIT_VARIABLES_BUTTON: {
                    BUTTON_ON_CLICK: self.edit_variables_clicked,
                    BUTTON_DESC: "Edit %s" % VARIABLES_NAME,
                    BUTTON_TOOLTIP: 'Edit existing %s. ' % VARIABLES_NAME
                },
                CWL_IMPORT_MEOW_BUTTON: {
                    BUTTON_ON_CLICK: self.import_from_meow_clicked,
                    BUTTON_DESC: "Convert MEOW",
                    BUTTON_TOOLTIP:
                        "Convert existing MEOW definitions into CWL"
                },
                CWL_IMPORT_DIR_BUTTON: {
                    BUTTON_ON_CLICK: self.import_from_dir_clicked,
                    BUTTON_DESC: "Read directory",
                    BUTTON_TOOLTIP: 'Imports CWL data from a given directory. '
                },
                CWL_EXPORT_DIR_BUTTON: {
                    BUTTON_ON_CLICK: self.export_to_dir_clicked,
                    BUTTON_DESC: "Export to directory",
                    BUTTON_TOOLTIP: 'Exports CWL data to a given directory. '
                }
            }
        }

    def display_widget(self):
        widget = widgets.VBox(
            [
                self.mode_toggle,
                self.visualisation_area,
                self.button_area,
                self.form_area,
                self.feedback_area
            ],
            layout=widgets.Layout(width='100%')
        )

        self.__update_workflow_visualisation()
        self.__construct_widget()

        return widget

    def __on_mode_selection_changed(self, change):
        new_mode = change['new']
        if change['type'] == 'change' \
                and change['name'] == 'value'\
                and new_mode != self.mode:
            if new_mode == CWL_MODE:
                self.mode = new_mode
                self.__construct_widget()
                self.__update_workflow_visualisation()
            elif new_mode == MEOW_MODE:
                self.mode = new_mode
                self.__construct_widget()
                self.__update_workflow_visualisation()

    def __check_state(self, state=None):
        if self.mode not in WIDGET_MODES:
            raise Exception("Internal state corrupted. Invalid mode %s. Only "
                            "valid modes are %s. " % (self.mode, WIDGET_MODES))
        if state:
            if self.mode != state:
                if self.mode not in WIDGET_MODES:
                    raise Exception(
                        "Internal state corrupted. Invalid function call for "
                        "state %s. Should be only accessible to %s. "
                        % (state, self.mode))

    def __construct_widget(self):
        self.__check_state()

        if self.mode == MEOW_MODE:
            self.__construct_meow_widget()

        elif self.mode == CWL_MODE:
            self.__construct_cwl_widget()

    def __construct_meow_widget(self):
        self.__check_state(state=MEOW_MODE)
        self.button_elements = {}
        self.__close_form()

        button_row_items = []
        button_layout = \
            widgets.Layout(width='%d%%' % (100/len(self.BUTTONS[MEOW_MODE])))
        for button_key, button_value in self.BUTTONS[MEOW_MODE].items():
            button = widgets.Button(
                value=False,
                description=button_value[BUTTON_DESC],
                disabled=True,
                button_style='',
                tooltip=button_value[BUTTON_TOOLTIP],
                layout=button_layout
            )
            button.on_click(button_value[BUTTON_ON_CLICK])
            self.button_elements[button_key] = button
            button_row_items.append(button)
        button_row = widgets.HBox(button_row_items)

        new_buttons = widgets.VBox([
            button_row
        ])

        self.__enable_top_buttons()
        if self.auto_import:
            if not self.meow[PATTERNS] and not self.meow[RECIPES]:
                if self.cwl[WORKFLOWS] \
                        or self.cwl[STEPS] \
                        or self.cwl[SETTINGS]:
                    self.__set_feedback(
                        "%s data detected, attempting to convert to %s "
                        "format. " % (CWL_MODE, MEOW_MODE)
                    )
                    status, result = self.__cwl_to_meow()

                    if status:
                        self.__import_meow_workflow(**result)
                    self.__enable_top_buttons()

                else:
                    self.__set_feedback(
                        "No %s data detected, attempting to import data from "
                        "VGrid. " % CWL_MODE
                    )
                    self.__import_from_vgrid(confirm=False)
            else:
                self.__set_feedback(
                    "As %s data is already present in the system. No "
                    "automatic import has taken place. " % MEOW_MODE
                )

        self.button_area.clear_output(wait=True)
        with self.button_area:
            display(new_buttons)

    def __construct_cwl_widget(self):
        self.__check_state(state=CWL_MODE)
        self.button_elements = {}
        self.__close_form()

        button_row_items = []
        button_layout = \
            widgets.Layout(width='%d%%' % (100 / len(self.BUTTONS[CWL_MODE])))
        for button_key, button_value in self.BUTTONS[CWL_MODE].items():
            button = widgets.Button(
                value=False,
                description=button_value[BUTTON_DESC],
                disabled=True,
                button_style='',
                tooltip=button_value[BUTTON_TOOLTIP],
                layout=button_layout
            )
            button.on_click(button_value[BUTTON_ON_CLICK])
            self.button_elements[button_key] = button
            button_row_items.append(button)
        button_row = widgets.HBox(button_row_items)

        new_buttons = widgets.VBox([
            button_row
        ])

        self.__enable_top_buttons()

        if self.auto_import:
            if not self.cwl[WORKFLOWS] \
                    and not self.cwl[STEPS] \
                    and not self.cwl[SETTINGS]:
                if self.meow[PATTERNS] or self.meow[RECIPES]:
                    self.__set_feedback(
                        "%s data detected, attempting to convert to %s "
                        "format. " % (MEOW_MODE, CWL_MODE)
                    )
                    status, result = self.__meow_to_cwl()

                    if status:
                        self.__import_cwl(**result)
                    self.__enable_top_buttons()
                else:
                    status, feedback = self.__import_from_dir()

                    if status:
                        self.cwl[WORKFLOWS] = feedback[WORKFLOWS]
                        self.cwl[STEPS] = feedback[STEPS]
                        self.cwl[SETTINGS] = feedback[SETTINGS]

                        self.__set_feedback(
                            "%s(s) %s, %s(s) %s, and %s(s) %s have been "
                            "automatically imported from %s. "
                            % (
                                WORKFLOW_NAME,
                                str(list(feedback[WORKFLOWS].keys())),
                                STEP_NAME,
                                str(list(feedback[STEPS].keys())),
                                VARIABLES_NAME,
                                str(list(feedback[VARIABLES].keys())),
                                self.cwl_import_export_dir
                            )
                        )
                        self.__update_workflow_visualisation()
                        self.__enable_top_buttons()

                    else:
                        self.__set_feedback(
                            "No %s data to import from %s and no %s data "
                            "detected. "
                            % (CWL_MODE, self.cwl_import_export_dir, MEOW_MODE)
                        )
            else:
                self.__set_feedback(
                    "As %s data is already present in the system. No "
                    "automatic import has taken place. " % CWL_MODE
                )

        self.button_area.clear_output(wait=True)
        with self.button_area:
            display(new_buttons)

    def new_pattern_clicked(self, button):
        self.__clear_feedback()
        self.__create_new_form(
            [
                PATTERN_FORM_INPUTS[FORM_PATTERN_NAME],
                PATTERN_FORM_INPUTS[FORM_PATTERN_TRIGGER_PATH],
                PATTERN_FORM_INPUTS[FORM_PATTERN_RECIPES],
                PATTERN_FORM_INPUTS[FORM_PATTERN_TRIGGER_FILE],
                PATTERN_FORM_INPUTS[FORM_PATTERN_TRIGGER_OUTPUT],
                PATTERN_FORM_INPUTS[FORM_PATTERN_NOTEBOOK_OUTPUT],
                PATTERN_FORM_INPUTS[FORM_PATTERN_OUTPUT],
                PATTERN_FORM_INPUTS[FORM_PATTERN_VARIABLES]
            ],
            self.__process_new_pattern,
            PATTERN_NAME
        )

    def edit_pattern_clicked(self, button):
        self.__clear_feedback()
        self.__create_new_form(
            [
                PATTERN_FORM_INPUTS[FORM_PATTERN_TRIGGER_PATH],
                PATTERN_FORM_INPUTS[FORM_PATTERN_RECIPES],
                PATTERN_FORM_INPUTS[FORM_PATTERN_TRIGGER_FILE],
                PATTERN_FORM_INPUTS[FORM_PATTERN_TRIGGER_OUTPUT],
                PATTERN_FORM_INPUTS[FORM_PATTERN_NOTEBOOK_OUTPUT],
                PATTERN_FORM_INPUTS[FORM_PATTERN_OUTPUT],
                PATTERN_FORM_INPUTS[FORM_PATTERN_VARIABLES]
            ],
            self.__process_editing_pattern,
            PATTERN_NAME,
            delete_func=self.__process_delete_pattern,
            selector_key=NAME,
            selector_dict=self.meow[PATTERNS]
        )

    def new_recipe_clicked(self, button):
        self.__clear_feedback()
        self.__create_new_form(
            [
                RECIPE_FORM_INPUTS[FORM_RECIPE_SOURCE],
                RECIPE_FORM_INPUTS[FORM_RECIPE_NAME]
            ],
            self.__process_new_recipe,
            RECIPE_NAME
        )

    def edit_recipe_clicked(self, button):
        self.__clear_feedback()
        self.__create_new_form(
            [
                RECIPE_FORM_INPUTS[FORM_RECIPE_SOURCE]
            ],
            self.__process_editing_recipe,
            RECIPE_NAME,
            delete_func=self.__process_delete_recipe,
            selector_key=NAME,
            selector_dict=self.meow[RECIPES]
        )

    # TODO implement
    def import_from_cwl_clicked(self, button):
        self.__close_form()
        self.__clear_feedback()

        status, result = self.__cwl_to_meow()

        if status:
            self.__import_meow_workflow(**result)

    def import_from_vgrid_clicked(self, button):
        self.__close_form()
        self.__clear_feedback()
        self.__import_from_vgrid()

    def export_to_vgrid_clicked(self, button):
        self.__close_form()
        self.__clear_feedback()
        self.__export_to_vgrid()

    def new_workflow_clicked(self, button):
        self.__clear_feedback()
        self.__create_new_form(
            [
                WORKFLOW_FORM_INPUTS[FORM_WORKFLOW_NAME],
                WORKFLOW_FORM_INPUTS[FORM_WORKFLOW_INPUTS],
                WORKFLOW_FORM_INPUTS[FORM_WORKFLOW_OUTPUTS],
                WORKFLOW_FORM_INPUTS[FORM_WORKFLOW_STEPS],
                WORKFLOW_FORM_INPUTS[FORM_WORKFLOW_REQUIREMENTS]
            ],
            self.__process_new_workflow,
            WORKFLOW_NAME
        )

    def edit_workflow_clicked(self, button):
        self.__clear_feedback()
        self.__create_new_form(
            [
                WORKFLOW_FORM_INPUTS[FORM_WORKFLOW_INPUTS],
                WORKFLOW_FORM_INPUTS[FORM_WORKFLOW_OUTPUTS],
                WORKFLOW_FORM_INPUTS[FORM_WORKFLOW_STEPS],
                WORKFLOW_FORM_INPUTS[FORM_WORKFLOW_REQUIREMENTS]
            ],
            self.__process_editing_workflow,
            WORKFLOW_NAME,
            delete_func=self.__process_delete_workflow,
            selector_key=CWL_NAME,
            selector_dict=self.cwl[WORKFLOWS]
        )

    def new_step_clicked(self, button):
        self.__clear_feedback()
        self.__create_new_form(
            [
                STEP_FORM_INPUTS[FORM_STEP_NAME],
                STEP_FORM_INPUTS[FORM_STEP_BASE_COMMAND],
                STEP_FORM_INPUTS[FORM_STEP_INPUTS],
                STEP_FORM_INPUTS[FORM_STEP_OUTPUTS],
                STEP_FORM_INPUTS[FORM_STEP_ARGUMENTS],
                STEP_FORM_INPUTS[FORM_STEP_REQUIREMENTS],
                STEP_FORM_INPUTS[FORM_STEP_HINTS],
                STEP_FORM_INPUTS[FORM_STEP_STDOUT]
            ],
            self.__process_new_step,
            STEP_NAME
        )

    def edit_step_clicked(self, button):
        self.__clear_feedback()
        self.__create_new_form(
            [
                STEP_FORM_INPUTS[FORM_STEP_BASE_COMMAND],
                STEP_FORM_INPUTS[FORM_STEP_INPUTS],
                STEP_FORM_INPUTS[FORM_STEP_OUTPUTS],
                STEP_FORM_INPUTS[FORM_STEP_ARGUMENTS],
                STEP_FORM_INPUTS[FORM_STEP_REQUIREMENTS],
                STEP_FORM_INPUTS[FORM_STEP_HINTS],
                STEP_FORM_INPUTS[FORM_STEP_STDOUT]
            ],
            self.__process_editing_step,
            STEP_NAME,
            delete_func=self.__process_delete_step,
            selector_key=NAME,
            selector_dict=self.cwl[STEPS]
        )

    def new_variables_clicked(self, button):
        self.__clear_feedback()
        self.__create_new_form(
            [
                VARIABLES_FORM_INPUTS[FORM_VARIABLES_NAME],
                VARIABLES_FORM_INPUTS[FORM_VARIABLES_VARIABLES]
            ],
            self.__process_new_variables,
            VARIABLES_NAME
        )

    def edit_variables_clicked(self, button):
        self.__clear_feedback()
        self.__create_new_form(
            [
                VARIABLES_FORM_INPUTS[FORM_VARIABLES_VARIABLES]
            ],
            self.__process_editing_variables,
            VARIABLES_NAME,
            delete_func=self.__process_delete_variables,
            selector_key=NAME,
            selector_dict=self.cwl[VARIABLES],
        )

    def import_from_meow_clicked(self, button):
        self.__close_form()
        self.__clear_feedback()

        status, result = self.__meow_to_cwl()

        if status:
            self.__add_to_feedback(
                "%s(s) %s, %s(s) %s, and %s(s) %s have been identified for "
                "import. Any currently registered %s(s), %s(s), and %s(s) "
                "will be overwritten. "
                % (
                    WORKFLOW_NAME,
                    str(list(result[WORKFLOWS].keys())),
                    STEP_NAME,
                    str(list(result[STEPS].keys())),
                    VARIABLES_NAME,
                    str(list(result[VARIABLES].keys())),
                    WORKFLOW_NAME,
                    STEP_NAME,
                    VARIABLES_NAME
                )
            )

            self.__create_confirmation_buttons(
                self.__import_cwl,
                result,
                "Confirm Import",
                "Cancel Import",
                "Import canceled. No local data has been changed. "
            )
        self.__enable_top_buttons()

    def import_from_dir_clicked(self, button):
        self.__close_form()
        self.__clear_feedback()

        status, feedback = self.__import_from_dir()

        if not status:
            self.__set_feedback(feedback)
            self.__enable_top_buttons()
            return

        if feedback[WORKFLOWS] or feedback[STEPS] or feedback[VARIABLES]:
            self.__add_to_feedback(
                "%s(s) %s, %s(s) %s, and %s(s) %s have been identified for "
                "import. Any currently registered %s(s), %s(s), and %s(s) "
                "will be overwritten. "
                % (
                    WORKFLOW_NAME,
                    str(list(feedback[WORKFLOWS].keys())),
                    STEP_NAME,
                    str(list(feedback[STEPS].keys())),
                    VARIABLES_NAME,
                    str(list(feedback[VARIABLES].keys())),
                    WORKFLOW_NAME,
                    STEP_NAME,
                    VARIABLES_NAME
                )
            )

            self.__create_confirmation_buttons(
                self.__import_cwl,
                feedback,
                "Confirm Import",
                "Cancel Import",
                "Import canceled. No local data has been changed. "
            )
        else:
            self.__add_to_feedback("No CWL inputs were found")
        self.__enable_top_buttons()

    def export_to_dir_clicked(self, button):
        # TODO update this description
        self.__close_form()
        self.__clear_feedback()

        if not os.path.exists(self.cwl_import_export_dir):
            os.mkdir(self.cwl_import_export_dir)

        for workflow_name, workflow in self.cwl[WORKFLOWS].items():

            status, feedback = check_workflow_is_valid(
                workflow_name,
                self.cwl
            )

            if not status:
                self.__add_to_feedback(
                    "Could not export %s %s. %s"
                    % (WORKFLOW_NAME, workflow_name, feedback)
                )
                break

            workflow_dir = os.path.join(
                self.cwl_import_export_dir,
                workflow_name
            )
            if not os.path.exists(workflow_dir):
                os.mkdir(workflow_dir)

            # copy required files
            missing_files = set()
            outlines = []
            for step_name, step in workflow[CWL_STEPS].items():
                for input_name, input_value in step[CWL_WORKFLOW_IN].items():
                    if '/' not in input_value \
                            and input_value in workflow[CWL_INPUTS]\
                            and workflow[CWL_INPUTS][input_value] == 'File':
                        settings = \
                            self.cwl[SETTINGS][workflow_name][CWL_VARIABLES]
                        file_name = settings[input_value][CWL_YAML_PATH]
                        if not os.path.exists(file_name):
                            missing_files.add(file_name)
                        else:
                            dest_path = os.path.join(workflow_dir, file_name)
                            copyfile(file_name, dest_path)

                outputs_list = \
                    list(self.cwl[STEPS][step_name][CWL_OUTPUTS].keys())
                outputs_string = '['
                for elem in outputs_list:
                    if len(outputs_string) > 1:
                        outputs_string += ', '
                    outputs_string += elem
                outputs_string += ']'
                outline = "    out: '%s'\n" % outputs_string
                outlines.append(outline)

            for step_name, step in self.cwl[STEPS].items():
                step_filename = '%s.cwl' % step_name
                step_file_path = os.path.join(
                    workflow_dir,
                    step_filename
                )
                with open(step_file_path, 'w') as cwl_file:
                    yaml.dump(
                        prepare_to_dump(step),
                        cwl_file,
                        default_flow_style=False
                    )

            # create workflow cwl file
            cwl_filename = '%s.cwl' % self.workflow_title
            cwl_file_path = os.path.join(workflow_dir, cwl_filename)
            with open(cwl_file_path, 'w') as cwl_file:
                yaml.dump(
                    prepare_to_dump(workflow),
                    cwl_file,
                    default_flow_style=False
                )

            # Edit yaml export of workflow_cwl_dict as it won't like exporting
            # the outputs section
            with open(cwl_file_path, 'r') as input_file:
                data = input_file.readlines()

            # TODO improve this, this will produce unpredictable behaviour
            for index, line in enumerate(data):
                for outline in outlines:
                    if line == outline:
                        data[index] = outline.replace('\'', '')

            with open(cwl_file_path, 'w') as output_file:
                output_file.writelines(data)

            # create yaml file
            yaml_filename = '%s.yml' % self.workflow_title
            yaml_file_path = os.path.join(workflow_dir, yaml_filename)
            with open(yaml_file_path, 'w') as yaml_file:
                yaml.dump(
                    self.cwl[SETTINGS][workflow_name][CWL_VARIABLES],
                    yaml_file,
                    default_flow_style=False
                )

            if not missing_files:
                self.__add_to_feedback(
                    "Export performed successfully. Files are present in "
                    "directory '%s' and can be called with:" % workflow_dir
                )
            else:
                self.__add_to_feedback(
                    "Export performed partially successfully. Workflow "
                    "definitions and steps were exported successfully but "
                    "some input files are missing. Please make the following "
                    "files available within the directory %s: "
                    % workflow_dir
                )
                self.__add_to_feedback(str(missing_files))
                self.__add_to_feedback(
                    "Once these files are present within the directory %s "
                    "the workflow can be called with: " % workflow_dir
                )

            self.__add_to_feedback(
                "toil-cwl-runner %s %s" % (cwl_filename, yaml_filename))

    def __enable_top_buttons(self):

        if self.button_elements:
            if self.mode == MEOW_MODE:
                self.button_elements[MEOW_NEW_PATTERN_BUTTON].disabled = \
                    False
                if self.meow[PATTERNS]:
                    self.button_elements[MEOW_EDIT_PATTERN_BUTTON].disabled = \
                        False
                else:
                    self.button_elements[MEOW_EDIT_PATTERN_BUTTON].disabled = \
                        True

                self.button_elements[MEOW_NEW_RECIPE_BUTTON].disabled = False
                if self.meow[RECIPES]:
                    self.button_elements[MEOW_EDIT_RECIPE_BUTTON].disabled = \
                        False
                else:
                    self.button_elements[MEOW_EDIT_RECIPE_BUTTON].disabled = \
                        True

                if self.cwl[WORKFLOWS] \
                        or self.cwl[STEPS] \
                        or self.cwl[SETTINGS]:
                    self.button_elements[MEOW_IMPORT_CWL_BUTTON].disabled = \
                        False
                else:
                    self.button_elements[MEOW_IMPORT_CWL_BUTTON].disabled = \
                        True

                if self.vgrid:
                    self.button_elements[MEOW_IMPORT_VGRID_BUTTON].disabled = \
                        False
                    self.button_elements[MEOW_EXPORT_VGRID_BUTTON].disabled = \
                        False
                else:
                    self.button_elements[MEOW_IMPORT_VGRID_BUTTON].disabled = \
                        True
                    self.button_elements[MEOW_IMPORT_VGRID_BUTTON].tooltip = \
                        "Import is not available as VGrid has not been " \
                        "specified. "
                    self.button_elements[MEOW_EXPORT_VGRID_BUTTON].disabled = \
                        True
                    self.button_elements[MEOW_EXPORT_VGRID_BUTTON].tooltip = \
                        "Export is not available as VGrid has not been " \
                        "specified. "

            elif self.mode == CWL_MODE:
                self.button_elements[CWL_NEW_WORKFLOW_BUTTON].disabled = False
                if self.cwl[WORKFLOWS]:
                    self.button_elements[CWL_EDIT_WORKFLOW_BUTTON].disabled = \
                        False
                else:
                    self.button_elements[CWL_EDIT_WORKFLOW_BUTTON].disabled = \
                        True

                self.button_elements[CWL_NEW_STEP_BUTTON].disabled = False
                if self.cwl[STEPS]:
                    self.button_elements[CWL_EDIT_STEP_BUTTON].disabled = False
                else:
                    self.button_elements[CWL_EDIT_STEP_BUTTON].disabled = True

                self.button_elements[CWL_NEW_VARIABLES_BUTTON].disabled = False
                if self.cwl[SETTINGS]:
                    self.button_elements[CWL_EDIT_VARIABLES_BUTTON].disabled =\
                        False
                else:
                    self.button_elements[CWL_EDIT_VARIABLES_BUTTON].disabled = \
                        True

                if self.meow[PATTERNS] or self.meow[RECIPES]:
                    self.button_elements[CWL_IMPORT_MEOW_BUTTON].disabled = \
                        False
                else:
                    self.button_elements[CWL_IMPORT_MEOW_BUTTON].disabled = \
                        True

                self.button_elements[CWL_IMPORT_DIR_BUTTON].disabled = False
                self.button_elements[CWL_EXPORT_DIR_BUTTON].disabled = False

    def __create_new_form(
            self, form_parts, done_function, label_text, selector_key=None,
            selector_dict=None, delete_func=None
    ):
        self.form_inputs = {}
        self.form_sections = {}
        dropdown = None

        rows = []
        if selector_key is not None and selector_dict is not None:
            options = []
            for key in selector_dict:
                options.append(key)

            label = widgets.Label(
                value="Select %s: " % label_text,
                layout=widgets.Layout(width='20%', min_width='10ex')
            )

            def on_dropdown_select(change):
                if change['type'] == 'change' and change['name'] == 'value':
                    to_update = [i[INPUT_KEY] for i in form_parts]
                    selected_object = selector_dict[change['new']]
                    if isinstance(selected_object, Pattern):
                        selected_object = selected_object.to_display_dict()
                    # Generate a form with enough inputs for all the data
                    for form_part in form_parts:
                        updating_element = \
                            self.form_inputs[form_part[INPUT_KEY]]
                        if isinstance(updating_element, list):

                            values_count = \
                                len(selected_object[form_part[INPUT_KEY]])
                            required_inputs = values_count - 1
                            if required_inputs < 0:
                                required_inputs = 0
                            if type(selected_object[form_part[INPUT_KEY]]) \
                                    == dict:
                                section = self.__form_multi_dict_input(
                                    form_part[INPUT_KEY],
                                    form_part[INPUT_NAME],
                                    form_part[INPUT_HELP],
                                    form_part[INPUT_OPTIONAL],
                                    required_inputs
                                )
                            else:
                                section = self.__form_multi_text_input(
                                    form_part[INPUT_KEY],
                                    form_part[INPUT_NAME],
                                    form_part[INPUT_HELP],
                                    form_part[INPUT_OPTIONAL],
                                    required_inputs
                                )
                            self.form_sections[form_part[INPUT_KEY]] = section

                    # Populate form with selected object information
                    for update in to_update:
                        updating_element = self.form_inputs[update]
                        if isinstance(updating_element, list):
                            value_list = selected_object[update]
                            for index, item in enumerate(updating_element):
                                # TODO get rid of this distinction
                                if isinstance(value_list, dict):
                                    keys = list(value_list.keys())
                                    if index < len(selected_object[update]):
                                        item[NAME_KEY].value = keys[index]
                                        item[VALUE_KEY].value = str(value_list[keys[index]])
                                else:
                                    if index < len(selected_object[update]):
                                        item.value = value_list[index]
                        else:
                            self.form_inputs[update].value = \
                                str(selected_object[update])

                    delete_button.disabled = False
                    self.__refresh_current_form_layout()
            dropdown = widgets.Dropdown(
                options=options,
                value=None,
                description="",
                disabled=False,
                layout=widgets.Layout(width='65%')
            )
            dropdown.observe(on_dropdown_select)

            def delete_button_click(button):
                delete_func(dropdown.value)
            delete_button = widgets.Button(
                value=False,
                description="Delete",
                disabled=True,
                button_style='',
                tooltip='Deletes the selected %s. Once done, this cannot be '
                        'undone. ' % label_text,
                layout=widgets.Layout(width='10%', min_width='8ex')
            )
            delete_button.on_click(delete_button_click)

            selector_row = widgets.HBox([
                label,
                dropdown,
                delete_button
            ])

            self.form_sections[FORM_SELECTOR_KEY] = selector_row
            rows.append(selector_row)

        for element in form_parts:
            if element[INPUT_TYPE] == FORM_SINGLE_INPUT:
                form_section = self.__form_single_text_input(
                    element[INPUT_KEY],
                    element[INPUT_NAME],
                    element[INPUT_HELP],
                    element[INPUT_OPTIONAL]
                )
                self.form_sections[element[INPUT_KEY]] = form_section
                rows.append(form_section)
            elif element[INPUT_TYPE] == FORM_MULTI_INPUT:
                form_section = self.__form_multi_text_input(
                    element[INPUT_KEY],
                    element[INPUT_NAME],
                    element[INPUT_HELP],
                    element[INPUT_OPTIONAL]
                )
                self.form_sections[element[INPUT_KEY]] = form_section
                rows.append(form_section)
            elif element[INPUT_TYPE] == FORM_DICT_INPUT:
                form_section = self.__form_multi_dict_input(
                    element[INPUT_KEY],
                    element[INPUT_NAME],
                    element[INPUT_HELP],
                    element[INPUT_OPTIONAL],
                )
                self.form_sections[element[INPUT_KEY]] = form_section
                rows.append(form_section)

        def done_button_click(button):
            values = {}
            if dropdown:
                values[selector_key] = dropdown.value
            for key, form_input in self.form_inputs.items():
                if isinstance(form_input, list):
                    values_list = []
                    for row in form_input:
                        if isinstance(row, dict):
                            values_dict = {}
                            for k, v in row.items():
                                values_dict[k] = v.value
                            values_list.append(values_dict)
                        else:
                            values_list.append(row.value)
                    values[key] = values_list
                else:
                    values[key] = form_input.value
            done_function(values)
        done_button = widgets.Button(
            value=False,
            description="Done",
            disabled=False,
            button_style='',
            tooltip='Create new %s with the given parameters. ' % label_text
        )
        done_button.on_click(done_button_click)

        def cancel_button_click(button):
            self.__close_form()
            self.__clear_feedback()

            pass
        cancel_button = widgets.Button(
            value=False,
            description="Cancel",
            disabled=False,
            button_style='',
            tooltip='Cancel %s creation. No data will be saved. ' % label_text
        )
        cancel_button.on_click(cancel_button_click)

        if selector_key is not None and selector_dict is not None:
            done_button.tooltip = \
                'Apply changes to selected %s. This will overwrite existing ' \
                'data and cannot be undone. ' % label_text
            cancel_button.tooltip = \
                'Cancel editing the selected %s. No data will be changed. ' \
                % label_text

        bottom_row = widgets.HBox([
            done_button,
            cancel_button
        ])
        self.form_sections[FORM_BUTTONS_KEY] = bottom_row
        rows.append(bottom_row)

        form = widgets.VBox(
            rows
        )

        self.form_area.clear_output(wait=True)
        with self.form_area:
            display(form)

    def __refresh_current_form_layout(self):

        rows = []
        for section in self.form_sections.values():
            rows.append(section)

        form = widgets.VBox(
            rows
        )

        self.form_area.clear_output(wait=True)
        with self.form_area:
            display(form)

    def __close_form(self):
        # self.displayed_form = None
        self.form_area.clear_output()
        self.__enable_top_buttons()
        self.__clear_current_form()

    def __clear_current_form(self):
        # TODO update this description

        self.form_inputs = {}
        # self.current_form_rows = {}
        # self.current_form_line_counts = {}

    def __make_help_button(self, help_text):
        # TODO update this description

        default_tooltip_text = 'Displays additional help text. '

        help_button = widgets.Button(
            value=False,
            description='',
            disabled=False,
            button_style='',
            tooltip=default_tooltip_text,
            icon='question',
            layout=widgets.Layout(width='5%', min_width='4ex')
        )
        help_html = widgets.HTML(
            value=""
        )

        def help_button_click(button):
            if help_html.value is "":
                message = help_text
                help_html.value = message
                help_button.tooltip = 'Hides the related help text. '
            else:
                help_html.value = ""
                help_button.tooltip = default_tooltip_text
        help_button.on_click(help_button_click)

        return help_button, help_html

    def __make_additional_input_row(self, key):
        hidden_label = widgets.Label(
            value="",
            layout=widgets.Layout(width='20%', min_width='10ex')
        )

        additional_input = widgets.Text(
            layout=widgets.Layout(width='75%')
        )

        self.form_inputs[key].append(additional_input)

        return widgets.HBox([
            hidden_label,
            additional_input
        ])

    def __make_dict_input_row(self, key, output_items):

        hidden_label = widgets.Label(
            value="",
            layout=widgets.Layout(width='20%', min_width='10ex')
        )

        name_input = widgets.Text(
            layout=widgets.Layout(width='20%')
        )

        value_input = widgets.Text(
            layout=widgets.Layout(width='55%')
        )

        self.form_inputs[key].append({
            NAME_KEY: name_input,
            VALUE_KEY: value_input
        })

        row = widgets.HBox([
            hidden_label,
            name_input,
            value_input
        ])

        output_items.insert(-1, row)

    def __form_single_text_input(
            self, key, display_text, help_text, optional=False
    ):
        label_text = display_text
        if optional:
            label_text += " (optional)"
        label = widgets.Label(
            value="%s: " % label_text,
            layout=widgets.Layout(width='20%', min_width='10ex')
        )

        input = widgets.Text(
            layout=widgets.Layout(width='70%')
        )

        self.form_inputs[key] = input

        help_button, help_text = self.__make_help_button(help_text)

        top_row_items = [
            label,
            input,
            help_button
        ]

        top_row = widgets.HBox(top_row_items)

        items = [
            top_row,
            help_text
        ]

        input_widget = widgets.VBox(
            items,
            layout=widgets.Layout(width='100%'))
        return input_widget

    def __form_multi_text_input(
            self, key, display_text, help_text, optional=False,
            additional_inputs=None,
    ):
        output_items = []

        label_text = display_text
        if optional:
            label_text += " (optional)"
        label = widgets.Label(
            value="%s: " % label_text,
            layout=widgets.Layout(width='20%', min_width='10ex')
        )

        input = widgets.Text(
            layout=widgets.Layout(width='59%')
        )

        self.form_inputs[key] = [input]

        def activate_remove_button():
            if key in self.form_inputs.keys():
                if len(self.form_inputs[key]) > 1:
                    remove_button.disabled = False
                    return
            remove_button.disabled = True

        def add_button_click(button):
            additional_row = self.__make_additional_input_row(key)
            output_items.insert(-1, additional_row)
            expanded_section = widgets.VBox(
                output_items,
                layout=widgets.Layout(width='100%')
            )
            self.form_sections[key] = expanded_section
            activate_remove_button()
            self.__refresh_current_form_layout()
        add_button = widgets.Button(
            value=False,
            description='',
            disabled=False,
            button_style='',
            tooltip="Add %s" % display_text.lower(),
            icon='plus',
            layout=widgets.Layout(width='5%', min_width='5ex')
        )
        add_button.on_click(add_button_click)

        def remove_button_click(button):
            del self.form_inputs[key][-1]
            del output_items[-2]
            reduced_section = widgets.VBox(
                output_items,
                layout=widgets.Layout(width='100%')
            )
            self.form_sections[key] = reduced_section
            activate_remove_button()
            self.__refresh_current_form_layout()
        remove_button = widgets.Button(
            value=False,
            description='',
            disabled=False,
            button_style='',
            tooltip='Removes the last %s. Note that if a value is in this '
                    'box it will be lost. ' % label_text.lower(),
            icon='minus',
            layout=widgets.Layout(width='5%', min_width='5ex')
        )
        remove_button.on_click(remove_button_click)
        activate_remove_button()

        help_button, help_text = self.__make_help_button(help_text)

        top_row_items = [
            label,
            input,
            add_button,
            remove_button,
            help_button
        ]

        top_row = widgets.HBox(top_row_items)

        output_items = [
            top_row,
            help_text
        ]

        if additional_inputs:
            for x in range(0, additional_inputs):
                additional_row = self.__make_additional_input_row(key)
                output_items.insert(-1, additional_row)

        section = widgets.VBox(
            output_items,
            layout=widgets.Layout(width='100%')
        )
        return section

    def __form_multi_dict_input(
            self, key, display_text, help_text,
            optional=False, additional_inputs=None,
    ):
        output_items = []

        label_text = display_text
        if optional:
            label_text += " (optional)"
        label = widgets.Label(
            value="%s: " % label_text,
            layout=widgets.Layout(width='20%', min_width='10ex')
        )

        key_label = widgets.Label(
            value="%s: " % NAME_KEY,
            layout=widgets.Layout(width='20%')
        )

        value_label = widgets.Label(
            value="%s: " % VALUE_KEY,
            layout=widgets.Layout(width='39%')
        )

        def activate_remove_button():
            if key in self.form_inputs.keys():
                if len(self.form_inputs[key]) > 1:
                    remove_button.disabled = False
                    return
            remove_button.disabled = True

        def add_button_click(button):
            self.__make_dict_input_row(key, output_items)
            expanded_section = widgets.VBox(
                output_items,
                layout=widgets.Layout(width='100%')
            )
            self.form_sections[key] = expanded_section
            activate_remove_button()
            self.__refresh_current_form_layout()
        add_button = widgets.Button(
            value=False,
            description='',
            disabled=False,
            button_style='',
            tooltip="Add %s" % display_text.lower(),
            icon='plus',
            layout=widgets.Layout(width='5%', min_width='5ex')
        )
        add_button.on_click(add_button_click)

        def remove_button_click(button):
            del self.form_inputs[key][-1]
            del output_items[-2]
            reduced_section = widgets.VBox(
                output_items,
                layout=widgets.Layout(width='100%')
            )
            self.form_sections[key] = reduced_section
            activate_remove_button()
            self.__refresh_current_form_layout()
        remove_button = widgets.Button(
            value=False,
            description='',
            disabled=False,
            button_style='',
            tooltip='Removes the last %s. Note that if a value is in this '
                    'box it will be lost. ' % label_text.lower(),
            icon='minus',
            layout=widgets.Layout(width='5%', min_width='5ex')
        )
        remove_button.on_click(remove_button_click)
        activate_remove_button()

        help_button, help_text = self.__make_help_button(help_text)

        top_row_items = [
            label,
            key_label,
            value_label,
            add_button,
            remove_button,
            help_button
        ]

        top_row = widgets.HBox(top_row_items)

        output_items = [
            top_row,
            help_text
        ]

        self.form_inputs[key] = []

        self.__make_dict_input_row(key, output_items)

        if additional_inputs:
            for x in range(0, additional_inputs):
                self.__make_dict_input_row(key, output_items)

        section = widgets.VBox(
            output_items,
            layout=widgets.Layout(width='100%')
        )
        return section

    def __create_confirmation_buttons(
            self, confirmation_function, confirmation_args, confirm_text,
            cancel_text, cancel_feedback
    ):
        confirm_button = widgets.Button(
            value=False,
            description=confirm_text,
            disabled=False,
            button_style='',
            tooltip='TODO'
        )

        def confirm_button_click(button):
            confirmation_function(**confirmation_args)

        confirm_button.on_click(confirm_button_click)

        cancel_button = widgets.Button(
            value=False,
            description=cancel_text,
            disabled=False,
            button_style='',
            tooltip='TODO'
        )

        def cancel_button_click(button):
            self.__set_feedback(cancel_feedback)
            self.__close_form()

        cancel_button.on_click(cancel_button_click)

        buttons_list = [
            confirm_button,
            cancel_button
        ]

        confirmation_buttons = widgets.HBox(buttons_list)

        with self.form_area:
            display(confirmation_buttons)

    def __process_new_pattern(self, values, editing=False):
        # TODO update this description

        try:
            pattern = Pattern(values[NAME])
            if not editing:
                if values[NAME] in self.meow[PATTERNS]:
                    msg = "%s name is not valid as another %s is " \
                          "already registered with that name. " \
                          % (PATTERN_NAME, PATTERN_NAME)
                    self.__set_feedback(msg)
                    return
            file_name = values[INPUT_FILE]
            trigger_paths = values[TRIGGER_PATHS]
            trigger_output = values[TRIGGER_OUTPUT]
            if len(trigger_paths) == 1:
                if trigger_output:
                    pattern.add_single_input(file_name,
                                             trigger_paths[0],
                                             output_path=trigger_output)
                else:
                    pattern.add_single_input(file_name, trigger_paths[0])
            else:
                # TODO Currently ignores any additional trigger paths.
                #  fix this once mig formatting complete.
                if trigger_output:
                    pattern.add_single_input(file_name,
                                             trigger_paths[0],
                                             output_path=trigger_output)
                else:
                    pattern.add_single_input(file_name, trigger_paths[0])
            notebook_return = values[NOTEBOOK_OUTPUT]
            if notebook_return:
                pattern.return_notebook(notebook_return)
            for recipe in values[RECIPES]:
                pattern.add_recipe(recipe)
            for variable in values[VARIABLES]:
                if variable[VALUE_KEY]:
                    pattern.add_variable(variable[NAME_KEY], variable[VALUE_KEY])
            for output in values[OUTPUT]:
                if output[VALUE_KEY]:
                    pattern.add_output(output[NAME_KEY], output[VALUE_KEY])
            valid, warnings = pattern.integrity_check()
            if valid:
                if pattern.name in self.meow[PATTERNS]:
                    word = 'updated'
                    try:
                        pattern.persistence_id = \
                            self.meow[PATTERNS][pattern.name].persistence_id
                    except AttributeError:
                        pass

                else:
                    word = 'created'
                self.meow[PATTERNS][pattern.name] = pattern
                msg = "%s \'%s\' %s. " % (PATTERN_NAME, pattern.name, word)
                if warnings:
                    msg += "\n%s" % warnings
                self.__set_feedback(msg)
                self.__update_workflow_visualisation()
                self.__close_form()
                return True
            else:
                msg = "%s is not valid. " % PATTERN_NAME
                if warnings:
                    msg += "\n%s" % warnings
                self.__set_feedback(msg)
                return False
        except Exception as e:
            msg = "Something went wrong with %s generation. %s" \
                  % (PATTERN_NAME, str(e))
            self.__set_feedback(msg)
            return False

    def __process_new_recipe(self, values, ignore_conflicts=False):
        # TODO update this description

        try:
            source = values[SOURCE]
            name = values[NAME]

            valid_path(
                source,
                'Source',
                extensions=NOTEBOOK_EXTENSIONS
            )
            if os.path.sep in source:
                filename = \
                    source[source.index('/') + 1:source.index('.')]
            else:
                filename = source[:source.index('.')]
            if not name:
                name = filename
            if not os.path.isfile(source):
                self.__set_feedback("Source %s was not found. " % source)
                return
            if name:
                valid_string(name,
                             'Name',
                             CHAR_UPPERCASE
                             + CHAR_LOWERCASE
                             + CHAR_NUMERIC
                             + CHAR_LINES)
                if not ignore_conflicts:
                    if name in self.meow[RECIPES]:
                        msg = "%s name is not valid as another %s " \
                              "is already registered with that name. Please " \
                              "try again using a different name. " \
                              % (RECIPE_NAME, RECIPE_NAME)
                        self.__set_feedback(msg)
                        return

            with open(source, "r") as read_file:
                notebook = json.load(read_file)
                recipe = create_recipe_dict(notebook, name, source)
                if name in self.meow[RECIPES]:
                    word = 'updated'
                    try:
                        recipe[PERSISTENCE_ID] = \
                            self.meow[RECIPES][name][PERSISTENCE_ID]
                    except KeyError:
                        pass
                else:
                    word = 'created'
                self.meow[RECIPES][name] = recipe
                self.__set_feedback(
                    "%s \'%s\' %s. " % (RECIPE_NAME, name, word)
                )
            self.__update_workflow_visualisation()
            self.__close_form()
            return True
        except Exception as e:
            self.__set_feedback(
                "Something went wrong with %s generation. %s "
                % (RECIPE_NAME, str(e))
            )
            return False

    def __process_new_workflow(self, values, editing=False):
        try:
            name = values[CWL_NAME]
            inputs_list = values[CWL_INPUTS]
            outputs_list = values[CWL_OUTPUTS]
            requirements_list = values[CWL_REQUIREMENTS]
            steps_list = values[CWL_STEPS]

            if not name:
                msg = "%s name was not provided. " % WORKFLOW_NAME
                self.__set_feedback(msg)
                return False

            valid_string(name,
                         'Name',
                         CHAR_UPPERCASE
                         + CHAR_LOWERCASE
                         + CHAR_NUMERIC
                         + CHAR_LINES)
            if not editing:
                if name in self.cwl[WORKFLOWS]:
                    msg = "%s name is not valid as another %s " \
                          "is already registered with that name. Please " \
                          "try again using a different name. " \
                          % (WORKFLOW_NAME, WORKFLOW_NAME)
                    self.__set_feedback(msg)
                    return False

            inputs_dict = list_to_dict(inputs_list)
            outputs_dict = list_to_dict(outputs_list)
            requirements_dict = list_to_dict(requirements_list)
            steps_dict = list_to_dict(steps_list)

            workflow = make_workflow_dict(name)
            workflow[CWL_INPUTS] = inputs_dict
            workflow[CWL_OUTPUTS] = outputs_dict
            workflow[CWL_REQUIREMENTS] = requirements_dict
            workflow[CWL_STEPS] = steps_dict

            self.cwl[WORKFLOWS][name] = workflow

            self.__set_feedback(
                "%s \'%s\': %s. " % (WORKFLOW_NAME, name, workflow)
            )

            self.__update_workflow_visualisation()
            self.__close_form()
            return True
        except Exception as e:
            self.__set_feedback(
                "Something went wrong with %s generation. %s "
                % (WORKFLOW_NAME, str(e))
            )
            return False

    def __process_new_step(self, values, editing=False):
        try:
            name = values[CWL_NAME]
            base_command = values[CWL_BASE_COMMAND]
            stdout = values[CWL_STDOUT]
            inputs_list = values[CWL_INPUTS]
            outputs_list = values[CWL_OUTPUTS]
            arguments_buffer = values[CWL_ARGUMENTS]
            requirements_list = values[CWL_REQUIREMENTS]
            hints_list = values[CWL_HINTS]

            # This is necessary as arguments_buffer may contain empty strings
            arguments = []
            for argument in arguments_buffer:
                if argument:
                    arguments.append(argument)

            if not name:
                msg = "%s name was not provided. " % STEP_NAME
                self.__set_feedback(msg)
                return False

            valid_string(name,
                         'Name',
                         CHAR_UPPERCASE
                         + CHAR_LOWERCASE
                         + CHAR_NUMERIC
                         + CHAR_LINES)
            if not editing:
                if name in self.cwl[STEPS]:
                    msg = "%s name is not valid as another %s " \
                          "is already registered with that name. Please " \
                          "try again using a different name. " \
                          % (STEP_NAME, STEP_NAME)
                    self.__set_feedback(msg)
                    return False

            inputs_dict = list_to_dict(inputs_list)
            outputs_dict = list_to_dict(outputs_list)
            requirements_dict = list_to_dict(requirements_list)
            hints_dict = list_to_dict(hints_list)

            step = make_step_dict(name, base_command)
            step[CWL_STDOUT] = stdout
            step[CWL_INPUTS] = inputs_dict
            step[CWL_OUTPUTS] = outputs_dict
            step[CWL_ARGUMENTS] = arguments
            step[CWL_REQUIREMENTS] = requirements_dict
            step[CWL_HINTS] = hints_dict

            self.cwl[STEPS][name] = step

            self.__set_feedback(
                "%s \'%s\': %s. " % (STEP_NAME, name, step)
            )

            self.__update_workflow_visualisation()
            self.__close_form()
            return True
        except Exception as e:
            self.__set_feedback(
                "Something went wrong with %s generation. %s "
                % (STEP_NAME, str(e))
            )
            return False

    def __process_new_variables(self, values, editing=False):
        try:
            name = values[CWL_NAME]
            variables_list = values[CWL_VARIABLES]

            if not name:
                msg = "%s name was not provided. " % VARIABLES_NAME
                self.__set_feedback(msg)
                return False

            valid_string(name,
                         'Name',
                         CHAR_UPPERCASE
                         + CHAR_LOWERCASE
                         + CHAR_NUMERIC
                         + CHAR_LINES)
            if not editing:
                if name in self.cwl[SETTINGS]:
                    msg = "%s name is not valid as another %s " \
                          "is already registered with that name. Please " \
                          "try again using a different name. " \
                          % (VARIABLES_NAME, VARIABLES_NAME)
                    self.__set_feedback(msg)
                    return False

            variables_dict = list_to_dict(variables_list)
            settings = make_settings_dict(name, variables_dict)
            self.cwl[VARIABLES][name] = settings

            self.__set_feedback(
                "%s \'%s\': %s. " % (VARIABLES_NAME, name, variables_dict)
            )

            self.__update_workflow_visualisation()
            self.__close_form()
            return True
        except Exception as e:
            self.__set_feedback(
                "Something went wrong with %s generation. %s "
                % (VARIABLES_NAME, str(e))
            )
            return False

    def __process_editing_pattern(self, values):
        # TODO update this description

        if self.__process_new_pattern(values, editing=True):
            self.__update_workflow_visualisation()
            self.__close_form()

    def __process_editing_recipe(self, values):
        # TODO update this description

        if self.__process_new_recipe(values, ignore_conflicts=True):
            self.__update_workflow_visualisation()
            self.__close_form()

    def __process_editing_workflow(self, values):
        if self.__process_new_workflow(values, editing=True):
            self.__update_workflow_visualisation()
            self.__close_form()

    def __process_editing_step(self, values):
        if self.__process_new_step(values, editing=True):
            self.__update_workflow_visualisation()
            self.__close_form()

    def __process_editing_variables(self, values):
        if self.__process_new_variables(values, editing=True):
            self.__update_workflow_visualisation()
            self.__close_form()

    def __process_delete_pattern(self, to_delete):
        if to_delete in self.meow[PATTERNS]:
            self.meow[PATTERNS].pop(to_delete)
        self.__set_feedback("%s %s deleted. " % (RECIPE_NAME, to_delete))
        self.__update_workflow_visualisation()
        self.__close_form()

    def __process_delete_recipe(self, to_delete):
        if to_delete in self.meow[RECIPES]:
            self.meow[RECIPES].pop(to_delete)
        self.__set_feedback("%s %s deleted. " % (PATTERN_NAME, to_delete))
        self.__update_workflow_visualisation()
        self.__close_form()

    def __process_delete_workflow(self, to_delete):
        if to_delete in self.cwl[WORKFLOWS]:
            self.cwl[WORKFLOWS].pop(to_delete)
        self.__set_feedback("%s %s deleted. " % (WORKFLOW_NAME, to_delete))
        self.__update_workflow_visualisation()
        self.__close_form()

    def __process_delete_step(self, to_delete):
        if to_delete in self.cwl[STEPS]:
            self.cwl[STEPS].pop(to_delete)
        self.__set_feedback("%s %s deleted. " % (STEP_NAME, to_delete))
        self.__update_workflow_visualisation()
        self.__close_form()

    def __process_delete_variables(self, to_delete):
        if to_delete in self.cwl[SETTINGS]:
            self.cwl[SETTINGS].pop(to_delete)
        self.__set_feedback("%s %s deleted. " % (VARIABLES_NAME, to_delete))
        self.__update_workflow_visualisation()
        self.__close_form()

    def __import_from_vgrid(self, confirm=True):
        if not self.vgrid:
            self.__add_to_feedback(NO_VGRID_MSG)
            return

        self.__add_to_feedback(
            "Importing workflow from Vgrid. This may take a few seconds.")

        try:
            _, response, _ = vgrid_workflow_json_call(
                self.vgrid,
                VGRID_READ,
                'any',
                {},
                print_feedback=False
            )
        except LookupError as error:
            self.__set_feedback(error)
            self.__enable_top_buttons()
            return
        except Exception as error:
            self.__set_feedback(str(error))
            self.__enable_top_buttons()
            return
        self.__clear_feedback()
        response_patterns = {}
        response_recipes = {}
        if VGRID_WORKFLOWS_OBJECT in response:
            for response_object in response[VGRID_WORKFLOWS_OBJECT]:
                if response_object[OBJECT_TYPE] == VGRID_PATTERN_OBJECT_TYPE:
                    response_patterns[response_object[NAME]] = response_object
                elif response_object[OBJECT_TYPE] == VGRID_RECIPE_OBJECT_TYPE:
                    response_recipes[response_object[NAME]] = response_object

            args = {
                PATTERNS: response_patterns,
                RECIPES: response_recipes
            }
            if confirm:
                self.__add_to_feedback(
                    "Found %s %s(s) from Vgrid %s: %s "
                    % (len(response_patterns), PATTERN_NAME, self.vgrid,
                       list(response_patterns.keys()))
                )
                self.__add_to_feedback(
                    "Found %s %s(s) from Vgrid %s: %s "
                   % (len(response_recipes), RECIPE_NAME, self.vgrid,
                      list(response_recipes.keys())))

                self.__add_to_feedback(
                    "Import these %s(s) and %s(s) into local memory? This "
                    "will overwrite any %s(s) or %s(s) currently in memory "
                    "that share the same name. "
                    % (PATTERN_NAME, RECIPE_NAME, PATTERN_NAME, RECIPE_NAME)
                )

                self.__create_confirmation_buttons(
                    self.__import_meow_workflow,
                    args,
                    "Confirm Import",
                    "Cancel Import",
                    "Import canceled. No local data has been changed. "
                )
            else:
                self.__import_meow_workflow(**args)

        elif response[OBJECT_TYPE] == VGRID_ERROR_TYPE:
            self.__set_feedback(response[VGRID_TEXT_TYPE])
        else:
            self.__set_feedback('Got an unexpected response')
            self.__add_to_feedback("Unexpected response: {}".format(response))
        self.__enable_top_buttons()

    def __import_meow_workflow(self, **kwargs):
        response_patterns = kwargs.get(PATTERNS, None)
        response_recipes = kwargs.get(RECIPES, None)

        self.mig_imports = {
            PATTERNS: {},
            RECIPES: {}
        }
        overwritten_patterns = []
        overwritten_recipes = []
        for key, pattern in response_patterns.items():
            if key in self.meow[PATTERNS]:
                overwritten_patterns.append(key)
            if not isinstance(pattern, Pattern):
                pattern = Pattern(pattern)
            self.meow[PATTERNS][key] = pattern
            try:
                self.mig_imports[PATTERNS][pattern.persistence_id] = \
                    deepcopy(pattern)
            except AttributeError:
                pass
        for key, recipe in response_recipes.items():
            if key in self.meow[RECIPES]:
                overwritten_recipes.append(key)
            self.meow[RECIPES][key] = recipe
            try:
                self.mig_imports[RECIPES][recipe[PERSISTENCE_ID]] = \
                    deepcopy(recipe)
            except KeyError:
                pass

        msg = "Imported %s %s(s) and %s %s(s). " \
              % (len(response_patterns), PATTERN_NAME,
                 len(response_recipes), RECIPE_NAME)
        if overwritten_patterns:
            msg += "<br/>Overwritten %s(s): %s " \
                   % (PATTERN_NAME, overwritten_patterns)
        if overwritten_recipes:
            msg += "<br/>Overwritten %s(s): %s " \
                   % (RECIPE_NAME, overwritten_recipes)
        self.__set_feedback(msg)
        self.__update_workflow_visualisation()
        self.__close_form()

    def __export_to_vgrid(self):
        if not self.vgrid:
            self.__set_feedback(NO_VGRID_MSG)
            return

        calls = []
        pattern_ids = []
        for _, pattern in self.meow[PATTERNS].items():
            attributes = {
                NAME: pattern.name,
                INPUT_FILE: pattern.trigger_file,
                TRIGGER_PATHS: pattern.trigger_paths,
                OUTPUT: pattern.outputs,
                RECIPES: pattern.recipes,
                VARIABLES: pattern.variables
            }
            try:
                if pattern.persistence_id:
                    attributes[PERSISTENCE_ID] = pattern.persistence_id
                    pattern_ids.append(pattern.persistence_id)
            except AttributeError:
                pass
            try:
                operation = None
                if PERSISTENCE_ID in attributes:
                    if self.meow[PATTERNS][pattern.name] != \
                            self.mig_imports[PATTERNS][pattern.persistence_id]:
                        operation = VGRID_UPDATE

                else:
                    operation = VGRID_CREATE
                if operation:
                    calls.append(
                        (
                            operation,
                            VGRID_PATTERN_OBJECT_TYPE,
                            attributes,
                            False,
                            pattern
                        )
                    )
            except LookupError as error:
                self.__set_feedback(error)
                return

        recipe_ids = []
        for _, recipe in self.meow[RECIPES].items():
            try:
                attributes = {
                    NAME: recipe[NAME],
                    RECIPE: recipe[RECIPE],
                    SOURCE: recipe[SOURCE]
                }
                try:
                    if recipe[PERSISTENCE_ID]:
                        attributes[PERSISTENCE_ID] = recipe[PERSISTENCE_ID]
                        recipe_ids.append(recipe[PERSISTENCE_ID])
                except KeyError:
                    pass
                operation = None
                if PERSISTENCE_ID in attributes:
                    if self.meow[RECIPES][recipe[NAME]] != \
                            self.mig_imports[RECIPES][recipe[PERSISTENCE_ID]]:
                        operation = VGRID_UPDATE
                else:
                    operation = VGRID_CREATE
                if operation:
                    calls.append(
                        (
                            operation,
                            VGRID_RECIPE_OBJECT_TYPE,
                            attributes,
                            False,
                            recipe
                        )
                    )
            except LookupError as error:
                self.__set_feedback(error)
                return

        operation = VGRID_DELETE
        for id, pattern in self.mig_imports[PATTERNS].items():
            if id not in pattern_ids:
                attributes = {
                    PERSISTENCE_ID: id,
                    NAME: pattern.name
                }
                calls.append(
                    (
                        operation,
                        VGRID_PATTERN_OBJECT_TYPE,
                        attributes,
                        False
                    )
                )
        for id, recipe in self.mig_imports[RECIPES].items():
            if id not in recipe_ids:
                attributes = {
                    PERSISTENCE_ID: id,
                    NAME: recipe[NAME]
                }
                calls.append(
                    (
                        operation,
                        VGRID_RECIPE_OBJECT_TYPE,
                        attributes,
                        False
                    )
                )
        self.__enable_top_buttons()

        if not calls:
            self.__set_feedback(
                "No %ss or %ss have been created, updated or "
                "deleted so there is nothing to export to the Vgrid"
                % (PATTERN_NAME, RECIPE_NAME)
            )
            return

        operation_combinations = [
            (VGRID_CREATE, VGRID_PATTERN_OBJECT_TYPE),
            (VGRID_CREATE, VGRID_RECIPE_OBJECT_TYPE),
            (VGRID_UPDATE, VGRID_PATTERN_OBJECT_TYPE),
            (VGRID_UPDATE, VGRID_RECIPE_OBJECT_TYPE),
            (VGRID_DELETE, VGRID_PATTERN_OBJECT_TYPE),
            (VGRID_DELETE, VGRID_RECIPE_OBJECT_TYPE),
        ]

        for operation in operation_combinations:
            relevant_calls = count_calls(calls, operation[0], operation[1])

            if relevant_calls:
                self.__add_to_feedback("Will %s %s %s: %s. "
                                       % (operation[0], len(relevant_calls),
                                          operation[1], relevant_calls))

        # Strip names from delete calls. They were only included for feedback
        # purposes and may complicate mig operations

        self.__create_confirmation_buttons(
            self.__export_workflow,
            {
                'calls': calls
            },
            "Confirm Export",
            "Cancel Export",
            "Export canceled. No VGrid data has been changed. "
        )

    def __export_workflow(self, **kwargs):
        self.__clear_feedback()
        calls = kwargs.get('calls', None)
        for call in calls:
            try:
                operation = call[0]
                object_type = call[1]
                args = call[2]

                _, response, _ = vgrid_workflow_json_call(
                    self.vgrid,
                    operation,
                    object_type,
                    args,
                    print_feedback=call[3]
                )

                msg = 'Unexpected feedback received'
                if 'text' in response:
                    if operation == VGRID_CREATE:
                        persistence_id = response['text']
                        if object_type == VGRID_PATTERN_OBJECT_TYPE:
                            pattern = call[4]
                            pattern.persistence_id = persistence_id
                            self.mig_imports[PATTERNS][persistence_id] = \
                                pattern
                            msg = "Created %s '%s'. " \
                                  % (PATTERN_NAME, pattern.name)
                        elif object_type == VGRID_RECIPE_OBJECT_TYPE:
                            recipe = call[4]
                            recipe[PERSISTENCE_ID] = persistence_id
                            self.mig_imports[RECIPES][persistence_id] = recipe
                            msg = "Created %s '%s'. " \
                                  % (RECIPE_NAME, recipe[NAME])

                    if operation == VGRID_UPDATE:
                        if object_type == VGRID_PATTERN_OBJECT_TYPE:
                            pattern = call[4]
                            self.mig_imports[PATTERNS][
                                pattern.persistence_id] = pattern
                            msg = "Updated %s '%s'. " \
                                  % (PATTERN_NAME, pattern.name)
                        elif object_type == VGRID_RECIPE_OBJECT_TYPE:
                            recipe = call[4]
                            self.mig_imports[RECIPES][
                                recipe[PERSISTENCE_ID]] = recipe
                            msg = "Updated %s '%s'. " \
                                  % (RECIPE_NAME, recipe[NAME])

                    if operation == VGRID_DELETE:
                        if object_type == VGRID_PATTERN_OBJECT_TYPE:
                            msg = "Deleted %s '%s'. " \
                                  % (PATTERN_NAME, args[NAME])
                        elif object_type == VGRID_RECIPE_OBJECT_TYPE:
                            msg = "Deleted %s '%s'. " \
                                  % (RECIPE_NAME, args[NAME])

                if 'error_text' in response:
                    feedback = response['error_text'].replace('\n', '<br/>')
                    msg = feedback
                self.__add_to_feedback(msg)

            except Exception as err:
                self.__set_feedback(err)
        self.__close_form()

    def __meow_to_cwl(self):
        meow_workflow = build_workflow_object(
            self.meow[PATTERNS],
            self.meow[RECIPES]
        )

        buffer_cwl = {
            WORKFLOWS: {},
            STEPS: {},
            SETTINGS: {}
        }

        step_count = 1
        yaml_dict = {}
        variable_references = {}
        pattern_to_step = {}
        step_to_pattern = {}
        output_lookups = {}
        for pattern in self.meow[PATTERNS].values():
            step_variable_dict = {}
            step_title = "step_%d" % step_count
            step_cwl_dict = make_step_dict(step_title, 'papermill')

            recipe_entry = "%d_notebook" % step_count
            result_entry = "%d_result" % step_count
            step_cwl_dict[CWL_INPUTS]['notebook'] = {
                CWL_INPUT_TYPE: 'File',
                CWL_INPUT_BINDING: {
                    CWL_INPUT_POSITION: 1
                }
            }
            # TODO edit this to combine recipes into one rather than ignoring
            #  them. Is currently misleading
            try:
                recipe = self.meow[RECIPES][pattern.recipes[0]]
                source_filename = strip_dirs(recipe[SOURCE])
            except KeyError:
                source_filename = PLACEHOLDER
            yaml_dict[recipe_entry] = {
                CWL_YAML_CLASS: 'File',
                CWL_YAML_PATH: source_filename
            }
            step_cwl_dict[CWL_INPUTS]['result'] = {
                CWL_INPUT_TYPE: 'string',
                CWL_INPUT_BINDING: {
                    CWL_INPUT_POSITION: 2
                }
            }
            yaml_dict[result_entry] = source_filename
            for result in DEFAULT_RESULT_NOTEBOOKS:
                if result in pattern.outputs:
                    yaml_dict[result_entry] = pattern.outputs[result]
            step_variable_dict['notebook'] = recipe_entry
            step_variable_dict['result'] = result_entry

            variable_count = 3
            for variable_key, variable_value in pattern.variables.items():
                # skip result variables
                if variable_key in DEFAULT_RESULT_NOTEBOOKS:
                    break

                if isinstance(variable_value, str):
                    if variable_value.startswith('"') \
                            and variable_value.endswith('"'):
                        variable_value = variable_value[1:-1]
                    if variable_value.startswith('\'') \
                            and variable_value.endswith('\''):
                        variable_value = variable_value[1:-1]
                variable_value = strip_dirs(variable_value)

                # If this is an input yaml file
                if variable_value == pattern.trigger_file \
                        and [e for e in pattern.trigger_paths
                             if '.yaml' in e or '.yml' in e]:

                    arg_key = "%d_%s" % (step_count, variable_key)

                    step_cwl_dict[CWL_INPUTS][variable_key] = {
                        CWL_INPUT_TYPE: 'File',
                        CWL_INPUT_BINDING: {
                            CWL_INPUT_PREFIX: '-f',
                            CWL_INPUT_POSITION: variable_count
                        }
                    }
                    yaml_dict[arg_key] = {
                        CWL_YAML_CLASS: 'File',
                        CWL_YAML_PATH: strip_dirs(pattern.trigger_paths[0])
                    }
                    step_variable_dict[variable_key] = arg_key
                    variable_count += 1

                else:
                    local_arg_key = "%s_key" % variable_key
                    local_arg_value = "%s_value" % variable_key
                    arg_key = "%d_%s" % (step_count, local_arg_key)
                    arg_value = "%d_%s" % (step_count, local_arg_value)
                    yaml_dict[arg_key] = variable_key

                    step_cwl_dict[CWL_INPUTS][local_arg_key] = {
                        CWL_INPUT_TYPE: 'string',
                        CWL_INPUT_BINDING: {
                            CWL_INPUT_PREFIX: '-p',
                            CWL_INPUT_POSITION: variable_count
                        }
                    }
                    variable_count += 1
                    input_type = 'string'
                    if variable_key in pattern.outputs:
                        variable_value = strip_dirs(pattern.outputs[variable_key])
                    yaml_dict[arg_value] = variable_value
                    if variable_key == pattern.trigger_file \
                            or ():
                        input_type = 'File'
                        yaml_dict[arg_value] = {
                            CWL_YAML_CLASS: 'File',
                            CWL_YAML_PATH: strip_dirs(pattern.trigger_paths[0])
                        }
                    elif isinstance(variable_value, str) \
                            and os.path.exists(variable_value):
                        input_type = 'File'
                        yaml_dict[arg_value] = {
                            CWL_YAML_CLASS: 'File',
                            CWL_YAML_PATH: variable_value
                        }

                    step_cwl_dict[CWL_INPUTS][local_arg_value] = {
                        CWL_INPUT_TYPE: input_type,
                        CWL_INPUT_BINDING: {
                            CWL_INPUT_POSITION: variable_count
                        }
                    }
                    step_variable_dict[local_arg_key] = arg_key
                    step_variable_dict[local_arg_value] = arg_value
                    variable_count += 1

            output_count = 0
            for output_key, output_value in pattern.outputs.items():
                local_output_key = "output_%d" % output_count

                if output_key in DEFAULT_RESULT_NOTEBOOKS:
                    output_binding = "%s.%s" % (CWL_INPUTS, output_key)
                else:
                    output_binding = "%s.%s_value" % (CWL_INPUTS, output_key)
                step_cwl_dict[CWL_OUTPUTS][local_output_key] = {
                    CWL_OUTPUT_TYPE: 'File',
                    CWL_OUTPUT_BINDING: {
                        CWL_OUTPUT_GLOB: "$(%s)" % output_binding
                    }
                }

                lookup_key = "%s_%s" % (pattern.name, output_key)
                output_lookups[lookup_key] = local_output_key

                output_count += 1

                # If non standard output then also add a variable note
                if output_key not in DEFAULT_RESULT_NOTEBOOKS:
                    local_arg_key = "%s_key" % output_key
                    local_arg_value = "%s_value" % output_key
                    arg_key = "%d_%s" % (step_count, local_arg_key)
                    arg_value = "%d_%s" % (step_count, local_arg_value)
                    yaml_dict[arg_key] = output_key
                    step_cwl_dict[CWL_INPUTS][local_arg_key] = {
                        CWL_INPUT_TYPE: 'string',
                        CWL_INPUT_BINDING: {
                            CWL_INPUT_PREFIX: '-p',
                            CWL_INPUT_POSITION: variable_count
                        }
                    }
                    variable_count += 1
                    input_type = 'string'
                    if output_key in pattern.outputs:
                        output_value = strip_dirs(pattern.outputs[output_key])
                    yaml_dict[arg_value] = output_value
                    if output_key == pattern.trigger_file:
                        input_type = 'File'
                        yaml_dict[arg_value] = {
                            CWL_YAML_CLASS: 'File',
                            CWL_YAML_PATH: strip_dirs(pattern.trigger_paths[0])
                        }

                    step_cwl_dict[CWL_INPUTS][local_arg_value] = {
                        CWL_INPUT_TYPE: input_type,
                        CWL_INPUT_BINDING: {
                            CWL_INPUT_POSITION: variable_count
                        }
                    }
                    step_variable_dict[local_arg_key] = arg_key
                    step_variable_dict[local_arg_value] = arg_value
                    variable_count += 1

            buffer_cwl[STEPS][step_title] = step_cwl_dict
            variable_references[step_title] = step_variable_dict
            pattern_to_step[pattern.name] = step_title
            step_to_pattern[step_title] = pattern.name
            step_count += 1

        buffer_cwl[SETTINGS][self.workflow_title] = \
            make_settings_dict(self.workflow_title, yaml_dict)

        workflow_cwl_dict = make_workflow_dict(self.workflow_title)

        for key, value in yaml_dict.items():
            if isinstance(value, dict):
                workflow_cwl_dict[CWL_INPUTS][key] = 'File'
            else:
                workflow_cwl_dict[CWL_INPUTS][key] = 'string'

        outlines = []
        for step_name, step in buffer_cwl[STEPS].items():

            separator = ', '
            all_outputs = separator.join(list(step[CWL_OUTPUTS].keys()))
            cwl_output = '[%s]' % all_outputs
            outline = "    %s: %s'\n" % (CWL_WORKFLOW_OUT, cwl_output)
            outlines.append(outline)

            step_dict = {
                CWL_WORKFLOW_RUN: '%s.cwl' % step_name,
                CWL_WORKFLOW_IN: {},
                CWL_WORKFLOW_OUT: cwl_output
            }

            for output_key, output_value in step[CWL_OUTPUTS].items():

                workflow_output_key = "output_%s_%s" % (step_name, output_key)
                workflow_cwl_dict[CWL_OUTPUTS][workflow_output_key] = {
                    CWL_OUTPUT_TYPE: 'File',
                    CWL_OUTPUT_SOURCE: '%s/%s' % (step_name, output_key)
                }

            separator = ', '
            all_outputs = separator.join(list(step[CWL_OUTPUTS].keys()))
            outline = "    %s: '[%s]'\n" % (CWL_WORKFLOW_OUT, all_outputs)
            outlines.append(outline)

            for input_key, input_value in step[CWL_INPUTS].items():
                step_dict[CWL_WORKFLOW_IN][input_key] = \
                    variable_references[step_name][input_key]

            current = meow_workflow[step_to_pattern[step_name]]
            if current[ANCESTORS]:
                for ancestor_key, ancestor_value in current[ANCESTORS].items():
                    ancestor_step_name = pattern_to_step[ancestor_key]
                    ancestor_outfile_key = ancestor_value['output_file']
                    output_lookup = "%s_%s" % (ancestor_key, ancestor_outfile_key)
                    ancestor_out = output_lookups[output_lookup]
                    current_key = "%s_value" % self.meow[PATTERNS][ancestor_key].trigger_file
                    if current_key in step_dict[CWL_WORKFLOW_IN]:
                        step_dict[CWL_WORKFLOW_IN][current_key] = \
                            "%s/%s" % (ancestor_step_name, ancestor_out)
                    else:
                        step_dict[CWL_WORKFLOW_IN][self.meow[PATTERNS][ancestor_key].trigger_file] = \
                            "%s/%s" % (ancestor_step_name, ancestor_out)

            workflow_cwl_dict[CWL_STEPS][step_name] = step_dict

        buffer_cwl[WORKFLOWS] = {
            self.workflow_title: workflow_cwl_dict
        }

        return True, buffer_cwl

    def __cwl_to_meow(self):
        buffer_meow = {
            PATTERNS: {},
            RECIPES: {}
        }

        for workflow_name, workflow in self.cwl[WORKFLOWS].items():
            status, msg = check_workflow_is_valid(workflow_name, self.cwl)

            if not status:
                return False, msg

            settings = self.cwl[SETTINGS][workflow_name][CWL_VARIABLES]

            for argument_key, argument_value in settings.items():
                if isinstance(argument_value, dict) \
                        and CWL_YAML_CLASS in argument_value\
                        and argument_value[CWL_YAML_CLASS] == 'File'\
                        and CWL_YAML_PATH in argument_value\
                        and '.' in argument_value[CWL_YAML_PATH]:
                    input_file = argument_value[CWL_YAML_PATH]
                    extension = input_file[input_file.rfind('.'):]

                    if extension in NOTEBOOK_EXTENSIONS:
                        source = os.path.join(
                            self.cwl_import_export_dir,
                            workflow_name,
                            input_file
                        )
                        name = input_file[:input_file.rfind('.')]

                        # try:
                        valid_string(
                            name,
                            'Name',
                            CHAR_UPPERCASE
                            + CHAR_LOWERCASE
                            + CHAR_NUMERIC
                            + CHAR_LINES
                        )
                        # except Exception:
                        #     break
                        if name not in buffer_meow[RECIPES]:
                            with open(source, "r") as read_file:
                                notebook = json.load(read_file)
                                recipe = create_recipe_dict(
                                    notebook,
                                    name,
                                    source
                                )
                                buffer_meow[RECIPES][name] = recipe

            key_text = '_key'
            value_text = '_value'
            for step_title, workflow_step in workflow[CWL_STEPS].items():
                step_name = get_step_name_from_title(step_title, workflow)
                status, msg = check_step_is_valid(step_name, self.cwl)
                if not status:
                    break

                step = self.cwl[STEPS][step_name]
                try:
                    pattern = Pattern(step_name)
                except Exception as ex:
                    break

                entries = {}
                unlinked = {}
                input_files = []
                for input_key, input_value in step[CWL_INPUTS].items():
                    settings_key = workflow_step[CWL_WORKFLOW_IN][input_key]
                    if '/' in settings_key:
                        target_step_key, target_value = settings_key.split('/')

                        status, glob = get_output_lookup(
                            target_step_key,
                            target_value,
                            workflow,
                            self.cwl[STEPS]
                        )
                        if not status:
                            break

                        status, result = get_glob_value(
                            glob,
                            target_step_key,
                            workflow,
                            settings
                        )
                        if not status:
                            break

                        setting = result

                    else:
                        setting = settings[settings_key]

                    if input_key.endswith(key_text):
                        entry = input_key[:input_key.rfind(key_text)]
                        if entry not in entries:
                            entries[entry] = {}
                        entries[entry]['key'] = setting
                    elif input_key.endswith(value_text):
                        entry = input_key[:input_key.rfind(value_text)]
                        if entry not in entries:
                            entries[entry] = {}
                        entries[entry]['value'] = setting
                    else:
                        entry = input_key
                        unlinked[input_key] = [input_value]

                    if isinstance(input_value, dict) and \
                            CWL_INPUT_TYPE in input_value and \
                            input_value[CWL_INPUT_TYPE] == 'File':
                        input_files.append(entry)

                # remove incomplete entries
                entry_keys = list(entries.keys())
                for entry in entry_keys:
                    if 'key' not in entries[entry]:
                        unlinked[entry] = entries['value']
                        entries.pop(entry)
                    if 'value' not in entries[entry]:
                        unlinked[entry] = entries['key']
                        entries.pop(entry)

                to_remove = []
                for file in input_files:
                    # this is probably a recipe
                    if file in unlinked:
                        try:
                            settings_key = workflow_step[CWL_WORKFLOW_IN][file]
                            if '/' in settings_key:
                                # TODO potentially do something here
                                break
                            filename = \
                                settings[settings_key][CWL_YAML_PATH]
                            extension = filename[filename.rfind('.'):]
                            if extension not in NOTEBOOK_EXTENSIONS:
                                break
                            name = filename[:filename.rfind('.')]
                            pattern.add_recipe(name)
                            to_remove.append(file)
                        except Exception:
                            pass
                for item in to_remove:
                    input_files.remove(item)
                    unlinked.pop(item)

                # this is probably the input file
                if len(input_files) == 1:
                    if input_files[0] in entries:
                        value = entries[input_files[0]]['value']
                        if isinstance(value, str):
                            pattern.add_single_input(
                                entries[input_files[0]]['key'],
                                value
                            )
                        elif isinstance(value, dict) \
                                and CWL_YAML_CLASS in value \
                                and CWL_YAML_PATH in value \
                                and value[CWL_YAML_CLASS] == 'File':
                            path = value[CWL_YAML_PATH]

                            pattern.add_single_input(
                                entries[input_files[0]]['key'],
                                path
                            )
                            input_files = []
                            entries.pop(input_files[0])
                    elif input_files[0] in unlinked:
                        key = input_files[0]
                        lookup_key = workflow_step[CWL_WORKFLOW_IN][key]
                        if '/' in lookup_key:

                            target_step_key, target_value = lookup_key.split(
                                '/')

                            status, glob = get_output_lookup(
                                target_step_key,
                                target_value,
                                workflow,
                                self.cwl[STEPS]
                            )
                            if not status:
                                break

                            status, result = get_glob_value(
                                glob,
                                target_step_key,
                                workflow,
                                settings
                            )
                            if not status:
                                break

                            pattern.add_single_input(key, result)
                            input_files = []
                            unlinked.pop(key)
                        else:
                            setting = settings[lookup_key]
                            pattern.add_single_input(key, setting)
                            input_files = []
                            unlinked.pop(key)

                # output
                for output_name, output in step[CWL_OUTPUTS].items():
                    if CWL_OUTPUT_TYPE not in output or \
                            output[CWL_OUTPUT_TYPE] != 'File' or \
                            CWL_OUTPUT_BINDING not in output or \
                            not isinstance(
                                output[CWL_OUTPUT_BINDING], dict
                            ) or \
                            'glob' not in output[CWL_OUTPUT_BINDING]:
                        break
                    glob = output[CWL_OUTPUT_BINDING]['glob']

                    status, result = \
                        get_glob_entry_keys(glob, step_name, workflow)

                    if status:
                        key_setting = result[0]
                        value_setting = result[1]
                        if key_setting in settings \
                                and value_setting in settings:
                            pattern.add_output(
                                settings[key_setting],
                                settings[value_setting]
                            )
                            break

                    status, glob_value = \
                        get_glob_value(glob, step_title, workflow, settings)

                    if not status:
                        break

                    if glob.startswith('$(') and glob.endswith(')'):
                        glob = glob[2:-1]
                        if '.' in glob:
                            glob = glob.split('.')[1]

                    pattern.add_output(glob, glob_value)

                    if glob in unlinked:
                        unlinked.pop(glob)
                    if glob in entries:
                        unlinked.pop(glob)

                for key, entry in entries.items():
                    try:
                        pattern.add_variable(entry['key'], entry['value'])
                    except Exception:
                        pass

                for key, value in unlinked.items():
                    try:
                        settings_key = workflow_step[CWL_WORKFLOW_IN][key]
                        setting = settings[settings_key]
                        if isinstance(setting, dict) \
                                and CWL_YAML_CLASS in setting \
                                and CWL_YAML_PATH in setting \
                                and setting[CWL_YAML_CLASS] == 'File':
                            setting = setting[CWL_YAML_PATH]
                        pattern.add_variable(key, setting)
                    except Exception:
                        pass

                if not pattern.trigger_file:
                    pattern.trigger_file = PLACEHOLDER
                if not pattern.trigger_paths:
                    pattern.trigger_paths = [PLACEHOLDER]
                if not pattern.recipes:
                    pattern.recipes = [PLACEHOLDER]

                buffer_meow[PATTERNS][pattern.name] = pattern

        return True, buffer_meow

    def __import_from_dir(self):
        buffer_cwl = {
            WORKFLOWS: {},
            STEPS: {},
            SETTINGS: {}
        }

        if not os.path.exists(self.cwl_import_export_dir):
            msg = "Cannot import from directory %s as it does not exist. If " \
                  "you intended to import from another directory it can be " \
                  "set during widget creation using the parameter '%s'. " \
                  % (self.cwl_import_export_dir, CWL_IMPORT_EXPORT_DIR_ARG)
            return False, msg

        directories = [
            d for d in os.listdir(self.cwl_import_export_dir)
            if os.path.isdir(os.path.join(self.cwl_import_export_dir, d))
        ]

        for directory in directories:
            dir_path = os.path.join(self.cwl_import_export_dir, directory)
            files = [
                f for f in os.listdir(dir_path)
                if os.path.isfile(os.path.join(dir_path, f))
            ]

            for file in files:
                if '.' not in file:
                    break
                filename = file[:file.index('.')]
                extension = file[file.index('.'):]
                if extension in YAML_EXTENSIONS:
                    with open(os.path.join(dir_path, file), 'r') as yaml_file:
                        yaml_dict = yaml.full_load(yaml_file)
                        settings = make_settings_dict(filename, yaml_dict)
                        buffer_cwl[SETTINGS][filename] = settings
                elif extension in CWL_EXTENSIONS:
                    with open(os.path.join(dir_path, file), 'r') as yaml_file:
                        yaml_dict = yaml.full_load(yaml_file)
                        if CWL_CLASS not in yaml_dict:
                            break

                        if yaml_dict[CWL_CLASS] == CWL_CLASS_WORKFLOW:
                            workflow = make_workflow_dict(filename)
                            if CWL_INPUTS in yaml_dict:
                                workflow[CWL_INPUTS] = yaml_dict[CWL_INPUTS]
                            if CWL_OUTPUTS in yaml_dict:
                                workflow[CWL_OUTPUTS] = yaml_dict[CWL_OUTPUTS]
                            if CWL_STEPS in yaml_dict:
                                workflow[CWL_STEPS] = yaml_dict[CWL_STEPS]
                            if CWL_REQUIREMENTS in yaml_dict:
                                workflow[CWL_REQUIREMENTS] = \
                                    yaml_dict[CWL_REQUIREMENTS]
                            buffer_cwl[WORKFLOWS][filename] = workflow

                        if yaml_dict[CWL_CLASS] == CWL_CLASS_COMMAND_LINE_TOOL:
                            if CWL_BASE_COMMAND not in yaml_dict:
                                break
                            base_command = yaml_dict[CWL_BASE_COMMAND]
                            step = make_step_dict(filename, base_command)
                            if CWL_INPUTS in yaml_dict:
                                step[CWL_INPUTS] = yaml_dict[CWL_INPUTS]
                            if CWL_OUTPUTS in yaml_dict:
                                step[CWL_OUTPUTS] = yaml_dict[CWL_OUTPUTS]
                            if CWL_ARGUMENTS in yaml_dict:
                                step[CWL_ARGUMENTS] = yaml_dict[CWL_ARGUMENTS]
                            if CWL_REQUIREMENTS in yaml_dict:
                                step[CWL_REQUIREMENTS] = \
                                    yaml_dict[CWL_REQUIREMENTS]
                            if CWL_HINTS in yaml_dict:
                                step[CWL_HINTS] = yaml_dict[CWL_HINTS]
                            if CWL_STDOUT in yaml_dict:
                                step[CWL_STDOUT] = yaml_dict[CWL_STDOUT]
                            buffer_cwl[STEPS][filename] = step
        return True, buffer_cwl

    def __import_cwl(self, **kwargs):
        workflows = kwargs.get(WORKFLOWS, None)
        steps = kwargs.get(STEPS, None)
        variables = kwargs.get(SETTINGS, None)

        overwritten_workflows = []
        overwritten_steps = []
        overwritten_variables = []
        for key, workflow in workflows.items():
            if key in self.cwl[WORKFLOWS]:
                overwritten_workflows.append(key)
            self.cwl[WORKFLOWS][key] = workflow

        for key, step in steps.items():
            if key in self.cwl[STEPS]:
                overwritten_steps.append(key)
            self.cwl[STEPS][key] = step

        for key, arguments in variables.items():
            if key in self.cwl[SETTINGS]:
                overwritten_variables.append(key)
            self.cwl[SETTINGS][key] = arguments

        msg = "Imported %s %s(s), %s %s(s) and %s %s(s). " \
              % (len(workflows), WORKFLOW_NAME,
                 len(steps), STEP_NAME,
                 len(variables), VARIABLES_NAME)
        if overwritten_workflows:
            msg += "<br/>Overwritten %s(s): %s " \
                   % (WORKFLOW_NAME, overwritten_workflows)
        if overwritten_steps:
            msg += "<br/>Overwritten %s(s): %s " \
                   % (STEP_NAME, overwritten_steps)
        if overwritten_variables:
            msg += "<br/>Overwritten %s(s): %s " \
                   % (VARIABLES_NAME, overwritten_variables)

        self.__set_feedback(msg)
        self.__update_workflow_visualisation()
        self.__close_form()

    def __update_workflow_visualisation(self):
        # TODO update this description

        self.__check_state()

        if self.mode == MEOW_MODE:
            # try:
            meow_workflow = build_workflow_object(
                self.meow[PATTERNS],
                self.meow[RECIPES]
            )
            # except:
            #     meow_workflow = {}

            visualisation = self.__get_meow_workflow_visualisation(
                self.meow[PATTERNS],
                self.meow[RECIPES],
                meow_workflow
            )

            self.visualisation_area.clear_output(wait=True)
            with self.visualisation_area:
                display(visualisation)
        elif self.mode == CWL_MODE:

            visualisation = self.__get_cwl_workflow_visualisation(
                self.cwl[WORKFLOWS],
                self.cwl[STEPS],
                self.cwl[SETTINGS]
            )

            self.visualisation_area.clear_output(wait=True)
            with self.visualisation_area:
                display(visualisation)

    def __get_meow_workflow_visualisation(self, patterns, recipes, workflow):
        # TODO update this description

        pattern_display = []

        for pattern in workflow.keys():
            pattern_display.append(
                self.__set_meow_node_dict(patterns[pattern])
            )

        link_display = []
        colour_display = [RED] * len(pattern_display)

        path_nodes = {}

        for pattern, pattern_dict in workflow.items():
            pattern_index = self.__get_node_index(pattern, pattern_display)
            if pattern_has_recipes(patterns[pattern], recipes):
                colour_display[pattern_index] = GREEN
            else:
                colour_display[pattern_index] = RED
            for file, input in pattern_dict[WORKFLOW_INPUTS].items():
                pattern_display.append(
                    self.__set_phantom_meow_node_dict(input)
                )
                colour_display.append(WHITE)
                node_index = len(pattern_display) - 1
                node_name = "%s_input_%s" % (pattern, file)
                path_nodes[node_name] = node_index
                link_display.append({
                    'source': node_index,
                    'target': pattern_index
                })
            for file, output in pattern_dict[WORKFLOW_OUTPUTS].items():
                pattern_display.append(
                    self.__set_phantom_meow_node_dict(output)
                )
                colour_display.append(WHITE)
                node_index = len(pattern_display) - 1
                node_name = "%s_output_%s" % (pattern, file)
                path_nodes[node_name] = node_index
                link_display.append({
                    'source': pattern_index,
                    'target': node_index
                })

        # Do this second as we need to make sure all patterns have been set
        # up before we can link them
        for pattern, pattern_dict in workflow.items():
            pattern_index = self.__get_node_index(pattern, pattern_display)
            for name, ancestor in pattern_dict[ANCESTORS].items():
                node_name = "%s_%s_%s" % (
                    ancestor['output_pattern'],
                    'output',
                    ancestor['output_file']
                )
                if node_name in path_nodes:
                    link_display.append({
                        'source': path_nodes[node_name],
                        'target': pattern_index
                    })

        graph = Graph(
            node_data=pattern_display,
            link_data=link_display,
            charge=-400,
            colors=colour_display,
            tooltip=MEOW_TOOLTIP
        )

        # TODO investiaget graph.interactions to see if we can get tooltip to
        #  only display for patterns
        graph.on_element_click(self.__meow_visualisation_element_click)
        graph.on_hover(self.__toggle_tooltips)

        fig_layout = widgets.Layout(width='100%', height='600px')

        return Figure(marks=[graph], layout=fig_layout)

    def __get_cwl_workflow_visualisation(self, workflows, steps, settings):
        # TODO update this description

        node_data = []
        link_data = []
        colour_data = []

        linked_workflows = {}
        node_indexes = {}
        index = 0

        for workflow_key, workflow in workflows.items():
            status, feedback = get_linked_workflow(
                workflow,
                steps,
                settings[workflow_key][CWL_VARIABLES]
            )
            if status:
                linked_workflows[workflow_key] = feedback

                for step_title, step_value in feedback.items():
                    if step_title not in steps:
                        break

                    step = steps[step_title]
                    node_data.append(self.__set_cwl_step_dict(step))
                    colour_data.append(GREEN)
                    name = "%s_%s" % (workflow_key, step_title)
                    node_indexes[name] = index
                    index += 1

                    for key, input in step_value['inputs'].items():
                        node_data.append(
                            self.__set_phantom_cwl_node_dict(input)
                        )
                        colour_data.append(WHITE)
                        descendant_index = index
                        link_data.append({
                            'source': descendant_index,
                            'target': node_indexes[name]
                        })
                        index += 1

                    for key, output in step_value['outputs'].items():
                        if isinstance(output, dict) \
                                and CWL_OUTPUT_GLOB in output:
                            output = output[CWL_OUTPUT_GLOB]
                        status, value = get_glob_value(
                            output,
                            step_title,
                            workflow,
                            settings
                        )

                        node_data.append(
                            self.__set_phantom_cwl_node_dict(value)
                        )
                        output_node_name = "%s_%s" % (name, key)
                        node_indexes[output_node_name] = index
                        colour_data.append(WHITE)
                        descendant_index = index
                        link_data.append({
                            'source': node_indexes[name],
                            'target': descendant_index
                        })
                        index += 1

                    for step_key, workflow_step in workflow[CWL_STEPS].items():
                        for input in workflow_step[CWL_WORKFLOW_IN].values():
                            if input not in \
                                    settings[workflow_key][CWL_VARIABLES]:
                                if input not in \
                                        list(step_value['ancestors'].values()):
                                    colour_data[node_indexes[name]] = RED
                            elif settings[workflow_key][CWL_VARIABLES][input]\
                                    == PLACEHOLDER:
                                colour_data[node_indexes[name]] = RED

                # loop through again once we know all steps have been set up
                # to link steps together
                for step_name, step_value in feedback.items():
                    name = "%s_%s" % (workflow_key, step_name)
                    if name not in node_indexes:
                        break

                    for key, ancestor in step_value['ancestors'].items():
                        key = get_step_name_from_title(key, workflow)
                        if '/' in ancestor:
                            first = ancestor[:ancestor.index('/')]
                            new_first = \
                                get_step_name_from_title(first, workflow)
                            ancestor = ancestor.replace(first, new_first)
                        source_name = "%s_%s_%s" \
                                      % (workflow_key, key, ancestor)

                        link_data.append({
                            'source': node_indexes[source_name],
                            'target': node_indexes[name]
                        })

        graph = Graph(
            node_data=node_data,
            link_data=link_data,
            charge=-400,
            colors=colour_data,
            tooltip=CWL_TOOLTIP
        )

        graph.on_element_click(self.__cwl_visualisation_element_click)
        graph.on_hover(self.__toggle_tooltips)

        fig_layout = widgets.Layout(width='100%', height='600px')

        return Figure(marks=[graph], layout=fig_layout)

    # TODO improve this to remove occasional flickering
    def __toggle_tooltips(self, graph, node):
        if node['data']['tooltip']:
            if not graph.tooltip:
                graph.tooltip_style = {'opacity': 0.9}
                if node['data']['tooltip'] == MEOW_MODE:
                    graph.tooltip = MEOW_TOOLTIP
                elif node['data']['tooltip'] == CWL_MODE:
                    graph.tooltip = CWL_TOOLTIP
        else:
            if graph.tooltip:
                graph.tooltip_style = {'opacity': 0.0}
                graph.tooltip = None

    def __set_meow_node_dict(self, pattern):
        # TODO update this description

        node_dict = {
            'label': pattern.name,
            'Name': pattern.name,
            'Recipe(s)': str(pattern.recipes),
            'Trigger Path(s)': str(pattern.trigger_paths),
            'Outputs(s)': str(pattern.outputs),
            'Input File': pattern.trigger_file,
            'Variable(s)': str(pattern.variables),
            'shape': 'circle',
            'shape_attrs': {'r': 30},
            'tooltip': MEOW_MODE
        }
        return node_dict

    def __set_phantom_meow_node_dict(self, label):
        # TODO update this description
        node_dict = {
            'label': label,
            'shape': 'rect',
            'shape_attrs': {'rx': 6, 'ry': 6, 'width': 60, 'height': 30},
            'tooltip': False
        }
        return node_dict

    def __set_cwl_step_dict(self, step):
        # TODO update this description

        node_dict = {
            'label': step[CWL_NAME],
            'Name': step[CWL_NAME],
            'Base Command': step[CWL_BASE_COMMAND],
            'Inputs(s)': str(list(step[CWL_INPUTS].keys())),
            'Outputs(s)': str(step[CWL_OUTPUTS]),
            'Argument(s)': str(step[CWL_ARGUMENTS]),
            'Requirement(s)': str(step[CWL_REQUIREMENTS]),
            'Hint(s)': str(step[CWL_HINTS]),
            'Stdout': step[CWL_STDOUT],
            'shape': 'circle',
            'shape_attrs': {'r': 30},
            'tooltip': CWL_MODE
        }
        return node_dict

    def __set_phantom_cwl_node_dict(self, label):
        # TODO update this description

        node_dict = {
            'label': label,
            'shape': 'rect',
            'shape_attrs': {'rx': 6, 'ry': 6, 'width': 60, 'height': 30},
            'tooltip': False
        }
        return node_dict

    def __get_node_index(self, pattern, nodes):
        # TODO update this description

        for index in range(0, len(nodes)):
            if nodes[index]['Name'] == pattern:
                return index
        return -1

    def __meow_visualisation_element_click(self, graph, element):
        # TODO update this description

        # pattern = self.patterns[element['data']['label']]
        # self.construct_new_edit_form(default=pattern)
        pass

    def __cwl_visualisation_element_click(self, graph, element):
        # TODO update this description
        pass

    def __add_to_feedback(self, to_add):
        # TODO update this description

        if self.feedback_area.value:
            self.feedback_area.value += "<br/>"
        self.feedback_area.value += to_add

    def __set_feedback(self, to_set):
        # TODO update this description

        self.feedback_area.value = to_set

    def __clear_feedback(self):
        # TODO update this description

        self.feedback_area.value = ""
