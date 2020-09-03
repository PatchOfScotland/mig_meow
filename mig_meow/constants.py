
# Only constants shared amongst multiple files should be declared here.
# Variables that are only used in one file should be declared there, unless it
# is clearer to group them here with appropriate variables.
# Variables may also need to be saved here if needed for testing.

DEFAULT_JSON_TIMEOUT = 60
DEFAULT_WORKFLOW_TITLE = 'workflow'
DEFAULT_MEOW_IMPORT_EXPORT_DIR = 'meow_directory'
DEFAULT_CWL_IMPORT_EXPORT_DIR = 'cwl_directory'

WORKFLOWS = 'workflows'
STEPS = 'steps'
SETTINGS = 'variables'

MEOW_NEW_PATTERN_BUTTON = 'meow_new_pattern_button'
MEOW_EDIT_PATTERN_BUTTON = 'meow_edit_pattern_button'
MEOW_NEW_RECIPE_BUTTON = 'meow_new_recipe_button'
MEOW_EDIT_RECIPE_BUTTON = 'meow_edit_recipe_button'
MEOW_IMPORT_CWL_BUTTON = 'meow_import_cwl_button'
MEOW_IMPORT_VGRID_BUTTON = 'meow_import_vgrid_button'
MEOW_EXPORT_VGRID_BUTTON = 'meow_export_vgrid_button'
MEOW_IMPORT_DIR_BUTTON = 'meow_import_dir_button'
MEOW_EXPORT_DIR_BUTTON = 'meow_export_dir_button'
MEOW_SAVE_SVG_BUTTON = 'meow_save_svg_button'

CWL_NEW_WORKFLOW_BUTTON = 'cwl_new_workflow_button'
CWL_EDIT_WORKFLOW_BUTTON = 'cwl_edit_workflow_button'
CWL_NEW_STEP_BUTTON = 'cwl_new_step_button'
CWL_EDIT_STEP_BUTTON = 'cwl_edit_step_button'
CWL_NEW_VARIABLES_BUTTON = 'cwl_new_variables_button'
CWL_EDIT_VARIABLES_BUTTON = 'cwl_edit_variables_button'
CWL_IMPORT_MEOW_BUTTON = 'cwl_import_meow_button'
CWL_IMPORT_DIR_BUTTON = 'cwl_import_dir_button'
CWL_EXPORT_DIR_BUTTON = 'cwl_export_dir_button'
CWL_SAVE_SVG_BUTTON = 'cwl_save_svg_button'

CWL_NAME = 'name'
CWL_CWL_VERSION = 'cwlVersion'
CWL_CLASS = 'class'
CWL_BASE_COMMAND = 'baseCommand'
CWL_INPUTS = 'inputs'
CWL_OUTPUTS = 'outputs'
CWL_ARGUMENTS = 'arguments'
CWL_REQUIREMENTS = 'requirements'
CWL_HINTS = 'hints'
CWL_STDOUT = 'stdout'
CWL_STEPS = 'steps'
CWL_VARIABLES = 'arguments'

CWL_OUTPUT_TYPE = 'type'
CWL_OUTPUT_BINDING = 'outputBinding'
CWL_OUTPUT_SOURCE = 'outputSource'
CWL_OUTPUT_GLOB = 'glob'

CWL_YAML_CLASS = 'class'
CWL_YAML_PATH = 'path'

CWL_WORKFLOW_RUN = 'run'
CWL_WORKFLOW_IN = 'in'
CWL_WORKFLOW_OUT = 'out'

DEFAULT_JOB_NAME = 'wf_job'

PATTERN_LIST = 'pattern_list'
RECIPE_LIST = 'recipe_list'

VGRID_WORKFLOWS_OBJECT = 'workflows'
VGRID_PATTERN_OBJECT_TYPE = 'workflowpattern'
VGRID_RECIPE_OBJECT_TYPE = 'workflowrecipe'
VGRID_ANY_OBJECT_TYPE = 'any'

VALID_WORKFLOW_TYPES = [
    VGRID_WORKFLOWS_OBJECT,
    VGRID_PATTERN_OBJECT_TYPE,
    VGRID_RECIPE_OBJECT_TYPE,
    VGRID_ANY_OBJECT_TYPE
]

VGRID_QUEUE_OBJECT_TYPE = 'queue'
VGRID_JOB_OBJECT_TYPE = 'job'
CANCEL_JOB = 'cancel_job'
RESUBMIT_JOB = 'resubmit_job'

VALID_JOB_TYPES = [
    VGRID_QUEUE_OBJECT_TYPE,
    VGRID_JOB_OBJECT_TYPE,
    CANCEL_JOB,
    RESUBMIT_JOB
]

VGRID_ERROR_TYPE = 'error_text'
VGRID_TEXT_TYPE = 'text'
VGRID_CREATE = 'create'
VGRID_READ = 'read'
VGRID_UPDATE = 'update'
VGRID_DELETE = 'delete'

VALID_OPERATIONS = [
    VGRID_CREATE,
    VGRID_READ,
    VGRID_UPDATE,
    VGRID_DELETE
]

OBJECT_TYPE = 'object_type'
PERSISTENCE_ID = 'persistence_id'
NAME = 'name'
INPUT_FILE = 'input_file'
TRIGGER_PATHS = 'input_paths'
OUTPUT = 'output'
RECIPE = 'recipe'
RECIPES = 'recipes'
VARIABLES = 'variables'
SWEEP = 'parameterize_over'
SWEEP_START = 'start'
SWEEP_STOP = 'stop'
SWEEP_JUMP = 'increment'
VGRID = 'vgrid'
SOURCE = 'source'
PATTERNS = 'patterns'
TRIGGER_RECIPES = 'trigger_recipes'
TASK_FILE = 'task_file'

CWL_CLASS_COMMAND_LINE_TOOL = 'CommandLineTool'
CWL_CLASS_WORKFLOW = 'Workflow'

PATTERN_NAME = 'Pattern'
RECIPE_NAME = 'Recipe'
WORKFLOW_NAME = 'Workflow'
STEP_NAME = 'Step'
VARIABLES_NAME = 'Arguments'

PLACEHOLDER = 'PLACEHOLDER'

VALID_PATTERN_MIN = {
    NAME: str,
    INPUT_FILE: str,
    TRIGGER_PATHS: list,
    TRIGGER_RECIPES: dict
}

VALID_PATTERN_OPTIONAL = {
    OUTPUT: dict,
    VARIABLES: dict,
    SWEEP: dict,
}

VALID_SWEEP_MIN = {
    SWEEP_START: [int, float],
    SWEEP_STOP: [int, float],
    SWEEP_JUMP: [int, float]
}

VALID_SWEEP_OPTIONAL = {

}

VALID_RECIPE_MIN = {
    NAME: str,
    RECIPE: dict,
    SOURCE: str
}

VALID_RECIPE_OPTIONAL = {

}

VALID_WORKFLOW_MIN = {
    CWL_NAME: str,
    CWL_CWL_VERSION: str,
    CWL_CLASS: str,
    CWL_INPUTS: dict,
    CWL_OUTPUTS: dict,
    CWL_STEPS: dict
}

VALID_WORKFLOW_OPTIONAL = {
    CWL_REQUIREMENTS: dict
}

VALID_STEP_MIN = {
    CWL_NAME: str,
    CWL_CWL_VERSION: str,
    CWL_CLASS: str,
    CWL_BASE_COMMAND: str,
    CWL_INPUTS: dict,
    CWL_OUTPUTS: dict
}

VALID_STEP_OPTIONAL = {
    CWL_STDOUT: str,
    CWL_ARGUMENTS: list,
    CWL_REQUIREMENTS: dict,
    CWL_HINTS: dict
}

VALID_SETTING_MIN = {
    CWL_NAME: str,
    CWL_VARIABLES: dict
}

VALID_SETTING_OPTIONAL = {
}

ANCESTORS = 'ancestors'
DESCENDANTS = 'descendants'
WORKFLOW_INPUTS = 'workflow inputs'
WORKFLOW_OUTPUTS = 'workflow outputs'

CHAR_LOWERCASE = 'abcdefghijklmnopqrstuvwxyz'
CHAR_UPPERCASE = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
CHAR_NUMERIC = '0123456789'
CHAR_LINES = '-_'

NOTEBOOK_EXTENSION = '.ipynb'
NOTEBOOK_EXTENSIONS = [
    NOTEBOOK_EXTENSION
]

GREEN = 'lightgreen'
RED = 'pink'
WHITE = 'lightgray'

COLOURS = [
    GREEN,
    RED,
    WHITE
]

NO_OUTPUT_SET_WARNING = \
    'No output has been set. The recipe may still output data but for the ' \
    'visualisation to be correct it should be told if this is so. '
NO_NAME_SET_ERROR = "A pattern name must be defined. "
NO_INPUT_FILE_SET_ERROR = \
    "An input file must be defined. This is the file that is used to " \
    "trigger any processing and can be defined using the methods " \
    "'.add_single_input' or 'add_gathering_input. "
NO_INPUT_PATH_SET_ERROR = \
    "At least one input path must be defined. This is the path to the file " \
    "that is used to trigger any processing and can be defined using the " \
    "methods '.add_single_input' or 'add_gathering_input. "
INVALID_INPUT_PATH_ERROR = "The input path is not valid. "
NO_RECIPES_SET_ERROR = "No recipes have been defined. "
PLACEHOLDER_ERROR = \
    "A placeholder value was detected. Please update this before proceeding. "

MEOW_MODE = 'MEOW'
CWL_MODE = 'CWL'
WIDGET_MODES = [
    MEOW_MODE,
    CWL_MODE
]

LOGGING_DIR = 'mig_meow_logs'
WORKFLOW_LOGFILE_NAME = 'workfow_widget'
MONITOR_LOGFILE_NAME = 'monitor_widget'
RUNNER_LOGFILE_NAME = 'workflow_runner'

KEYWORD_PATH = "{PATH}"
KEYWORD_REL_PATH = "{REL_PATH}"
KEYWORD_DIR = "{DIR}"
KEYWORD_REL_DIR = "{REL_DIR}"
KEYWORD_FILENAME = "{FILENAME}"
KEYWORD_PREFIX = "{PREFIX}"
KEYWORD_VGRID = "{VGRID}"
KEYWORD_EXTENSION = "{EXTENSION}"
KEYWORD_JOB = "{JOB}"

MIG_TRIGGER_KEYWORDS = [
    KEYWORD_PATH,
    KEYWORD_REL_PATH,
    KEYWORD_DIR,
    KEYWORD_REL_DIR,
    KEYWORD_FILENAME,
    KEYWORD_PREFIX,
    KEYWORD_VGRID,
    KEYWORD_EXTENSION,
    KEYWORD_JOB
]
