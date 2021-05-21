import unittest
import copy
import nbformat
import os

from mig_meow.constants import NO_OUTPUT_SET_WARNING, MEOW_MODE, CWL_MODE, \
    DEFAULT_WORKFLOW_TITLE, DEFAULT_CWL_IMPORT_EXPORT_DIR, PATTERNS, RECIPES, \
    WORKFLOWS, STEPS, SETTINGS, MEOW_NEW_RECIPE_BUTTON, \
    MEOW_EDIT_RECIPE_BUTTON, MEOW_EDIT_PATTERN_BUTTON, \
    MEOW_IMPORT_VGRID_BUTTON, MEOW_EXPORT_VGRID_BUTTON, \
    MEOW_NEW_PATTERN_BUTTON, MEOW_IMPORT_CWL_BUTTON, DEFAULT_JOB_NAME, \
    NO_NAME_SET_ERROR, NO_RECIPES_SET_ERROR, NO_INPUT_PATH_SET_ERROR, \
    NO_INPUT_FILE_SET_ERROR, PLACEHOLDER_ERROR, \
    INVALID_INPUT_PATH_ERROR, PLACEHOLDER, NAME, INPUT_FILE, TRIGGER_PATHS, \
    TRIGGER_RECIPES, OUTPUT, VARIABLES, SOURCE, RECIPE, CWL_NAME, \
    CWL_REQUIREMENTS, CWL_CWL_VERSION, CWL_CLASS, CWL_BASE_COMMAND, \
    CWL_INPUTS, CWL_OUTPUTS, CWL_STEPS, CWL_STDOUT, CWL_ARGUMENTS, CWL_HINTS, \
    CWL_VARIABLES, CWL_CLASS_WORKFLOW, CWL_CLASS_COMMAND_LINE_TOOL, SWEEP, \
    SWEEP_START, SWEEP_STOP, SWEEP_JUMP, VALID_ENVIRONMENTS_LOCAL, \
    VALID_ENVIRONMENTS_MIG, ENVIRONMENTS, ENVIRONMENTS_MIG, ENVIRONMENTS_LOCAL
from mig_meow.cwl import check_workflows_dict, check_steps_dict, \
    check_settings_dict
from mig_meow.validation import is_valid_recipe_dict, is_valid_pattern_dict, \
    is_valid_workflow_dict, is_valid_step_dict, is_valid_setting_dict, \
    is_valid_environments_dict
from mig_meow.meow import Pattern, check_patterns_dict, \
    build_workflow_object, create_recipe_dict, check_recipes_dict, \
    parameter_sweep_entry, get_parameter_sweep_values
from mig_meow.workflow_widget import WorkflowWidget, NAME_KEY, VALUE_KEY, \
    SWEEP_START_KEY, SWEEP_STOP_KEY, SWEEP_JUMP_KEY

EMPTY_NOTEBOOK = 'test_notebook.ipynb'
ANOTHER_NOTEBOOK = 'another_notebook.ipynb'
ANALYSIS_NOTEBOOK = os.path.join(
    DEFAULT_CWL_IMPORT_EXPORT_DIR,
    DEFAULT_WORKFLOW_TITLE,
    'data_analysis.ipynb'
)
PLOTTING_NOTEBOOK = os.path.join(
    DEFAULT_CWL_IMPORT_EXPORT_DIR,
    DEFAULT_WORKFLOW_TITLE,
    'data_plotting.ipynb'
)
EXTENSIONLESS_NOTEBOOK = 'test_notebook'
DOES_NOT_EXIST = 'does_not_exit.ipynb'

REQUIRED_FILES = [
    EMPTY_NOTEBOOK,
    ANOTHER_NOTEBOOK,
    EXTENSIONLESS_NOTEBOOK,
    ANALYSIS_NOTEBOOK,
    PLOTTING_NOTEBOOK
]

REQUIRED_ABSENT_FILES = [
    DOES_NOT_EXIST
]

NOTEBOOKS = [
    EMPTY_NOTEBOOK,
    ANOTHER_NOTEBOOK,
    EXTENSIONLESS_NOTEBOOK,
    ANALYSIS_NOTEBOOK,
    PLOTTING_NOTEBOOK
]

VALID_PATTERN_DICT = {
    NAME: 'test_pattern',
    TRIGGER_PATHS: ['dir/literal.path'],
    TRIGGER_RECIPES: {
        'trigger_id': {
            'recipe_id': {
                'name': 'test_recipe',
                'source': 'source.ipynb',
                'recipe': {}
            }
        }
    },
    INPUT_FILE: 'trigger_file_name',
    OUTPUT: {
        'outfile_1': 'dir_1/out.path',
        'outfile_2': 'dir_2/out.path'
    },
    VARIABLES: {
        'int': 0,
        'float': 3.5,
        'array': [0, 1],
        'dict': {1: 1, 2: 2},
        'set': {1, 2},
        'char': 'c',
        'string': "String",
        'boolean': True
    }
}

VALID_RECIPE_DICT = {
    NAME: 'test_recipe',
    SOURCE: EMPTY_NOTEBOOK,
    RECIPE: {
        'cells': [],
        'metadata': {},
        'nbformat': 4,
        'nbformat_minor': 5
    }
}

VALID_WORKFLOW_DICT = {
    CWL_NAME: 'workflow_name',
    CWL_CWL_VERSION: 'v1.0',
    CWL_CLASS: 'Workflow',
    CWL_INPUTS: {
        'analysis_notebook': 'File',
        'analysis_result': 'string',
        'analysis_yaml_file': 'File',
        'analysis_dssc': 'File',
        'analysis_interim_yaml': 'string',
        'plotting_notebook': 'File',
        'plotting_result': 'string',
    },
    CWL_OUTPUTS: {
        'final_plot': {
            'type': 'File',
            'outputSource': 'plot/result_notebook'
        }
    },
    CWL_STEPS: {
        'analysis': {
            'run': 'data_analysis.cwl',
            'in': {
                'notebook': 'analysis_notebook',
                'result': 'analysis_result',
                'yaml_file': 'analysis_yaml_file',
                'dssc_file': 'analysis_dssc',
                'interim_yaml_title': 'analysis_interim_yaml'
            },
            'out': '[result_notebook, interim_yaml]'
        },
        'plot': {
            'run': 'data_plotting.cwl',
            'in': {
                'notebook': 'plotting_notebook',
                'result': 'plotting_result',
                'yaml_file': 'analysis/interim_yaml'
            },
            'out': '[result_notebook]'
        }
    },
    CWL_REQUIREMENTS: {}
}

VALID_STEP_DICT = {
    CWL_NAME: 'step_name',
    CWL_CWL_VERSION: 'v1.0',
    CWL_CLASS: 'CommandLineTool',
    CWL_BASE_COMMAND: 'papermill',
    CWL_STDOUT: '',
    CWL_INPUTS: {
        'notebook': {
            'inputBinding': {
                'position': 1
            },
            'type': 'File'
        },
        'result': {
            'inputBinding': {
                'position': 2
            },
            'type': 'string'
        },
        'yaml_file': {
            'inputBinding': {
                'prefix': '-f',
                'position': 3
            },
            'type': 'File'
        },
        'dssc_file': {
            'type': 'File'
        },
        'interim_yaml_title': {
            'type': 'string'
        }
    },
    CWL_OUTPUTS: {
        'result_notebook': {
            'outputBinding': {
                'glob': '$(inputs.result)'
            },
            'type': 'File'
        },
        'interim_yaml': {
            'outputBinding': {
                'glob': '$(inputs.interim_yaml_title)'
            },
            'type': 'File'
        }
    },
    CWL_ARGUMENTS: [],
    CWL_REQUIREMENTS: {
        'InitialWorkDirRequirement': {
            'listing': '- $(inputs.dssc_file)'
        }
    },
    CWL_HINTS: {}
}

VALID_SETTINGS_DICT = {
    CWL_NAME: 'settings_name',
    CWL_VARIABLES: {
        'int': 0,
        'float': 3.5,
        'array': [0, 1],
        'dict': {1: 1, 2: 2},
        'set': {1, 2},
        'char': 'c',
        'string': "String",
        'boolean': True
    }
}

VALID_PATTERN_FORM_VALUES = {
    NAME: 'test_pattern',
    TRIGGER_PATHS: ['dir/literal.path'],
    RECIPES: [
        'test_recipe'
    ],
    INPUT_FILE: 'trigger_file_name',
    OUTPUT: [
        {
            NAME_KEY: 'outfile_1',
            VALUE_KEY: 'dir_1/out.path'
        },
        {
            NAME_KEY: 'outfile_2',
            VALUE_KEY: 'dir_2/out.path'
        }
    ],
    VARIABLES: [
        {
            NAME_KEY: 'int',
            VALUE_KEY: 0
        },
        {
            NAME_KEY: 'float',
            VALUE_KEY: 3.5
        },
        {
            NAME_KEY: 'array',
            VALUE_KEY: [0, 1]
        },
        {
            NAME_KEY: 'dict',
            VALUE_KEY: {1: 1, 2: 2}
        },
        {
            NAME_KEY: 'set',
            VALUE_KEY: {1, 2}
        },
        {
            NAME_KEY: 'char',
            VALUE_KEY: 'c'
        },
        {
            NAME_KEY: 'string',
            VALUE_KEY: "String"
        },
        {
            NAME_KEY: 'boolean',
            VALUE_KEY: True
        }
    ],
    SWEEP: [
        {
            NAME_KEY: 'going_up',
            SWEEP_START_KEY: 0,
            SWEEP_STOP_KEY: 10,
            SWEEP_JUMP_KEY: 1
        },
        {
            NAME_KEY: 'going_down',
            SWEEP_START_KEY: 0,
            SWEEP_STOP_KEY: -10,
            SWEEP_JUMP_KEY: -1
        }
    ]
}

VALID_RECIPE_FORM_VALUES = {
    NAME: 'test_recipe',
    SOURCE: EMPTY_NOTEBOOK
}

VALID_WORKFLOW_FORM_VALUES = {
    CWL_NAME: 'workflow_name',
    CWL_INPUTS: [
        {
            'Name': 'analysis_notebook',
            'Value': 'File'
        },
        {
            'Name': 'analysis_result',
            'Value': 'string'
        },
        {
            'Name': 'analysis_yaml_file',
            'Value': 'File'
        },
        {
            'Name': 'analysis_dssc',
            'Value': 'File'
        },
        {
            'Name': 'analysis_interim_yaml',
            'Value': 'string'
        },
        {
            'Name': 'plotting_notebook',
            'Value': 'File'
        },
        {
            'Name': 'plotting_result',
            'Value': 'string'
        }
    ],
    CWL_OUTPUTS: [
        {
            'Name': 'final_plot',
            'Value': "{'type': 'File','outputSource': 'plot/result_notebook'}"
        }
    ],
    CWL_STEPS: [
        {
            'Name': 'analysis',
            'Value': "{'run': 'data_analysis.cwl', 'in':{'notebook': "
                     "'analysis_notebook', 'result': 'analysis_result', "
                     "'yaml_file': 'analysis_yaml_file', 'dssc_file': "
                     "'analysis_dssc', 'interim_yaml_title': "
                     "'analysis_interim_yaml'},'out': '[result_notebook, "
                     "interim_yaml]'}"
        },
        {
            'Name': 'plot',
            'Value': "{'run': 'data_plotting.cwl', 'in':{'notebook': "
                     "'plotting_notebook', 'result': 'plotting_result', "
                     "'yaml_file': 'analysis/interim_yaml'}, 'out': "
                     "'[result_notebook]'}"
        }
    ],
    CWL_REQUIREMENTS: {},
}

VALID_STEP_FORM_VALUES = {
    CWL_NAME: 'step_name',
    CWL_BASE_COMMAND: 'papermill',
    CWL_STDOUT: '',
    CWL_INPUTS: [
        {
            'Name': 'notebook',
            'Value': "{'inputBinding': {'position': 1}, 'type': 'File'}"
        },
        {
            'Name': 'result',
            'Value': "{'inputBinding': {'position': 2}, 'type': 'string'}"
        },
        {
            'Name': 'yaml_file',
            'Value': "{'inputBinding': {'position': 3, 'prefix': '-f'}, "
                     "'type': 'File'}"
        },
        {
            'Name': 'dssc_file',
            'Value': "{'type': 'File'}"
        },
        {
            'Name': 'interim_yaml_title',
            'Value': "{'type': 'string'}"
        },
    ],
    CWL_OUTPUTS: [
        {
            'Name': 'result_notebook',
            'Value': "{"
                        "'outputBinding':{"
                            "'glob': '$(inputs.result)'"
                        "},"
                        "'type': 'File'"
                     "}"
        },
        {
            'Name': 'interim_yaml',
            'Value': "{"
                        "'outputBinding':{"
                            "'glob': '$(inputs.interim_yaml_title)'"
                        "}, "
                        "'type': 'File'"
                     "}"
        }
    ],
    CWL_ARGUMENTS: [],
    CWL_REQUIREMENTS: [
        {
            'Name': 'InitialWorkDirRequirement',
            'Value': "{'listing':'- $(inputs.dssc_file)'}"
        }
    ],
    CWL_HINTS: []
}

VALID_SETTINGS_FORM_VALUES = {
    CWL_NAME: 'settings_name',
    CWL_VARIABLES: [
        {
            'Name': 'int',
            'Value': 0
        },
        {
            'Name': 'float',
            'Value': 3.5
        },
        {
            'Name': 'array',
            'Value': [0, 1]
        },
        {
            'Name': 'dict',
            'Value': {1: 1, 2: 2}
        },
        {
            'Name': 'set',
            'Value': {1, 2}
        },
        {
            'Name': 'char',
            'Value': 'c'
        },
        {
            'Name': 'string',
            'Value': "String"
        },
        {
            'Name': 'boolean',
            'Value': True
        }
    ]
}


class WorkflowTest(unittest.TestCase):
    def setUp(self):
        for file in REQUIRED_FILES:
            if os.path.exists(file):
                raise Exception(
                    "Required test location '%s' is already in use"
                    % file
                )

        for file in REQUIRED_ABSENT_FILES:
            if os.path.exists(file):
                raise Exception(
                    "Required test location '%s' is already in use"
                    % file
                )

        for file in NOTEBOOKS:
            if os.path.sep in file:
                dirs_list = file.split(os.path.sep)
                current_path = ''
                for directory in range(len(dirs_list) - 1):
                    current_path += dirs_list[directory]
                    if not os.path.exists(current_path):
                        os.mkdir(current_path)
                    current_path += os.path.sep
            notebook = nbformat.v4.new_notebook()
            nbformat.write(notebook, file)

    def tearDown(self):
        for file in REQUIRED_FILES:
            os.remove(file)

    def testPatternDictCheck(self):
        # Test valid pattern dict is accepted
        valid, msg = is_valid_pattern_dict(VALID_PATTERN_DICT)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that 'output' is optional.
        no_output_dict = copy.deepcopy(VALID_PATTERN_DICT)
        no_output_dict.pop(OUTPUT)
        valid, msg = is_valid_pattern_dict(no_output_dict)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that 'variables' is optional.
        no_variables_dict = copy.deepcopy(VALID_PATTERN_DICT)
        no_variables_dict.pop(VARIABLES)
        valid, msg = is_valid_pattern_dict(no_variables_dict)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test non-dict is rejected
        valid, msg = is_valid_pattern_dict(1)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test invalid 'name' type is rejected
        incorrect_name_dict = copy.deepcopy(VALID_PATTERN_DICT)
        incorrect_name_dict[NAME] = 1
        valid, msg = is_valid_pattern_dict(incorrect_name_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test invalid 'input_paths' type is rejected
        incorrect_paths_dict = copy.deepcopy(VALID_PATTERN_DICT)
        incorrect_paths_dict[TRIGGER_PATHS] = 1
        valid, msg = is_valid_pattern_dict(incorrect_paths_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test invalid 'trigger_recipes' type is rejected
        incorrect_recipes_dict = copy.deepcopy(VALID_PATTERN_DICT)
        incorrect_recipes_dict[TRIGGER_RECIPES] = 1
        valid, msg = is_valid_pattern_dict(incorrect_recipes_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test invalid 'input_file' type is rejected
        incorrect_file_dict = copy.deepcopy(VALID_PATTERN_DICT)
        incorrect_file_dict[INPUT_FILE] = 1
        valid, msg = is_valid_pattern_dict(incorrect_file_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test invalid 'output' type is rejected.
        incorrect_output_dict = copy.deepcopy(VALID_PATTERN_DICT)
        incorrect_output_dict[OUTPUT] = 1
        valid, msg = is_valid_pattern_dict(incorrect_output_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test invalid 'variables' type is rejected.
        incorrect_variables_dict = copy.deepcopy(VALID_PATTERN_DICT)
        incorrect_variables_dict[VARIABLES] = 1
        valid, msg = is_valid_pattern_dict(incorrect_variables_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test missing 'name' key is rejected.
        no_name_dict = copy.deepcopy(VALID_PATTERN_DICT)
        no_name_dict.pop(NAME)
        valid, msg = is_valid_pattern_dict(no_name_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test missing 'input_paths' key is rejected.
        no_paths_dict = copy.deepcopy(VALID_PATTERN_DICT)
        no_paths_dict.pop(TRIGGER_PATHS)
        valid, msg = is_valid_pattern_dict(no_paths_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test missing 'trigger_recipes' key is rejected.
        no_recipes_dict = copy.deepcopy(VALID_PATTERN_DICT)
        no_recipes_dict.pop(TRIGGER_RECIPES)
        valid, msg = is_valid_pattern_dict(no_recipes_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test missing 'input_file' key is rejected.
        no_file_dict = copy.deepcopy(VALID_PATTERN_DICT)
        no_file_dict.pop(INPUT_FILE)
        valid, msg = is_valid_pattern_dict(no_file_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test extra keys do not fail, if 'strict' is left False.
        extra_values_dict = copy.deepcopy(VALID_PATTERN_DICT)
        extra_values_dict['extra'] = 'extra'
        valid, msg = is_valid_pattern_dict(extra_values_dict)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test extra keys fail if 'strict set to True.
        valid, msg = is_valid_pattern_dict(extra_values_dict, strict=True)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

    def testNewPatternCreation(self):
        test_pattern = Pattern('standard_pattern')

        # Test that pattern with only a name is not valid.
        valid, _ = test_pattern.integrity_check()
        self.assertFalse(valid)

        test_pattern.add_single_input('input_file', 'dir/regex.path')
        # Test that we cannot add a 'single input' once one has already been
        # defined
        with self.assertRaises(Exception):
            test_pattern.add_single_input('another_input', 'dir/regex.path')

        # Test that pattern is not valid without recipe.
        valid, msg = test_pattern.integrity_check()
        self.assertFalse(valid)

        test_pattern.add_recipe('recipe')
        test_pattern.add_recipe('recipe')

        # Test that both recipes have been added.
        self.assertEqual(len(test_pattern.recipes), 2)

        # Test that pattern is now valid, but that it returns a no output
        # warning.
        valid, msg = test_pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, NO_OUTPUT_SET_WARNING)

        test_pattern.add_output('output_file', 'dir/regex.path')
        test_pattern.add_output('another_output', 'dir/regex.path')
        # Test that we cannot define two outputs with the same name.
        with self.assertRaises(Exception):
            test_pattern.add_output('another_output', 'dir/regex.path')

        test_pattern.return_notebook('dir/notebook.path')

        test_pattern.add_variable('int', 0)
        test_pattern.add_variable('float', 3.5)
        test_pattern.add_variable('array', [0, 1])
        test_pattern.add_variable('dict', {1: 1, 2: 2})
        test_pattern.add_variable('set', {1, 2})
        test_pattern.add_variable('char', 'c')
        test_pattern.add_variable('string', "String")
        test_pattern.add_variable('boolean', True)

        # Test that pattern is still valid with added variables
        valid, msg = test_pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that we cannot add a variable that already has been defined.
        with self.assertRaises(Exception):
            test_pattern.add_variable('int', 1)

        # Test that pattern is still valid and the 3 above tests have not
        # invalidated the pattern.
        valid, msg = test_pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

    def testDictPatternCreation(self):
        # Test pattern is valid with valid dictionary input. This simulates a
        # dictionary provided by the MiG, with an already registered recipe.
        test_pattern = Pattern(VALID_PATTERN_DICT)
        valid, msg = test_pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        alt_pattern_dict = {
            NAME: 'alt_dict_pattern',
            TRIGGER_PATHS: ['dir/literal.path'],
            TRIGGER_RECIPES: {
                'trigger_id': {
                    'recipe_name': {}
                }
            },
            INPUT_FILE: 'trigger_file_name',
            OUTPUT: {
                'outfile_1': 'dir_1/outpath.txt',
                'outfile_2': 'dir_2/outpath.txt',
            },
            VARIABLES: {
                'int': 0,
                'float': 3.5,
                'array': [0, 1],
                'dict': {1: 1, 2: 2},
                'set': {1, 2},
                'char': 'c',
                'string': "String",
                'boolean': True
            }
        }

        # Test pattern is valid with valid dictionary input. This simulates a
        # dictionary provided by the MiG, with a recipe not yet registered.
        test_alt_pattern = Pattern(alt_pattern_dict)
        valid, msg = test_alt_pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that no 'name' value is rejected.
        test_alt_pattern.name = None
        valid, msg = test_alt_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, NO_NAME_SET_ERROR)

        # Test that an empty 'name' value is rejected.
        test_alt_pattern.name = ''
        valid, msg = test_alt_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, NO_NAME_SET_ERROR)

        invalid_recipes = {
            NAME: 'invalid_recipes',
            TRIGGER_PATHS: ['dir/literal.path'],
            TRIGGER_RECIPES: {
                'recipe_name': {}
            },
            INPUT_FILE: 'trigger_file_name',
            OUTPUT: {
                'outfile_1': 'dir_1/outpath.txt',
                'outfile_2': 'dir_2/outpath.txt',
            },
            VARIABLES: {
                'int': 0,
                'float': 3.5,
                'array': [0, 1],
                'dict': {1: 1, 2: 2},
                'set': {1, 2},
                'char': 'c',
                'string': "String",
                'boolean': True
            }
        }

        # Test that incorrectly formatted 'trigger_recipes' values is rejected.
        with self.assertRaises(Exception):
            Pattern(invalid_recipes)

        no_paths = {
            NAME: 'dict_pattern',
            TRIGGER_PATHS: [],
            TRIGGER_RECIPES: {
                'trigger_id': {
                    'recipe_id': {
                        'name': 'test_recipe',
                        'source': 'source.ipynb',
                        'recipe': {}
                    }
                }
            },
            INPUT_FILE: 'trigger_file_name',
            OUTPUT: {
                'outfile_1': 'dir_1/outpath.txt',
                'outfile_2': 'dir_2/outpath.txt',
            },
            VARIABLES: {
                'int': 0,
                'float': 3.5,
                'array': [0, 1],
                'dict': {1: 1, 2: 2},
                'set': {1, 2},
                'char': 'c',
                'string': "String",
                'boolean': True,
                'outfile_1': 'something'
            }
        }

        invalid_in_file = {
            NAME: 'dict_pattern',
            TRIGGER_PATHS: ['path'],
            TRIGGER_RECIPES: {
                'trigger_id': {
                    'recipe_id': {
                        'name': 'test_recipe',
                        'source': 'source.ipynb',
                        'recipe': {}
                    }
                }
            },
            INPUT_FILE: '',
            OUTPUT: {
                'outfile_1': 'dir_1/outpath.txt',
                'outfile_2': 'dir_2/outpath.txt',
            },
            VARIABLES: {
                'int': 0,
                'float': 3.5,
                'array': [0, 1],
                'dict': {1: 1, 2: 2},
                'set': {1, 2},
                'char': 'c',
                'string': "String",
                'boolean': True,
                'outfile_1': 'something'
            }
        }

        # Test that empty 'input_file' value is rejected.
        with self.assertRaises(Exception):
            Pattern(invalid_in_file)

        # Test that no pattern 'trigger_file' is rejected.
        no_infile_pattern = Pattern(VALID_PATTERN_DICT)
        no_infile_pattern.trigger_file = None
        valid, msg = no_infile_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, NO_INPUT_FILE_SET_ERROR)

        # Test that empty pattern 'trigger_file is rejected.
        no_infile_pattern.trigger_file = ''
        valid, msg = no_infile_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, NO_INPUT_FILE_SET_ERROR)

    def testPatternPlaceholderCheck(self):
        # Test that pattern is valid with valid dictionary.
        test_pattern = Pattern(VALID_PATTERN_DICT)
        valid, msg = test_pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that placeholder name value is invalid.
        placeholder_name_pattern = Pattern(VALID_PATTERN_DICT)
        placeholder_name_pattern.name = PLACEHOLDER
        valid, msg = placeholder_name_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, PLACEHOLDER_ERROR)

        # Test that placeholder 'input_file' is invalid.
        placeholder_trigger_file_pattern = Pattern(VALID_PATTERN_DICT)
        placeholder_trigger_file_pattern.trigger_file = PLACEHOLDER
        placeholder_trigger_file_pattern.variables[PLACEHOLDER] = PLACEHOLDER
        valid, msg = placeholder_trigger_file_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, PLACEHOLDER_ERROR)

        # Test that placeholder 'trigger_paths' is invalid.
        placeholder_trigger_paths_pattern = Pattern(VALID_PATTERN_DICT)
        placeholder_trigger_paths_pattern.trigger_paths = PLACEHOLDER
        valid, msg = placeholder_trigger_paths_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, PLACEHOLDER_ERROR)

        # Test that placeholder 'recipes' is invalid.
        placeholder_recipes_pattern = Pattern(VALID_PATTERN_DICT)
        placeholder_recipes_pattern.recipes = PLACEHOLDER
        valid, msg = placeholder_recipes_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, PLACEHOLDER_ERROR)

        # Test that placeholder being in 'trigger_paths' list is invalid.
        placeholder_in_path_entries_pattern = Pattern(VALID_PATTERN_DICT)
        placeholder_in_path_entries_pattern.trigger_paths[0] = PLACEHOLDER
        valid, msg = placeholder_in_path_entries_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, PLACEHOLDER_ERROR)

        # Test that placeholder being in 'recipes' list is invalid.
        placeholder_recipe_entries_pattern = Pattern(VALID_PATTERN_DICT)
        placeholder_recipe_entries_pattern.recipes[0] = PLACEHOLDER
        valid, msg = placeholder_recipe_entries_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, PLACEHOLDER_ERROR)

        # Test that placeholder being in 'variables' keys is invalid.
        placeholder_variable_key_pattern = Pattern(VALID_PATTERN_DICT)
        placeholder_variable_key_pattern.variables[PLACEHOLDER] = 'value'
        valid, msg = placeholder_variable_key_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, PLACEHOLDER_ERROR)

        # Test that placeholder being in 'variables' values is invalid.
        placeholder_variable_value_pattern = Pattern(VALID_PATTERN_DICT)
        placeholder_variable_value_pattern.variables['extra'] = PLACEHOLDER
        valid, msg = placeholder_variable_value_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, PLACEHOLDER_ERROR)

        # Test that placeholder being in 'output' keys is invalid.
        placeholder_output_key_pattern = Pattern(VALID_PATTERN_DICT)
        placeholder_output_key_pattern.outputs[PLACEHOLDER] = 'path'
        placeholder_output_key_pattern.variables[PLACEHOLDER] = PLACEHOLDER
        valid, msg = placeholder_output_key_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, PLACEHOLDER_ERROR)

        # Test that placeholder being in 'output' values is invalid.
        placeholder_output_value_pattern = Pattern(VALID_PATTERN_DICT)
        placeholder_output_value_pattern.outputs['extra'] = PLACEHOLDER
        placeholder_output_value_pattern.variables['extra'] = 'extra'
        valid, msg = placeholder_output_value_pattern.integrity_check()
        self.assertFalse(valid)
        self.assertEqual(msg, PLACEHOLDER_ERROR)

    def testPatternIdentify(self):
        test_pattern_1 = Pattern('identical_pattern')

        test_pattern_1.add_single_input('trigger_file_name', 'dir/regex.path')

        test_pattern_1.add_output('outfile_1', 'dir_1/outpath.txt')
        test_pattern_1.add_output('outfile_2', 'dir_2/outpath.txt')

        test_pattern_1.add_recipe('recipe')

        test_pattern_1.add_variable('int', 0)
        test_pattern_1.add_variable('float', 3.5)
        test_pattern_1.add_variable('array', [0, 1])
        test_pattern_1.add_variable('dict', {1: 1, 2: 2})
        test_pattern_1.add_variable('set', {1, 2})
        test_pattern_1.add_variable('char', 'c')
        test_pattern_1.add_variable('string', "String")
        test_pattern_1.add_variable('boolean', True)

        # Test that first pattern is valid.
        valid, msg = test_pattern_1.integrity_check()
        self.assertTrue(valid)

        pattern_dict = {
            NAME: 'identical_pattern',
            TRIGGER_PATHS: ['dir/regex.path'],
            TRIGGER_RECIPES: {
                'trigger_id': {
                    'recipe_id': {
                        'name': 'recipe',
                        'source': 'source.ipynb',
                        'recipe': {}
                    }
                }
            },
            INPUT_FILE: 'trigger_file_name',
            OUTPUT: {
                'outfile_1': 'dir_1/outpath.txt',
                'outfile_2': 'dir_2/outpath.txt',
            },
            VARIABLES: {
                'int': 0,
                'float': 3.5,
                'array': [0, 1],
                'dict': {1: 1, 2: 2},
                'set': {1, 2},
                'char': 'c',
                'string': "String",
                'boolean': True
            }
        }

        # Test that second pattern is valid.
        test_pattern_2 = Pattern(pattern_dict)
        valid, msg = test_pattern_2.integrity_check()
        self.assertTrue(valid)

        pattern_dict['persistence_id'] = '12345678910'

        # Test that third pattern is valid
        test_pattern_3 = Pattern(pattern_dict)
        valid, msg = test_pattern_3.integrity_check()
        self.assertTrue(valid)

        # Test that first and second patterns are equal
        self.assertTrue(test_pattern_1 == test_pattern_2)

        # Test that first and third patterns are not equal
        self.assertFalse(test_pattern_1 == test_pattern_3)

        # Test that second and third patterns are not equal
        self.assertFalse(test_pattern_2 == test_pattern_3)

    def testPatternsDictCheck(self):
        # Test that check on patterns dict is acceptable
        pattern_one = Pattern(VALID_PATTERN_DICT)

        pattern_two_dict = copy.deepcopy(VALID_PATTERN_DICT)
        pattern_two_dict[NAME] = 'second_pattern'
        pattern_two = Pattern(pattern_two_dict)

        patterns = {
            pattern_one.name: pattern_one,
            pattern_two.name: pattern_two
        }

        # Test that dict of patterns is a dict of patterns.
        valid, msg = check_patterns_dict(patterns)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that non-dict types are rejected.
        valid, msg = check_patterns_dict(1)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        wrong_names_patterns = {
            pattern_one.name: pattern_two,
            pattern_two.name: pattern_one
        }

        # Test that wrongly labeled patterns are rejected.
        valid, msg = check_patterns_dict(wrong_names_patterns)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        wrong_type = {
            pattern_one.name: pattern_one,
            pattern_two.name: 2
        }

        # Test that wrongly typed patterns are rejected.
        valid, msg = check_patterns_dict(wrong_type)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        invalid_pattern = Pattern(VALID_PATTERN_DICT)
        invalid_pattern.recipes = None

        invalid_patterns = {
            pattern_one.name: pattern_one,
            pattern_two.name: invalid_pattern
        }

        # Test that invalid patterns are rejected.
        valid, msg = check_patterns_dict(invalid_patterns)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

    def testRecipeDictCheck(self):
        # Test that valid dict is valid.
        valid, msg = is_valid_recipe_dict(VALID_RECIPE_DICT)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that non-dict type is rejected.
        valid, msg = is_valid_recipe_dict(1)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that invalid 'name' type is rejected.
        incorrect_name_dict = copy.deepcopy(VALID_RECIPE_DICT)
        incorrect_name_dict[NAME] = 1
        valid, msg = is_valid_recipe_dict(incorrect_name_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that invalid 'source' type is rejected.
        incorrect_source_dict = copy.deepcopy(VALID_RECIPE_DICT)
        incorrect_source_dict[SOURCE] = 1
        valid, msg = is_valid_recipe_dict(incorrect_source_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that invalid 'recipe' type is rejected.
        incorrect_recipe_dict = copy.deepcopy(VALID_RECIPE_DICT)
        incorrect_recipe_dict[RECIPE] = 1
        valid, msg = is_valid_recipe_dict(incorrect_recipe_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that no 'name' key is rejected.
        no_name_dict = copy.deepcopy(VALID_RECIPE_DICT)
        no_name_dict.pop(NAME)
        valid, msg = is_valid_recipe_dict(no_name_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that no 'source' key is rejected.
        no_source_dict = copy.deepcopy(VALID_RECIPE_DICT)
        no_source_dict.pop(SOURCE)
        valid, msg = is_valid_recipe_dict(no_source_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that no 'recipe' key is rejected.
        no_recipe_dict = copy.deepcopy(VALID_RECIPE_DICT)
        no_recipe_dict.pop(RECIPE)
        valid, msg = is_valid_recipe_dict(no_recipe_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that extra keys are still valid when 'strict' left set to False.
        extra_values_dict = copy.deepcopy(VALID_RECIPE_DICT)
        extra_values_dict['extra'] = 'extra'
        valid, msg = is_valid_recipe_dict(extra_values_dict)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that extra keys are rejected when 'strict' set to True.
        valid, msg = is_valid_recipe_dict(extra_values_dict, strict=True)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

    def testRecipeCreation(self):
        notebook_dict = nbformat.read(EMPTY_NOTEBOOK, nbformat.NO_CONVERT)

        recipe_dict = create_recipe_dict(
            notebook_dict,
            VALID_RECIPE_DICT[NAME],
            EMPTY_NOTEBOOK
        )

        # Test that created recipe has expected values.
        self.assertTrue(recipe_dict == VALID_RECIPE_DICT)

        # Test that created recipe is valid
        valid, msg = is_valid_recipe_dict(recipe_dict)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

    def testRecipesDictCheck(self):
        recipe_one = copy.deepcopy(VALID_RECIPE_DICT)
        recipe_two = copy.deepcopy(VALID_RECIPE_DICT)
        recipe_two[NAME] = 'second_recipe'

        recipes = {
            recipe_one[NAME]: recipe_one,
            recipe_two[NAME]: recipe_two
        }

        # Test that check on recipes dict is acceptable
        valid, msg = check_recipes_dict(recipes)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that non-dict types are rejected.
        valid, msg = check_recipes_dict(1)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        wrong_names_recipes = {
            recipe_one[NAME]: recipe_two,
            recipe_two[NAME]: recipe_one
        }

        # Test that wrongly labeled recipes are rejected.
        valid, msg = check_recipes_dict(wrong_names_recipes)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        wrong_type = {
            recipe_one[NAME]: recipe_one,
            recipe_two[NAME]: 2
        }

        # Test that wrongly typed recipes are rejected.
        valid, msg = check_recipes_dict(wrong_type)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        invalid_recipe = copy.deepcopy(VALID_RECIPE_DICT)
        invalid_recipe[SOURCE] = None

        invalid_recipes = {
            recipe_one[NAME]: recipe_one,
            recipe_two[NAME]: invalid_recipe
        }

        # Test that invalid recipes are rejected.
        valid, msg = check_recipes_dict(invalid_recipes)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

    def testWorkflowDictCheck(self):
        # Test that valid dict is valid.
        valid, msg = is_valid_workflow_dict(VALID_WORKFLOW_DICT)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that non-dict type is rejected.
        valid, msg = is_valid_workflow_dict(1)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that non 'Workflow' class is rejected.
        incorrect_class_dict = copy.deepcopy(VALID_WORKFLOW_DICT)
        incorrect_class_dict[CWL_CLASS] = CWL_CLASS_COMMAND_LINE_TOOL
        valid, msg = is_valid_workflow_dict(incorrect_class_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that invalid 'name' type is rejected.
        incorrect_name_dict = copy.deepcopy(VALID_WORKFLOW_DICT)
        incorrect_name_dict[CWL_NAME] = 1
        valid, msg = is_valid_workflow_dict(incorrect_name_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that invalid 'cwl_version' type is rejected.
        incorrect_version_dict = copy.deepcopy(VALID_WORKFLOW_DICT)
        incorrect_version_dict[CWL_CWL_VERSION] = 1
        valid, msg = is_valid_workflow_dict(incorrect_version_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that invalid 'class' type is rejected.
        incorrect_class_dict = copy.deepcopy(VALID_WORKFLOW_DICT)
        incorrect_class_dict[CWL_CLASS] = 1
        valid, msg = is_valid_workflow_dict(incorrect_class_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that invalid 'inputs' type is rejected.
        incorrect_inputs_dict = copy.deepcopy(VALID_WORKFLOW_DICT)
        incorrect_inputs_dict[CWL_INPUTS] = 1
        valid, msg = is_valid_workflow_dict(incorrect_inputs_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that invalid 'outputs' type is rejected.
        incorrect_outputs_dict = copy.deepcopy(VALID_WORKFLOW_DICT)
        incorrect_outputs_dict[CWL_OUTPUTS] = 1
        valid, msg = is_valid_workflow_dict(incorrect_outputs_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that invalid 'steps' type is rejected.
        incorrect_steps_dict = copy.deepcopy(VALID_WORKFLOW_DICT)
        incorrect_steps_dict[CWL_STEPS] = 1
        valid, msg = is_valid_workflow_dict(incorrect_steps_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that invalid 'requirements' type is rejected.
        incorrect_requirements_dict = copy.deepcopy(VALID_WORKFLOW_DICT)
        incorrect_requirements_dict[CWL_REQUIREMENTS] = 1
        valid, msg = is_valid_workflow_dict(incorrect_requirements_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that no 'name' key is rejected.
        no_name_dict = copy.deepcopy(VALID_WORKFLOW_DICT)
        no_name_dict.pop(CWL_NAME)
        valid, msg = is_valid_workflow_dict(no_name_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that no 'cwl_version' key is rejected.
        no_version_dict = copy.deepcopy(VALID_WORKFLOW_DICT)
        no_version_dict.pop(CWL_CWL_VERSION)
        valid, msg = is_valid_workflow_dict(no_version_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that no 'class' key is rejected.
        no_class_dict = copy.deepcopy(VALID_WORKFLOW_DICT)
        no_class_dict.pop(CWL_CLASS)
        valid, msg = is_valid_workflow_dict(no_class_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that no 'inputs' key is rejected.
        no_inputs_dict = copy.deepcopy(VALID_WORKFLOW_DICT)
        no_inputs_dict.pop(CWL_INPUTS)
        valid, msg = is_valid_workflow_dict(no_inputs_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that no 'outputs' key is rejected.
        no_outputs_dict = copy.deepcopy(VALID_WORKFLOW_DICT)
        no_outputs_dict.pop(CWL_OUTPUTS)
        valid, msg = is_valid_workflow_dict(no_outputs_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that no 'steps' key is rejected.
        no_steps_dict = copy.deepcopy(VALID_WORKFLOW_DICT)
        no_steps_dict.pop(CWL_STEPS)
        valid, msg = is_valid_workflow_dict(no_steps_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that 'requirements' key is optional.
        no_requirements_dict = copy.deepcopy(VALID_WORKFLOW_DICT)
        no_requirements_dict.pop(CWL_REQUIREMENTS)
        valid, msg = is_valid_workflow_dict(no_requirements_dict)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that extra keys are still valid when 'strict' left set to False.
        extra_values_dict = copy.deepcopy(VALID_WORKFLOW_DICT)
        extra_values_dict['extra'] = 'extra'
        valid, msg = is_valid_workflow_dict(extra_values_dict)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that extra keys are rejected when 'strict' set to True.
        valid, msg = is_valid_workflow_dict(extra_values_dict, strict=True)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

    def testWorkflowCreation(self):
        workflow_dict = copy.deepcopy(VALID_WORKFLOW_DICT)

        # Test that created workflow is valid
        valid, msg = is_valid_workflow_dict(workflow_dict)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

    def testWorkflowsDictCheck(self):
        workflow_one = copy.deepcopy(VALID_WORKFLOW_DICT)
        workflow_two = copy.deepcopy(VALID_WORKFLOW_DICT)
        workflow_two[CWL_NAME] = 'second_workflow'

        workflows = {
            workflow_one[CWL_NAME]: workflow_one,
            workflow_two[CWL_NAME]: workflow_two
        }

        # Test that check on workflows dict is acceptable
        valid, msg = check_workflows_dict(workflows)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that non-dict types are rejected.
        valid, msg = check_workflows_dict(1)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        wrong_names_workflows = {
            workflow_one[CWL_NAME]: workflow_two,
            workflow_two[CWL_NAME]: workflow_one
        }

        # Test that wrongly labeled workflows are rejected.
        valid, msg = check_workflows_dict(wrong_names_workflows)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        wrong_type = {
            workflow_one[CWL_NAME]: workflow_one,
            workflow_two[CWL_NAME]: 2
        }

        # Test that wrongly typed workflows are rejected.
        valid, msg = check_workflows_dict(wrong_type)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        invalid_workflow = copy.deepcopy(VALID_WORKFLOW_DICT)
        invalid_workflow[CWL_NAME] = None

        invalid_workflows = {
            workflow_one[CWL_NAME]: workflow_one,
            workflow_two[CWL_NAME]: invalid_workflow
        }

        # Test that invalid workflows are rejected.
        valid, msg = check_workflows_dict(invalid_workflows)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

    def testStepDictCheck(self):
        # Test that valid dict is valid.
        valid, msg = is_valid_step_dict(VALID_STEP_DICT)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that non-dict type is rejected.
        valid, msg = is_valid_step_dict(1)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that non 'CommandLineTool' class is rejected.
        incorrect_class_dict = copy.deepcopy(VALID_STEP_DICT)
        incorrect_class_dict[CWL_CLASS] = CWL_CLASS_WORKFLOW
        valid, msg = is_valid_step_dict(incorrect_class_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that invalid 'name' type is rejected.
        incorrect_name_dict = copy.deepcopy(VALID_STEP_DICT)
        incorrect_name_dict[CWL_NAME] = 1
        valid, msg = is_valid_step_dict(incorrect_name_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that invalid 'cwl_version' type is rejected.
        incorrect_version_dict = copy.deepcopy(VALID_STEP_DICT)
        incorrect_version_dict[CWL_CWL_VERSION] = 1
        valid, msg = is_valid_step_dict(incorrect_version_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that invalid 'class' type is rejected.
        incorrect_class_dict = copy.deepcopy(VALID_STEP_DICT)
        incorrect_class_dict[CWL_CLASS] = 1
        valid, msg = is_valid_step_dict(incorrect_class_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that invalid 'inputs' type is rejected.
        incorrect_inputs_dict = copy.deepcopy(VALID_STEP_DICT)
        incorrect_inputs_dict[CWL_INPUTS] = 1
        valid, msg = is_valid_step_dict(incorrect_inputs_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that invalid 'outputs' type is rejected.
        incorrect_outputs_dict = copy.deepcopy(VALID_STEP_DICT)
        incorrect_outputs_dict[CWL_OUTPUTS] = 1
        valid, msg = is_valid_step_dict(incorrect_outputs_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that invalid 'base_command' type is rejected.
        incorrect_base_command_dict = copy.deepcopy(VALID_STEP_DICT)
        incorrect_base_command_dict[CWL_BASE_COMMAND] = 1
        valid, msg = is_valid_step_dict(incorrect_base_command_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that invalid 'stdout' type is rejected.
        incorrect_stdout_dict = copy.deepcopy(VALID_STEP_DICT)
        incorrect_stdout_dict[CWL_STDOUT] = 1
        valid, msg = is_valid_step_dict(incorrect_stdout_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that invalid 'arguments' type is rejected.
        incorrect_arguments_dict = copy.deepcopy(VALID_STEP_DICT)
        incorrect_arguments_dict[CWL_ARGUMENTS] = 1
        valid, msg = is_valid_step_dict(incorrect_arguments_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that invalid 'requirements' type is rejected.
        incorrect_requirements_dict = copy.deepcopy(VALID_STEP_DICT)
        incorrect_requirements_dict[CWL_REQUIREMENTS] = 1
        valid, msg = is_valid_step_dict(incorrect_requirements_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that invalid 'hints' type is rejected.
        incorrect_hints_dict = copy.deepcopy(VALID_STEP_DICT)
        incorrect_hints_dict[CWL_HINTS] = 1
        valid, msg = is_valid_step_dict(incorrect_hints_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that no 'name' key is rejected.
        no_name_dict = copy.deepcopy(VALID_STEP_DICT)
        no_name_dict.pop(CWL_NAME)
        valid, msg = is_valid_step_dict(no_name_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that no 'cwl_version' key is rejected.
        no_version_dict = copy.deepcopy(VALID_STEP_DICT)
        no_version_dict.pop(CWL_CWL_VERSION)
        valid, msg = is_valid_step_dict(no_version_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that no 'class' key is rejected.
        no_class_dict = copy.deepcopy(VALID_STEP_DICT)
        no_class_dict.pop(CWL_CLASS)
        valid, msg = is_valid_step_dict(no_class_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that no 'inputs' key is rejected.
        no_inputs_dict = copy.deepcopy(VALID_STEP_DICT)
        no_inputs_dict.pop(CWL_INPUTS)
        valid, msg = is_valid_step_dict(no_inputs_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that no 'outputs' key is rejected.
        no_outputs_dict = copy.deepcopy(VALID_STEP_DICT)
        no_outputs_dict.pop(CWL_OUTPUTS)
        valid, msg = is_valid_step_dict(no_outputs_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that no 'base_command' key is rejected.
        no_base_command_dict = copy.deepcopy(VALID_STEP_DICT)
        no_base_command_dict.pop(CWL_BASE_COMMAND)
        valid, msg = is_valid_step_dict(no_base_command_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that 'stdout' key is optional.
        no_stdout_dict = copy.deepcopy(VALID_STEP_DICT)
        no_stdout_dict.pop(CWL_STDOUT)
        valid, msg = is_valid_step_dict(no_stdout_dict)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that 'arguments' key is optional.
        no_arguments_dict = copy.deepcopy(VALID_STEP_DICT)
        no_arguments_dict.pop(CWL_ARGUMENTS)
        valid, msg = is_valid_step_dict(no_arguments_dict)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that 'requirements' key is optional.
        no_requirements_dict = copy.deepcopy(VALID_STEP_DICT)
        no_requirements_dict.pop(CWL_REQUIREMENTS)
        valid, msg = is_valid_step_dict(no_requirements_dict)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that 'hints' key is optional.
        no_hints_dict = copy.deepcopy(VALID_STEP_DICT)
        no_hints_dict.pop(CWL_HINTS)
        valid, msg = is_valid_step_dict(no_hints_dict)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that extra keys are still valid when 'strict' left set to False.
        extra_values_dict = copy.deepcopy(VALID_STEP_DICT)
        extra_values_dict['extra'] = 'extra'
        valid, msg = is_valid_step_dict(extra_values_dict)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that extra keys are rejected when 'strict' set to True.
        valid, msg = is_valid_step_dict(extra_values_dict, strict=True)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

    def testStepCreation(self):
        step_dict = copy.deepcopy(VALID_STEP_DICT)

        # Test that created step is valid
        valid, msg = is_valid_step_dict(step_dict)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

    def testStepsDictCheck(self):
        step_one = copy.deepcopy(VALID_STEP_DICT)
        step_two = copy.deepcopy(VALID_STEP_DICT)
        step_two[CWL_NAME] = 'second_step'

        steps = {
            step_one[CWL_NAME]: step_one,
            step_two[CWL_NAME]: step_two
        }

        # Test that check on steps dict is acceptable
        valid, msg = check_steps_dict(steps)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that non-dict types are rejected.
        valid, msg = check_steps_dict(1)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        wrong_names_steps = {
            step_one[CWL_NAME]: step_two,
            step_two[CWL_NAME]: step_one
        }

        # Test that wrongly labeled steps are rejected.
        valid, msg = check_steps_dict(wrong_names_steps)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        wrong_type = {
            step_one[CWL_NAME]: step_one,
            step_two[CWL_NAME]: 2
        }

        # Test that wrongly typed steps are rejected.
        valid, msg = check_steps_dict(wrong_type)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        invalid_step = copy.deepcopy(VALID_STEP_DICT)
        invalid_step[CWL_NAME] = None

        invalid_steps = {
            step_one[CWL_NAME]: step_one,
            step_two[CWL_NAME]: invalid_step
        }

        # Test that invalid steps are rejected.
        valid, msg = check_steps_dict(invalid_steps)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

    def testSettingDictCheck(self):
        # Test that valid dict is valid.
        valid, msg = is_valid_setting_dict(VALID_SETTINGS_DICT)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that non-dict type is rejected.
        valid, msg = is_valid_setting_dict(1)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that invalid 'variables' type is rejected.
        incorrect_variables_dict = copy.deepcopy(VALID_SETTINGS_DICT)
        incorrect_variables_dict[CWL_VARIABLES] = 1
        valid, msg = is_valid_setting_dict(incorrect_variables_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that no 'name' key is rejected.
        no_name_dict = copy.deepcopy(VALID_SETTINGS_DICT)
        no_name_dict.pop(CWL_NAME)
        valid, msg = is_valid_setting_dict(no_name_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that not 'variables' key is rejected.
        no_variables_dict = copy.deepcopy(VALID_SETTINGS_DICT)
        no_variables_dict.pop(CWL_VARIABLES)
        valid, msg = is_valid_setting_dict(no_variables_dict)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        # Test that extra keys are still valid when 'strict' left set to False.
        extra_values_dict = copy.deepcopy(VALID_SETTINGS_DICT)
        extra_values_dict['extra'] = 'extra'
        valid, msg = is_valid_setting_dict(extra_values_dict)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that extra keys are rejected when 'strict' set to True.
        valid, msg = is_valid_setting_dict(extra_values_dict, strict=True)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

    def testSettingCreation(self):
        setting_dict = copy.deepcopy(VALID_SETTINGS_DICT)

        # Test that created setting is valid
        valid, msg = is_valid_setting_dict(setting_dict)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

    def testSettingsDictCheck(self):
        setting_one = copy.deepcopy(VALID_SETTINGS_DICT)
        setting_two = copy.deepcopy(VALID_SETTINGS_DICT)
        setting_two[CWL_NAME] = 'second_setting'

        settings = {
            setting_one[CWL_NAME]: setting_one,
            setting_two[CWL_NAME]: setting_two
        }

        # Test that check on settings dict is acceptable
        valid, msg = check_settings_dict(settings)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that non-dict types are rejected.
        valid, msg = check_settings_dict(1)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        wrong_names_settings = {
            setting_one[CWL_NAME]: setting_two,
            setting_two[CWL_NAME]: setting_one
        }

        # Test that wrongly labeled settings are rejected.
        valid, msg = check_settings_dict(wrong_names_settings)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        wrong_type = {
            setting_one[CWL_NAME]: setting_one,
            setting_two[CWL_NAME]: 2
        }

        # Test that wrongly typed settings are rejected.
        valid, msg = check_settings_dict(wrong_type)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

        invalid_setting = copy.deepcopy(VALID_SETTINGS_DICT)
        invalid_setting[CWL_NAME] = None

        invalid_settings = {
            setting_one[CWL_NAME]: setting_one,
            setting_two[CWL_NAME]: invalid_setting
        }

        # Test that invalid settings are rejected.
        valid, msg = check_settings_dict(invalid_settings)
        self.assertFalse(valid)
        self.assertIsNotNone(msg)

    def testMeowWorkflow(self):
        pattern_one_dict = {
            NAME: 'first_pattern',
            TRIGGER_PATHS: ['start'],
            TRIGGER_RECIPES: {
                'trigger_id': {
                    'recipe_id': {
                        'name': 'recipe',
                        'source': 'source.ipynb',
                        'recipe': {}
                    }
                }
            },
            INPUT_FILE: 'trigger_file_name',
            OUTPUT: {
                'outfile_1': '{VGRID}/first/one',
                'outfile_2': '{VGRID}/first/two',
            },
            VARIABLES: {}
        }

        # Test pattern_one is valid. This should have no ancestors and pattern
        # two and three and descendants.
        pattern_one = Pattern(pattern_one_dict)
        valid, msg = pattern_one.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        pattern_two_dict = {
            'name': 'second_pattern',
            'input_paths': ['first/one'],
            'trigger_recipes': {
                'trigger_id': {
                    'recipe_id': {
                        'name': 'recipe',
                        'source': 'source.ipynb',
                        'recipe': {}
                    }
                }
            },
            'input_file': 'trigger_file_name',
            'output': {},
            'variables': {}
        }

        # Test pattern_two is valid but has a no output warning. This should
        # have pattern one as an ancestor and no descendants.
        pattern_two = Pattern(pattern_two_dict)
        valid, msg = pattern_two.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, NO_OUTPUT_SET_WARNING)

        pattern_three_dict = {
            'name': 'third_pattern',
            'input_paths': ['first/two'],
            'trigger_recipes': {
                'trigger_id': {
                    'recipe_id': {
                        'name': 'recipe',
                        'source': 'source.ipynb',
                        'recipe': {}
                    }
                }
            },
            'input_file': 'trigger_file_name',
            'output': {
                'outfile': '{VGRID}/third/one'
            },
            'variables': {}
        }

        # Test pattern_three is valid. This should have pattern one and five
        # as ancestors and pattern 4 as a descendant.
        pattern_three = Pattern(pattern_three_dict)
        valid, msg = pattern_three.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        pattern_four_dict = {
            'name': 'fourth_pattern',
            'input_paths': ['third/one'],
            'trigger_recipes': {
                'trigger_id': {
                    'recipe_id': {
                        'name': 'recipe',
                        'source': 'source.ipynb',
                        'recipe': {}
                    }
                }
            },
            'input_file': 'trigger_file_name',
            'output': {
                'outfile': '{VGRID}/four/one'
            },
            'variables': {}
        }

        # Test pattern_four is valid. This should have pattern three as an
        # ancestor and pattern five as a descendant.
        pattern_four = Pattern(pattern_four_dict)
        valid, msg = pattern_four.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        pattern_five_dict = {
            'name': 'fifth_pattern',
            'input_paths': ['four/one'],
            'trigger_recipes': {
                'trigger_id': {
                    'recipe_id': {
                        'name': 'recipe',
                        'source': 'source.ipynb',
                        'recipe': {}
                    }
                }
            },
            'input_file': 'trigger_file_name',
            'output': {
                'outfile': '{VGRID}/first/two'
            },
            'variables': {}
        }

        # Test pattern_five is valid. This should have pattern four as an
        # ancestor and pattern three as a descendant.
        pattern_five = Pattern(pattern_five_dict)
        valid, msg = pattern_five.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        pattern_six_dict = {
            'name': 'sixth_pattern',
            'input_paths': ['unlinked'],
            'trigger_recipes': {
                'trigger_id': {
                    'recipe_id': {
                        'name': 'recipe',
                        'source': 'source.ipynb',
                        'recipe': {}
                    }
                }
            },
            'input_file': 'trigger_file_name',
            'output': {},
            'variables': {}
        }

        # Test pattern_six is valid but has a no output warning. This should
        # have no descendants or ancestors.
        pattern_six = Pattern(pattern_six_dict)
        valid, msg = pattern_six.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, NO_OUTPUT_SET_WARNING)

        patterns = {
            pattern_one.name: pattern_one,
            pattern_two.name: pattern_two,
            pattern_three.name: pattern_three,
            pattern_four.name: pattern_four,
            pattern_five.name: pattern_five,
            pattern_six.name: pattern_six
        }

        # Test that all patterns stored correctly.
        valid, msg = check_patterns_dict(patterns)
        self.assertTrue(valid)

        # Test that valid workflow is valid.
        valid, workflow = build_workflow_object(patterns)
        self.assertTrue(valid)

        # Test that returned workflow object is valid
        self.assertIsInstance(workflow, dict)
        self.assertEqual(len(workflow), len(patterns))
        for node_key, node in workflow.items():
            self.assertIsInstance(node, dict)
            self.assertIn('ancestors', node)
            self.assertIn('descendants', node)
            self.assertIn('workflow inputs', node)
            self.assertIn('workflow outputs', node)

        # Test that first pattern node has been correctly setup.
        self.assertEqual(workflow['first_pattern']['ancestors'], {})
        self.assertIn(
            'second_pattern', workflow['first_pattern']['descendants']
        )
        self.assertIn(
            'third_pattern', workflow['first_pattern']['descendants']
        )
        self.assertEqual(len(workflow['first_pattern']['descendants']), 2)

        # Test that second pattern node has been correctly setup.
        self.assertIn('first_pattern', workflow['second_pattern']['ancestors'])
        self.assertEqual(len(workflow['second_pattern']['ancestors']), 1)
        self.assertEqual(workflow['second_pattern']['descendants'], {})

        # Test that third pattern node has been correctly setup.
        self.assertIn('first_pattern', workflow['third_pattern']['ancestors'])
        self.assertIn('fifth_pattern', workflow['third_pattern']['ancestors'])
        self.assertEqual(len(workflow['third_pattern']['ancestors']), 2)
        self.assertIn(
            'fourth_pattern', workflow['third_pattern']['descendants']
        )
        self.assertEqual(len(workflow['third_pattern']['descendants']), 1)

        # Test that fourth pattern node has been correctly setup.
        self.assertIn('third_pattern', workflow['fourth_pattern']['ancestors'])
        self.assertEqual(len(workflow['fourth_pattern']['ancestors']), 1)
        self.assertIn(
            'fifth_pattern', workflow['fourth_pattern']['descendants']
        )
        self.assertEqual(len(workflow['fourth_pattern']['descendants']), 1)

        # Test that fifth pattern node has been correctly setup.
        self.assertIn('fourth_pattern', workflow['fifth_pattern']['ancestors'])
        self.assertEqual(len(workflow['fifth_pattern']['ancestors']), 1)
        self.assertIn(
            'third_pattern', workflow['fifth_pattern']['descendants']
        )
        self.assertEqual(len(workflow['fifth_pattern']['descendants']), 1)

        # Test that sixth pattern node has been correctly setup.
        self.assertEqual(workflow['sixth_pattern']['ancestors'], {})
        self.assertEqual(workflow['sixth_pattern']['descendants'], {})

    def testWorkflowWidgetCreation(self):
        workflow_widget = WorkflowWidget()

        # Test that default setup arguments are correct.
        self.assertEqual(workflow_widget.mode, MEOW_MODE)
        self.assertFalse(workflow_widget.auto_import)
        self.assertEqual(
            workflow_widget.workflow_title, DEFAULT_WORKFLOW_TITLE
        )
        self.assertEqual(
            workflow_widget.cwl_import_export_dir,
            DEFAULT_CWL_IMPORT_EXPORT_DIR
        )
        self.assertEqual(workflow_widget.meow[PATTERNS], {})
        self.assertEqual(workflow_widget.meow[RECIPES], {})
        self.assertEqual(workflow_widget.cwl[WORKFLOWS], {})
        self.assertEqual(workflow_widget.cwl[STEPS], {})
        self.assertEqual(workflow_widget.cwl[SETTINGS], {})
        self.assertIsNone(workflow_widget.vgrid)

        # Test that valid pattern is valid.
        pattern = Pattern(VALID_PATTERN_DICT)
        valid, msg = pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        args = {
            'mode': 'CWL',
            'auto_import': True,
            'export_name': 'example_name',
            'debug': False,
            'cwl_dir': 'test_dir',
            PATTERNS: {
                pattern.name: pattern
            },
            RECIPES: {
                VALID_RECIPE_DICT[NAME]: VALID_RECIPE_DICT
            },
            WORKFLOWS: {
                VALID_WORKFLOW_DICT[NAME]: VALID_WORKFLOW_DICT
            },
            STEPS: {
                VALID_STEP_DICT[NAME]: VALID_STEP_DICT
            },
            SETTINGS: {
                VALID_SETTINGS_DICT[NAME]: VALID_SETTINGS_DICT
            },
            'vgrid': 'sample_vgrid'
        }

        workflow_widget = WorkflowWidget(**args)

        # Test that provided keyword arguments are implemented correctly.
        self.assertEqual(workflow_widget.mode, CWL_MODE)
        self.assertTrue(workflow_widget.auto_import)
        self.assertEqual(workflow_widget.workflow_title, 'example_name')
        self.assertEqual(workflow_widget.cwl_import_export_dir, 'test_dir')
        self.assertEqual(len(workflow_widget.meow[PATTERNS]), 1)
        self.assertIn(pattern.name, workflow_widget.meow[PATTERNS])
        self.assertEqual(len(workflow_widget.meow[RECIPES]), 1)
        self.assertIn(VALID_RECIPE_DICT[NAME], workflow_widget.meow[RECIPES])
        self.assertEqual(len(workflow_widget.cwl[WORKFLOWS]), 1)
        self.assertIn(
            VALID_WORKFLOW_DICT[NAME], workflow_widget.cwl[WORKFLOWS]
        )
        self.assertEqual(len(workflow_widget.cwl[STEPS]), 1)
        self.assertIn(VALID_STEP_DICT[NAME], workflow_widget.cwl[STEPS])
        self.assertEqual(len(workflow_widget.cwl[SETTINGS]), 1)
        self.assertIn(VALID_SETTINGS_DICT[NAME], workflow_widget.cwl[SETTINGS])
        self.assertEqual(workflow_widget.vgrid, 'sample_vgrid')

        superfluous_args = {
            'extra': 0
        }
        # Test that unsupported keyword arguments are rejected.
        with self.assertRaises(ValueError):
            WorkflowWidget(**superfluous_args)

        # Test that invalid 'mode' is rejected.
        invalid_mode = {
            'mode': 'Unknown'
        }
        with self.assertRaises(AttributeError):
            WorkflowWidget(**invalid_mode)

        # Test that incorrect 'patterns' type is rejected.
        unformatted_pattern_args = {
            PATTERNS: 5
        }
        #
        with self.assertRaises(TypeError):
            WorkflowWidget(**unformatted_pattern_args)

        # Test that incorrect 'recipes' type is rejected.
        unformatted_recipe_args = {
            RECIPES: 5
        }
        #
        with self.assertRaises(TypeError):
            WorkflowWidget(**unformatted_recipe_args)

        # Test that incorrect 'workflows' type is rejected.
        unformatted_workflows_args = {
            WORKFLOWS: 5
        }
        #
        with self.assertRaises(TypeError):
            WorkflowWidget(**unformatted_workflows_args)

        # Test that incorrect 'steps' type is rejected.
        unformatted_step_args = {
            STEPS: 5
        }
        #
        with self.assertRaises(TypeError):
            WorkflowWidget(**unformatted_step_args)

        # Test that incorrect 'settings' type is rejected.
        unformatted_settings_args = {
            SETTINGS: 5
        }
        #
        with self.assertRaises(TypeError):
            WorkflowWidget(**unformatted_settings_args)

        # Test that incorrect 'vgrid' type is rejected.
        unformatted_vgrid_args = {
            'vgrid': 5
        }
        #
        with self.assertRaises(TypeError):
            WorkflowWidget(**unformatted_vgrid_args)

        # Test that incorrect 'auto_import' type is rejected.
        unformatted_auto_import_args = {
            'auto_import': 5
        }
        #
        with self.assertRaises(TypeError):
            WorkflowWidget(**unformatted_auto_import_args)

        # Test that incorrect 'cwl_dir' type is rejected.
        unformatted_cwl_dir_args = {
            'cwl_dir': 5
        }
        #
        with self.assertRaises(TypeError):
            WorkflowWidget(**unformatted_cwl_dir_args)

        # Test that incorrect 'export_name' type is rejected.
        unformatted_export_name_args = {
            'export_name': 5
        }
        #
        with self.assertRaises(TypeError):
            WorkflowWidget(**unformatted_export_name_args)

    def testWorkflowWidgetPatternInteractions(self):
        workflow_widget = WorkflowWidget()
        workflow_widget.construct_widget()

        # Test that no patterns at setup.
        self.assertEqual(workflow_widget.meow[PATTERNS], {})

        # Test that valid pattern dict is accepted.
        completed = \
            workflow_widget.process_new_pattern(VALID_PATTERN_FORM_VALUES)
        self.assertTrue(completed)

        # Test that two patterns cannot be added with same name
        same_name_values = copy.deepcopy(VALID_PATTERN_FORM_VALUES)
        completed = workflow_widget.process_new_pattern(same_name_values)
        self.assertFalse(completed)

        # Test that pattern with incomplete values is rejected.
        incomplete_values = copy.deepcopy(VALID_PATTERN_FORM_VALUES)
        incomplete_values.pop(TRIGGER_PATHS)
        completed = workflow_widget.process_new_pattern(incomplete_values)
        self.assertFalse(completed)

        # Test that pattern has been recorded in widget database.
        self.assertEqual(len(workflow_widget.meow[PATTERNS]), 1)
        self.assertIn(
            VALID_PATTERN_FORM_VALUES[NAME],
            workflow_widget.meow[PATTERNS]
        )

        # Test that stored pattern is valid.
        extracted_pattern = \
            workflow_widget.meow[PATTERNS][VALID_PATTERN_FORM_VALUES[NAME]]
        valid, msg = extracted_pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that baseline tester pattern is valid.
        tester_pattern = Pattern(VALID_PATTERN_DICT)
        valid, msg = tester_pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that the stored pattern has the expected values.
        self.assertTrue(tester_pattern == extracted_pattern)

        updated_pattern_values = copy.deepcopy(VALID_PATTERN_FORM_VALUES)
        updated_pattern_values[VARIABLES] = [
            {
                'Name': 'int',
                'Value': 45
            },
            {
                'Name': 'string',
                'Value': "Word"
            }
        ]

        updated_pattern_dict = copy.deepcopy(VALID_PATTERN_DICT)
        updated_pattern_dict[VARIABLES] = {
            'int': 45,
            'string': "Word"
        }

        # Test that edit completed
        complete = \
            workflow_widget.process_editing_pattern(updated_pattern_values)
        self.assertTrue(complete)

        # Test that pattern is still present after update, and that it is the
        # only pattern.
        self.assertEqual(len(workflow_widget.meow[PATTERNS]), 1)
        self.assertIn(
            VALID_PATTERN_FORM_VALUES[NAME],
            workflow_widget.meow[PATTERNS]
        )

        # Test that updated pattern is still valid.
        updated_pattern = \
            workflow_widget.meow[PATTERNS][VALID_PATTERN_FORM_VALUES[NAME]]
        valid, msg = updated_pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that baseline tester pattern is valid
        updated_tester_pattern = Pattern(updated_pattern_dict)
        valid, msg = updated_tester_pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that updated pattern has expected values.
        self.assertTrue(updated_pattern == updated_tester_pattern)

        # Test that updated pattern differs from its previous version.
        self.assertFalse(extracted_pattern == updated_pattern)

        # Test that updated base tester pattern differs from its previous
        # version.
        self.assertFalse(tester_pattern == updated_tester_pattern)

        # Test that pattern is still only pattern in widget database.
        self.assertEqual(len(workflow_widget.meow[PATTERNS]), 1)
        self.assertIn(
            VALID_PATTERN_FORM_VALUES[NAME],
            workflow_widget.meow[PATTERNS]
        )

        # Test that editing pattern with incomplete values fails.
        complete = workflow_widget.process_editing_pattern(incomplete_values)
        self.assertFalse(complete)

        # Test pattern is still valid and has not been updated by previous
        # failed update.
        self.assertEqual(len(workflow_widget.meow[PATTERNS]), 1)
        self.assertIn(
            VALID_PATTERN_FORM_VALUES[NAME],
            workflow_widget.meow[PATTERNS]
        )
        updated_pattern = \
            workflow_widget.meow[PATTERNS][VALID_PATTERN_FORM_VALUES[NAME]]
        valid, msg = updated_pattern.integrity_check()
        self.assertTrue(valid)
        self.assertEqual(msg, '')
        self.assertTrue(updated_pattern == updated_tester_pattern)
        self.assertFalse(extracted_pattern == updated_pattern)
        self.assertFalse(tester_pattern == updated_tester_pattern)

        # Test that pattern that has not been registered cannot be deleted,
        # and that patterns that are registered are not deleted instead.
        completed = workflow_widget.process_delete_pattern('unregistered_name')
        self.assertFalse(completed)
        self.assertEqual(len(workflow_widget.meow[PATTERNS]), 1)
        self.assertIn(
            VALID_PATTERN_FORM_VALUES[NAME],
            workflow_widget.meow[PATTERNS]
        )

        # Test that registered pattern can be deleted.
        completed = workflow_widget.process_delete_pattern(
            VALID_PATTERN_FORM_VALUES[NAME]
        )
        self.assertTrue(completed)
        self.assertEqual(workflow_widget.meow[PATTERNS], {})

    def testWorkflowWidgetRecipeInteractions(self):
        workflow_widget = WorkflowWidget()
        workflow_widget.construct_widget()

        # Test that no recipes at setup.
        self.assertEqual(workflow_widget.meow[RECIPES], {})

        # Test that valid recipe dict is accepted.
        completed = \
            workflow_widget.process_new_recipe(VALID_RECIPE_FORM_VALUES)
        self.assertTrue(completed)

        # Test that two recipes cannot be added with same name
        same_name_values = copy.deepcopy(VALID_RECIPE_FORM_VALUES)
        completed = workflow_widget.process_new_recipe(same_name_values)
        self.assertFalse(completed)

        sourceless_recipe = copy.deepcopy(VALID_RECIPE_FORM_VALUES)
        sourceless_recipe[SOURCE] = DOES_NOT_EXIST

        # Test that sourceless recipe is rejected.
        completed = workflow_widget.process_new_recipe(sourceless_recipe)
        self.assertFalse(completed)

        extensionless_recipe = copy.deepcopy(VALID_RECIPE_FORM_VALUES)
        extensionless_recipe[SOURCE] = EXTENSIONLESS_NOTEBOOK

        # Test that extensionless recipe is rejected.
        completed = workflow_widget.process_new_recipe(extensionless_recipe)
        self.assertFalse(completed)

        # Test that recipe with incomplete values is rejected.
        incomplete_values = copy.deepcopy(VALID_RECIPE_FORM_VALUES)
        incomplete_values.pop(SOURCE)
        completed = workflow_widget.process_new_recipe(incomplete_values)
        self.assertFalse(completed)

        # Test that recipe has been recorded in widget database.
        self.assertEqual(len(workflow_widget.meow[RECIPES]), 1)
        self.assertIn(
            VALID_RECIPE_FORM_VALUES[NAME],
            workflow_widget.meow[RECIPES]
        )

        # Test that stored recipe is valid.
        extracted_recipe = \
            workflow_widget.meow[RECIPES][VALID_RECIPE_FORM_VALUES[NAME]]
        valid, msg = is_valid_recipe_dict(extracted_recipe)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that baseline tester recipe is valid.
        tester_recipe = copy.deepcopy(VALID_RECIPE_DICT)
        valid, msg = is_valid_recipe_dict(tester_recipe)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that the stored recipe has the expected values.
        self.assertTrue(tester_recipe == extracted_recipe)

        updated_recipe_values = copy.deepcopy(VALID_RECIPE_FORM_VALUES)
        updated_recipe_values[SOURCE] = ANOTHER_NOTEBOOK

        updated_tester_recipe = copy.deepcopy(VALID_RECIPE_DICT)
        updated_tester_recipe[SOURCE] = ANOTHER_NOTEBOOK

        # Test that edit completed.
        complete = \
            workflow_widget.process_editing_recipe(updated_recipe_values)
        self.assertTrue(complete)

        # Test that recipe is still present after update, and that it is the
        # only recipe.
        self.assertEqual(len(workflow_widget.meow[RECIPES]), 1)
        self.assertIn(
            VALID_RECIPE_FORM_VALUES[NAME],
            workflow_widget.meow[RECIPES]
        )

        # Test that updated recipe is still valid.
        updated_recipe = \
            workflow_widget.meow[RECIPES][VALID_RECIPE_FORM_VALUES[NAME]]
        valid, msg = is_valid_recipe_dict(updated_recipe)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that baseline tester recipe is valid
        valid, msg = is_valid_recipe_dict(updated_tester_recipe)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that updated recipe has expected values.
        self.assertTrue(updated_recipe == updated_tester_recipe)

        # Test that updated recipe differs from its previous version.
        self.assertFalse(extracted_recipe == updated_recipe)

        # Test that updated base tester pattern differs from its previous
        # version.
        self.assertFalse(tester_recipe == updated_tester_recipe)

        # Test that recipe is still only recipe in widget database.
        self.assertEqual(len(workflow_widget.meow[RECIPES]), 1)
        self.assertIn(
            VALID_RECIPE_FORM_VALUES[NAME],
            workflow_widget.meow[RECIPES]
        )

        # Test that editing recipe with incomplete values fails.
        complete = workflow_widget.process_editing_recipe(incomplete_values)
        self.assertFalse(complete)

        # Test recipe is still valid and has not been updated by previous
        # failed update.
        self.assertEqual(len(workflow_widget.meow[RECIPES]), 1)
        self.assertIn(
            VALID_RECIPE_FORM_VALUES[NAME],
            workflow_widget.meow[RECIPES]
        )
        updated_recipe = \
            workflow_widget.meow[RECIPES][VALID_RECIPE_FORM_VALUES[NAME]]
        valid, msg = is_valid_recipe_dict(updated_recipe)
        self.assertTrue(valid)
        self.assertEqual(msg, '')
        self.assertTrue(updated_recipe == updated_tester_recipe)
        self.assertFalse(extracted_recipe == updated_recipe)
        self.assertFalse(tester_recipe == updated_tester_recipe)

        # Test that recipe that has not been registered cannot be deleted,
        # and that recipes that are registered are not deleted instead.
        completed = workflow_widget.process_delete_recipe('unregistered_name')
        self.assertFalse(completed)
        self.assertEqual(len(workflow_widget.meow[RECIPES]), 1)
        self.assertIn(
            VALID_RECIPE_FORM_VALUES[NAME],
            workflow_widget.meow[RECIPES]
        )

        # Test that registered recipe can be deleted.
        completed = workflow_widget.process_delete_recipe(
            VALID_RECIPE_FORM_VALUES[NAME]
        )
        self.assertTrue(completed)
        self.assertEqual(workflow_widget.meow[RECIPES], {})

    def testWorkflowWidgetWorkflowInteractions(self):
        workflow_widget = WorkflowWidget()
        workflow_widget.construct_widget()

        # Test that no workflows at setup.
        self.assertEqual(workflow_widget.cwl[WORKFLOWS], {})

        # Test that valid workflow dict is accepted.
        completed = \
            workflow_widget.process_new_workflow(VALID_WORKFLOW_FORM_VALUES)
        self.assertTrue(completed)

        # Test that two workflows cannot be added with same name
        same_name_values = copy.deepcopy(VALID_WORKFLOW_FORM_VALUES)
        completed = workflow_widget.process_new_workflow(same_name_values)
        self.assertFalse(completed)

        # Test that workflow with incomplete values is rejected.
        incomplete_values = copy.deepcopy(VALID_WORKFLOW_FORM_VALUES)
        incomplete_values.pop(CWL_INPUTS)
        completed = workflow_widget.process_new_workflow(incomplete_values)
        self.assertFalse(completed)

        # Test that workflow has been recorded in widget database.
        self.assertEqual(len(workflow_widget.cwl[WORKFLOWS]), 1)
        self.assertIn(
            VALID_WORKFLOW_FORM_VALUES[CWL_NAME],
            workflow_widget.cwl[WORKFLOWS]
        )

        # Test that stored workflow is valid.
        extracted_workflow = \
            workflow_widget.cwl[
                WORKFLOWS][VALID_WORKFLOW_FORM_VALUES[CWL_NAME]]
        valid, msg = is_valid_workflow_dict(extracted_workflow)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that baseline tester workflow is valid.
        tester_workflow = copy.deepcopy(VALID_WORKFLOW_DICT)
        valid, msg = is_valid_workflow_dict(tester_workflow)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that the stored workflow has the expected values.
        self.assertTrue(tester_workflow == extracted_workflow)

        updated_workflow_values = copy.deepcopy(VALID_WORKFLOW_FORM_VALUES)
        updated_workflow_values[CWL_OUTPUTS] = {}

        updated_tester_workflow = copy.deepcopy(VALID_WORKFLOW_DICT)
        updated_tester_workflow[CWL_OUTPUTS] = {}

        # Test that edit completed.
        complete = \
            workflow_widget.process_editing_workflow(updated_workflow_values)
        self.assertTrue(complete)

        # Test that workflow is still present after update, and that it is the
        # only workflow.
        self.assertEqual(len(workflow_widget.cwl[WORKFLOWS]), 1)
        self.assertIn(
            VALID_WORKFLOW_FORM_VALUES[CWL_NAME],
            workflow_widget.cwl[WORKFLOWS]
        )

        # Test that updated workflow is still valid.
        updated_workflow = \
            workflow_widget.cwl[
                WORKFLOWS][VALID_WORKFLOW_FORM_VALUES[CWL_NAME]]
        valid, msg = is_valid_workflow_dict(updated_workflow)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that baseline tester workflow is valid
        valid, msg = is_valid_workflow_dict(updated_tester_workflow)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that updated workflow has expected values.
        self.assertTrue(updated_workflow == updated_tester_workflow)

        # Test that updated workflow differs from its previous version.
        self.assertFalse(extracted_workflow == updated_workflow)

        # Test that updated base tester pattern differs from its previous
        # version.
        self.assertFalse(tester_workflow == updated_tester_workflow)

        # Test that workflow is still only workflow in widget database.
        self.assertEqual(len(workflow_widget.cwl[WORKFLOWS]), 1)
        self.assertIn(
            VALID_WORKFLOW_FORM_VALUES[CWL_NAME],
            workflow_widget.cwl[WORKFLOWS]
        )

        # Test that editing workflow with incomplete values fails.
        complete = workflow_widget.process_editing_workflow(incomplete_values)
        self.assertFalse(complete)

        # Test workflow is still valid and has not been updated by previous
        # failed update.
        self.assertEqual(len(workflow_widget.cwl[WORKFLOWS]), 1)
        self.assertIn(
            VALID_WORKFLOW_FORM_VALUES[CWL_NAME],
            workflow_widget.cwl[WORKFLOWS]
        )
        updated_workflow = \
            workflow_widget.cwl[
                WORKFLOWS][VALID_WORKFLOW_FORM_VALUES[CWL_NAME]]
        valid, msg = is_valid_workflow_dict(updated_workflow)
        self.assertTrue(valid)
        self.assertEqual(msg, '')
        self.assertTrue(updated_workflow == updated_tester_workflow)
        self.assertFalse(extracted_workflow == updated_workflow)
        self.assertFalse(tester_workflow == updated_tester_workflow)

        # Test that workflow that has not been registered cannot be deleted,
        # and that workflows that are registered are not deleted instead.
        completed = \
            workflow_widget.process_delete_workflow('unregistered_name')
        self.assertFalse(completed)
        self.assertEqual(len(workflow_widget.cwl[WORKFLOWS]), 1)
        self.assertIn(
            VALID_WORKFLOW_FORM_VALUES[CWL_NAME],
            workflow_widget.cwl[WORKFLOWS]
        )

        # Test that registered workflow can be deleted.
        completed = workflow_widget.process_delete_workflow(
            VALID_WORKFLOW_FORM_VALUES[CWL_NAME]
        )
        self.assertTrue(completed)
        self.assertEqual(workflow_widget.cwl[WORKFLOWS], {})

    def testWorkflowWidgetStepInteractions(self):
        workflow_widget = WorkflowWidget()
        workflow_widget.construct_widget()

        # Test that no steps at setup.
        self.assertEqual(workflow_widget.cwl[STEPS], {})

        # Test that valid step dict is accepted.
        completed = \
            workflow_widget.process_new_step(VALID_STEP_FORM_VALUES)
        self.assertTrue(completed)

        # Test that two steps cannot be added with same name
        same_name_values = copy.deepcopy(VALID_STEP_FORM_VALUES)
        completed = workflow_widget.process_new_step(same_name_values)
        self.assertFalse(completed)

        # Test that step with incomplete values is rejected.
        incomplete_values = copy.deepcopy(VALID_STEP_FORM_VALUES)
        incomplete_values.pop(CWL_INPUTS)
        completed = workflow_widget.process_new_step(incomplete_values)
        self.assertFalse(completed)

        # Test that step has been recorded in widget database.
        self.assertEqual(len(workflow_widget.cwl[STEPS]), 1)
        self.assertIn(
            VALID_STEP_FORM_VALUES[CWL_NAME],
            workflow_widget.cwl[STEPS]
        )

        # Test that stored step is valid.
        extracted_step = \
            workflow_widget.cwl[STEPS][
                VALID_STEP_FORM_VALUES[CWL_NAME]]
        valid, msg = is_valid_step_dict(extracted_step)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that baseline tester step is valid.
        tester_step = copy.deepcopy(VALID_STEP_DICT)
        valid, msg = is_valid_step_dict(tester_step)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that the stored step has the expected values.
        self.assertTrue(tester_step == extracted_step)

        updated_step_values = copy.deepcopy(VALID_STEP_FORM_VALUES)
        updated_step_values[CWL_OUTPUTS] = {}

        updated_tester_step = copy.deepcopy(VALID_STEP_DICT)
        updated_tester_step[CWL_OUTPUTS] = {}

        # Test that edit completed.
        complete = \
            workflow_widget.process_editing_step(updated_step_values)
        self.assertTrue(complete)

        # Test that step is still present after update, and that it is the
        # only step.
        self.assertEqual(len(workflow_widget.cwl[STEPS]), 1)
        self.assertIn(
            VALID_STEP_FORM_VALUES[CWL_NAME],
            workflow_widget.cwl[STEPS]
        )

        # Test that updated step is still valid.
        updated_step = \
            workflow_widget.cwl[STEPS][
                VALID_STEP_FORM_VALUES[CWL_NAME]]
        valid, msg = is_valid_step_dict(updated_step)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that baseline tester step is valid
        valid, msg = is_valid_step_dict(updated_tester_step)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that updated step has expected values.
        self.assertTrue(updated_step == updated_tester_step)

        # Test that updated step differs from its previous version.
        self.assertFalse(extracted_step == updated_step)

        # Test that updated base tester pattern differs from its previous
        # version.
        self.assertFalse(tester_step == updated_tester_step)

        # Test that step is still only step in widget database.
        self.assertEqual(len(workflow_widget.cwl[STEPS]), 1)
        self.assertIn(
            VALID_STEP_FORM_VALUES[CWL_NAME],
            workflow_widget.cwl[STEPS]
        )

        # Test that editing step with incomplete values fails.
        complete = workflow_widget.process_editing_step(incomplete_values)
        self.assertFalse(complete)

        # Test step is still valid and has not been updated by previous
        # failed update.
        self.assertEqual(len(workflow_widget.cwl[STEPS]), 1)
        self.assertIn(
            VALID_STEP_FORM_VALUES[CWL_NAME],
            workflow_widget.cwl[STEPS]
        )
        updated_step = \
            workflow_widget.cwl[STEPS][
                VALID_STEP_FORM_VALUES[CWL_NAME]]
        valid, msg = is_valid_step_dict(updated_step)
        self.assertTrue(valid)
        self.assertEqual(msg, '')
        self.assertTrue(updated_step == updated_tester_step)
        self.assertFalse(extracted_step == updated_step)
        self.assertFalse(tester_step == updated_tester_step)

        # Test that step that has not been registered cannot be deleted,
        # and that steps that are registered are not deleted instead.
        completed = workflow_widget.process_delete_step(
            'unregistered_name')
        self.assertFalse(completed)
        self.assertEqual(len(workflow_widget.cwl[STEPS]), 1)
        self.assertIn(
            VALID_STEP_FORM_VALUES[CWL_NAME],
            workflow_widget.cwl[STEPS]
        )

        # Test that registered step can be deleted.
        completed = workflow_widget.process_delete_step(
            VALID_STEP_FORM_VALUES[CWL_NAME]
        )
        self.assertTrue(completed)
        self.assertEqual(workflow_widget.cwl[STEPS], {})

    def testWorkflowWidgetsSettingsInteractions(self):
        workflow_widget = WorkflowWidget()
        workflow_widget.construct_widget()

        # Test that no settings at setup.
        self.assertEqual(workflow_widget.cwl[SETTINGS], {})

        # Test that valid setting dict is accepted.
        completed = \
            workflow_widget.process_new_variables(VALID_SETTINGS_FORM_VALUES)
        self.assertTrue(completed)

        # Test that two settings cannot be added with same name
        same_name_values = copy.deepcopy(VALID_SETTINGS_FORM_VALUES)
        completed = workflow_widget.process_new_variables(same_name_values)
        self.assertFalse(completed)

        # Test that setting with incomplete values is rejected.
        incomplete_values = copy.deepcopy(VALID_SETTINGS_FORM_VALUES)
        incomplete_values.pop(CWL_VARIABLES)
        completed = workflow_widget.process_new_variables(incomplete_values)
        self.assertFalse(completed)

        # Test that setting has been recorded in widget database.
        self.assertEqual(len(workflow_widget.cwl[SETTINGS]), 1)
        self.assertIn(
            VALID_SETTINGS_FORM_VALUES[CWL_NAME],
            workflow_widget.cwl[SETTINGS]
        )

        # Test that stored setting is valid.
        extracted_setting = \
            workflow_widget.cwl[SETTINGS][
                VALID_SETTINGS_FORM_VALUES[CWL_NAME]]
        valid, msg = is_valid_setting_dict(extracted_setting)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that baseline tester setting is valid.
        tester_setting = copy.deepcopy(VALID_SETTINGS_DICT)
        valid, msg = is_valid_setting_dict(tester_setting)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that the stored setting has the expected values.
        self.assertTrue(tester_setting == extracted_setting)

        updated_setting_values = copy.deepcopy(VALID_SETTINGS_FORM_VALUES)
        updated_setting_values[CWL_VARIABLES] = {}

        updated_tester_setting = copy.deepcopy(VALID_SETTINGS_DICT)
        updated_tester_setting[CWL_VARIABLES] = {}

        # Test that edit completed.
        complete = \
            workflow_widget.process_editing_variables(updated_setting_values)
        self.assertTrue(complete)

        # Test that setting is still present after update, and that it is the
        # only setting.
        self.assertEqual(len(workflow_widget.cwl[SETTINGS]), 1)
        self.assertIn(
            VALID_SETTINGS_FORM_VALUES[CWL_NAME],
            workflow_widget.cwl[SETTINGS]
        )

        # Test that updated setting is still valid.
        updated_setting = \
            workflow_widget.cwl[SETTINGS][
                VALID_SETTINGS_FORM_VALUES[CWL_NAME]]
        valid, msg = is_valid_setting_dict(updated_setting)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that baseline tester setting is valid
        valid, msg = is_valid_setting_dict(updated_tester_setting)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

        # Test that updated setting has expected values.
        self.assertTrue(updated_setting == updated_tester_setting)

        # Test that updated setting differs from its previous version.
        self.assertFalse(extracted_setting == updated_setting)

        # Test that updated base tester pattern differs from its previous
        # version.
        self.assertFalse(tester_setting == updated_tester_setting)

        # Test that setting is still only setting in widget database.
        self.assertEqual(len(workflow_widget.cwl[SETTINGS]), 1)
        self.assertIn(
            VALID_SETTINGS_FORM_VALUES[CWL_NAME],
            workflow_widget.cwl[SETTINGS]
        )

        # Test that editing setting with incomplete values fails.
        complete = workflow_widget.process_editing_variables(incomplete_values)
        self.assertFalse(complete)

        # Test setting is still valid and has not been updated by previous
        # failed update.
        self.assertEqual(len(workflow_widget.cwl[SETTINGS]), 1)
        self.assertIn(
            VALID_SETTINGS_FORM_VALUES[CWL_NAME],
            workflow_widget.cwl[SETTINGS]
        )
        updated_setting = \
            workflow_widget.cwl[SETTINGS][
                VALID_SETTINGS_FORM_VALUES[CWL_NAME]]
        valid, msg = is_valid_setting_dict(updated_setting)
        self.assertTrue(valid)
        self.assertEqual(msg, '')
        self.assertTrue(updated_setting == updated_tester_setting)
        self.assertFalse(extracted_setting == updated_setting)
        self.assertFalse(tester_setting == updated_tester_setting)

        # Test that setting that has not been registered cannot be deleted,
        # and that settings that are registered are not deleted instead.
        completed = workflow_widget.process_delete_variables(
            'unregistered_name')
        self.assertFalse(completed)
        self.assertEqual(len(workflow_widget.cwl[SETTINGS]), 1)
        self.assertIn(
            VALID_SETTINGS_FORM_VALUES[CWL_NAME],
            workflow_widget.cwl[SETTINGS]
        )

        # Test that registered setting can be deleted.
        completed = workflow_widget.process_delete_variables(
            VALID_SETTINGS_FORM_VALUES[CWL_NAME]
        )
        self.assertTrue(completed)
        self.assertEqual(workflow_widget.cwl[SETTINGS], {})

    def testMEOWToCWLIndividuals(self):
        pass
        # workflow_widget = WorkflowWidget()
        # workflow_widget.construct_widget()
        #
        # # Test that valid pattern dict is accepted.
        # completed = \
        #     workflow_widget.process_new_pattern(VALID_PATTERN_FORM_VALUES)
        # self.assertTrue(completed)
        #
        # # Test that only pattern present is one just created.
        # self.assertEqual(len(workflow_widget.meow[PATTERNS]), 1)
        # self.assertIn(
        #     VALID_PATTERN_FORM_VALUES[NAME],
        #     workflow_widget.meow[PATTERNS]
        # )
        #
        # expected_feedback = {
        #     'steps': {
        #         'step_1': {
        #             'arguments': [],
        #             'baseCommand': 'papermill',
        #             'class': 'CommandLineTool',
        #             'cwlVersion': 'v1.0',
        #             'hints': {},
        #             'inputs': {
        #                 'notebook': {
        #                     'inputBinding': {
        #                         'position': 1
        #                     },
        #                     'type': 'File'
        #                 },
        #                 'outfile_1_key': {
        #                     'inputBinding': {
        #                         'position': 7,
        #                         'prefix': '-p'
        #                     },
        #                     'type': 'string'
        #                 },
        #                 'outfile_1_value': {
        #                     'inputBinding': {
        #                         'position': 8
        #                     },
        #                     'type': 'string'
        #                 },
        #                 'outfile_2_key': {
        #                     'inputBinding': {
        #                         'position': 9,
        #                         'prefix': '-p'
        #                     },
        #                     'type': 'string'
        #                 },
        #                 'outfile_2_value': {
        #                     'inputBinding': {
        #                         'position': 10
        #                     },
        #                     'type': 'string'
        #                 },
        #                 'result': {
        #                     'inputBinding': {
        #                         'position': 2
        #                     },
        #                     'type': 'string'
        #                 },
        #                 'trigger_file_name_key': {
        #                     'inputBinding': {
        #                         'position': 5,
        #                         'prefix': '-p'
        #                     },
        #                     'type': 'string'
        #                 },
        #                 'trigger_file_name_value': {
        #                     'inputBinding': {
        #                         'position': 6
        #                     },
        #                     'type': 'File'
        #                 }
        #             },
        #             'name': 'step_1',
        #             'outputs': {
        #                 'output_0': {
        #                     'outputBinding': {
        #                         'glob': '$(inputs.trigger_file_name_value)'
        #                     },
        #                     'type': 'File'
        #                 },
        #                 'output_1': {
        #                     'outputBinding': {
        #                         'glob': '$(inputs.wf_job)'
        #                     },
        #                     'type': 'File'
        #                 },
        #                 'output_2': {
        #                     'outputBinding': {
        #                         'glob': '$(inputs.outfile_1_value)'
        #                     },
        #                     'type': 'File'
        #                 },
        #                 'output_3': {
        #                     'outputBinding': {
        #                         'glob': '$(inputs.outfile_2_value)'
        #                     },
        #                     'type': 'File'
        #                 }
        #             },
        #             'requirements': {},
        #             'stdout': ''
        #         }
        #     },
        #     'variables': {
        #         'workflow': {
        #             'arguments': {
        #                 '1_notebook': {
        #                     'class': 'File',
        #                     'path': 'PLACEHOLDER'
        #                 },
        #                 '1_outfile_1_key': 'outfile_1',
        #                 '1_outfile_1_value': 'out.path',
        #                 '1_outfile_2_key': 'outfile_2',
        #                 '1_outfile_2_value': 'out.path',
        #                 '1_result': 'notebook/output.path',
        #                 '1_trigger_file_name_key': 'trigger_file_name',
        #                 '1_trigger_file_name_value': {
        #                     'class': 'File',
        #                     'path': 'literal.path'
        #                 }
        #             },
        #             'name': 'workflow'
        #         }
        #     },
        #     'workflows': {
        #         'workflow': {
        #             'class': 'Workflow',
        #             'cwlVersion': 'v1.0',
        #             'inputs': {
        #                 '1_notebook': 'File',
        #                 '1_outfile_1_key': 'string',
        #                 '1_outfile_1_value': 'string',
        #                 '1_outfile_2_key': 'string',
        #                 '1_outfile_2_value': 'string',
        #                 '1_result': 'string',
        #                 '1_trigger_file_name_key': 'string',
        #                 '1_trigger_file_name_value': 'File'
        #             },
        #             'name': 'workflow',
        #             'outputs': {
        #                 'output_step_1_output_0': {
        #                     'outputSource': 'step_1/output_0',
        #                     'type': 'File'
        #                 },
        #                 'output_step_1_output_1': {
        #                     'outputSource': 'step_1/output_1',
        #                     'type': 'File'
        #                 },
        #                 'output_step_1_output_2': {
        #                     'outputSource': 'step_1/output_2',
        #                     'type': 'File'
        #                 },
        #                 'output_step_1_output_3': {
        #                     'outputSource': 'step_1/output_3',
        #                     'type': 'File'
        #                 }
        #             },
        #             'requirements': {},
        #             'steps': {
        #                 'step_1': {
        #                     'in': {
        #                         'notebook': '1_notebook',
        #                         'outfile_1_key': '1_outfile_1_key',
        #                         'outfile_1_value': '1_outfile_1_value',
        #                         'outfile_2_key': '1_outfile_2_key',
        #                         'outfile_2_value': '1_outfile_2_value',
        #                         'result': '1_result',
        #                         'trigger_file_name_key':
        #                             '1_trigger_file_name_key',
        #                         'trigger_file_name_value':
        #                             '1_trigger_file_name_value'
        #                     },
        #                     'out': '[output_0, output_1, output_2, output_3]',
        #                     'run': 'step_1.cwl'
        #                 }
        #             }
        #         }
        #     }
        # }
        #
        # # Test that MEOW to CWL conversion has completed without issue.
        # valid, cwl = workflow_widget.meow_to_cwl()
        # self.assertTrue(valid)
        # self.assertTrue(cwl == expected_feedback)
        #
        # # Test that workflow is valid
        # for workflow in cwl[WORKFLOWS].values():
        #     valid, msg = is_valid_workflow_dict(workflow)
        #     self.assertTrue(valid)
        #     self.assertEqual(msg, '')
        #
        # # Test that step is valid
        # for step in cwl[STEPS].values():
        #     valid, msg = is_valid_step_dict(step)
        #     self.assertTrue(valid)
        #     self.assertEqual(msg, '')
        #
        # # Test that settings are valid
        # for setting in cwl[SETTINGS].values():
        #     valid, msg = is_valid_setting_dict(setting)
        #     self.assertTrue(valid)
        #     self.assertEqual(msg, '')
        #
        # # Test that valid recipe dict is accepted.
        # completed = \
        #     workflow_widget.process_new_recipe(VALID_RECIPE_FORM_VALUES)
        # self.assertTrue(completed)
        #
        # expected_feedback['variables']['workflow']['arguments'][
        #     '1_notebook']['path'] = VALID_RECIPE_FORM_VALUES[SOURCE]
        #
        # # Test that MEOW to CWL conversion with relevant recipe has completed
        # # without issue.
        # valid, cwl = workflow_widget.meow_to_cwl()
        # self.assertTrue(valid)
        # self.assertTrue(cwl == expected_feedback)

    def testMEOWToCWLWorkflows(self):
        pass

    def testCWLToMEOW(self):
        pass
        # analysis_step_dict = {
        #     CWL_NAME: 'data_analysis',
        #     CWL_CWL_VERSION: 'v1.0',
        #     CWL_CLASS: 'CommandLineTool',
        #     CWL_BASE_COMMAND: 'papermill',
        #     CWL_STDOUT: '',
        #     CWL_INPUTS: {
        #         'notebook': {
        #             'inputBinding': {
        #                 'position': 1
        #             },
        #             'type': 'File'
        #         },
        #         'result': {
        #             'inputBinding': {
        #                 'position': 2
        #             },
        #             'type': 'string'
        #         },
        #         'yaml_file': {
        #             'inputBinding': {
        #                 'prefix': '-f',
        #                 'position': 3
        #             },
        #             'type': 'File'
        #         },
        #         'dssc_file': {
        #             'type': 'File'
        #         },
        #         'interim_yaml_title': {
        #             'type': 'string'
        #         }
        #     },
        #     CWL_OUTPUTS: {
        #         'result_notebook': {
        #             'outputBinding': {
        #                 'glob': '$(inputs.result)'
        #             },
        #             'type': 'File'
        #         },
        #         'interim_yaml': {
        #             'outputBinding': {
        #                 'glob': '$(inputs.interim_yaml_title)'
        #             },
        #             'type': 'File'
        #         }
        #     },
        #     CWL_ARGUMENTS: [],
        #     CWL_REQUIREMENTS: {
        #         'InitialWorkDirRequirement': {
        #             'listing': '- $(inputs.dssc_file)'
        #         }
        #     },
        #     CWL_HINTS: {}
        # }
        # plotting_step_dict = {
        #     CWL_NAME: 'data_plotting',
        #     CWL_CWL_VERSION: 'v1.0',
        #     CWL_CLASS: 'CommandLineTool',
        #     CWL_BASE_COMMAND: 'papermill',
        #     CWL_STDOUT: '',
        #     CWL_INPUTS: {
        #         'notebook': {
        #             'inputBinding': {
        #                 'position': 1
        #             },
        #             'type': 'File'
        #         },
        #         'result': {
        #             'inputBinding': {
        #                 'position': 2
        #             },
        #             'type': 'string'
        #         },
        #         'yaml_file': {
        #             'inputBinding': {
        #                 'prefix': '-f',
        #                 'position': 3
        #             },
        #             'type': 'File'
        #         }
        #     },
        #     CWL_OUTPUTS: {
        #         'result_notebook': {
        #             'outputBinding': {
        #                 'glob': '$(inputs.result)'
        #             },
        #             'type': 'File'
        #         }
        #     },
        #     CWL_ARGUMENTS: [],
        #     CWL_REQUIREMENTS: {},
        #     CWL_HINTS: {}
        # }
        # workflow_dict = {
        #     CWL_NAME: DEFAULT_WORKFLOW_TITLE,
        #     CWL_CWL_VERSION: 'v1.0',
        #     CWL_CLASS: 'Workflow',
        #     CWL_INPUTS: {
        #         'analysis_notebook': 'File',
        #         'analysis_result': 'string',
        #         'analysis_yaml_file': 'File',
        #         'analysis_dssc': 'File',
        #         'analysis_interim_yaml': 'string',
        #         'plotting_notebook': 'File',
        #         'plotting_result': 'string',
        #     },
        #     CWL_OUTPUTS: {
        #         'final_plot': {
        #             'type': 'File',
        #             'outputSource': 'plot/result_notebook'
        #         }
        #     },
        #     CWL_STEPS: {
        #         'analysis': {
        #             'run': 'data_analysis.cwl',
        #             'in': {
        #                 'notebook': 'analysis_notebook',
        #                 'result': 'analysis_result',
        #                 'yaml_file': 'analysis_yaml_file',
        #                 'dssc_file': 'analysis_dssc',
        #                 'interim_yaml_title': 'analysis_interim_yaml'
        #             },
        #             'out': '[result_notebook, interim_yaml]'
        #         },
        #         'plot': {
        #             'run': 'data_plotting.cwl',
        #             'in': {
        #                 'notebook': 'plotting_notebook',
        #                 'result': 'plotting_result',
        #                 'yaml_file': 'analysis/interim_yaml'
        #             },
        #             'out': '[result_notebook]'
        #         }
        #     },
        #     CWL_REQUIREMENTS: {}
        # }
        # settings_dict = {
        #     CWL_NAME: DEFAULT_WORKFLOW_TITLE,
        #     CWL_VARIABLES: {
        #         'analysis_notebook': {
        #             'class': 'File',
        #             'path': 'data_analysis.ipynb'
        #         },
        #         'analysis_result': 'data_analysis_result.ipynb',
        #         'analysis_yaml_file': {
        #             'class': 'File',
        #             'path': 'initial_params.yaml'
        #         },
        #         'analysis_dssc': {
        #             'class': 'File',
        #             'path': 'dssc.py'
        #         },
        #         'analysis_interim_yaml': 'interim.yaml',
        #         'plotting_notebook': {
        #             'class': 'File',
        #             'path': 'data_plotting.ipynb'
        #         },
        #         'plotting_result': 'data_plotting_result.ipynb'
        #     }
        # }
        #
        # args = {
        #     WORKFLOWS: {
        #         workflow_dict[CWL_NAME]: workflow_dict
        #     },
        #     STEPS: {
        #         analysis_step_dict[CWL_NAME]: analysis_step_dict,
        #         plotting_step_dict[CWL_NAME]: plotting_step_dict
        #     },
        #     SETTINGS: {
        #         settings_dict[CWL_NAME]: settings_dict
        #     },
        # }
        #
        # workflow_widget = WorkflowWidget(**args)
        # workflow_widget.construct_widget()
        #
        # # Test that args have imported correctly
        # self.assertEqual(len(workflow_widget.cwl[WORKFLOWS]), 1)
        # self.assertIn(workflow_dict[CWL_NAME], workflow_widget.cwl[WORKFLOWS])
        # self.assertEqual(len(workflow_widget.cwl[STEPS]), 2)
        # self.assertIn(analysis_step_dict[CWL_NAME], workflow_widget.cwl[STEPS])
        # self.assertIn(plotting_step_dict[CWL_NAME], workflow_widget.cwl[STEPS])
        # self.assertEqual(len(workflow_widget.cwl[SETTINGS]), 1)
        # self.assertIn(settings_dict[CWL_NAME], workflow_widget.cwl[SETTINGS])
        #
        # # Test that conversion is successful
        # valid, meow = workflow_widget.cwl_to_meow()
        # print(meow)
        # self.assertTrue(valid)
        #
        # # Test that valid MEOW objects are produced.
        # valid, msg = check_patterns_dict(meow[PATTERNS])
        # self.assertTrue(valid)
        # self.assertEqual(msg, '')
        # valid, msg = check_recipes_dict(meow[RECIPES])
        # self.assertTrue(valid)
        # self.assertEqual(msg, '')

    # TODO come back to this once cwl testing done.
    def testWorkflowWidgetMeowButtonEnabling(self):
        workflow_widget = WorkflowWidget()
        workflow_widget.construct_widget()

        # Test that no patterns and recipes at start.
        self.assertEqual(workflow_widget.meow[PATTERNS], {})
        self.assertEqual(workflow_widget.meow[RECIPES], {})

        for key, button in workflow_widget.button_elements.items():
            if key == MEOW_NEW_PATTERN_BUTTON:
                # Test that new pattern button is enabled.
                self.assertFalse(button.disabled)
            if key == MEOW_EDIT_PATTERN_BUTTON:
                # Test that edit pattern button is disabled.
                self.assertTrue(button.disabled)
            if key == MEOW_NEW_RECIPE_BUTTON:
                # Test that new recipe button is enabled.
                self.assertFalse(button.disabled)
            if key == MEOW_EDIT_RECIPE_BUTTON:
                # Test that edit recipe button is disabled.
                self.assertTrue(button.disabled)
            if key == MEOW_IMPORT_CWL_BUTTON:
                # Test that cwl import button is disabled.
                self.assertTrue(button.disabled)
            if key == MEOW_IMPORT_VGRID_BUTTON:
                # Test that vgrid import button is disabled.
                self.assertTrue(button.disabled)
            if key == MEOW_EXPORT_VGRID_BUTTON:
                # Test that vgrid export button is disabled.
                self.assertTrue(button.disabled)

        # Test that valid pattern dict is accepted.
        completed = \
            workflow_widget.process_new_pattern(VALID_PATTERN_FORM_VALUES)
        self.assertTrue(completed)
        self.assertEqual(len(workflow_widget.meow[PATTERNS]), 1)

        # Test that edit pattern button is now enabled.
        self.assertFalse(
            workflow_widget.button_elements[MEOW_EDIT_PATTERN_BUTTON].disabled
        )

        # Test that pattern is now deleted.
        completed = workflow_widget.process_delete_pattern(
            VALID_PATTERN_FORM_VALUES[NAME]
        )
        self.assertTrue(completed)
        self.assertEqual(workflow_widget.meow[PATTERNS], {})

        # Test that edit pattern button is disabled.
        self.assertTrue(
            workflow_widget.button_elements[MEOW_EDIT_PATTERN_BUTTON].disabled
        )

        # Test that valid recipe dict is accepted.
        completed = \
            workflow_widget.process_new_recipe(VALID_RECIPE_FORM_VALUES)
        self.assertTrue(completed)
        self.assertEqual(len(workflow_widget.meow[RECIPES]), 1)

        # Test that edit pattern button is now enabled.
        self.assertFalse(
            workflow_widget.button_elements[MEOW_EDIT_RECIPE_BUTTON].disabled
        )

        # Test that recipe is now deleted.
        completed = workflow_widget.process_delete_recipe(
            VALID_RECIPE_FORM_VALUES[NAME]
        )
        self.assertTrue(completed)
        self.assertEqual(workflow_widget.meow[RECIPES], {})

        # Test that edit recipe button is disabled.
        self.assertTrue(
            workflow_widget.button_elements[MEOW_EDIT_RECIPE_BUTTON].disabled
        )

        workflow_widget = WorkflowWidget(vgrid='vgrid')
        workflow_widget.construct_widget()

        # Test that vgrid button are enabled when vgrid provided.
        self.assertFalse(
            workflow_widget.button_elements[MEOW_IMPORT_VGRID_BUTTON].disabled
        )
        self.assertFalse(
            workflow_widget.button_elements[MEOW_EXPORT_VGRID_BUTTON].disabled
        )

    def testParamSweepCounting(self):

        expected_sweep = {
            SWEEP_START: 1,
            SWEEP_STOP: 10,
            SWEEP_JUMP: 1
        }
        sweep = parameter_sweep_entry('test', 1, 10, 1)

        self.assertEqual(expected_sweep, sweep)

        expected_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        values = get_parameter_sweep_values(sweep)

        self.assertEqual(expected_values, values)

    def testEnvironmentsLocal(self):
        valid_a = {
            'local': {
                'dependencies': [
                    'watchdog',
                    'mig_meow'
                ]
            }
        }

        invalid_a = {
            'local': {
                'dependencies': [
                    'watchdog',
                    'mig_meow'
                ],
                'extra': ''
            }
        }

        status, feedback = is_valid_environments_dict(valid_a, strict=False)
        self.assertTrue(status)
        self.assertEqual(feedback, '')

        status, feedback = is_valid_environments_dict(valid_a, strict=True)
        self.assertTrue(status)
        self.assertEqual(feedback, '')

        status, feedback = is_valid_environments_dict(invalid_a, strict=False)
        self.assertTrue(status)
        self.assertEqual(feedback, '')

        status, feedback = is_valid_environments_dict(invalid_a, strict=True)
        self.assertFalse(status)
        self.assertEqual(feedback, "Unknown dependency 'extra'. Valid are: "
                                   "%s" % VALID_ENVIRONMENTS_LOCAL)

        invalid_b = {
            'local': {
                'dependencies': [
                    'watchdog',
                    1
                ]
            }
        }

        self.assertRaises(TypeError, is_valid_environments_dict, invalid_b)

    def testEnvironmentsMiG(self):
        valid_a = {
            'mig': {
                'nodes': '1',
                'cpu cores': '1',
                'wall time': '1',
                'memory': '1',
                'disks': '1',
                'cpu-architecture': '1',
                'fill': [
                    'CPUCOUNT'
                ],
                'environment variables': [
                    'VAR=42'
                ],
                'notification': [
                    'email: SETTINGS'
                ],
                'retries': '1',
                'runtime environments': [
                    'PAPERMILL'
                ]
            }
        }

        invalid_a = {
            'mig': {
                'nodes': '1',
                'cpu cores': '1',
                'wall time': '1',
                'memory': '1',
                'disks': '1',
                'cpu-architecture': '1',
                'fill': [
                    'CPUCOUNT'
                ],
                'environment variables': [
                    'VAR=42'
                ],
                'notification': [
                    'email: SETTINGS'
                ],
                'retries': '1',
                'runtime environments': [
                    'PAPERMILL'
                ],
                'extra': ''
            }
        }

        status, feedback = is_valid_environments_dict(valid_a, strict=False)
        self.assertTrue(status)
        self.assertEqual(feedback, '')

        status, feedback = is_valid_environments_dict(valid_a, strict=True)
        self.assertTrue(status)
        self.assertEqual(feedback, '')

        status, feedback = is_valid_environments_dict(invalid_a, strict=False)
        self.assertTrue(status)
        self.assertEqual(feedback, '')

        status, feedback = is_valid_environments_dict(invalid_a, strict=True)
        self.assertFalse(status)
        self.assertEqual(feedback, "Unknown dependency 'extra'. Valid are: "
                                   "%s" % VALID_ENVIRONMENTS_MIG)

        invalid_nodes = {
            'mig': {
                'nodes': 1
            }
        }

        status, feedback = is_valid_environments_dict(invalid_nodes)
        self.assertFalse(status)

        invalid_cores = {
            'mig': {
                'cpu cores': 1
            }
        }

        status, feedback = is_valid_environments_dict(invalid_cores)
        self.assertFalse(status)

        invalid_time = {
            'mig': {
                'wall time': 1
            }
        }

        status, feedback = is_valid_environments_dict(invalid_time)
        self.assertFalse(status)

        invalid_memory = {
            'mig': {
                'memory': 1
            }
        }

        status, feedback = is_valid_environments_dict(invalid_memory)
        self.assertFalse(status)

        invalid_disks = {
            'mig': {
                'disks': 1
            }
        }

        status, feedback = is_valid_environments_dict(invalid_disks)
        self.assertFalse(status)

        invalid_architecture = {
            'mig': {
                'cpu-architecture': 1,
            }
        }

        status, feedback = is_valid_environments_dict(invalid_architecture)
        self.assertFalse(status)

        invalid_fill = {
            'mig': {
                'fill': [
                    'EVERYTHING'
                ]
            }
        }

        status, feedback = is_valid_environments_dict(invalid_fill)
        self.assertFalse(status)

        invalid_env_a = {
            'mig': {
                'environment variables': 'VAR=42'
            }
        }

        status, feedback = is_valid_environments_dict(invalid_env_a)
        self.assertFalse(status)

        invalid_env_b = {
            'mig': {
                'environment variables': [
                    'VAR==42'
                ]
            }
        }

        status, feedback = is_valid_environments_dict(invalid_env_b)
        self.assertFalse(status)

        invalid_env_c = {
            'mig': {
                'environment variables': [
                    'VAR42'
                ]
            }
        }

        status, feedback = is_valid_environments_dict(invalid_env_c)
        self.assertFalse(status)

        invalid_env_d = {
            'mig': {
                'environment variables': [
                    'VAR42='
                ]
            }
        }

        status, feedback = is_valid_environments_dict(invalid_env_d)
        self.assertFalse(status)

        invalid_env_e = {
            'mig': {
                'environment variables': [
                    '=VAR42'
                ]
            }
        }

        status, feedback = is_valid_environments_dict(invalid_env_e)
        self.assertFalse(status)

        invalid_notification_a = {
            'mig': {
                'notification': 'email: SETTINGS'
            }
        }

        status, feedback = is_valid_environments_dict(invalid_notification_a)
        self.assertFalse(status)

        invalid_notification_b = {
            'mig': {
                'notification': [
                    'email::SETTINGS'
                ]
            }
        }

        status, feedback = is_valid_environments_dict(invalid_notification_b)
        self.assertFalse(status)

        invalid_notification_c = {
            'mig': {
                'notification': [
                    'emailSETTINGS'
                ]
            }
        }

        status, feedback = is_valid_environments_dict(invalid_notification_c)
        self.assertFalse(status)

        invalid_notification_d = {
            'mig': {
                'notification': [
                    ':emailSETTINGS'
                ]
            }
        }

        status, feedback = is_valid_environments_dict(invalid_notification_d)
        self.assertFalse(status)

        invalid_notification_e = {
            'mig': {
                'notification': [
                    'emailSETTINGS:'
                ]
            }
        }

        status, feedback = is_valid_environments_dict(invalid_notification_e)
        self.assertFalse(status)

        invalid_retries = {
            'mig': {
                'retries': 1,
            }
        }

        status, feedback = is_valid_environments_dict(invalid_retries)
        self.assertFalse(status)

        invalid_runtime = {
            'mig': {
                'runtime environments': 'PAPERMILL'
            }
        }

        status, feedback = is_valid_environments_dict(invalid_runtime)
        self.assertFalse(status)

    def testRecipeEnvironmentsLocal(self):
        notebook_dict = nbformat.read(EMPTY_NOTEBOOK, nbformat.NO_CONVERT)

        recipe_dict = create_recipe_dict(
            notebook_dict,
            VALID_RECIPE_DICT[NAME],
            EMPTY_NOTEBOOK,
            environments={
                'local': {
                    'dependencies': [
                        'watchdog',
                        'mig_meow'
                    ]
                }
            }
        )

        expanded_valid_recipe_dict = copy.deepcopy(VALID_RECIPE_DICT)
        expanded_valid_recipe_dict[ENVIRONMENTS] = {
            'local': {
                'dependencies': [
                    'watchdog',
                    'mig_meow'
                ]
            }
        }

        print(recipe_dict)
        print(expanded_valid_recipe_dict)

        # Test that created recipe has expected values.
        self.assertTrue(recipe_dict == expanded_valid_recipe_dict)

        # Test that created recipe is valid
        valid, msg = is_valid_recipe_dict(recipe_dict)
        self.assertTrue(valid)
        self.assertEqual(msg, '')

    def testRecipeEnvironmentsMiG(self):
        notebook_dict = nbformat.read(EMPTY_NOTEBOOK, nbformat.NO_CONVERT)

        recipe_dict = create_recipe_dict(
            notebook_dict,
            VALID_RECIPE_DICT[NAME],
            EMPTY_NOTEBOOK,
            environments={
                'mig': {
                    'nodes': '1',
                    'cpu cores': '1',
                    'wall time': '1',
                    'memory': '1',
                    'disks': '1',
                    'cpu-architecture': '1',
                    'fill': [
                        'CPUCOUNT'
                    ],
                    'environment variables': [
                        'VAR=42'
                    ],
                    'notification': [
                        'email: SETTINGS'
                    ],
                    'retries': '1',
                    'runtime environments': [
                        'PAPERMILL'
                    ]
                }
            }
        )

        expanded_valid_recipe_dict = copy.deepcopy(VALID_RECIPE_DICT)
        expanded_valid_recipe_dict[ENVIRONMENTS] = {
            'mig': {
                'nodes': '1',
                'cpu cores': '1',
                'wall time': '1',
                'memory': '1',
                'disks': '1',
                'cpu-architecture': '1',
                'fill': [
                    'CPUCOUNT'
                ],
                'environment variables': [
                    'VAR=42'
                ],
                'notification': [
                    'email: SETTINGS'
                ],
                'retries': '1',
                'runtime environments': [
                    'PAPERMILL'
                ]
            }
        }

        # Test that created recipe has expected values.
        self.assertTrue(recipe_dict == expanded_valid_recipe_dict)

        # Test that created recipe is valid
        valid, msg = is_valid_recipe_dict(recipe_dict)
        self.assertTrue(valid)
        self.assertEqual(msg, '')
