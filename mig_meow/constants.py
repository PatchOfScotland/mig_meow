
VGRID_MODE = 'vgrid'
WIDGET_MODES = [
    VGRID_MODE
]

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
VGRID_ERROR_TYPE = 'error_text'
VGRID_TEXT_TYPE = 'text'
VGRID_CREATE = 'create'
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
PATTERNS = 'patterns'

INPUT_NAME = "input_name"
INPUT_TRIGGER_FILE = "input_trigger_file"
INPUT_TRIGGER_PATH = "input_trigger_path"
INPUT_TRIGGER_OUTPUT = "input_trigger_output"
INPUT_NOTEBOOK_OUTPUT = "input_notebook_output"
INPUT_INPUT = "input_input"
INPUT_OUTPUT = "input_output"
INPUT_RECIPES = "input_recipes"
INPUT_VARIABLES = "input_variables"
ALL_PATTERN_INPUTS = [
    INPUT_NAME,
    INPUT_TRIGGER_FILE,
    INPUT_TRIGGER_PATH,
    INPUT_TRIGGER_OUTPUT,
    INPUT_NOTEBOOK_OUTPUT,
    # INPUT_INPUT,
    INPUT_OUTPUT,
    INPUT_RECIPES,
    INPUT_VARIABLES
]
INPUT_SOURCE = "input_source"
ALL_RECIPE_INPUTS = [
    INPUT_SOURCE,
    INPUT_NAME
]

OUTPUT_MAGIC_CHAR = '*'

PLACEHOLDER = ''

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
    # OBJECT_TYPE: str,
    # PERSISTENCE_ID: str,
    # TRIGGERS: dict,
    # OWNER: str,
    NAME: str,
    RECIPE: dict,
    SOURCE: str,
    # VGRID: str
}

ANCESTORS = 'ancestors'
DESCENDENTS = 'descendents'

WORKFLOW_NODE = {
    DESCENDENTS: []
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

COLOURS = [
    GREEN,
    RED
]

