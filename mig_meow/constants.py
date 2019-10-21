
MEOW_MODE = 'MEOW'
CWL_MODE = 'CWL'
WIDGET_MODES = [
    MEOW_MODE,
    CWL_MODE
]

YAML_EXTENSIONS = [
    '.yaml',
    '.yml'
]

CWL_EXTENSIONS = [
    '.cwl'
]

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

CWL_WORKFLOWS_REQUIREMENTS = [
    CWL_CWL_VERSION,
    CWL_CLASS,
    CWL_BASE_COMMAND,
    CWL_INPUTS,
    CWL_OUTPUTS,
    CWL_STEPS,
    CWL_REQUIREMENTS,
    CWL_ARGUMENTS
]

CWL_STEP_REQUIREMENTS = [
    CWL_CWL_VERSION,
    CWL_CLASS,
    CWL_BASE_COMMAND,
    CWL_INPUTS,
    CWL_OUTPUTS,
    CWL_ARGUMENTS,
    CWL_REQUIREMENTS,
    CWL_HINTS,
    CWL_STDOUT
]

CWL_INPUT_TYPE = 'type'
CWL_INPUT_BINDING = 'inputBinding'
CWL_INPUT_POSITION = 'position'
CWL_INPUT_PREFIX = 'prefix'

CWL_OUTPUT_TYPE = 'type'
CWL_OUTPUT_BINDING = 'outputBinding'
CWL_OUTPUT_SOURCE = 'outputSource'
CWL_OUTPUT_GLOB = 'glob'

CWL_YAML_CLASS = 'class'
CWL_YAML_PATH = 'path'

CWL_WORKFLOW_RUN = 'run'
CWL_WORKFLOW_IN = 'in'
CWL_WORKFLOW_OUT = 'out'

NOTEBOOK_EXTENSION = '.ipynb'
DEFAULT_JOB_NAME = 'wf_job'
DEFAULT_JOB_NAME_EXTENSION = DEFAULT_JOB_NAME + NOTEBOOK_EXTENSION
PATTERN_EXTENSION = '.pattern'

PATTERN_NAME = 'Pattern'
RECIPE_NAME = 'Recipe'

PATTERN_LIST = 'pattern_list'
RECIPE_LIST = 'recipe_list'

VGRID_WORKFLOWS_OBJECT = 'workflows'
VGRID_PATTERN_OBJECT_TYPE = 'workflowpattern'
VGRID_RECIPE_OBJECT_TYPE = 'workflowrecipe'
VGRID_QUEUE_OBJECT_TYPE = 'queue'
VGRID_JOB_OBJECT_TYPE = 'job'

MRSL_VGRID = 'VGRID'

VGRID_ERROR_TYPE = 'error_text'
VGRID_TEXT_TYPE = 'text'
VGRID_CREATE = 'create'
VGRID_READ = 'read'
VGRID_UPDATE = 'update'
VGRID_DELETE = 'delete'

PATTERNS_DIR = '.workflow_patterns_home'
RECIPES_DIR = '.workflow_recipes_home'
EXPORT_DIR = '.meow_export_home'
FILES_DIR = 'vgrid_files_home'

OBJECT_TYPE = 'object_type'
PERSISTENCE_ID = 'persistence_id'
TRIGGER = 'trigger'
TRIGGERS = 'triggers'
OWNER = 'owner'
NAME = 'name'
INPUT_FILE = 'input_file'
TRIGGER_PATHS = 'trigger_paths'
OUTPUT = 'output'
RECIPE = 'recipe'
RECIPES = 'recipes'
VARIABLES = 'variables'
VGRID = 'vgrid'
SOURCE = 'source'
MOUNT_USER_DIR = 'mount_user_dir'
PATTERNS = 'patterns'

TRIGGER_ACTION = 'manual_trigger'
CANCEL_JOB = 'cancel_job'
RESUBMIT_JOB = 'resubmit_job'

TRIGGER_PATH = "trigger_path"
TRIGGER_OUTPUT = "trigger_output"
NOTEBOOK_OUTPUT = "notebook_output"
ALL_PATTERN_INPUTS = [
    NAME,
    INPUT_FILE,
    TRIGGER_PATH,
    TRIGGER_OUTPUT,
    NOTEBOOK_OUTPUT,
    OUTPUT,
    RECIPES,
    VARIABLES
]

CWL_CLASS_COMMAND_LINE_TOOL = 'CommandLineTool'
CWL_CLASS_WORKFLOW = 'Workflow'

WORKFLOW_NAME = 'Workflow'
STEP_NAME = 'Step'
VARIABLES_NAME = 'Arguments'

ALL_RECIPE_INPUTS = [
    SOURCE,
    NAME,
]

OUTPUT_MAGIC_CHAR = '*'

PLACEHOLDER = 'PLACEHOLDER'

VALID_PATTERN = {
    OBJECT_TYPE: str,
    PERSISTENCE_ID: str,
    TRIGGER: dict,
    OWNER: str,
    NAME: str,
    INPUT_FILE: str,
    TRIGGER_PATHS: list,
    OUTPUT: dict,
    RECIPES: list,
    VARIABLES: dict,
    VGRID: str
}

VALID_RECIPE = {
    NAME: str,
    RECIPE: dict,
    SOURCE: str,
    MOUNT_USER_DIR: bool
}

ANCESTORS = 'ancestors'
DESCENDANTS = 'descendants'
WORKFLOW_INPUTS = 'workflow inputs'
WORKFLOW_OUTPUTS = 'workflow outputs'

WORKFLOW_NODE = {
    DESCENDANTS: []
}

CHAR_LOWERCASE = 'abcdefghijklmnopqrstuvwxyz'
CHAR_UPPERCASE = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
CHAR_NUMERIC = '0123456789'
CHAR_LINES = '-_'

DEFAULT_WORKFLOW_FILENAME = 'meow_workflow_file'

WORKFLOW_IMAGE_EXTENSION = ".png"

NOTEBOOK_EXTENSIONS = [
    NOTEBOOK_EXTENSION
]

GREEN = 'green'
RED = 'red'
WHITE = 'white'
BLUE = 'blue'

COLOURS = [
    GREEN,
    RED,
    WHITE
]
