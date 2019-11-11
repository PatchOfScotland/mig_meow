
# Only constants shared amongst multiple files should be declared here.
# Variables that are only used in one file should be declared there, unless it
# is clearer to group them here with appropriate variables.

WORKFLOWS = 'workflows'
STEPS = 'steps'
SETTINGS = 'variables'

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
TRIGGER = 'trigger'
TRIGGERS = 'triggers'
OWNER = 'owner'
NAME = 'name'
INPUT_FILE = 'input_file'
TRIGGER_PATHS = 'input_paths'
OUTPUT = 'output'
RECIPE = 'recipe'
RECIPES = 'recipes'
VARIABLES = 'variables'
VGRID = 'vgrid'
SOURCE = 'source'
PATTERNS = 'patterns'
TRIGGER_RECIPES = 'trigger_recipes'
TRIGGER_OUTPUT = "trigger_output"
NOTEBOOK_OUTPUT = "notebook_output"

CWL_CLASS_COMMAND_LINE_TOOL = 'CommandLineTool'
CWL_CLASS_WORKFLOW = 'Workflow'

PATTERN_NAME = 'Pattern'
RECIPE_NAME = 'Recipe'
WORKFLOW_NAME = 'Workflow'
STEP_NAME = 'Step'
VARIABLES_NAME = 'Arguments'

PLACEHOLDER = 'PLACEHOLDER'

VALID_PATTERN = {
    OBJECT_TYPE: str,
    PERSISTENCE_ID: str,
    TRIGGER: dict,
    OWNER: str,
    NAME: str,
    INPUT_FILE: str,
    TRIGGER_PATHS: list,
    TRIGGER_RECIPES: dict,
    OUTPUT: dict,
    VARIABLES: dict,
    VGRID: str
}

VALID_RECIPE = {
    NAME: str,
    RECIPE: dict,
    SOURCE: str
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

GREEN = 'green'
RED = 'red'
WHITE = 'white'

COLOURS = [
    GREEN,
    RED,
    WHITE
]

NO_OUTPUT_SET_WARNING = \
    'No output has been set, meaning no resulting data will be copied back ' \
    'into the vgrid. ANY OUTPUT WILL BE LOST. '

MEOW_MODE = 'MEOW'
CWL_MODE = 'CWL'
WIDGET_MODES = [
    MEOW_MODE,
    CWL_MODE
]

DEFAULT_WORKFLOW_TITLE = 'workflow'
DEFAULT_CWL_IMPORT_EXPORT_DIR = 'cwl_directory'
